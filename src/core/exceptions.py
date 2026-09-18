"""Custom exceptions for the RAG system."""

from typing import Any, Optional

class RAGException(Exception):
    """Base exception for all RAG errors."""

    def __init__(self, message: str, details: Optional[dict[str, Any]] = None):
        """
        Initialize exception.

        Args:
            message: Error message
            details: Additional error details
        """

        self.message = message
        self.details = details or {}

        super().__init__(self.message)




# =============================================================================
# Document Processing Exceptions
# =============================================================================


class DocumentProcessingError(RAGException):
    """Error during document processing."""
    pass

class ParsingError(DocumentProcessingError):
    """Error during document parsing."""
    pass






# =============================================================================
# Utility Functions
# =============================================================================

def format_error_response(exception: RAGException) -> dict[str, Any]:
    """
    Format exception as error response dictionary.

    Args:
        exception: Exception instance

    Returns:
        Error response dictionary 


    """

    return {
        "error": exception.__class__.__name__,
        "message": exception.message,
        "details": exception.details
    }