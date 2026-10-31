"""Chunking phase: turns parsed documents into validated chunks, ready for embedding."""


# import asyncio # for writing concurrent code using async and await
# import hashlib # for secure hashing and message digests
# import re
# import threading # Provided a way to run multiple threads (smaller units of a process)


import uuid

# If you are only using the docling-core package, you must ensure to install the chunking extra if you want to use HuggingFace tokenizers
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
# It uses hybrid approach, applying tokenization-aware refinements on top of document-based hierarchical chunking


from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

from docling_core.types.doc import DoclingDocument # is the object Docling returns after parsing: result.document 

from loguru import logger

from transformers import PreTrainedTokenizerBase


from src.chunking.chunk_models import Chunk

from src.parser.base import ParsedDocument

"""
class ChunkingService:
    "
    Splits parsed documents into chunks sized for the embedding model.

    Build one per process (Start up or in the worker), with the shared tokenizer from load_tokenizer

    "

    def __init__(
            self,
            *,
            tokenizer: PreTrainedTokenizerBase,
            config: Optional[ChunkConfig] = None,
            model_name: str = "BAAI/bge-m3"
            ) -> None:

        # Validation
        if not isinstance(tokenizer, PreTrainedTokenizerBase):
            raise TypeError(
                f"Tokenizer must be a Hugging Face tokenizer (from load_tokenizer()), get {type(tokenizer).__name__}"
            )

        self.config = config or ChunkConfig()

        # One tokenizer for everything: chunk sizes are measured exactly as the embedding model counts them
        # Internal 
        self._tokenizer = HuggingFaceTokenizer.from_pretrained(model_name=model_name, tokenizer=tokenizer, max_tokens=self.config.max_token)
        self._docling = HybridChunker(tokenizer=self._tokenizer, merge_peers=self.config.merge_peers)
        #self._lock = threadiung.lock()

        logger.info(f"Chunking ready: up to: {self.config.max_token} tokens per chunk ({tokenizer.name_or_path})")



    # ---- Public API ----------------------------------------------------------------------------------------------

    def chunk(self, parsed: ParsedDocument) -> list[Chunk]:
        "If the parsed by Docling, use HybridChunker, plain text the fallback."
        # First I need to get the source ~ the file name, attached to every chunk, so i know where each chunk came from.
        # I need it later for citations and for filtering or deleting chunks by file
        source = parsed.metadata.get("file_name", "") # returns empty string instead of crashing with KEyError if the metadata has no file name
        docling_document = getattr(parsed, "docling_document", None) # it reads attribute safely. Safe access - so missing attribute doesn't crash 

        if docling_document is not None:
            # Apply chunk_docling
            pass

        # apply chunk text

    

    def chunk_docling(
            self,
            doc: DoclingDocument,
            *                       # makes everything after doc keyword-only, so callers must write document_id = ... not pass by position
            document_id: str,
            source: str,
            file_format:str = ""
    ) -> list[Chunk]:
        "
        It turns a Docling document into chunks

        PDF, DOCX, HTML: follows headings, keeps tables whole, keeps page numbers.
        "
        # Collect drafts
        drafts = []

        # Loop over the Docling chunks
        # HybridChunker splits the document along its structure: sections, paragraphs, tables
        for piece in self._docling.chunk(dl_doc=doc):
            # Headings ~ ["Leave Policy", "Annual Leave"]. or [] handles None, and each title gets cleaned.
            headings = [self._clean(h) for h in piece.meta.headings or []]
            # Pages ~ A piece can span several document items, and each item records where it came from (prov). This collects every pages number, removes duplicates with a set {} amd sort them - give lile [3,4]
            pages = sorted({prov.page_no for item in piece.meta.doc_items for prov in item.prov})

            # Fit ~ likely splits or adjusts the text to our size limits and returns one or more drafts. extend adds them all to the list
            drafts.extend(self._fit(self._clean(piece.text), headings, pages))\

        # page required ~ PDF have real pages, while HTML doesn't
        require_pages = file_format.lower() in self.config.paginated_formats
        
        # Finish - Turn draft into final Chunk objects with IDs and metadata (source, strategy, pages), and likely validates them
        return 

"""

from docling_core.types.doc.document import DoclingDocument

class ChunkingService:
    """
    Split the parsed document into chunks sized for the embedding model. Build one per process
    """

    def __init__(
            self,
            *,
            tokenizer: PreTrainedTokenizerBase,
            max_tokens: int = 512

    ) -> None:
        self.max_tokens = max_tokens
        # Built once, reused for every document. Sizes are measured with embedding models own tokenizer
        # Internal attributes
        self._tokenizer = HuggingFaceTokenizer(tokenizer=tokenizer, max_tokens=max_tokens)
        self._docling = HybridChunker(tokenizer=self._tokenizer)


    def chunk_docling(
            self,
            doc: DoclingDocument,
            *,
            document_id: str,
            source: str
    ) -> list[Chunk]:
        """
        It turns docling document into chunks

        PDF, DOCX, HTML: follows headings, keeps tables whole, keeps page numbers.
        """

        # collect chunks
        chunks = []

        for index, piece in enumerate(self._docling.chunk(dl_doc=doc)):
            pages = sorted({prov.page_no for item in piece.meta.doc_items for prov in item.prov})

            chunks.append(
                Chunk(
                    # Better: put this in a Chunk.make_id(document_id, index) helper in chunk_models.py, so every chunker (not just chunk_docling) uses the same ID logic.
                    chunk_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document_id}:{index}")),
                    document_id=document_id,
                    chunk_index=index,
                    source=source,
                    text= piece.text,
                    headings=piece.meta.headings or [],
                    pages=pages,
                )
            )

        return chunks





text = """

Remote work guidelines

Remote work, part 1. Staff may work from home up to 6 days a week when their manager agrees and their tasks allow it. Staff may work from home up to 6 days a week when their manager agrees and their tasks allow it.

Equipment, part 1. The IT team lends a laptop and a headset, and staff return both within 4 days of leaving. The IT team lends a laptop and a headset, and staff return both within 4 days of leaving.

Security, part 1. Laptops must lock after 3 minutes without use, and company ﬁles stay on approved storage. Laptops must lock after 3 minutes without use, and company ﬁles stay on approved storage.

Finance, part 1. The ﬁnance team refunds internet costs up to 20 QAR a month against a valid receipt. The ﬁnance team refunds internet costs up to 20 QAR a month against a valid receipt.

Meetings, part 1. Online meetings start on time, cameras are on when possible, and notes are shared within 3 hours. Online meetings start on time, cameras are on when possible, and notes are shared within 3 hours.

Remote work, part 2. Staff may work from home up to 7 days a week when their manager agrees and their tasks allow it. Staff may work from home up to 7 days a week when their manager agrees and their tasks allow it.

Equipment, part 2. The IT team lends a laptop and a headset, and staff return both within 5 days of leaving. The IT team lends a laptop and a headset, and staff return both within 5 days of leaving.

Security, part 2. Laptops must lock after 4 minutes without use, and company ﬁles stay on approved storage. Laptops must lock after 4 minutes without use, and company ﬁles stay on approved storage.

Finance, part 2. The ﬁnance team refunds internet costs up to 30 QAR a month against a valid receipt. The ﬁnance team refunds internet costs up to 30 QAR a month against a valid receipt.

Meetings, part 2. Online meetings start on time, cameras are on when possible, and notes are shared within 4 hours. Online meetings start on time, cameras are on when possible, and notes are shared within 4 hours.

Remote work, part 3. Staff may work from home up to 8 days a week when their manager agrees and their tasks allow it. Staff may work from home up to 8 days a week when their manager agrees and their tasks allow it.

Equipment, part 3. The IT team lends a laptop and a headset, and staff return both within 6 days of leaving. The IT team lends a laptop and a headset, and staff return both within 6 days of leaving.

Security, part 3. Laptops must lock after 5 minutes without use, and company ﬁles stay on approved storage. Laptops must lock after 5 minutes without use, and company ﬁles stay on approved storage.

Finance, part 3. The ﬁnance team refunds internet costs up to 40 QAR a month against a valid receipt. The ﬁnance team refunds internet costs up to 40 QAR a month against a valid receipt.

Meetings, part 3. Online meetings start on time, cameras are on when possible, and notes are shared within 5 hours. Online meetings start on time, cameras are on when possible, and notes are shared within 5 hours.

Remote work, part 4. Staff may work from home up to 2 days a week when their manager agrees and their tasks allow it. Staff may work from home up to 2 days a week when their manager agrees and their tasks allow it.

Equipment, part 4. The IT team lends a laptop and a headset, and staff return both within 7 days of leaving. The IT team lends a laptop and a headset, and staff return both within 7 days of leaving.

Security, part 4. Laptops must lock after 6 minutes without use, and company ﬁles stay on approved storage. Laptops must lock after 6 minutes without use, and company ﬁles stay on approved storage.

Finance, part 4. The ﬁnance team refunds internet costs up to 50 QAR a month against a valid receipt. The ﬁnance team refunds internet costs up to 50 QAR a month against a valid receipt.

Meetings, part 4. Online meetings start on time, cameras are on when possible, and notes are shared within 6 hours. Online meetings start on time, cameras are on when possible, and notes are shared within 6 hours.




Remote work, part 5. Staff may work from home up to 3 days a week when their manager agrees and their tasks allow it. Staff may work from home up to 3 days a week when their manager agrees and their tasks allow it.

Equipment, part 5. The IT team lends a laptop and a headset, and staff return both within 8 days of leaving. The IT team lends a laptop and a headset, and staff return both within 8 days of leaving.

Security, part 5. Laptops must lock after 7 minutes without use, and company ﬁles stay on approved storage. Laptops must lock after 7 minutes without use, and company ﬁles stay on approved storage.

Finance, part 5. The ﬁnance team refunds internet costs up to 60 QAR a month against a valid receipt. The ﬁnance team refunds internet costs up to 60 QAR a month against a valid receipt.

Meetings, part 5. Online meetings start on time, cameras are on when possible, and notes are shared within 7 hours. Online meetings start on time, cameras are on when possible, and notes are shared within 7 hours.

Remote work, part 6. Staff may work from home up to 4 days a week when their manager agrees and their tasks allow it. Staff may work from home up to 4 days a week when their manager agrees and their tasks allow it.

Equipment, part 6. The IT team lends a laptop and a headset, and staff return both within 2 days of leaving. The IT team lends a laptop and a headset, and staff return both within 2 days of leaving.

Security, part 6. Laptops must lock after 8 minutes without use, and company ﬁles stay on approved storage. Laptops must lock after 8 minutes without use, and company ﬁles stay on approved storage.

Finance, part 6. The ﬁnance team refunds internet costs up to 70 QAR a month against a valid receipt. The ﬁnance team refunds internet costs up to 70 QAR a month against a valid receipt.

Meetings, part 6. Online meetings start on time, cameras are on when possible, and notes are shared within 8 hours. Online meetings start on time, cameras are on when possible, and notes are shared within 8 hours.

Remote work, part 7. Staff may work from home up to 5 days a week when their manager agrees and their tasks allow it. Staff may work from home up to 5 days a week when their manager agrees and their tasks allow it.

Equipment, part 7. The IT team lends a laptop and a headset, and staff return both within 3 days of leaving. The IT team lends a laptop and a headset, and staff return both within 3 days of leaving.

Security, part 7. Laptops must lock after 2 minutes without use, and company ﬁles stay on approved storage. Laptops must lock after 2 minutes without use, and company ﬁles stay on approved storage.

Finance, part 7. The ﬁnance team refunds internet costs up to 80 QAR a month against a valid receipt. The ﬁnance team refunds internet costs up to 80 QAR a month against a valid receipt.

Meetings, part 7. Online meetings start on time, cameras are on when possible, and notes are shared within 2 hours. Online meetings start on time, cameras are on when possible, and notes are shared within 2 hours.

Remote work, part 8. Staff may work from home up to 6 days a week when their manager agrees and their tasks allow it. Staff may work from home up to 6 days a week when their manager agrees and their tasks allow it.

Equipment, part 8. The IT team lends a laptop and a headset, and staff return both within 4 days of leaving. The IT team lends a laptop and a headset, and staff return both within 4 days of leaving.

Security, part 8. Laptops must lock after 3 minutes without use, and company ﬁles stay on approved storage. Laptops must lock after 3 minutes without use, and company ﬁles stay on approved storage.

Finance, part 8. The ﬁnance team refunds internet costs up to 20 QAR a month against a valid receipt. The ﬁnance team refunds internet costs up to 20 QAR a month against a valid receipt.

Meetings, part 8. Online meetings start on time, cameras are on when possible, and notes are shared within 3 hours. Online meetings start on time, cameras are on when possible, and notes are shared within 3 hours.


## 1. Working hours

Staff work from 7:30 to 15:30, Sunday to Thursday.

### 1.1 Ramadan hours

During Ramadan, working hours are 9:00 to 14:00.

## 2. Salaries

| Grade | Monthly salary (QAR) |
|-------|----------------------|
| A     | 12,000               |
| B     | 18,500               |

"""





