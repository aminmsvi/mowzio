import inspect
from abc import ABC, abstractmethod
from typing import Any, Dict


class Tool(ABC):
    """Base class for all tools that can be used by the Agent."""

    @property
    @abstractmethod
    def name(self) -> str:
        """The name of the tool."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """A description of what the tool does."""
        pass

    @property
    def parameters(self) -> Dict[str, Dict[str, Any]]:
        """The parameters that the tool accepts."""
        params = {}
        sig = inspect.signature(self.execute)
        for param_name, _ in sig.parameters.items():
            if param_name != 'self':
                params[param_name] = {
                    "type": "string",
                    "description": f"Parameter {param_name} for {self.name}"
                }
        return params

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute the tool with the given parameters."""
        pass
