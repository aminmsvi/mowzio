import time
from typing import Any, Dict, List, Optional

from db.redis.redis_interface import RedisInterface


class FakeRedisAdapter(RedisInterface):
    """
    A fake implementation of the RedisInterface for testing and development.
    This client simulates Redis behavior using in-memory dictionaries.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}
        self._expiries: Dict[str, float] = {}
        self._hashes: Dict[str, Dict[str, str]] = {}
        self._lists: Dict[str, List[str]] = {}

    def _check_expiry(self, key: str) -> None:
        """Helper to remove expired keys."""
        if key in self._expiries and self._expiries[key] < time.time():
            self.delete(key)
            if key in self._hashes:
                del self._hashes[key]
            if key in self._lists:
                del self._lists[key]

    def set(self, key: str, value: str, expiry: Optional[int] = None) -> bool:
        self._check_expiry(key)
        self._data[key] = value
        if expiry is not None:
            self._expiries[key] = time.time() + expiry
        elif key in self._expiries:  # remove existing expiry if not set
            del self._expiries[key]
        return True

    def get(self, key: str) -> Optional[str]:
        self._check_expiry(key)
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        self._check_expiry(key)
        deleted = False
        if key in self._data:
            del self._data[key]
            deleted = True
        if key in self._expiries:
            del self._expiries[key]
            deleted = True  # Even if only expiry existed
        if key in self._hashes:
            del self._hashes[key]
            deleted = True
        if key in self._lists:
            del self._lists[key]
            deleted = True
        return deleted

    def exists(self, key: str) -> bool:
        self._check_expiry(key)
        return key in self._data or key in self._hashes or key in self._lists

    def expire(self, key: str, seconds: int) -> bool:
        self._check_expiry(key)
        if self.exists(key):
            if seconds > 0:
                self._expiries[key] = time.time() + seconds
            else:  # Effectively delete if seconds is 0 or negative
                return self.delete(key)
            return True
        return False

    def ttl(self, key: str) -> int:
        self._check_expiry(key)
        if key not in self._expiries:
            return (
                -1 if self.exists(key) else -2
            )  # -1 if key exists but no expiry, -2 if not exists

        remaining = self._expiries[key] - time.time()
        return (
            int(remaining) if remaining > 0 else -2
        )  # Redis returns -2 if expired or not found

    def hset(self, name: str, key: str, value: str) -> bool:
        self._check_expiry(name)  # Hash itself can expire
        if name not in self._hashes:
            self._hashes[name] = {}
        is_new_field = key not in self._hashes[name]
        self._hashes[name][key] = value
        return is_new_field  # Returns 1 if field is new, 0 if field was updated. Bool True for new.

    def hget(self, name: str, key: str) -> Optional[str]:
        self._check_expiry(name)
        if name in self._hashes:
            return self._hashes[name].get(key)
        return None

    def hgetall(self, name: str) -> Dict[str, str]:
        self._check_expiry(name)
        return self._hashes.get(name, {})

    def hdel(self, name: str, *keys: str) -> int:
        self._check_expiry(name)
        if name not in self._hashes:
            return 0

        deleted_count = 0
        for key_to_delete in keys:
            if key_to_delete in self._hashes[name]:
                del self._hashes[name][key_to_delete]
                deleted_count += 1

        if not self._hashes[name]:  # remove hash if empty
            del self._hashes[name]
            if name in self._data:  # also remove from _data if it was marked there
                del self._data[name]
            if name in self._expiries:
                del self._expiries[name]
        return deleted_count

    def lpush(self, name: str, *values: str) -> int:
        self._check_expiry(name)  # List itself can expire
        if name not in self._lists:
            self._lists[name] = []
        for value in reversed(values):  # lpush prepends, so iterate reversed
            self._lists[name].insert(0, value)
        return len(self._lists[name])

    def rpush(self, name: str, *values: str) -> int:
        self._check_expiry(name)  # List itself can expire
        if name not in self._lists:
            self._lists[name] = []
        for value in values:
            self._lists[name].append(value)
        return len(self._lists[name])

    def lrange(self, name: str, start: int, end: int) -> List[str]:
        self._check_expiry(name)
        if name not in self._lists:
            return []

        # Python slicing end is exclusive, Redis end is inclusive
        # Also handle Redis-style negative indices (-1 is last, -2 is second to last etc.)
        list_len = len(self._lists[name])

        # Convert Redis-style end index to Python slice end index
        if end == -1:
            effective_end = list_len
        elif end < -1:
            effective_end = list_len + end + 1
        else:
            effective_end = end + 1

        return self._lists[name][start:effective_end]

    def flush_db(self) -> bool:
        self._data.clear()
        self._expiries.clear()
        self._hashes.clear()
        self._lists.clear()
        return True

    def ping(self) -> bool:
        return True

    def close(self) -> None:
        # No-op for a fake client, as there's no real connection.
        pass
