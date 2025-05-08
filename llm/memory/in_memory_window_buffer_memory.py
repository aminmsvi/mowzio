from collections import deque
from typing import List, Optional, Deque

from .memory import Memory, Message


class InMemoryWindowBufferMemory(Memory):
    """
    An in-memory, window-buffered implementation of the Memory interface.
    Preserves a single system prompt while keeping only the most recent non-system messages.
    """

    def __init__(self, window_size: int = 20):
        """
        Initialize a message history with a maximum window size.

        Args:
            window_size: Maximum number of non-system messages to retain.
        """
        self._window_size = window_size
        self._messages: Deque[Message] = deque()
        self._system_message: Optional[Message] = None

    def add_message(self, message: Message) -> None:
        """
        Add a message to the history, maintaining the window size limit.
        System prompts are always preserved, and only one system prompt is allowed.

        Args:
            message: A Message object containing the role and content.
        """
        if message.role == "system":
            self._system_message = (
                message  # Replace existing system message or set new one
            )
        else:
            self._messages.append(message)
            # Maintain window size for non-system messages
            while len(self._messages) > self._window_size:
                self._messages.popleft()

    def get_messages(self) -> List[Message]:
        """
        Retrieve all messages from the history, including the system prompt if set.

        Returns:
            A list of Message objects.
        """
        all_messages: List[Message] = []
        if self._system_message:
            all_messages.append(self._system_message)
        all_messages.extend(list(self._messages))
        return all_messages

    def clear_messages(self, system_prompt: Optional[Message] = None) -> None:
        """
        Clear all messages from the history, optionally preserving a system prompt.

        Args:
            system_prompt: Optional system prompt to retain after clearing.
                           If provided and its role is "system", it will be set.
        """
        self._messages.clear()
        self._system_message = None
        if system_prompt and system_prompt.role == "system":
            self._system_message = system_prompt

    def remove_last_message(self) -> None:
        """
        Remove the last non-system message from the history.
        This operation does not affect the system prompt.
        """
        if self._messages:
            self._messages.pop()
