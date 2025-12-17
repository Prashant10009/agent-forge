from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.core.model_client import ModelClient


MEMORY_PATH = os.path.join("data", "brain_memory.json")


@dataclass
class MemoryEntry:
    """One remembered episode of the orchestrator doing something."""

    id: int
    mode: str                   # "file", "project", "meta-project", "doc-extract", etc.
    goal: str                   # user description / high-level goal
    target_path: str            # file path or project root or doc path
    status: str                 # "success", "failed", "partial"
    summary: str                # short natural-language summary of what happened
    metadata: Dict[str, Any]    # extra structured info (deps, files, errors)
    created_at: str             # ISO timestamp


class OrchestratorBrain:
    """
    Simple brain for the Orchestrator:

    - Stores past tasks in a JSON file (data/brain_memory.json)
    - Can retrieve "similar" tasks based on goal text and target path
    - Uses the model to compress that into a useful hint/guardrail
      that can be injected into prompts.
    """

    def __init__(self, model_client: ModelClient, memory_path: str = MEMORY_PATH):
        self.model_client = model_client
        self.memory_path = memory_path
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)

    # ---------- Low-level storage ----------

    def _load_all(self) -> List[MemoryEntry]:
        if not os.path.exists(self.memory_path):
            return []
        try:
            with open(self.memory_path, "r", encoding="utf-8") as f:
                raw = json.load(f)
        except Exception:
            return []

        entries: List[MemoryEntry] = []
        for item in raw:
            try:
                entries.append(
                    MemoryEntry(
                        id=int(item["id"]),
                        mode=str(item.get("mode", "")),
                        goal=str(item.get("goal", "")),
                        target_path=str(item.get("target_path", "")),
                        status=str(item.get("status", "")),
                        summary=str(item.get("summary", "")),
                        metadata=item.get("metadata") or {},
                        created_at=str(item.get("created_at", "")),
                    )
                )
            except Exception:
                continue
        return entries

    def _save_all(self, entries: List[MemoryEntry]) -> None:
        data = [asdict(e) for e in entries]
        with open(self.memory_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    # ---------- Public API: remember + recall ----------

    def remember(
        self,
        mode: str,
        goal: str,
        target_path: str,
        status: str,
        summary: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Store a new memory entry."""

        entries = self._load_all()
        next_id = (max((e.id for e in entries), default=0) + 1) if entries else 1

        entry = MemoryEntry(
            id=next_id,
            mode=mode,
            goal=goal,
            target_path=target_path,
            status=status,
            summary=summary,
            metadata=metadata or {},
            created_at=datetime.utcnow().isoformat(),
        )
        entries.append(entry)
        self._save_all(entries)

    def get_memory_hint(
        self,
        mode: str,
        goal: str,
        target_path: str,
        max_entries: int = 5,
    ) -> str:
        """
        Retrieve a natural-language hint summarizing relevant past experience.

        - Finds past entries with similar mode and overlapping tokens in goal/target_path.
        - Asks the model to summarize how those experiences might guide the new task.
        - Returns a short text that can be injected into prompts.
        """
        entries = self._load_all()
        if not entries:
            return ""

        goal_tokens = set(goal.lower().split())
        path_tokens = set(target_path.lower().replace("\\", "/").split("/"))

        def score(e: MemoryEntry) -> int:
            s = 0
            if e.mode == mode:
                s += 3
            # token overlap on goal
            e_goal_tokens = set(e.goal.lower().split())
            s += len(goal_tokens & e_goal_tokens)
            # simple path prefix match / overlap
            e_path_tokens = set(e.target_path.lower().replace("\\", "/").split("/"))
            s += 2 * len(path_tokens & e_path_tokens)
            # bonus for successes
            if e.status == "success":
                s += 2
            return s

        scored = sorted(entries, key=score, reverse=True)
        top = [e for e in scored if score(e) > 0][:max_entries]

        if not top:
            return ""

        # Build a compact description of relevant episodes
        bullets = []
        for e in top:
            bullets.append(
                f"- [#{e.id}] mode={e.mode}, status={e.status}, "
                f"target={e.target_path!r}, summary={e.summary}"
            )

        episodes_text = "\n".join(bullets)

        # Ask the model to compress this into a guardrail-style hint
                # Ask the model to compress this into a guardrail-style hint
        user_prompt = (
            "You are the 'brain' of a multi-agent coding system.\n"
            "You will see a new task (mode + goal + target_path) and several past episodes.\n"
            "Your job is to summarize what lessons or patterns from the past episodes\n"
            "should guide the new task. Focus on:\n"
            "- libraries/dependencies that were useful\n"
            "- project structures that worked\n"
            "- common pitfalls (e.g. import paths, missing requirements)\n"
            "- anything that should be reused or avoided.\n\n"
            f"NEW TASK:\n- mode: {mode}\n- goal: {goal}\n- target_path: {target_path}\n\n"
            "PAST EPISODES:\n"
            f"{episodes_text}\n\n"
            "Now write a short advisory note (3-10 lines) that the orchestrator can include\n"
            "in prompts to other agents. The note should be plain text, no markdown, and\n"
            "should be phrased as 'Hints from past experience: ...'."
        )

        # Call the model client; it usually returns a dict with 'role' and 'content'
        resp = self.model_client.chat(
            messages=[
                {"role": "system", "content": "You are a helpful memory summarizer."},
                {"role": "user", "content": user_prompt},
            ]
        )

        # Normalize to a plain string
        if isinstance(resp, dict):
            # Most ModelClients return {"role": "...", "content": "..."}
            message = resp.get("content") or resp.get("message") or ""
        else:
            message = resp

        if not message:
            return ""

        if isinstance(message, dict):
            # Turn dict into a readable JSON snippet
            message_str = json.dumps(message, indent=2, ensure_ascii=False)
        else:
            message_str = str(message)

        hint = message_str.strip()
        return hint


