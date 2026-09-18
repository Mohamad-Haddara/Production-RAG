"""
Base parser interface for document processing
It defines the contract every document parser must follow.
"""

from abc import ABC, abstractclassmethod
from pathlib import Path
from typing import Union, BinaryIO, Optional

from pydantic import BaseModel


class ParsedDocument(BaseModel):
    """Model for parsed document content."""

    document_id: str
    content: str
    metadata: dict
    format: str
    sections: Optional[list[dict]] = None
    tables: Optional[list[dict]] = None
    figures: Optional[list[dict]] = None
    references: Optional[list[dict]] = None

