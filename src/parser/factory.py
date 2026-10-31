"""Parser factory for selection appropriate parser based on file type"""
# Factory that picksthe parser by file extension through BaseParser

"""
One production note: create the factory once per process, at app startup or in the worker, never once per request. 
DoclingParser() loads Docling’s AI models, which takes seconds and a lot of memory.
"""

from pathlib import Path
from typing import Union

from loguru import logger

from src.parser.base import BaseParser
from src.parser.docling_parser import DoclingParser
from src.parser.csv_parser import CSVParser 
from src.parser.json_parser import JSONParser

from src.core.exceptions import ParsingError


class ParserFactory:
    """
    Factory for creating appropriate parser based on file format.
    """

    def __init__(self):
        """Initialize parser factory with available parser."""
        self.parsers: list[BaseParser] = [
            DoclingParser(),
            #CSVParser(),
            #JSONParser()
        ]


        logger.info(f"Parser factory initialized with {len(self.parsers)} parser")


    def get_parser(self, file_path: Union[str, Path]) -> BaseParser:
        """
        Get appropriate parser for file.

        Args:
            file_path: Path to file

        Returns:
            Parser instance

        Raises:
            ParsingError: If no parser supports the file format
        """

        file_path = Path(file_path) # normalize input
        extension = file_path.suffix.lower() # return extension

        # Find parser that supports this format
        for parser in self.parsers:
            if parser.supports_format(extension): # our base class defines
                logger.info(f"Selected {parser.__class__.__name__} for {extension}")
                return parser

        raise  ParsingError(
             f"No parser available for format: {extension}",
            details={"supported_formats": self.get_supported_formats()}
        )


    def get_supported_formats(self) -> list[str]:
        """
        Get all supported file formats.

        Returns:
            list of suppported file extension
        """

        formats = set()
        for parser in self.parsers:
            formats.update(parser.get_supported_formats())


        return sorted(formats)

    
    def supported_formats(self, file_extension: str) -> bool:
        """
        Check if format is supported.

        Args:
            file_extension: File extension to check

        Retrun
            True if format is supported

        """

        return file_extension.lower() in self.get_supported_formats()