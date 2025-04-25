from abc import ABC, abstractmethod
from typing import List, Optional, Literal
from dataclasses import dataclass


@dataclass
class Message:
    """
    Represents a message in a conversation.
    """
    content: str
    role: Literal["system", "user", "assistant"]

    def to_dict(self) -> dict:
        """Convert the message to a dictionary format."""
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, message_dict: dict) -> "Message":
        """Create a Message from a dictionary."""
        return cls(
            role=message_dict["role"],
            content=message_dict["content"]
        )


class Memory(ABC):
    """
    Abstract base class defining the interface for different message history storage strategies.
    This follows the Strategy pattern to allow different implementations for storing chat history.
    """

    @abstractmethod
    def add_message(self, message: Message) -> None:
        """
        Add a message to the history.

        Args:
            message: A Message object containing the role and content.
        """

    @abstractmethod
    def get_messages(self) -> List[Message]:
        """
        Retrieve all messages from the history.

        Returns:
            A list of Message objects.
        """

    @abstractmethod
    def clear_messages(self, system_prompt: Optional[Message] = None) -> None:
        """
        Clear all messages from the history, optionally preserving a system prompt.

        Args:
            system_prompt: Optional system prompt to retain after clearing.
        """

    @abstractmethod
    def remove_last_message(self) -> None:
        """
        Remove the last message from the history if it is not the system prompt.
        """
