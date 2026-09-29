"""Wrapper for Chonkie chunking library."""

import uuid
from typing import Optional

from chonkie import (
    TokenChunker,
    SemanticChunker,
    SDPMChunker
)

from loguru import logger




class ChonkieWrapper:
    """Wrapper for Chonkie chunking strategy."""

    