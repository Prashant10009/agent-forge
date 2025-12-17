# src/tools/code_runner_tool.py

import sys
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.core.tool_base import Tool


class CodeRunnerTool(Tool):
    name = "code_runner"
    description = "Run Python scripts in the workspace and capture stdout/stderr."

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()

    def _safe_path(self, relative_path: str) -> Path:
        p = (self.base_dir / relative_path).resolve()
        if not str(p).startswith(str(self.base_dir)):
            raise ValueError("Attempted path escape outside of base_dir.")
        return p

    def run(
        self,
        path: str,
        args: Optional[List[str]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Run a Python script at `path` (relative to workspace).
        Returns dict with exit_code, stdout, stderr, and cmd.
        """
        script_path = self._safe_path(path)

        cmd: List[str] = [sys.executable, str(script_path)]
        if args:
            cmd.extend(args)

        proc = subprocess.run(
            cmd,
            cwd=str(self.base_dir),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "cmd": cmd,
        }
