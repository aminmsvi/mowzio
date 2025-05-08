from app.config import settings
from app.db.redis.redis_adapter import RedisAdapter


class RedisFactory:
    """
    Factory class for creating Redis adapter instances.

    This follows the Factory pattern to centralize the creation of
    Redis adapter instances with application configuration.
    """

    @staticmethod
    def create_adapter(
        db: int = 0,
        socket_timeout: int = 5,
        retry_on_timeout: bool = True,
    ) -> RedisAdapter:
        """
        Create a Redis adapter instance with application configuration.

        Args:
            db: Redis database number (default: 0)
            socket_timeout: Socket timeout in seconds (default: 5)
            retry_on_timeout: Whether to retry on timeout (default: True)

        Returns:
            A configured RedisAdapter instance
        """
        return RedisAdapter(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=db,
            socket_timeout=socket_timeout,
            retry_on_timeout=retry_on_timeout,
        )
