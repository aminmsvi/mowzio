from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class RedisInterface(ABC):
    """
    Interface for Redis client operations.
    """

    @abstractmethod
    def set(self, key: str, value: str, expiry: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis, with optional expiration.
        """
        pass

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis by key.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.
        """
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.
        """
        pass

    @abstractmethod
    def expire(self, key: str, seconds: int) -> bool:
        """
        Set an expiration time for a key.
        """
        pass

    @abstractmethod
    def ttl(self, key: str) -> int:
        """
        Get the remaining time to live for a key.
        """
        pass

    @abstractmethod
    def hset(self, name: str, key: str, value: str) -> bool:
        """
        Set a field in a hash stored at key.
        """
        pass

    @abstractmethod
    def hget(self, name: str, key: str) -> Optional[str]:
        """
        Get the value of a hash field.
        """
        pass

    @abstractmethod
    def hgetall(self, name: str) -> Dict[str, str]:
        """
        Get all fields and values in a hash.
        """
        pass

    @abstractmethod
    def hdel(self, name: str, *keys: str) -> int:
        """
        Delete one or more hash fields.
        """
        pass

    @abstractmethod
    def lpush(self, name: str, *values: str) -> int:
        """
        Prepend values to a list.
        """
        pass

    @abstractmethod
    def rpush(self, name: str, *values: str) -> int:
        """
        Append values to a list.
        """
        pass

    @abstractmethod
    def lrange(self, name: str, start: int, end: int) -> List[str]:
        """
        Get a range of elements from a list.
        """
        pass

    @abstractmethod
    def flush_db(self) -> bool:
        """
        Delete all keys in the current database.
        """
        pass

    @abstractmethod
    def ping(self) -> bool:
        """
        Check if a connection to Redis is established.
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the Redis connection.
        """
        pass
