"""Pydantic model for document chunks."""


import uuid
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator



# CHUNK_NAMESPACE = uuid.UUID("6f1c2a4e-3b7d-4e8a-9c51-2d0f8b7e4a13")

"""
def make_chunk_id(document_id: str, chunk_index: int) -> str:
    "Deterministic UUID for a chunk (Qdrant accepts UUID as point IDs)"
    return uuid.uuid5(CHUNK_NAMESPACE, f"{document_id}:{chunk_index}")
"""


class ChunkConfig(BaseModel):
    """Setting/Configuration for the chunking. The default suit BGE-M3."""

    max_token: int = Field(default=512, ge=32) # chunk size in the embedding model's tokens, heading path included
    text_overlap_tokens: int = Field(default=50, ge=0) # plain-text fallback only
    merge_peers: bool = True # merge undersized neighboring chunks that share same headings
    normalize_unicode: bool = True
    paginated_formats: tuple[str, ...] = ("pdf",) # formats whose chunks must carry page numbers



class Chunk(BaseModel):
    """One piece of a document, ready to embed and store."""

    chunk_id: str
    document_id: str
    chunk_index: int
    source: str # original file name for citations
    #strategy: Literal["docling", "records", "text"]
    text: str # the chunk as shown in citations
    #embed_text: str # heading path + text: what gets embed
    headings: list[str] = []
    pages: list[int] = []
    #token_count: int # tokens in embed_text
    #content_hash: str # sha256 of embed_text, for de-duplication


    def payload(self) -> dict:
        """JSON-safe metadata to store next to the vector."""
        pass

