"""CSV parser for tabular data"""


import csv
import uuid

from io import StringIO 
from pathlib import Path
from typing import BinaryIO, Union, Optional


from loguru import logger

from src.parser.base import ParsedDocument
from src.core.exceptions import ParsingError

import asyncio



class CSVParser:
    """Parser for CSV files."""

    # Define the supported formats
    SUPPORTED_FORMATS = [".csv"]


    async def parse(
            self,
            file_path: Union[str, BinaryIO, Path],
            document_id: Optional[str] = None
    ) -> ParsedDocument:

        """
        Parse CSV files.

        Args:
            file_path: Path to CSV file or file-like object
            document_id: Optional document ID

        Returns:
            ParsedDocument with CSV content as text

        Raises:
            ParsingError: If parsing fails
        
        """

        try:
            # Generate document id if not provided
            if document_id is None:
                document_id = str(uuid.uuid4())
                logger.info(f"document id: {document_id}")

            # Read CSV content
            if isinstance(file_path, (str, Path)):
                file_path = Path(file_path) # Convert into Path object
                # The file on disk is always bytes. Whether your code sees bytes or text depends on how you open it.
                # Read a file from disk
                with open(file_path, "r", encoding="utf-8") as f: # text — Python decodes as it reads
                    content = f.read() # whole file -> one str --> This is fine for CSV file with 50 KB
                    # readline() # oneline -> str
                    # readlines() # all lines -> list[str],  also whole file in memory
                    filename = file_path.name
                    file_size = file_path.stat().st_size

                    #logger.info(f"Content: {content[100:800]}")
                    #logger.info(f"File name: {filename}")
                    #logger.info(f"file size: {file_size}")

            else:
                content = file_path.read().decode("utf-8")
                filename = "uploaded.csv"
                file_size = len(content)

            # Parse CSV to extract structure
            # It turn the CSV files into markdown table
            csv_reader = csv.DictReader(StringIO(content)) # Read each row into dict keyed by the header
            rows = list(csv_reader) # pull them into memory, then codes takes the keys of the first row as headers and builds table line by line
            #logger.info(f"rows: {rows[0:20]}")

            # Convert to markdown table for better readability
            # The reason to do this is that markdown tables are the format LLMs read tables in most reliably, and it matches what Docling outputs for other file types.
            if rows:
                headers = list(rows[0].keys())
                markdown_content = "| " + " | ".join(headers) + " |\n"
                markdown_content += "| " + " | ".join(["---"] * len(headers)) + " |\n"

                for row in rows:
                    markdown_content += "| " + " | ".join(str(row.get(h, "")) for h in headers) + " |\n"
            else:
                markdown_content = content

           
            """
            The bigger question is size. Above a few hundred rows this produces one giant table that won't fit in a chunk, 
            and slicing it mid-table leaves chunks with no header. At that point serialize each row into a sentence instead, 
            or keep the data in Postgres and query it.
            """

            # Create metadata
            metadata = {
                "filename": filename,
                "file_size": file_size,
                "parser": "csv",
                "row_count": len(rows),
                "column_count": len(rows[0]) if rows else 0,
                "column": list(rows[0].keys()) if rows else 0
            }

            #logger.info(f"row: {row}")
            #ogger.info(f"metadata: {metadata}")

            #  Create table representation
            tables = [{
                "table_id":"main_table",
                "content": rows,
                "row_count": len(rows),
                "column_count": len(rows[0]) if rows else 0
            }]  if rows else []


            #logger.info(f"Tables: {tables}")

            logger.info(f"Parsed CSV: {len(rows)} rows, {len(rows[0]) if rows else 0} columns")

            return ParsedDocument(
                    document_id=document_id,
                    content=markdown_content,
                    metadata=metadata,
                    format="csv",
                    tables=tables,
                            )    

        except Exception as e:
            logger.error(f"Failed to parse CSV: {e}")
            raise ParsingError(f"CSV parsing failed {e}")    


       
        



if __name__ == "__main__":
    csv_reader = CSVParser()

    doc = asyncio.run(csv_reader.parse("/Users/mhaddara/Documents/AI Applications/RAG/clean.csv"))
    print(doc.tables[:20])