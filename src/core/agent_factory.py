from pathlib import Path
from typing import Dict, Any

import yaml

from src.core.agent_base import Agent
from src.core.model_client import ModelClient
from src.core.tool_base import ToolRegistry


class AgentFactory:
    """
    Builds Agent instances from a YAML config file.

    Expected YAML structure (config/agents.yaml):

    agents:
      planner:
        role: "..."
        allowed_tools: ["filesystem", "code_runner"]
      code_writer:
        role: "..."
        allowed_tools: ["filesystem"]
      ...

    This lets us define/modify agents without changing Python code.
    """

    def __init__(
        self,
        model_client: ModelClient,
        tool_registry: ToolRegistry,
        config_path: str = "config/agents.yaml",
    ):
        self.model_client = model_client
        self.tool_registry = tool_registry

        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Agent config file not found at {self.config_path}. "
                f"Create it (e.g., config/agents.yaml)."
            )

        with self.config_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        agents_cfg = data.get("agents")
        if not isinstance(agents_cfg, dict):
            raise ValueError(
                f"Invalid agents config in {self.config_path}: "
                f"expected 'agents' mapping."
            )

        self.agents_cfg: Dict[str, Dict[str, Any]] = agents_cfg

    def get(self, name: str) -> Agent:
        """
        Build an Agent instance for the given name using the YAML config.
        """
        cfg = self.agents_cfg.get(name)
        if not cfg:
            raise KeyError(
                f"Agent '{name}' is not defined in {self.config_path}."
            )

        role = cfg.get("role", "").strip()
        if not role:
            raise ValueError(
                f"Agent '{name}' in {self.config_path} has no 'role' text."
            )

        allowed_tools = cfg.get("allowed_tools") or []
        if not isinstance(allowed_tools, list):
            raise ValueError(
                f"Agent '{name}' allowed_tools must be a list."
            )

        return Agent(
            name=name,
            role=role,
            model_client=self.model_client,
            tool_registry=self.tool_registry,
            allowed_tools=allowed_tools,
        )
