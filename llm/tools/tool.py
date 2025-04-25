import inspect
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict

@dataclass
class ToolCall:
    """Represents a tool call from the LLM."""
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ToolParameter:
    """Represents a parameter for a tool."""
    type: str
    description: str

    def to_dict(self):
        return {
            "type": self.type,
            "description": self.description
        }


class Tool(ABC):
    """Base class for all tools that can be used by the Agent."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool."""

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does."""

    @property
    def parameters(self) -> Dict[str, ToolParameter]:
        """The parameters that the tool accepts."""
        params = {}
        sig = inspect.signature(self.execute)
        for param_name, _ in sig.parameters.items():
            if param_name != "self":
                params[param_name] = ToolParameter(
                    type="string",
                    description=f"Parameter {param_name} for {self.name}",
                )
        return params

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with the given parameters."""
