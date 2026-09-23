"""
Redis Cache Utilities.

- Using async client 'redis.asyncio'
- RedisCache is small custom wrapper
- Most caching is just get → if missing, compute → set with a TTL.

In RAG work it's useful for:
    - Caching LLM responses for repeated questions, which save cost and latency
    - Caching embeddings so I don't need to re-embed same text
    - Semantic Caching -> When I return a cached answer for similar questions
    - Chat Hisotry/ session memory -> for agents
    - Rate Limiting API users

For learning, focus on these: key-value basics, TTL, cache key design 
(e.g., hashing the query + model name), and invalidation (when to clear stale cache).


A quick practical path:
Run Redis locally with Docker: docker run -p 6379:6379 redis
Play with commands in redis-cli (SET, GET, EXPIRE, HSET, LPUSH).
Add a simple cache to one of your FastAPI endpoints.
Try caching LLM responses or embeddings in your RAG project.


1. Read methods first, ignores body.
Methods usually cluster: connection (connect, disconnect), core cache (get, set, delete), and helpers (_make_key, _serialize).

2. Find the 2-3 methods that actually matter.
In a cache, it's almost always get and set. Everything else supports those. Read those two closely, trace what they call.

3. Then draw it — but keep it simple:
- Box with the class name
- Attributes on top (host, port, client, default_ttl)
- Methods grouped by purpose below

4. Run it, don't just read it.
Add print statements or a debugger breakpoint inside get and set, 
then call them. Watching the values flow through teaches more than any diagram.


redis-py guide
Connect Python application to a Redis database.

redis-py is the Python client for Redis.

redis-py requires a running Redis server. 

pip install redis

Install redis on docker for local development

A) docker run -d --name redis -p 6379:6379 redis
-d runs it in the background
- --name redis names the container
-p 6379:6379 exposes the default Redis port to your app


B) Then in your .env: REDIS_HOST=localhost, REDIS_PORT=6379
To manage it:
- docker stop redis # stop
- docker start redis # start again
- docker exec -it redis redis-cl3 # Open Redis CLI


C) Better for a real project: use docker-compose so your app + Redis start together
Then docker compose up

For actual production, you usually don't self-host Redis in a plain container — you'd use a managed service 
(Azure Cache for Redis, since you're on Azure) so you get persistence, backups, and failover handled for you. 
But that's later. For learning and local dev, the Docker container above is exactly right.


I can connect redis server using redis-cli, just as I connect to any Redis instancxe.
docker exec -it redis redis-cli
"""

import json
from typing import Optional, Any


import redis.asyncio as aioredis

from loguru import logger



class RedisCache:
    """
    Async Redis cache wrapper.
    """

    def __init__(
            self,
            host: str = "localhost",
            port: int = 6379,
            db: int = 0,
            password: Optional[str] = None,
            default_ttl: int = 3600,
            key_prefix: str = "hybrid_rag:"
    ):

        """
        Initialize Redis Cache.

        Args:
            - host: Redis host
            - port: Redis port
            - db: Redis database number
            - password: Redis password (optional)
            - default: Default TTL in seconds
            - key_prefix: Prefix for all cache keys
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.default_ttl = default_ttl
        self.key_prefix = key_prefix

        logger.info(f"Initialize RedisCache: ({self.host}: {self.port}, db = {self.db})")


    async def connect(self) -> None:
        """
        Connect to redis

        Raises:
            RedisConnectionError If connection fails
        
        """

        try:
            # opens the connection to Redis
            # Build redis client from a connection string - await ~ connecting is async -> so I wait for it
            self.client = await aioredis.from_url(
                f"redis://{self.host}:{self.port}/{self.db}",  # Address: (host, port, database number)
                password=self.password, # auth, if a server needs it
                encoding="utf-8", # how bytes are turned into text
                decode_responses=True # return str instead of raw bytes so i get "value"

            )

            # Test connection
            await self.client.ping()
            logger.info("Successfully connected to Redis")

        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            # raise an error

        # Create disconnect


        #make a key
        def _make_key(self, key: str) ->str:
            """
            Create a full cache key with prefix.

            Args:
                - key: Base key

            Returns:
                - Full key with prefix
            """

            return f"{self.key_prefix(key)}"