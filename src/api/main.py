"""FastAPI application for advanced RAG"""

from fastapi import FastAPI
from loguru import logger




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
