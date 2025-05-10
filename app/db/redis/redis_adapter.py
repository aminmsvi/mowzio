from typing import Dict, List, Optional

import redis
from redis.exceptions import RedisError

from app.config import settings


class RedisAdapter:
    """
    A wrapper for Redis client that provides a clean interface for database operations.
    """

    def __init__(
        self,
        db: int = 0,
        socket_timeout: int = 5,
        retry_on_timeout: bool = True,
    ):
        """
        Initialize the Redis adapter with connection parameters.

        Args:
            db: Redis database number (default: 0)
            socket_timeout: Socket timeout in seconds (default: 5)
            retry_on_timeout: Whether to retry on timeout (default: True)
        """
        self._connection_params = {
            "host": settings.REDIS_HOST,
            "port": settings.REDIS_PORT,
            "password": settings.REDIS_PASSWORD,
            "db": db,
            "socket_timeout": socket_timeout,
            "retry_on_timeout": retry_on_timeout,
            "decode_responses": True,
            "ssl": True,
        }
        self._client = self._create_client()

    def _create_client(self) -> redis.Redis:
        """
        Create a new Redis client instance.

        Returns:
            A configured Redis client
        """
        return redis.Redis(**self._connection_params)

    def set(self, key: str, value: str, expiry: Optional[int] = None) -> bool:
        """
        Set a key-value pair in Redis, with optional expiration.

        Args:
            key: The key to set
            value: The value to store
            expiry: Optional expiration time in seconds

        Returns:
            True if successful, False otherwise

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return bool(self._client.set(key, value, ex=expiry))
        except RedisError as e:
            raise RedisAdapterError(f"Error setting key {key}: {str(e)}")

    def get(self, key: str) -> Optional[str]:
        """
        Get a value from Redis by key.

        Args:
            key: The key to retrieve

        Returns:
            The value if key exists, None otherwise

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return self._client.get(key)
        except RedisError as e:
            raise RedisAdapterError(f"Error getting key {key}: {str(e)}")

    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis.

        Args:
            key: The key to delete

        Returns:
            True if key was deleted, False if key didn't exist

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return bool(self._client.delete(key))
        except RedisError as e:
            raise RedisAdapterError(f"Error deleting key {key}: {str(e)}")

    def exists(self, key: str) -> bool:
        """
        Check if a key exists in Redis.

        Args:
            key: The key to check

        Returns:
            True if key exists, False otherwise

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return bool(self._client.exists(key))
        except RedisError as e:
            raise RedisAdapterError(f"Error checking existence of key {key}: {str(e)}")

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set an expiration time for a key.

        Args:
            key: The key to set expiration on
            seconds: Expiration time in seconds

        Returns:
            True if timeout was set, False if key doesn't exist

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return bool(self._client.expire(key, seconds))
        except RedisError as e:
            raise RedisAdapterError(f"Error setting expiry for key {key}: {str(e)}")

    def ttl(self, key: str) -> int:
        """
        Get the remaining time to live for a key.

        Args:
            key: The key to check

        Returns:
            TTL in seconds, -1 if key has no expiry, -2 if key doesn't exist

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return self._client.ttl(key)
        except RedisError as e:
            raise RedisAdapterError(f"Error getting TTL for key {key}: {str(e)}")

    def hset(self, name: str, key: str, value: str) -> bool:
        """
        Set a field in a hash stored at key.

        Args:
            name: Hash name
            key: Field name
            value: Field value

        Returns:
            True if field is a new field and value was set, False otherwise

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return bool(self._client.hset(name, key, value))
        except RedisError as e:
            raise RedisAdapterError(f"Error setting hash field {name}:{key}: {str(e)}")

    def hget(self, name: str, key: str) -> Optional[str]:
        """
        Get the value of a hash field.

        Args:
            name: Hash name
            key: Field name

        Returns:
            Value of the field if it exists, None otherwise

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return self._client.hget(name, key)
        except RedisError as e:
            raise RedisAdapterError(f"Error getting hash field {name}:{key}: {str(e)}")

    def hgetall(self, name: str) -> Dict[str, str]:
        """
        Get all fields and values in a hash.

        Args:
            name: Hash name

        Returns:
            Dictionary of field-value pairs

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return self._client.hgetall(name)
        except RedisError as e:
            raise RedisAdapterError(
                f"Error getting all fields from hash {name}: {str(e)}"
            )

    def hdel(self, name: str, *keys: str) -> int:
        """
        Delete one or more hash fields.

        Args:
            name: Hash name
            keys: One or more fields to delete

        Returns:
            Number of fields that were removed

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return self._client.hdel(name, *keys)
        except RedisError as e:
            raise RedisAdapterError(f"Error deleting fields from hash {name}: {str(e)}")

    def lpush(self, name: str, *values: str) -> int:
        """
        Prepend values to a list.

        Args:
            name: List name
            values: One or more values to prepend

        Returns:
            Length of the list after the push operation

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return self._client.lpush(name, *values)
        except RedisError as e:
            raise RedisAdapterError(f"Error pushing to list {name}: {str(e)}")

    def rpush(self, name: str, *values: str) -> int:
        """
        Append values to a list.

        Args:
            name: List name
            values: One or more values to append

        Returns:
            Length of the list after the push operation

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return self._client.rpush(name, *values)
        except RedisError as e:
            raise RedisAdapterError(f"Error pushing to list {name}: {str(e)}")

    def lrange(self, name: str, start: int, end: int) -> List[str]:
        """
        Get a range of elements from a list.

        Args:
            name: List name
            start: Start index
            end: End index

        Returns:
            List of elements in the specified range

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return self._client.lrange(name, start, end)
        except RedisError as e:
            raise RedisAdapterError(f"Error getting range from list {name}: {str(e)}")

    def flush_db(self) -> bool:
        """
        Delete all keys in the current database.

        Returns:
            True if successful

        Raises:
            RedisAdapterError: If a Redis-specific error occurs
        """
        try:
            return bool(self._client.flushdb())
        except RedisError as e:
            raise RedisAdapterError(f"Error flushing database: {str(e)}")

    def ping(self) -> bool:
        """
        Check if a connection to Redis is established.

        Returns:
            True if connection is alive, False otherwise
        """
        try:
            return self._client.ping()
        except RedisError:
            return False

    def close(self) -> None:
        """
        Close the Redis connection.
        """
        try:
            self._client.close()
        except RedisError as e:
            raise RedisAdapterError(f"Error closing Redis connection: {str(e)}")


class RedisAdapterError(Exception):
    """Custom exception for Redis adapter errors."""

    pass
