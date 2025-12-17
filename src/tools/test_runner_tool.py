import subprocess
from pathlib import Path
from typing import Dict, Any, Optional

from src.core.tool_base import Tool


class TestRunnerTool(Tool):
    """
    Simple tool to run pytest in a given project directory.

    Usage via Agent:
      agent.use_tool("test_runner", project_root="src/projects/todo_app_v2")

    It will run `pytest` in that directory and return:
      {
        "exit_code": int,
        "stdout": str,
        "stderr": str,
        "cmd": [ ... ]
      }
    """

    name = "test_runner"

    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir).resolve()

    def run(self, project_root: str, tests_path: Optional[str] = None) -> Dict[str, Any]:
        root = (self.base_dir / project_root).resolve()

        if tests_path:
            tests_dir = root / tests_path
        else:
            tests_dir = root / "tests"

        # If tests directory doesn't exist, still run pytest in root;
        # pytest will report "no tests collected" which is fine.
        workdir = root

        cmd = ["pytest"]
        if tests_dir.exists():
            cmd.append(str(tests_dir))

        try:
            proc = subprocess.run(
                cmd,
                cwd=workdir,
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {
                "exit_code": proc.returncode,
                "stdout": proc.stdout,
                "stderr": proc.stderr,
                "cmd": cmd,
                "workdir": str(workdir),
            }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": str(e),
                "cmd": cmd,
                "workdir": str(workdir),
            }
