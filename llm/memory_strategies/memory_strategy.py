from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class MemoryStrategy(ABC):
    """
    Abstract base class defining the interface for different message history storage strategies.
    This follows the Strategy pattern to allow different implementations for storing chat history.
    """

    @abstractmethod
    def add_message(self, message: Dict[str, str]) -> None:
        """
        Add a message to the history.

        Args:
            message: A dictionary containing the message with 'role' and 'content' keys.
        """
        pass

    @abstractmethod
    def get_messages(self) -> List[Dict[str, str]]:
        """
        Retrieve all messages from the history.

        Returns:
            A list of message dictionaries.
        """
        pass

    @abstractmethod
    def clear_messages(self, system_prompt: Optional[Dict[str, str]] = None) -> None:
        """
        Clear all messages from the history, optionally preserving a system prompt.

        Args:
            system_prompt: Optional system prompt to retain after clearing.
        """
        pass

    @abstractmethod
    def remove_last_message(self) -> None:
        """
        Remove the last message from the history if it is not the system prompt.
        """
        pass
