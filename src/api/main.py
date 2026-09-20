"""FastAPI application for Advanced RAG"""

from contextlib import asynccontextmanager


from fastapi import FastAPI
from loguru import logger
from typing import AsyncIterator


"""
Strategy for Serving Generative AI Models

Small model can be loaded and used on CPU, but in production scenario, I want to use larger models to produce
higher-quality results that may run only on GPUs and requires significant amount of VRAM.

In addition to leverage GPU, I will need to pick a model-serving strategy, and the best option is Be compute efficient:

Be Compute Efficient - Use the FastAPI lifespan to preload models that can be reused for every request


Preload Models with FastAPI Lifespan
-------------------------------------
The most compute-efficient strategy for loading models in FastAPI is to use application lifespan.
With this approach I load the models on application startup and unloaded them on shutdown. During 
shutdown, I can do any cleanup steps required, such as filesystem cleanup or logging.

The main benefit os this strategy is to avoid reloading heavy models on each request. So that I can
load heavy model once and then make generations on every request coming using preloaded model.

As a result, I will save several minutes in processing time in exchane for chunk of or RAM (or VRAM if using GPU).

Also users will experience shorter response time.



"""

# I can implement model prelaoding using application lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """

    # Startup
    logger.info("Starting Advanced RAG API...")

    



# Create FastAPI app
app = FastAPI(
    title="RAG API",
    description="Production-Ready RAG system",
    version="1.0.0"
)




# root endpoint 
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
