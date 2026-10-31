"""Document Management API Endpoint"""

from fastapi import APIRouter, status, UploadFile, File, HTTPException
from loguru import logger
import uuid
from pathlib import Path

from src.parser.factory import ParserFactory
import asyncio


router = APIRouter(
    prefix="/api/v1/documents", 
    tags=["documents"]
    )

# Supported formats come from ParseFactory's class method
MAX_UPLOAD_SIZE = 1024 * 1024 * 20 # 20 MB


# Built once, reused (Docling is heavy to construct)
parser_factory = ParserFactory()


# Simple in-memory status store - replace it with Postgres later
# Resets on restart and isn't shared across workers; fine for a first version.
_status: dict[str, dict] = {}

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...)
) -> dict:
    """
    Upload a document: Validate it, store the original in Blob, return document_id.
    Parsing happens later in /ingest.

    

    Args:
        file: Uploaded file

    Returns:
        Upload confirmation with document_id
    
    """
    filename = Path(file.filename or "").name
    suffix = Path(filename).suffix.lower()
    logger.info(f"Document upload requested: {filename}")
    logger.info(f"The suffix is: {suffix}")

    if not parser_factory.supported_formats(suffix):
       raise HTTPException(status_code=415, detail=f"Unsupported format: {suffix}") # HTTP 415 - Unsupported media type - status code client-side error - the server is refuising to process a request because the data format os the payload is not supported

    # pull the entire uploaded file into memory as bytes (But hufe upload never fills the server memory)
    contents = await file.read(MAX_UPLOAD_SIZE + 1) # content now as bytes ~ reads all the content as bytes - await because reading in async

    # To do anything with the file -> send it to Blob, write to a temp path. I need its actual content
    # file.filename -> give us a name. file.read(-> give us the data.

    """
    One thing to know: it reads the whole file at once. For your 10 MB cap that's fine. For very large files you'd instead read in chunks 
    (await file.read(1024*1024) in a loop) to avoid loading it all into RAM — but you don't need that yet.
    """

    if len(contents) > MAX_UPLOAD_SIZE: # 20 MB = 1KB*1KB = 1MB * 10 = 10MB
        raise HTTPException(status_code=400, detail="File is too large (max 10 MB)")

    document_id = uuid.uuid4() # a string, so lookup with in ID from a URL match

    blob_name = f"{document_id}/{file.filename}"


    _status[document_id] = {
        "documnet_id": document_id,
        "filename": file.filename,
        "blob_path": "Later",
        "status": "uploaded" 
    }

    logger.info(f"Stored {filename} as {blob_name}")

    return {
        "message": "Document upload endpoint - implementation pending",
        "document_id": document_id,
        "filename": file.filename,
        "content": file.content_type,
        "note": "Full document processing pipeline required",
        "status":"uploaded"

    }



@router.post("/ingest", status_code= status.HTTP_202_ACCEPTED)
async def ingest_document(document_id: str) -> str:
    """
    Ingest a document (process and index).

    Args:
        document_id: Document ID to ingest

    Returns:
        Ingestion status
    
    """

    logger.info(f"Document ingestion requests: {document_id}")


    # Next step: put a job on queue. A worker copies the stored files (locally or Azure Blob Storage) - (storage.download_to_file)
    # Parse it (ParseFactory), chunks, embeds and indexes it, updating doc['status'] as it goes:
    # "queued" -> "parsing" -> "indexed" (or "failed")


    return {
        "message": "Document ingestion endpoint - implementation pending",
        "document_id": document_id,
        "status": "",
        "note": "Requires parser, chunker, embedder, and indexer integration"
    }






