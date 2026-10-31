
"""
Test for the chunking phase. Run from the project root: uv run pytest 
"""

# There is something called Test-Driven Development ~ which means I write test before I write code, write soluition that pass all the test


import pytest


from docling_core.types.doc import (
    DoclingDocument,
    BoundingBox,
    DocItemLabel,
    ProvenanceItem,
    Size,
    TableCell,
    TableData,
)

from tokenizers import Tokenizer, models, pre_tokenizers
from transformers import PreTrainedTokenizerFast


from src.chunking.chunker import ChunkingService


MAX_TOKENS = 64


@pytest.fixture(scope="module")
def tokenizer() -> PreTrainedTokenizerFast:
    # Production passes the real BGE-M3 tokenizer
    raw = Tokenizer(models.WordLevel(vocab={"[UNK]": 0}, unk_token="[UNK]"))
    raw.pre_tokenizer = pre_tokenizers.Whitespace()
    return PreTrainedTokenizerFast(tokenizer_object=raw, unk_token="[UNK]")


@pytest.fixture(scope="module")
def service(tokenizer) -> ChunkingService:
    return ChunkingService(tokenizer=tokenizer, max_tokens=MAX_TOKENS)



def _prov(page: int, text: str) -> ProvenanceItem:
    return ProvenanceItem(page_no=page, bbox=BoundingBox(l=0, t=0, r=100, b=10), charspan=(0, len(text)))



def make_report(paginated: bool = True) -> DoclingDocument:
    """A small two-page report: title, two sections, one table."""
    doc = DoclingDocument(name="report")

    def prov(page, text):
        return _prov(page, text) if paginated else None

    if paginated:
        doc.add_page(page_no=1, size=Size(width=600, height=800))
        doc.add_page(page_no=2, size=Size(width=600, height=800))
    doc.add_title(text="Annual Report", prov=prov(1, "Annual Report"))
    doc.add_heading(text="1. Results", level=1, prov=prov(1, "1. Results"))
    doc.add_text(label=DocItemLabel.TEXT, text="Enrolment grew in all partner schools.", prov=prov(1, "x" * 38))
    doc.add_heading(text="2. Costs", level=1, prov=prov(2, "2. Costs"))
    doc.add_text(label=DocItemLabel.TEXT, text="Operating costs fell this year.", prov=prov(2, "x" * 31))
    cells = [
        TableCell(
            text=value,
            start_row_offset_idx=row,
            end_row_offset_idx=row + 1,
            start_col_offset_idx=col,
            end_col_offset_idx=col + 1,
            column_header=(row == 0),
        )
        for row, values in enumerate([["Year", "Students"], ["2025", "1200"]])
        for col, value in enumerate(values)
    ]
    doc.add_table(data=TableData(num_rows=2, num_cols=2, table_cells=cells), prov=prov(2, "table"))
    return doc


def test_docling_chunks_keep_headings_and_pages(service):
    chunks = service.chunk_docling(make_report(), document_id="doc-1", source="report.pdf")

    results = next(c for c in chunks if "Enrolment" in c.text)

    assert results.headings == ["Annual Report", "1. Results"]
    assert results.pages == [1]

    table = next(c for c in chunks if "1200" in c.text)  # the table stays in one chunk, under its section
    assert "Students" in table.text
    assert table.headings == ["Annual Report", "2. Costs"]
    assert table.pages == [2]