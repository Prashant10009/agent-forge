from typing import List, Dict, Any, Optional

from src.core.model_client import ModelClient
from src.core.tool_base import ToolRegistry


class Agent:
    """
    Base Agent:
      - has a name and role
      - has access to a model client
      - can use a subset of tools via the registry
    """

    def __init__(
        self,
        name: str,
        role: str,
        model_client: ModelClient,
        tool_registry: ToolRegistry,
        allowed_tools: Optional[List[str]] = None,
    ):
        self.name = name
        self.role = role
        self.model_client = model_client
        self.tool_registry = tool_registry
        self.allowed_tools = allowed_tools or []

    def _call_model(self, messages: List[Dict[str, str]]) -> str:
        message = self.model_client.chat(messages=messages)
        return message.get("content", "") if isinstance(message, dict) else str(message)

    def use_tool(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self.allowed_tools:
            raise PermissionError(
                f"Agent {self.name} is not allowed to use tool {tool_name}."
            )
        tool = self.tool_registry.get(tool_name)
        return tool.run(**kwargs)
