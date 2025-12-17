import os
from typing import Any
from pathlib import Path

from src.core.tool_base import Tool


class FilesystemTool(Tool):
    name = "filesystem"
    description = "Read, write, and list project files in the workspace."

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()

    def _safe_path(self, relative_path: str) -> Path:
        p = (self.base_dir / relative_path).resolve()
        if not str(p).startswith(str(self.base_dir)):
            raise ValueError("Attempted path escape outside of base_dir.")
        return p

    def run(self, action: str, path: str = "", content: str = "") -> Any:
        if action == "read":
            file_path = self._safe_path(path)
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()

        if action == "write":
            file_path = self._safe_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Written {len(content)} chars to {file_path}"

        if action == "list":
            dir_path = self._safe_path(path or ".")
            return [
                str(p.relative_to(self.base_dir)) for p in dir_path.rglob("*")
                if p.is_file()
            ]

        raise ValueError(f"Unknown action: {action}")
