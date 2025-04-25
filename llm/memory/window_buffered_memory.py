from typing import List, Optional

from .memory import Memory, Message


class WindowBufferedMemory(Memory):
    """
    In-memory implementation of the Memory interface.
    Stores a limited window of message history in memory.
    Preserves system prompts while keeping only the most recent messages.
    """

    def __init__(self, window_size: int = 20):
        """
        Initialize an empty message history with a maximum window size.

        Args:
            window_size: Maximum number of non-system messages to retain.
        """
        self._message_history: List[Message] = []
        self._window_size = window_size

    def add_message(self, message: Message) -> None:
        """
        Add a message to the in-memory history, maintaining the window size limit.
        System prompts are always preserved regardless of window size.

        Args:
            message: A Message object containing the role and content.
        """
        self._message_history.append(message)

        # Count system messages to exclude them from the window limit
        system_messages = [
            m for m in self._message_history if m.role == "system"
        ]
        non_system_count = len(self._message_history) - len(system_messages)

        # Remove oldest non-system messages if we exceed the window size
        while non_system_count > self._window_size:
            # Find the first non-system message to remove
            for i, msg in enumerate(self._message_history):
                if msg.role != "system":
                    self._message_history.pop(i)
                    non_system_count -= 1
                    break

    def get_messages(self) -> List[Message]:
        """
        Retrieve all messages from the in-memory history.

        Returns:
            A list of Message objects.
        """
        return self._message_history.copy()

    def clear_messages(self, system_prompt: Optional[Message] = None) -> None:
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
            if self._message_history[-1].role != "system":
                self._message_history.pop()
