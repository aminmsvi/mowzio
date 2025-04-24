from typing import List, Dict, Optional
from .memory_strategy import MemoryStrategy


class InMemoryStrategy(MemoryStrategy):
    """
    In-memory implementation of the MemoryStrategy interface.
    Stores message history in a simple list in memory.
    """

    def __init__(self):
        """Initialize an empty message history."""
        self._message_history: List[Dict[str, str]] = []

    def add_message(self, message: Dict[str, str]) -> None:
        """
        Add a message to the in-memory history.

        Args:
            message: A dictionary containing the message with 'role' and 'content' keys.
        """
        self._message_history.append(message)

    def get_messages(self) -> List[Dict[str, str]]:
        """
        Retrieve all messages from the in-memory history.

        Returns:
            A list of message dictionaries.
        """
        return self._message_history.copy()

    def clear_messages(self, system_prompt: Optional[Dict[str, str]] = None) -> None:
        """
        Clear all messages from the in-memory history, optionally preserving a system prompt.

        Args:
            system_prompt: Optional system prompt to retain after clearing.
        """
        self._message_history = []
        if system_prompt:
            self._message_history.append(system_prompt)

    def remove_last_message(self) -> None:
        """
        Remove the last message from the history if it is not the system prompt.
        """
        if self._message_history:  # Check if the list is not empty
            # Check if the last message's role is not 'system' before removing
            if self._message_history[-1].get("role") != "system":
                self._message_history.pop()