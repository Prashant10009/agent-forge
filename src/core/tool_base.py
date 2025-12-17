from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """
    Base class for all tools.
    Each tool exposes:
      - a unique name
      - a description
      - a 'run' method that takes arguments and returns a result.
    """

    name: str = "base_tool"
    description: str = "Abstract base tool."

    @abstractmethod
    def run(self, **kwargs) -> Any:
        ...


class ToolRegistry:
    """
    Keeps track of available tools by name.
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        if tool.name in self._tools:
            raise ValueError(f"Tool with name {tool.name} already registered.")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"Tool {name} not found.")
        return self._tools[name]

    def list_tools(self) -> Dict[str, str]:
        return {name: tool.description for name, tool in self._tools.items()}
