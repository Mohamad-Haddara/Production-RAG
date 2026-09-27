"""
BGE embeddings using sentence-transformers.

Include:
    - retries + backoff
    - async wrapper
    - batching
    - FP16
    - query/document split
    - normalize


"""

import asyncio
import hashlib
import time
from typing import Optional, Union, Any, Dict, List
from pathlib import Path

import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from loguru import logger


from src.core.config import AppSettings

class EmbeddingCache:
    """
    In-memory cache for embeddings.
    """

    pass



class BGEEmbedder:
    """
    BGE embeddings generator using sentence-transformers.
    """

    # Query instruction for retrieval tasks
    QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "

    def __init__(
            self,
            model_name: str = "BAAI/bge-m3",
            device: Optional[str] = None,
            
    )