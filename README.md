# Agent Forge

Agent Forge is a **config-driven multi-agent coding system**: one Orchestrator coordinates specialized agents to **plan projects**, **generate/edit code**, **run code**, **run tests**, and even do **meta-project bootstrapping** (agents + files + deps) from a single prompt.

This repo currently ships:
- a **CLI** (`src/apps/cli.py`)
- a **FastAPI server** (`src/apps/api.py`)
- a **Streamlit GUI** for document extraction (`src/projects/doc_extractor_gui/app.py`)

---

## Key features

### Multi-agent workflows
- **File generation**: generate a single Python file from a description.
- **File editing**: edit an existing file with a “change request” prompt.
- **Generate + run + auto-debug**: run the generated script; if it fails, Debugger attempts a full-file fix and reruns.
- **Project planning + build**: Planner outputs a JSON file plan; Orchestrator generates all files.
- **Run tests**: run `pytest` for a generated project.

### Triad mode (multi-persona coding)
- `--triad` uses three engineering personas (**sentinel**, **storm**, **creator**) to draft candidates, then a **chief engineer** merges/picks the final output.

### Meta-project mode (bootstrap bigger systems)
- `--mode meta-project` asks the triad for a *meta-plan* (agents + project files + deps + tests),
  the chief merges it into one plan, then the Orchestrator:
  - merges new agents into `config/agents.yaml`
  - writes a `requirements.txt` into the target project root
  - generates project files + tests

### Web + GUI
- **FastAPI** endpoints for “chat-to-code”, project chat, listing tasks/projects/files, uploads, and launching the doc GUI.
- **Streamlit** doc extractor GUI that calls the Orchestrator’s document extraction service.

---

## Architecture (high level)

```text
User (CLI / API / GUI)
  │
  ▼
Orchestrator (src/core/orchestrator.py)
  ├─ ModelClient (openrouter | ollama | ollama_cloud | mock)
  ├─ ToolRegistry
  │    ├─ filesystem
  │    ├─ code_runner
  │    └─ test_runner
  ├─ AgentFactory (config/agents.yaml)
  ├─ TaskLog (SQLite: data/memory.db)
  └─ OrchestratorBrain (JSON memory: data/brain_memory.json)
