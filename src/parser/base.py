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
    async def parser(
        self,
        file_path: Union[str, Path, BinaryIO],
        document_id: Optional[str] = None
    ) -> ParsedDocument:
        """
        Parse a document and extract content and metadata

        Args:
            file_path: Path to document file or file-like object
            document_id: Optional document ID (generated if nor provided)


        Return:
            ParsedDocument containing extracted content and metadata

        Raises:
            ParsingError: If parsing fails        
        """
        pass

    @abstractmethod
    def supports_format(self, file_extension: str) -> bool:
        """
        Check if parser supports given file format.

        Args:
            file_extension: File extension (e.g., '.pdf', '.txt')

        Returns:
            True if format is supported
        """
        pass


    @abstractmethod
    def get_supported_formats(self) -> list[str]:
        """
        Get list of supported file formats.

        Returns:
            List of supported file extensions
        """

        return []
