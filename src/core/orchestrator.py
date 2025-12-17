from typing import Dict, Any, List
import os
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any
import yaml  # make sure PyYAML is installed: pip install pyyaml
from src.core.brain import OrchestratorBrain
from src.core.model_client import ModelClient
from src.core.tool_base import ToolRegistry
from src.core.agent_base import Agent
from src.tools.filesystem_tool import FilesystemTool
from src.tools.code_runner_tool import CodeRunnerTool
from src.tools.test_runner_tool import TestRunnerTool
from src.memory.sql_store import TaskLog
from src.core.agent_factory import AgentFactory
from src.projects.doc_extractor.doc_service import DocumentExtractorService




class Orchestrator:
    """
    Orchestrator v6:

    - Model backend
    - Tools (filesystem, code_runner, test_runner)
    - Agents (via YAML + AgentFactory):
        * planner
        * code_writer
        * runner
        * debugger
        * tester
        * triad engineers (sentinel_engineer, storm_engineer, creator_engineer)
        * chief_engineer
    - Capabilities:
        * generate single file
        * generate + run + auto-debug single file
        * triad-based single-file generation
        * plan + build multi-file project
        * run project tests (pytest)
        * meta-project build:
            - ask triad engineers for meta-plan (agents + files + deps)
            - chief merges meta-plans
            - apply meta-plan:
                - create/merge agents in config/agents.yaml
                - write requirements.txt
                - generate all project files
    """

    def __init__(self, workspace_dir: str = "."):
        self.logger = logging.getLogger(__name__)
        self.workspace_dir = workspace_dir

        # Model backend
        backend = os.getenv("AGENTFORGE_MODEL_BACKEND", "ollama_cloud")
        default_model = os.getenv("AGENTFORGE_MODEL_NAME", "gpt-oss:20b")

        self.model_client = ModelClient(
            backend=backend,
            default_model=default_model,
        )

        # Tools
        self.tool_registry = ToolRegistry()
        self.tool_registry.register(FilesystemTool(base_dir=self.workspace_dir))
        self.tool_registry.register(CodeRunnerTool(base_dir=self.workspace_dir))
        self.tool_registry.register(TestRunnerTool(base_dir=self.workspace_dir))

        # Memory / logs
        memory_db_path = os.path.join(self.workspace_dir, "data", "memory.db")
        self.task_log = TaskLog(db_path=memory_db_path)

        memory_json_path = os.path.join(self.workspace_dir, "data", "brain_memory.json")
        self.brain = OrchestratorBrain(
            model_client=self.model_client,
            memory_path=memory_json_path,
        )

        # Agents
        config_path = os.path.join(self.workspace_dir, "config", "agents.yaml")
        self.agents_config_path = config_path
        self.agent_factory = AgentFactory(
            model_client=self.model_client,
            tool_registry=self.tool_registry,
            config_path=config_path,
        )

        # 👇 Safely initialize doc extractor service
        try:
            self.doc_service = DocumentExtractorService(
                model_client=self.model_client,
                brain=self.brain,
                logger=self.logger,
            )
        except Exception as e:
            # Don't let one tool kill the whole API
            self.logger.exception("Failed to init DocumentExtractorService: %s", e)
            self.doc_service = None



    # ---------- Agent helpers (thin wrappers over AgentFactory) ----------

    def _make_planner_agent(self) -> Agent:
        return self.agent_factory.get("planner")

    def _make_code_writer_agent(self) -> Agent:
        return self.agent_factory.get("code_writer")

    def _make_runner_agent(self) -> Agent:
        return self.agent_factory.get("runner")

    def _make_debugger_agent(self) -> Agent:
        return self.agent_factory.get("debugger")

    def _make_tester_agent(self) -> Agent:
        return self.agent_factory.get("tester")

    def _make_sentinel_engineer(self) -> Agent:
        return self.agent_factory.get("sentinel_engineer")

    def _make_storm_engineer(self) -> Agent:
        return self.agent_factory.get("storm_engineer")

    def _make_creator_engineer(self) -> Agent:
        return self.agent_factory.get("creator_engineer")

    def _make_chief_engineer(self) -> Agent:
        return self.agent_factory.get("chief_engineer")
    def run_document_extractor(self, file_path: str) -> Dict[str, Any]:
        if self.doc_service is None:
            raise RuntimeError(
                "Document extractor service is not available; "
                "check server logs for initialization errors."
            )
        return self.doc_service.llm_classify_and_extract(file_path)

    # ---------- Helpers ----------

    def _strip_code_fences(self, text: str) -> str:
        """
        If the model returns ```python ... ``` style blocks,
        extract just the inner code. Otherwise, return as-is.
        """
        if "```" not in text:
            return text

        parts = text.split("```")
        if len(parts) < 3:
            # something weird, just return original
            return text

        # The content between the first and second ``` is usually the code block.
        code_block = parts[1]

        # Remove language tag like 'python' on the first line if present
        if "\n" in code_block:
            first_line, rest = code_block.split("\n", 1)
            if first_line.strip().lower().startswith("python"):
                return rest

        return code_block

    def _extract_json(self, text: str) -> str:
        """
        Extract a JSON object from a model response.

        Handles:
          - raw JSON: { ... }
          - fenced JSON: ```json\n{ ... }\n```
          - other junk around a single top-level { ... } object
        """
        text = text.strip()

        # Case 1: already looks like a JSON object
        if text.startswith("{") and text.endswith("}"):
            return text

        # Case 2: inside ```json ... ``` or ``` ... ```
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                candidate = part.strip()
                # If the part starts with 'json', strip that language tag.
                if candidate.lower().startswith("json"):
                    candidate = candidate[4:].lstrip()  # remove 'json' + whitespace

                # Now see if there's a JSON object inside this chunk.
                start = candidate.find("{")
                end = candidate.rfind("}")
                if start != -1 and end != -1 and start < end:
                    return candidate[start : end + 1]

        # Case 3: no fences, but there is a JSON object somewhere in the text
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and start < end:
            return text[start : end + 1]

        # Fallback: return original and hope it's JSON-ish
        return text

    # ---------- Planning API (standard project planner) ----------

    def _plan_project(self, project_root: str, goal: str) -> Dict[str, Any]:
        """
        Use the Planner agent to design a multi-file project plan.
        Tries once, and if the JSON is invalid, asks the planner to repair it.
        """

        planner = self._make_planner_agent()

        def call_planner_for_plan(prompt: str) -> str:
            raw = planner._call_model(
                messages=[
                    {"role": "system", "content": planner.role},
                    {"role": "user", "content": prompt},
                ]
            )
            return self._extract_json(raw)

        # 1st attempt: normal planning prompt
        base_prompt = (
            "Design a small but well-structured Python project.\n"
            f"Project root (for your information only): {project_root}\n\n"
            "High-level goal:\n"
            f"{goal}\n\n"
            "Remember:\n"
            "- Respond with ONLY JSON following the schema described in your system prompt.\n"
            "- No markdown, no comments, no extra text.\n"
        )

        json_str = call_planner_for_plan(base_prompt)

        # Try to parse; if it fails, do one repair attempt
        for attempt in range(2):
            try:
                plan = json.loads(json_str)
                break
            except json.JSONDecodeError as e:
                if attempt == 1:
                    # After a repair attempt, still invalid → give a helpful error
                    raise ValueError(
                        f"Planner returned invalid JSON even after repair attempt: {e}\n"
                        f"JSON string was:\n{json_str}"
                    )

                # 2nd attempt: ask planner to repair its JSON
                repair_prompt = (
                    "You previously tried to return a JSON plan, but it was invalid JSON.\n"
                    "Here is what you returned:\n"
                    "----- INVALID JSON START -----\n"
                    f"{json_str}\n"
                    "----- INVALID JSON END -----\n\n"
                    f"The JSON decoder error was:\n{str(e)}\n\n"
                    "Please return a CORRECTED JSON object that strictly follows the schema:\n"
                    "{\n"
                    '  \"summary\": \"short summary of the project\",\n'
                    '  \"files\": [\n'
                    "    {\n"
                    '      \"path\": \"relative/path.py\",\n'
                    '      \"description\": \"What goes in this file\",\n'
                    '      \"entrypoint\": true or false\n'
                    "    }\n"
                    "  ]\n"
                    "}\n\n"
                    "Respond with ONLY valid JSON. No markdown, no comments, no extra keys, no extra text."
                )

                json_str = call_planner_for_plan(repair_prompt)

        # At this point, plan is a parsed dict
        if "files" not in plan or not isinstance(plan["files"], list):
            raise ValueError("Planner did not return a valid 'files' list.")

        # Basic validation and path normalization
        normalized_files = []
        project_root_norm = project_root.replace("\\", "/").strip("./")

        for f in plan["files"]:
            path = f.get("path", "").strip().replace("\\", "/")
            if not path:
                continue
            if path.startswith("/"):
                path = path.lstrip("/")

            parts = path.split("/")
            if any(part == ".." for part in parts):
                continue

            # also strip any accidental project_root prefix
            if project_root_norm:
                prefix = project_root_norm + "/"
                while path.startswith(prefix):
                    path = path[len(prefix):]

            normalized_files.append(
                {
                    "path": path,
                    "description": f.get("description", "").strip(),
                    "entrypoint": bool(f.get("entrypoint", False)),
                }
            )

        if not normalized_files:
            raise ValueError("Planner returned no usable files.")

        plan["files"] = normalized_files
        return plan

    # ---------- Single-file public API ----------

    def generate_file(self, file_path: str, description: str) -> Dict[str, Any]:
        """
        Generate a Python file at `file_path` matching the given `description`,
        and record it as a task in the task log.
        """
        # Create a task record
        goal = f"Generate file {file_path}: {description}"
        task_id = self.task_log.create_task(goal=goal, file_path=file_path)

        # Use the main code-writer agent
        agent = self._make_code_writer_agent()

        # Ask the brain for any relevant past experience
        memory_hint = self.brain.get_memory_hint(
            mode="file",
            goal=description,
            target_path=file_path,
        )
        hint_text = (
            f"\n\nHints from past experience:\n{memory_hint}\n"
            if memory_hint
            else ""
        )

        prompt = (
            "Write a single, complete, runnable Python 3 source file.\n"
            f"- Target file path (for your information only): {file_path}\n"
            "- The file must be pure Python 3 code ONLY.\n"
            "- DO NOT use shell commands, bash, os.system, subprocess, or EOF heredocs.\n"
            "- DO NOT write commands that create or modify files.\n"
            "- Just write the Python code itself.\n"
            "- Prefer a simple structure with a main() function and the usual\n"
            "  if __name__ == '__main__': main() pattern when appropriate.\n"
            "\n"
            "Requirements for this file:\n"
            f"{description}\n"
            f"{hint_text}"
            "\n"
            "Respond with ONLY the file content. No explanations, "
            "no markdown, no backticks."
        )

        try:
            # Ask the model for the file content
            raw_content = agent._call_model(
                messages=[
                    {"role": "system", "content": agent.role},
                    {"role": "user", "content": prompt},
                ]
            )

            # Strip any accidental markdown fences
            content = self._strip_code_fences(raw_content).strip()

            # Write the file using the filesystem tool
            tool_result = agent.use_tool(
                "filesystem", action="write", path=file_path, content=content
            )

            # Mark task as generated
            self.task_log.complete_task(
                task_id=task_id,
                status="generated",
                message=str(tool_result),
            )

            # Teach the brain about this success (NOW tool_result is defined)
            self.brain.remember(
                mode="file",
                goal=description,
                target_path=file_path,
                status="success",
                summary=f"Generated file {file_path}",
                metadata={"tool_result": tool_result},
            )

            return {
                "task_id": task_id,
                "file_path": file_path,
                "tool_result": tool_result,
                "content": content,
                "preview": content[:400],
            }

        except Exception as e:
            # Mark task as failed
            self.task_log.complete_task(
                task_id=task_id,
                status="failed",
                message=str(e),
            )
            # Remember failure for future hints
            self.brain.remember(
                mode="file",
                goal=description,
                target_path=file_path,
                status="failed",
                summary=f"Failed generating file {file_path}: {e}",
                metadata={},
            )
            raise



    def generate_and_run(
        self,
        file_path: str,
        description: str,
        max_retries: int = 1,
    ) -> Dict[str, Any]:
        """
        Generate a Python file, run it, and optionally debug it if it fails.

        Returns:
          {
            "task_id": int,
            "file_path": str,
            "generate": { ... },
            "runs": [ {exit_code, stdout, stderr, cmd}, ... ],
            "final_exit_code": int
          }
        """
        gen_result = self.generate_file(file_path=file_path, description=description)
        task_id = gen_result["task_id"]

        runs: List[Dict[str, Any]] = []
        attempts = 0
        final_exit_code = None

        while attempts <= max_retries:
            attempts += 1

            # Run the file
            runner = self._make_runner_agent()
            run_result = runner.use_tool(
                "code_runner",
                path=file_path,
                args=None,
                timeout=30,
            )
            runs.append(run_result)
            final_exit_code = run_result["exit_code"]

            if run_result["exit_code"] == 0:
                # Success!
                self.task_log.complete_task(
                    task_id=task_id,
                    status="run_success",
                    message=f"Command: {run_result['cmd']}, stdout: {run_result['stdout']}",
                )
                break

            if attempts > max_retries:
                # Already retried enough
                self.task_log.complete_task(
                    task_id=task_id,
                    status="run_failed",
                    message=f"Final stderr: {run_result['stderr']}",
                )
                break

            # Debug and rewrite the file
            debugger = self._make_debugger_agent()

            current_source = debugger.use_tool(
                "filesystem",
                action="read",
                path=file_path,
            )

            debug_prompt = (
                "You are debugging a Python file.\n"
                "Here is the current source code:\n"
                "----- SOURCE START -----\n"
                f"{current_source}\n"
                "----- SOURCE END -----\n\n"
                "Here is the error output from running this file:\n"
                "----- ERROR START -----\n"
                f"{run_result['stderr']}\n"
                "----- ERROR END -----\n\n"
                "Return a FULLY CORRECTED version of the ENTIRE Python file.\n"
                "Respond with ONLY the Python code. No explanations, "
                "no markdown, and no backticks."
            )

            raw_fix = debugger._call_model(
                messages=[
                    {"role": "system", "content": debugger.role},
                    {"role": "user", "content": debug_prompt},
                ]
            )

            fixed_content = self._strip_code_fences(raw_fix).strip()

            debugger.use_tool(
                "filesystem",
                action="write",
                path=file_path,
                content=fixed_content,
            )

        return {
            "task_id": task_id,
            "file_path": file_path,
            "generate": gen_result,
            "runs": runs,
            "final_exit_code": final_exit_code,
        }

    # ---------- Triad-based single-file generation ----------
    def _make_code_editor_agent(self) -> Agent:
        role = (
            "You are a senior code editor working on an existing project.\n"
            "You MUST treat the current file content as the source of truth and EDIT it.\n"
            "Rules:\n"
            "- Preserve existing public APIs and behavior unless explicitly told to change them.\n"
            "- Prefer minimal changes over full rewrites.\n"
            "- If something is unclear or impossible without more context, leave a TODO comment instead of guessing.\n"
            "- Respond with ONLY the full updated file content (no explanations, no markdown)."
        )
        return Agent(
            name="CodeEditor",
            role=role,
            model_client=self.model_client,
            tool_registry=self.tool_registry,
            allowed_tools=[],  # we write the file ourselves via FilesystemTool
        )
    def edit_file(self, file_path: str, description: str) -> Dict[str, Any]:
        """
        Edit an existing file according to `description`, preserving behavior where possible.
        If the file does not exist, this falls back to creating it like generate_file().
        """
        path = Path(file_path)
        agent = self._make_code_editor_agent()

        fs: FilesystemTool = self.tool_registry.get("filesystem")  # type: ignore

        # If file exists, read its current content
        if path.exists():
            current = fs.read(str(path))
        else:
            current = ""

        # Build prompt
        prompt = (
            "You are editing this existing file.\n"
            "User request:\n"
            f"{description}\n\n"
            "Current file content:\n"
            "---------------- BEGIN FILE ----------------\n"
            f"{current}\n"
            "----------------- END FILE -----------------\n\n"
            "Return ONLY the full updated file content. No explanations, no markdown."
        )

        new_content = agent._call_model(
            messages=[
                {"role": "system", "content": agent.role},
                {"role": "user", "content": prompt},
            ]
        )

        tool_result = fs.write(str(path), new_content)

        return {
            "file_path": str(path),
            "tool_result": tool_result,
            "preview": new_content[:400],
        }
    def triad_generate_file(self, file_path: str, description: str) -> Dict[str, Any]:
        """
        Use three different engineering personas to propose implementations,
        then let the chief engineer pick or merge them into a final file.

        Returns a dict like:
          {
            "task_id": int,
            "file_path": str,
            "candidates": [
              {"name": "...", "label": "...", "preview": "..."},
              ...
            ],
            "final_preview": str,
          }
        """

        # Create a high-level task record
        goal = f"Triad generate file {file_path}: {description}"
        task_id = self.task_log.create_task(goal=goal, file_path=file_path)

        # 1) Collect candidates from the three personas
        personas = [
            ("sentinel_engineer", "Sentinel"),
            ("storm_engineer", "Storm"),
            ("creator_engineer", "Creator"),
        ]

        candidates: List[Dict[str, Any]] = []

        for internal_name, label in personas:
            agent = self.agent_factory.get(internal_name)

            persona_prompt = (
                "You are one of three collaborating software engineers.\n"
                f"Your persona: {label} engineer.\n\n"
                "Your task is to produce a single, complete Python 3 source file that satisfies:\n"
                f"- Target file path (for your information only): {file_path}\n"
                f"- Requirements:\n{description}\n\n"
                "You should follow your own engineering style as described in your system role.\n"
                "Respond with ONLY the Python code for this file. No explanations, no markdown, no backticks."
            )

            raw = agent._call_model(
                messages=[
                    {"role": "system", "content": agent.role},
                    {"role": "user", "content": persona_prompt},
                ]
            )
            code = self._strip_code_fences(raw).strip()

            candidates.append(
                {
                    "name": internal_name,
                    "label": label,
                    "code": code,
                }
            )

        # 2) Ask the chief engineer to pick or merge the candidates
        chief = self._make_chief_engineer()

        chief_user_content_lines = [
            "You are the chief engineer. You will receive three candidate Python files "
            "for the SAME target file. Your job is to choose or merge them into ONE final file.",
            "",
            f"Target file path (for your information only): {file_path}",
            f"Original requirements:\n{description}",
            "",
            "Here are the candidates:",
        ]

        for idx, cand in enumerate(candidates, start=1):
            chief_user_content_lines.append(
                f"\nCandidate {idx} ({cand['label']}):\n"
                f"----- CANDIDATE {idx} START -----\n"
                f"{cand['code']}\n"
                f"----- CANDIDATE {idx} END -----"
            )

        chief_user_content_lines.append(
            "\nInstructions:\n"
            "- Carefully compare the candidates.\n"
            "- Choose the best one, or merge their ideas into a single improved file.\n"
            "- The final result must be valid, runnable Python 3 code.\n"
            "- Respond with ONLY the final Python code. No commentary, no markdown, no backticks."
        )

        chief_user_content = "\n".join(chief_user_content_lines)

        chief_raw = chief._call_model(
            messages=[
                {"role": "system", "content": chief.role},
                {"role": "user", "content": chief_user_content},
            ]
        )

        final_code = self._strip_code_fences(chief_raw).strip()

        # 3) Write the chosen/merged file using the filesystem tool
        writer = self._make_code_writer_agent()
        tool_result = writer.use_tool(
            "filesystem",
            action="write",
            path=file_path,
            content=final_code,
        )

        # 4) Mark the task as completed
        self.task_log.complete_task(
            task_id=task_id,
            status="generated",
            message=f"Triad candidates: {len(candidates)}, wrote final file.",
        )

        return {
            "task_id": task_id,
            "file_path": file_path,
            "candidates": [
                {
                    "name": c["name"],
                    "label": c["label"],
                    "preview": c["code"][:200],
                }
                for c in candidates
            ],
            "final_preview": final_code[:400],
            "tool_result": tool_result,
        }

    # ---------- Project planning + multi-file build (standard) ----------

    def plan_and_build_project(
        self,
        project_root: str,
        goal: str,
    ) -> Dict[str, Any]:
        """
        High-level: plan a multi-file project and generate all files under `project_root`.

        Returns:
          {
            "project_task_id": int,
            "project_root": str,
            "plan": {summary, files:[...]},
            "file_results": [ ... ]
          }
        """
        # Normalize project_root for comparisons (posix-style)
        project_root_norm = project_root.replace("\\", "/").strip("./")

        # Project-level task
        project_goal = f"Plan and build project at {project_root}: {goal}"
        project_task_id = self.task_log.create_task(
            goal=project_goal,
            file_path=project_root,
        )

        try:
            plan = self._plan_project(project_root=project_root, goal=goal)

            # Update task as planned
            self.task_log.complete_task(
                task_id=project_task_id,
                status="planned",
                message=f"Planned {len(plan['files'])} files. Summary: {plan.get('summary', '')}",
            )

            file_results: List[Dict[str, Any]] = []

            for file_spec in plan["files"]:
                raw_path = file_spec["path"].strip().replace("\\", "/")
                file_desc = file_spec.get("description", "")
                entrypoint = file_spec.get("entrypoint", False)

                # Treat all paths as relative to project_root.
                rel_path = raw_path

                # If the planner included the project root in the path one or more times,
                # strip all leading occurrences: project_root_norm/...
                if project_root_norm:
                    prefix = project_root_norm + "/"
                    while rel_path.startswith(prefix):
                        rel_path = rel_path[len(prefix):]

                # Skip empty / weird paths
                rel_path = rel_path.strip()
                if not rel_path:
                    continue

                full_path = os.path.join(project_root, rel_path)

                # Enrich file description with global goal + entrypoint info
                full_desc = (
                    f"{file_desc}\n\n"
                    f"Overall project goal: {goal}\n"
                    f"This file is{' ' if entrypoint else ' not '}the main entrypoint."
                )

                res = self.generate_file(
                    file_path=full_path,
                    description=full_desc,
                )
                file_results.append(res)

            # Mark project as completed
            self.task_log.complete_task(
                task_id=project_task_id,
                status="completed",
                message=f"Generated {len(file_results)} files.",
            )

            return {
                "project_task_id": project_task_id,
                "project_root": project_root,
                "plan": plan,
                "file_results": file_results,
            }

        except Exception as e:
            self.task_log.complete_task(
                task_id=project_task_id,
                status="failed",
                message=str(e),
            )
            raise

    # ---------- Project tests ----------

    def run_project_tests(self, project_root: str) -> Dict[str, Any]:
        """
        Run pytest for a given project_root using the tester agent.

        Returns:
          {
            "project_root": str,
            "result": {
              "exit_code": int,
              "stdout": str,
              "stderr": str,
              "cmd": [...],
              "workdir": str,
            }
          }
        """
        tester = self._make_tester_agent()

        result = tester.use_tool(
            "test_runner",
            project_root=project_root,
            tests_path=None,
        )

        return {
            "project_root": project_root,
            "result": result,
        }

    # ---------- Meta-planning with triad (approach-level) ----------

    def _triad_meta_plan(self, project_root: str, goal: str) -> Dict[str, Any]:
        """
        Ask the three engineering personas to propose a meta-plan for a project:
        - which agents to add
        - which files to create
        - which dependencies to use
        - which tests to add

        Then ask the chief to merge them into a single final meta-plan.

        Expected schema:

        {
          "project": {
            "root": "src/projects/doc_extractor",
            "summary": "Short summary"
          },
          "agents": [
            {
              "name": "agent_name",
              "role": "long role text",
              "allowed_tools": ["filesystem", ...]
            }
          ],
          "files": [
            {
              "path": "package/module.py",
              "description": "What goes here",
              "entrypoint": true or false
            }
          ],
          "dependencies": ["pytesseract", "pdfplumber"],
          "tests": [
            {
              "path": "tests/test_something.py",
              "description": "What it tests"
            }
          ]
        }
        """

        personas = [
            ("sentinel_engineer", "Sentinel"),
            ("storm_engineer", "Storm"),
            ("creator_engineer", "Creator"),
        ]

        candidate_plans: List[Dict[str, Any]] = []

        schema_hint = (
            "Return a JSON object with the following structure:\n"
            "{\n"
            '  "project": {\n'
            '    "root": "string, project root path",\n'
            '    "summary": "short summary of the project"\n'
            "  },\n"
            '  "agents": [\n'
            "    {\n"
            '      "name": "agent_name",\n'
            '      "role": "detailed role description text",\n'
            '      "allowed_tools": ["filesystem", "code_runner", "test_runner"]\n'
            "    }\n"
            "  ],\n"
            '  "files": [\n'
            "    {\n"
            '      "path": "relative/path.py",\n'
            '      "description": "what this file contains",\n'
            '      "entrypoint": true or false\n'
            "    }\n"
            "  ],\n"
            '  "dependencies": ["package1", "package2"],\n'
            '  "tests": [\n'
            "    {\n"
            '      "path": "tests/test_file.py",\n'
            '      "description": "what is tested here"\n'
            "    }\n"
            "  ]\n"
            "}\n"
            "Respond with ONLY JSON. No markdown, no comments, no extra text."
        )

        for internal_name, label in personas:
            agent = self.agent_factory.get(internal_name)

            prompt = (
                "You are one of three collaborating software engineers.\n"
                f"Your persona: {label} engineer.\n\n"
                "Your task is to propose a meta-plan for a Python project.\n"
                f"Project root (for your information only): {project_root}\n"
                f"High-level goal:\n{goal}\n\n"
                "Your meta-plan should describe:\n"
                "- Which AGENTS should be added or used (names, roles, allowed_tools).\n"
                "- Which FILES the project should contain (paths, descriptions, entrypoint flags).\n"
                "- Which Python DEPENDENCIES should be listed in requirements.txt.\n"
                "- Which TESTS should exist (paths + descriptions).\n\n"
                f"{schema_hint}"
            )

            raw = agent._call_model(
                messages=[
                    {"role": "system", "content": agent.role},
                    {"role": "user", "content": prompt},
                ]
            )
            json_str = self._extract_json(raw)

            try:
                plan = json.loads(json_str)
                plan["_source_engineer"] = label
                candidate_plans.append(plan)
            except json.JSONDecodeError:
                # Skip invalid candidate
                continue

        if not candidate_plans:
            raise ValueError("Triad meta-planning failed: no valid JSON meta-plans produced.")

        # Ask chief to merge the candidate meta-plans
        chief = self._make_chief_engineer()

        merged_prompt_lines = [
            "You are the chief engineer.\n",
            "You will receive several candidate META-PLANS for the SAME project.\n",
            "Each meta-plan is a JSON object with keys: project, agents, files, dependencies, tests.\n",
            "Your job is to MERGE them into ONE FINAL META-PLAN that follows the same schema.\n",
            "You must:\n",
            "- Preserve the best ideas from each candidate.\n",
            "- Avoid duplicates in agents, files, dependencies, and tests.\n",
            "- Ensure paths are coherent and under the given project root.\n",
            "- Ensure each agent has a useful role and allowed_tools list.\n",
            "- Ensure files have clear descriptions and at least one entrypoint file.\n",
            "- Ensure dependencies cover all required libraries but are not redundant.\n",
            "- Ensure tests make sense for the chosen structure.\n",
            "Respond with ONLY a single JSON object following the schema. No markdown, no comments.\n",
            f"Project root (for your information only): {project_root}\n",
            f"High-level goal:\n{goal}\n\n",
            "Here are the candidate meta-plans:\n",
        ]

        for idx, plan in enumerate(candidate_plans, start=1):
            label = plan.get("_source_engineer", f"Candidate{idx}")
            merged_prompt_lines.append(
                f"----- META-PLAN {idx} ({label}) START -----\n"
                f"{json.dumps({k: v for k, v in plan.items() if k != '_source_engineer'}, indent=2)}\n"
                f"----- META-PLAN {idx} END -----\n"
            )

        merged_prompt_lines.append(
            "\nNow produce the final merged meta-plan JSON.\n"
            "Remember: ONLY JSON, no extra text."
        )

        chief_raw = chief._call_model(
            messages=[
                {"role": "system", "content": chief.role},
                {"role": "user", "content": "\n".join(merged_prompt_lines)},
            ]
        )

        merged_json_str = self._extract_json(chief_raw)
        meta_plan = json.loads(merged_json_str)

        # Normalize some basics
        project = meta_plan.get("project") or {}
        project["root"] = project_root
        project.setdefault("summary", goal)
        meta_plan["project"] = project

        meta_plan.setdefault("agents", [])
        meta_plan.setdefault("files", [])
        meta_plan.setdefault("dependencies", [])
        meta_plan.setdefault("tests", [])

        return meta_plan

    # ---------- Meta-plan application helpers ----------

    def _apply_meta_agents(self, agents_spec: List[Dict[str, Any]]) -> None:
        """
        Merge new/updated agents from meta-plan into config/agents.yaml.
        """
        if not agents_spec:
            return

        # Load existing YAML
        if os.path.exists(self.agents_config_path):
            with open(self.agents_config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        if not isinstance(data, dict):
            data = {}

        agents_cfg = data.get("agents")
        if not isinstance(agents_cfg, dict):
            agents_cfg = {}
        data["agents"] = agents_cfg

        for spec in agents_spec:
            name = (spec.get("name") or "").strip()
            role = (spec.get("role") or "").strip()
            allowed_tools = spec.get("allowed_tools") or []

            if not name or not role:
                continue

            agents_cfg[name] = {
                "role": role,
                "allowed_tools": allowed_tools,
            }

        with open(self.agents_config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)

    def _write_requirements(self, project_root: str, dependencies: List[str]) -> None:
        """
        Write or overwrite requirements.txt in the project root based on dependencies.
        """
        if not dependencies:
            return

        deps = sorted({d.strip() for d in dependencies if d and d.strip()})
        if not deps:
            return

        req_path = os.path.join(project_root, "requirements.txt")
        os.makedirs(project_root, exist_ok=True)

        with open(req_path, "w", encoding="utf-8") as f:
            f.write("\n".join(deps) + "\n")

    # ---------- Meta-project build (triad → meta-plan → full project) ----------

    def meta_build_project(
        self,
        project_root: str,
        goal: str,
    ) -> Dict[str, Any]:
        """
        High-level meta-build:

        - Uses triad engineers to propose meta-plans (agents, files, dependencies, tests).
        - Uses chief engineer to merge into one meta-plan.
        - Applies meta-plan:
            * merges agents into config/agents.yaml
            * writes requirements.txt under project_root
            * generates all project files via generate_file()

        Returns:
          {
            "project_task_id": int,
            "project_root": str,
            "meta_plan": {...},
            "file_results": [ ... ]
          }
        """

        project_root_norm = project_root.replace("\\", "/").strip("./")
        project_goal = f"Meta-build project at {project_root}: {goal}"
        project_task_id = self.task_log.create_task(
            goal=project_goal,
            file_path=project_root,
        )
        memory_hint = self.brain.get_memory_hint(
                mode="meta-project",
                goal=goal,
                target_path=project_root,
            )

        try:
            # 1) Triad meta-plan
            meta_plan = self._triad_meta_plan(project_root=project_root, goal=goal)

            # 2) Apply agents
            self._apply_meta_agents(meta_plan.get("agents") or [])

            # 3) Write requirements.txt
            self._write_requirements(
                project_root=project_root,
                dependencies=meta_plan.get("dependencies") or [],
            )

            # 4) Generate files (including tests)
            file_specs: List[Dict[str, Any]] = []
            for f in meta_plan.get("files") or []:
                file_specs.append(
                    {
                        "path": f.get("path", "").strip().replace("\\", "/"),
                        "description": f.get("description", "").strip(),
                        "entrypoint": bool(f.get("entrypoint", False)),
                    }
                )

            for t in meta_plan.get("tests") or []:
                file_specs.append(
                    {
                        "path": (t.get("path") or "").strip().replace("\\", "/"),
                        "description": (t.get("description") or "").strip(),
                        "entrypoint": False,
                    }
                )

            file_specs = [f for f in file_specs if f["path"]]

            file_results: List[Dict[str, Any]] = []

            for file_spec in file_specs:
                raw_path = file_spec["path"]
                file_desc = file_spec.get("description", "")
                entrypoint = file_spec.get("entrypoint", False)

                rel_path = raw_path
                if project_root_norm:
                    prefix = project_root_norm + "/"
                    while rel_path.startswith(prefix):
                        rel_path = rel_path[len(prefix):]

                rel_path = rel_path.strip()
                if not rel_path:
                    continue

                full_path = os.path.join(project_root, rel_path)

                full_desc = (
                    f"{file_desc}\n\n"
                    f"Overall project goal: {goal}\n"
                    f"This file is{' ' if entrypoint else ' not '}the main entrypoint."
                )

                res = self.generate_file(
                    file_path=full_path,
                    description=full_desc,
                )
                file_results.append(res)

            self.task_log.complete_task(
                task_id=project_task_id,
                status="completed",
                message=f"Meta-plan applied. Generated {len(file_results)} files.",
            )

            return {
                "project_task_id": project_task_id,
                "project_root": project_root,
                "meta_plan": meta_plan,
                "file_results": file_results,
            }

        except Exception as e:
            self.task_log.complete_task(
                task_id=project_task_id,
                status="failed",
                message=str(e),
            )
            raise
