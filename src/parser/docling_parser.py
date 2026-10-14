"""Parser using Docling for PDF, DOCX, and HTML documents."""
#Create component to load once and reuse - Docling loads heavy models, so creating it per request would reload them every time.
# Class give us one place for our rules
"""
1. Create it once: build DocumentConverter in __init__, and create the class once through an @lru_cache factory so each worker process loads the models only once.
2. Pass config in: OCR, table settings, and limits come from your Pydantic Settings, not hardcoded values.
3. One job only: the class only parses. Chunking, embedding, and the Qdrant upsert are separate classes that your Celery task calls in order.
4. Return your own type: return a ParsedDocument, not Docling objects, and put a Protocol in front so tests can use a fake.
5. Handle failures: check result.status (a PDF can partly fail), set a page limit, and raise your own ParsingError.
6. Keep it off the request path: parsing is slow and blocking, so run it in the Celery worker, never directly inside an async endpoint.



Design a class by answering 6 questions:
1. What does it return? -> ParsedDocument (our own dataclass)
2. What can go wrong? → your own exceptions, ParsingError and UnsupportedFileError
3. What does it need for its whole life? → __init__
4. What does the app ask it to do? → public methods, parse() and warm_up()
5. What are the steps inside? → private methods, _validate() and _to_parsed()
6. How is it created? → a factory that builds it once


What goes in __init__ ?
* Put in: settings (OCR, page, and size limit), and expensive objects built once, like converter
* Keep out: per-document data like the file path or result. Those are method arguments and return values.
* Keep out: real work like parsing, network calls, or reading env vars.


Methods
- Keep the public API small (1–3 methods), named as verbs, with docstrings that say what they raise.
- One job per class: no chunking, embedding, or Qdrant code here.
- Never store the last document on self. A stateless object is safe to reuse for every task.
- Other things you'll see in production classes
@staticmethod: a helper that doesn't use self.
@classmethod: an alternative constructor, like DoclingParser.from_settings(s).
@property: a read-only value, like parser.max_pages.
__repr__: readable output in logs and the debugger.
UPPER_CASE class constants, like SUPPORTED_SUFFIXES.
close() or with support, only when it holds something to release. Qdrant's client does, Docling doesn't.
A module-level logger that logs metadata (name, pages, time), never document text.
Inheritance: skip it until you have a second implementation. A Protocol covers testing.


"""

"""
A production-style Docling parser class

Design any class by answering 6 questions: 
1. What does it return? -> ParsedDocument (our own class)
2. What can go wrong? -> ParsingError or UnsupportedFileError
3. What does it need for its life? -> __init__: settings + converter, built once
4. What does the app ask it to do? -> public methods: warm_up(), parse()
5. What are the steps inside?      -> private methods: _validate(), _to_parsed()
6. How is it created?              -> a factory in deps.py, one per process

"""
import asyncio
from loguru import logger
import re
import uuid # Universal Unique Identifier - 128-bit value - Guaranteed to be unique  - It is hexadecimal ID written with as 32 characters - collision is very low ~ low possible of duplication
from pathlib import Path # way to handle file and directory path
from typing import Union, BinaryIO, Optional, Any


from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions


from src.parser.base import ParsedDocument
from src.core.exceptions import ParsingError


# When docling parse a file, it splits into pieces like title, headlines, paragraphs, tables and pictures.
# These classes are the types of these pieces. The parser uses them to check what each piece is
from docling_core.types.doc import (
    DoclingDocument, # Whole parse document (result.document) ~ used in typed hint
    PictureItem, # An image or chart ~ used in _extract_figures
    SectionHeaderItem,
    TableItem, # A table ~ used in _extract_tables
    TextItem, 
    TitleItem, # The document title ~ used in title metadata and the first section 

)

REFERENCE_HEADINGS = {"references", "bibliography", "works cited", "reference list"}




class DoclingParser:
    """Parser using Docling for PDF, DOCX, and HTML documents. Build one per process."""

    
    SUPPORTED_FORMAT = [".pdf", ".docx", ".html", ".htm"]
    


    def __init__(
            self,
            *, # keyword-only, so calls read as DoclingParser(do_ocr=True)
            do_ocr: bool = True,
            artifcat_path: Optional[Union[str, Path]] = str,
            timeout_s: float = 300, # per document: Docling returns PARTIAL SUCCESS when it is hit
            max_pages: int = 500,
            max_file_mb: int = 50,
            max_concurrency: int = 1, # conversion are CPU/GPU heavy: scale with worker processes, not threads,
            warmup: bool = True, # load models at startup so a broken setup fails at bools, not on the first request 
            ) -> None:
        """Initialize docling parser"""

        # Define PDF pipeline options
        options = PdfPipelineOptions(
            do_ocr= do_ocr,
            do_table_structure= True,
            document_timeout=timeout_s,
            artifacts_path=artifcat_path,

        )
        # No try/except here: if the converter can't be built, startup should fail loudly.
        self.converter = DocumentConverter(
            format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
        )

        if warmup:
            self.converter.initialize_pipeline(InputFormat.PDF)

        self.max_pages = max_pages
        self.max_file_size = max_file_mb
        self._slots = asyncio.Semaphore(max_concurrency) # require revision

        logger.info("Docling Parser initialized successfully")




    async def parser(
            self,
            file_path: Union[str, Path, BinaryIO],
            document_id: Optional[str] = None
    ) -> ParsedDocument:
        """
        Parse document using Docling.

        Args:
            - file_path: Path to document file
            - document_id: Optional document_id

        Returns:
            - ParsedDocument with extracted content and metadata

        Raises:
            ParsingError: If parsing fails
        """

        try:
            # Convert file_path to Path object
            # It converts the file's address into a Path object.
            if isinstance(file_path, (str, Path)):
                file_path = Path(file_path)
                if not file_path.exists():
                    raise ParsingError(f"File not found: {file_path}")

                elif file_path.suffix.lower() not in self.SUPPORTED_FORMAT:
                    raise ParsingError(f"Unsupported format: {file_path.name}")

            else: 
                raise ParsingError("Docling parser requires file path, not file object")

            # Generate document ID if not provided
            if document_id is None:
                document_id = str(uuid.uuid4())

            # covnert document
            logger.info(f"Parsing document: {file_path}")
            result = self.coverter.convert(
                path = str(file_path),
                )
            
            # Extract content
            content = result.document.export_to_markdown()

            # Extract metadata
            metadata = self._extract_metadata(result, file_path)

            # Extract sections
            sections = self._extract_sections(result)

            # Extract tables
            tables = self._extract_tables(result)

            #Extract figures
            figures = self._extract_figures(result)

            #Extract references
            references = self._extract_references(result)





        except Exception as e:
            pass

        

        

        return ParsedDocument(
            document_id = document_id,
            content = content,
            metadata=metadata,
            format=file_path.suffix[1:], # remove leading dot
            sections = sections,
            tables = tables,
            figures=figures,
            references=references
        )

    @staticmethod
    def _page(item) -> Optional[int]:
        """1-based page number; None for formats without pages (DOCX, HTML)."""
        return item.prov[0].page_no if item.prov else None


    def _extract_metadata(self, result, file_path: Path) -> dict:
        """Extract metadata from parsed document."""

        metadata = {
            "file_path": file_path,
            "file_size": file_path.stat().st_size if file_path.exists() else 0,
            "parser":"docling"
        }

        # Try to extract document metadata if available
        if hasattr(result.document, "metadata"):
            doc_metadata = result.document.metadata
            if doc_metadata:
                metadata.update(
                    {
                        "title": getattr(doc_metadata, "title", None),
                        "author": getattr(doc_metadata, "author", None),
                        "creation_date": getattr(doc_metadata, "creation_date", None),
                        "modification_date": getattr(doc_metadata, "modification_date", None),
                        "page_count": getattr(doc_metadata, "page_count", None),
                        "parser":"docling",
                        "status": result.status.value
                    }
                )

        return metadata



    def _extract_sections(self, result) ->list[dict]:
        """Extract document sections with hierarchy"""

        sections = []

        try:

            # Iterate through document structure
            for idx, item in enumerate(result.document.children):
                if hasattr(item, "label") and "heading" in item.label.lower():
                    section = {
                        "section_id": f"section_{idx}",
                        "title": item.text if hasattr(item, "text") else "",
                        "level": int(item.label.split("_")[-1]) if "_" in item.label else 1,
                        "content": "",
                        "position": idx
                    }

                    sections.append(section)


        except Exception as e:
            logger.warning(f"Could not extract sections: {e}")

        return sections


    def _extract_tables(self, doc: DoclingDocument) -> list[dict]:
        """Extract tables with captions and page numbers from document."""

        tables: list[dict] = []

        try:
            for item, _ in doc.iterate_items(): # walk the document from top to bottom
                if isinstance(item, TableItem):
                    tables.append(
                        {
                            "table_id": item.self_ref,
                            "caption": item.caption_text(doc) or None,
                            "content": item.export_to_markdown(doc),
                            "page": self._page,
                            "position": len(tables)
                        }
                    )
        except Exception as e:
            logger.warning(f"Could not extract tables: {e}")

        return tables


    def _extract_figures(self, result) -> list[dict]:
        """Extract figures/images from document."""
        figures = []
        try:
            for idx, item in enumerate(result.document.children):
                if hasattr(item, "label") and "figure" in item.label.lower():
                    figure = {
                        "figure_id": f"figure_{idx}",
                        "caption": getattr(item, "caption", None),
                        "position": idx
                    }

                    figures.append(figure)

        except Exception as e:
            logger.warning(f"Could not extract figures: {e}")

        return figures




    def _extract_references(self, result) -> list[str]:
        """Extract references/bibliography."""
        references = []

        try:
            # Look for references section
            in_references = False
            for item in result.document.children:
                if hasattr(item, "text"):
                    text_lower = item.text.lower()
                    if "references" in text_lower or "bibliography" in text_lower:
                        in_references = True
                        continue

                    if in_references and hasattr(item, "label"):
                        if "heading" in item.label.lower():
                            break  # End of references section
                        references.append(item.text)
        except Exception as e:
            logger.warning(f"Could not extract references: {e}")

        return references


if __name__ == "__main__":

    # parser is an async - so calling it just creates a coroutine
    converter = DoclingParser()
    doc = asyncio.run(converter.parser("Alice_in_Wonderland.pdf"))
    print(f"\nThe content: {doc.content[:100]}")
    print(f"\nThe metatadata: {doc.metadata}")
    print(f"\nThe reference: {doc.references}")
    print(f"\nThe table: {doc.tables}")
    print(f"\nThe figures: {doc.figures}")
    