"""
Base parser interface for document processing
It defines the contract every document parser must follow.
"""

from abc import ABC, abstractmethod
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

# It's a method a base class declares but doesn't implement, forcing every subclass to provide it.
class BaseParser(ABC):
    """Abstract base class for document parser."""


    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """
        Check if parser supports given file format.

        Args:
            file_extension: File extension (e.g., '.pdf', '.txt')

        Returns:
            True if format is supported
        """

