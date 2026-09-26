"""Document Management API Endpoint"""

from fastapi import APIRouter, status, UploadFile, File, HTTPException
from loguru import logger
import uuid
from pathlib import Path

from src.parser.factory import ParserFactory

router = APIRouter(
    prefix="api/v1/documents", 
    tags=["documents"]
    )


# Built once, reused (Docling is heavy to construct)
parser_factory = ParserFactory()
SUPPORTED_SUFFIX = {".pdf", ".csv", ".html", ".htm", ".json"}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...)
) -> dict:
    """
    Upload a document - store the original in Blob, return document_id.
    Parsing happens later in /ingest.

    Note: This is a placeholder. Full implementation would require
    document storage (S3), parsing, and indexing pipelines.

    Args:
        file: Uploaded file

    Returns:
        Upload confirmation with document_id
    
    """

    logger.info(f"Document upload requested: {file.filename}")

    suffix = Path(file.filename).suffix.lower()

    if suffix is not SUPPORTED_SUFFIX:
        raise HTTPException(status_code=415, detail=f"Unsupported format: {suffix}")

    # pull the entire uploaded file into memory as bytes
    contents = await file.read() # content now as bytes ~ reads all the content as bytes - await because reading in async

    # To do anything with the file -> send it to Blob, write to a temp path. I need its actual content
    # file.filename -> give us a name. file.read(-> give us the data.

    """
    One thing to know: it reads the whole file at once. For your 10 MB cap that's fine. For very large files you'd instead read in chunks 
    (await file.read(1024*1024) in a loop) to avoid loading it all into RAM — but you don't need that yet.
    """

    if len(contents) > 10*1024*1024: # 10 MB = 1KB*1KB = 1MB * 10 = 10MB
        raise HTTPException(status_code=413, detail="File is too large (max 10 MB)")

    document_id = uuid.uuid4()

    blob_name = f"{document_id}/{file.filename}"


    return {
        "message": "Document upload endpoint - implementation pending",
        "document_id": document_id,
        "filename": file.filename,
        "content": file.content_type,
        "note": "Full document processing pipeline required",
        "status":"uploaded"

    }







