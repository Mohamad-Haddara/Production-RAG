"""FastAPI application for Advanced RAG"""

from contextlib import asynccontextmanager


from fastapi import FastAPI
from loguru import logger
from typing import AsyncIterator

from fastapi.middleware.cors import CORSMiddleware
from src.utils.cache import RedisCache, cache as global_cache
from src.core.config import AppSettings



# Initialize settings
settings = AppSettings()

"""
Strategy for Serving Generative AI Models

Small model can be loaded and used on CPU, but in production scenario, I want to use larger models to produce
higher-quality results that may run only on GPUs and requires significant amount of VRAM.

In addition to leverage GPU, I will need to pick a model-serving strategy, and the best option is Be compute efficient:

Be Compute Efficient - Use the FastAPI lifespan to preload models that can be reused for every request


Lifespan Events
----------------
FastAPI lifespan events are excellent for handling initialization and cleanup of our service.

During server startup, I can create a database connection pools or load GenAI models into memory
for reuse for every requests. Afterward, before server shutdown, I can clean up by unloading AI models,
closing connection pools, deleting temporary artifacts, and logging events.

By using lifespan events, our FastAPI service performs long-running operations like model loading at the start,
before serving requests, and keeps it loaded for reuse among requests. During server shutdown, you can then gracefully
finish all remaining and queued requests before running any cleanup operations. 



Preload Models with FastAPI Lifespan
-------------------------------------
The most compute-efficient strategy for loading models in FastAPI is to use application lifespan.
With this approach I load the models on application startup and unloaded them on shutdown. During 
shutdown, I can do any cleanup steps required, such as filesystem cleanup or logging.

The main benefit os this strategy is to avoid reloading heavy models on each request. So that I can
load heavy model once and then make generations on every request coming using preloaded model.

As a result, I will save several minutes in processing time in exchane for chunk of or RAM (or VRAM if using GPU).

Also users will experience shorter response time.



The code below - It is FastAPI lifespan handler: code before yield runs once when the app starts, code after yield
runs once when it shuts down.

On Startup:
1. Logs that the API is starting
2. If 'redis_host' is set, it creates a RedisCache (default TTL 1 hour) and connects.
3. It stores that cache in the module-level variable 'src.utils.cache.cache', so the rest of the app can use it.
4. If Redis fails, it logs a warning and keeps running without cache, so Redis outage doesn't crash the API.

'yield': the app runs and serves requests here.


On shutdown:
- Logs shutdown and disconnects the Redis Cahce


One likely bug: shutdown checks global_cache, but startup assigns cache_module.cache. If global_cache came from from src.utils.cache import cache as global_cache, it was bound to the old value (None) at import time and never updates. In that case the disconnect never runs. Fix it by using the same reference:
python
if cache_module.cache:
    await cache_module.cache.disconnect()
(Move import src.utils.cache as cache_module to the top of the file so it's available in both places.)


When the application starts, it creates the Redis cache connection once, before any requests come in.
Then every request reuses that same connection. When the app stops, it closes the connection.
If Redis isn't configured or fails to connect, the app still starts, just without caching.


Notes:
- When app is started, I should see the redis is loaded immediately onto memory
- Before I use lifespan, The redis is loaded only when I made a first request

- Don't load large GenAI model becuase it can consume a lot of resources.
So that, becuase of some model requires 24GB of memory to perform inference, I should try to deploy models
on separate application instances and GPUs instead.

"""

# I can implement model prelaoding using application lifespan
@asynccontextmanager # this decorator used to handle startup and shutdown events as a part of an async context manager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.

    - The context manager will run code before and after the yield keyword
    - The yield in the decorated lifespan function separates the startup and shutdown phases
    - Code prior to the yield ~ runs at application startup before any requests are handled
    - When I want to termniate the application, FastAPI will run the code after the yeild keyword
    as a part of shutdown phase
    """

    # Startup
    logger.info("Starting Advanced RAG API...")

    # Initialize Redis cache (Preload at a startup)
    #if settings.redis_host:
    try:
        redis_cache = RedisCache(
            host=settings.redis_host,
            port = settings.redis_port,
            password=settings.redis_password,
            default_ttl=3600
        )

        await redis_cache.connect()

        # Set global cache
        import src.utils.cache as cache_module
        cache_module.cache = redis_cache

        logger.info("Redis cache initialized")

    except Exception as e:
        logger.warning(f"Failed to intialize redis: {e}. Continuing withou cache.")

    #else:
        #logger.info("Redis not configured, running without cache.")


    logger.info("API startup complete")


    yield

    # Shutdown 
    logger.info("Shutting down Advanced RAG API...")

    # Disconnect cache -  during shutdown
    if global_cache:
        await global_cache.disconnect()

    logger.info("API shutdown complete")


    



# Create FastAPI App (server) - pass lifespan function to use
app = FastAPI(
    title="RAG API",
    description="Production-Ready RAG system",
    version="1.0.0",
    lifespan=lifespan
)


"""
Custom Middleware And CORS Support
------------------------------------

FastAPI enables us to add middleware components to our app router to intercept the communication between our API endpoints and clients.
Each middleware, sitting infront of our endpoints, allows us to access the request and response objects to modify them as needed.

I can add logic around how request should be processed before they are handed off to the route handlers. Once the response is generated
I can perform operation on response such as modifying headers, logging operations, and setting cookies before sending it off to the client.


A Common pattern in backend development is to use middleware to:
1) Add extra headers to a response
2) Perform basic checks on incoming requests
3) Support CORS requests - CORS implementation (cross-origin resource sharing)
4) Logging and Monitoring 
5) Rate Limiting
6) Content Filtering


Cross-origin resource sharing
---------------------------------
CORS is a security mechanism implemented in browsers to control how resources on a web page can be requested from another domain,
and is relevant only when sending requests directly from the browser instead of a server.

Browsers use CORS to check whether they are allowed to send requests to the server from a different origin (e.g domain)
than server.

For example, if our client is hosted on 'https://example.com' and it needs to fetch data from an API hosted on 
'https://api.example.com', the browser will block this request unless the API server has CORS enabled.

For now, I can bypass these CORS errors by adding a CORS middleware on our server





CORS -> it's the browser asking our server, "Is this website allowed to read our response?"


The problem it solves
Browsers enforce the Same-Origin Policy. JavaScript on https://app.com can't read responses from https://api.com unless api.com explicitly allows it. An "origin" is scheme + domain + port, so http://localhost:3000 and http://localhost:8000 count as different origins.
Without this rule, any site you visit could quietly call your bank's API using your logged-in cookies and read the results.

How it works
Your frontend at localhost:3000 calls fetch("http://localhost:8000/chat").
The browser adds the header Origin: http://localhost:3000.
Your server responds with Access-Control-Allow-Origin: http://localhost:3000.
The browser checks that header. If it matches, JS gets the response. If not, you see a CORS error.



Key points that confuse people
The server still receives and processes the request. The browser only blocks JS from reading the response.
It's browser-only. curl, Postman, and server-to-server calls ignore CORS completely.
The fix is always on the server, not the frontend


Avoid allow_origins=["*"] in production, especially with credentials.

Note:
- Check the browsers network tab to view what happened to the outgoing requests.
- After some investigations, you should notice that your browser has blocked outgoing requests
to your server as its preflight cross-origin resource sharing (CORS) checks with your server have failed.


"""
# Apply CORS settings
# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Configure for production
    allow_credentials=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)






# Create Root Endpoint 
@app.get("/")
async def root():
    """Root Endpoint"""
    return {
        "message": "Advacned RAG API",
        "docs":"/docs",
        "health":"/health",
        "metrics":"/metrics"
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host = "0.0.0.0",
        port = 8000,
        reload = True,
        log_level = "info"
        )
