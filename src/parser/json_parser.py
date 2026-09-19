"""JSON parser for structured data"""

import json
import uuid

from pathlib import Path
from typing import BinaryIO, Union, Optional

from src.core.exceptions import ParsingError
from src.parser.base import ParsedDocument


from loguru import logger

class JSONParser:
    """Parser for JSON files."""

    # Define supported format
    SUPPORTED_FORMATS = [".json", ".jsonl"]

    async def parse(
            self,
            file_path: Union[str, Path, BinaryIO],
            document_id: Optional[str] = None
    ):

        """
        Parse JSON file.
        
        Args:
            file_path: Path to JSON file
            document_id: Optional document ID

        Return
            ParsedDocument with JSON content as formatted text

        Raises
            ParsingError: If parsing fails
        """
        try:
            # Generate document id if not provided
            if document_id is None:
                document_id = str(uuid.uuid4())


            if isinstance(file_path, (str, Path)):
                file_path = Path(file_path)
                with open(file_path,"r", encoding="utf-8-encoding") as f:
                    content = f.read()
                    filename = file_path.name
                    file_size = file_path.stat().st_size


            else:
                content = file_path.read().decode("utf-8")
                filename = "uploaded.csv"
                file_size = len(content)


            # Parse JSON
            try:
                data = json.load()

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {e}")

            # Convert to human-readable format
            # json.dump() used to convert(serialize) python object into JSON-formatted stread and write it directly to a file
            formatted_content = json.dumps(data, indent=2, ensure_ascii=False)


            # Extract metadata
            metadata = {
                "filename": filename,
                "file_size": file_size,
                "parser": "json",
                "data_type": type(data).__name__
            }

            if isinstance(data, list):
                metadata["item_count"] = len(data)
            elif isinstance(data, dict):
                metadata["key_count"] = len(data.keys())
                metadata["keys"] = list(data.keys())[:10]  # First 10 keys

            logger.info(f"Parsed JSON: {metadata.get('data_type')}")

            return ParsedDocument(
                document_id=document_id,
                content=formatted_content,
                metadata=metadata,
                format="json"
            )



        except Exception as e:
            logger.error(f"Failed to parse json: {e}")
            raise ParsingError(f"JSON parsing failed: {e}")