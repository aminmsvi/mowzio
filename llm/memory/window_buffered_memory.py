from typing import List, Optional
import json

from app.db.redis.redis_factory import RedisFactory
from app.db.redis.redis_adapter import RedisAdapter
from .memory import Memory, Message

REDIS_KEY_PREFIX = "chat:memory:"
REDIS_DB = 0


class WindowBufferedMemory(Memory):
    """
    A window-buffered implementation of the Memory interface.
    Preserves system prompts while keeping only the most recent messages.
    """

    def __init__(self, window_size: int = 20):
        """
        Initialize a message history with a maximum window size.

        Args:
            window_size: Maximum number of non-system messages to retain.
        """
        self._window_size = window_size
        self._redis: RedisAdapter = RedisFactory.create_redis_adapter(db=REDIS_DB)
        self._messages_key = f"{REDIS_KEY_PREFIX}messages"

    def add_message(self, message: Message) -> None:
        """
        Add a message to the history, maintaining the window size limit.
        System prompts are always preserved regardless of window size.

        Args:
            message: A Message object containing the role and content.
        """
        # Serialize the message and add it to the Redis list
        self._redis.rpush(self._messages_key, message.to_json())

        # Get all messages to apply window size limit
        all_messages = self.get_messages()

        # Count system messages to exclude them from the window limit
        system_messages = [m for m in all_messages if m.role == "system"]
        non_system_count = len(all_messages) - len(system_messages)

        # If we exceed the window size, rebuild the list without the oldest non-system messages
        if non_system_count > self._window_size:
            # Delete the existing list
            self._redis.delete(self._messages_key)

            # Preserve system messages
            preserved_messages = system_messages.copy()

            # Add the most recent non-system messages up to window_size
            non_system_messages = [m for m in all_messages if m.role != "system"]
            preserved_messages.extend(non_system_messages[-self._window_size :])

            # Sort messages back into original order
            preserved_messages.sort(key=lambda m: all_messages.index(m))

            # Add all preserved messages back to Redis
            for msg in preserved_messages:
                self._redis.rpush(self._messages_key, msg.to_json())

    def get_messages(self) -> List[Message]:
        """
        Retrieve all messages from the history.

        Returns:
            A list of Message objects.
        """
        # Get all serialized messages from Redis
        serialized_messages = self._redis.lrange(self._messages_key, 0, -1)

        # Deserialize each message
        return [Message.from_json(msg) for msg in serialized_messages]

    def clear_messages(self, system_prompt: Optional[Message] = None) -> None:
        """
        Clear all messages from the history, optionally preserving a system prompt.

        Args:
            system_prompt: Optional system prompt to retain after clearing.
        """
        # Delete the existing list
        self._redis.delete(self._messages_key)

        # If a system prompt is provided, add it back
        if system_prompt:
            self._redis.rpush(self._messages_key, system_prompt.to_json())

    def remove_last_message(self) -> None:
        """
        Remove the last message from the history if it is not the system prompt.
        """
        messages = self.get_messages()
        if not messages:
            return

        # Check if the last message is not a system message
        if messages[-1].role != "system":
            # Rebuild the list without the last message
            self._redis.delete(self._messages_key)

            # Add all messages except the last one back to Redis
            for msg in messages[:-1]:
                self._redis.rpush(self._messages_key, msg.to_json())
