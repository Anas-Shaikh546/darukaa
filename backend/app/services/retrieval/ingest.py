"""
Ingestion pipeline for Darukaa's evidence corpus.

Hard rule: this module only ever indexes text that was actually extracted
from a source file on disk (PDF or .txt). It never generates, paraphrases,
or invents scientific content. If extraction fails or produces nothing
usable, the source is skipped and flagged - never silently replaced with
placeholder text.

Required provenance per chunk (Step 4 of the Day 1 plan):
    source, title, source_url, source_file, page, year, document_type,
    topic, variables, location_scope
Values that aren't known for a given source are left as None rather than
guessed.

Usage:
    python -m app.services.retrieval.ingest
This walks RAW_DOCS_PATH, extracts + chunks every .pdf/.txt file that has
a matching sidecar metadata file, embeds the chunks locally, and upserts
them into ChromaDB (upsert = re-running ingestion is idempotent).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pypdf import PdfReader

load_dotenv()

RAW_DOCS_PATH = Path(os.getenv("RAW_DOCS_PATH", "../knowledge/raw"))
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", "../knowledge/chroma"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "darukaa_evidence")
EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)

CHUNK_CHAR_SIZE = 1200
CHUNK_CHAR_OVERLAP = 150


class IngestionError(Exception):
    """Raised when a source cannot be safely ingested."""


@dataclass
class SourceMetadata:
    """Provenance sidecar for a source file, loaded from <file>.meta.json."""

    source: Optional[str] = None
    title: Optional[str] = None
    source_url: Optional[str] = None
    year: Optional[int] = None
    document_type: Optional[str] = None
    topic: Optional[str] = None
    variables: list[str] = field(default_factory=list)
    location_scope: Optional[str] = None

    @classmethod
    def load(cls, meta_path: Path) -> "SourceMetadata":
        if not meta_path.exists():
            raise IngestionError(
                f"Missing provenance sidecar for source: {meta_path}. "
                "A document without a metadata file cannot be indexed as evidence."
            )
        data = json.loads(meta_path.read_text(encoding="utf-8"))
        return cls(**data)


@dataclass
class ExtractedPage:
    page_number: Optional[int]
    text: str


def extract_pdf_pages(path: Path) -> list[ExtractedPage]:
    """Extract real text per page from a PDF."""
    try:
        reader = PdfReader(str(path))
    except Exception as exc:
        raise IngestionError(
            f"Could not open PDF {path}: {exc}"
        ) from exc

    pages: list[ExtractedPage] = []

    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append(
                ExtractedPage(
                    page_number=i,
                    text=text,
                )
            )

    if not pages:
        raise IngestionError(
            f"No extractable text found in {path}. PDF may be scanned/image-only. "
            "Flagging for manual handling instead of fabricating content."
        )

    return pages


def extract_text_file(path: Path) -> list[ExtractedPage]:
    """Extract a plain-text source as a single 'page'."""
    text = path.read_text(
        encoding="utf-8",
        errors="strict",
    ).strip()

    if not text:
        raise IngestionError(f"Source file is empty: {path}")

    return [
        ExtractedPage(
            page_number=None,
            text=text,
        )
    ]


def is_bibliography_chunk(text: str) -> bool:
    """Check if a chunk is likely a bibliography or reference list."""
    text_lower = text.lower()

    bib_indicators = [
        "references",
        "bibliography",
        "references cited",
        "literature cited",
        "selected references",
        "further reading",
        "acknowledgments",
        "references and notes",
        "works cited",
        "reference list",
    ]

    if any(indicator in text_lower for indicator in bib_indicators):
        return True

    author_hits = re.findall(
        r"\b[A-Z][a-zA-Z\-]+,\s*[A-Z]\.",
        text,
    )
    year_hits = re.findall(
        r"\b(?:19|20)\d{2}\b",
        text,
    )
    lines = text.split("\n")

    if len(author_hits) >= 3 and len(year_hits) >= 2:
        return True

    if len(author_hits) >= 2 and (
        len(author_hits) / max(len(lines), 1)
    ) > 0.3:
        return True

    return False


def chunk_text(
    text: str,
    size: int = CHUNK_CHAR_SIZE,
    overlap: int = CHUNK_CHAR_OVERLAP,
) -> list[str]:
    """Simple sliding-window chunking."""
    text = text.strip()

    if len(text) <= size:
        return [
            text
        ] if text and not is_bibliography_chunk(text) else []

    chunks: list[str] = []
    start = 0

    while start < len(text):
        end = min(start + size, len(text))
        window = text[start:end]

        if end < len(text):
            split_at = max(
                window.rfind("\n\n"),
                window.rfind(". "),
            )

            if split_at > size * 0.5:
                end = start + split_at + 1

        chunk = text[start:end].strip()

        if chunk and not is_bibliography_chunk(chunk):
            chunks.append(chunk)

        if end >= len(text):
            break

        start = max(
            end - overlap,
            start + 1,
        )

    return chunks


def deterministic_chunk_id(
    source_file: str,
    page: Optional[int],
    chunk_text_value: str,
) -> str:
    """SHA-256 of source file + page + chunk text."""
    key = f"{source_file}|{page}|{chunk_text_value}"

    return hashlib.sha256(
        key.encode("utf-8")
    ).hexdigest()


def build_records(
    path: Path,
    meta: SourceMetadata,
) -> list[dict]:
    """Extract, chunk, and attach provenance for one source file."""
    if path.suffix.lower() == ".pdf":
        pages = extract_pdf_pages(path)

    elif path.suffix.lower() == ".txt":
        pages = extract_text_file(path)

    else:
        raise IngestionError(
            f"Unsupported source type: {path.suffix} ({path})"
        )

    records: list[dict] = []

    for extracted in pages:
        for chunk in chunk_text(extracted.text):
            chunk_id = deterministic_chunk_id(
                str(path),
                extracted.page_number,
                chunk,
            )

            records.append(
                {
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": {
                        "source": meta.source,
                        "title": meta.title,
                        "source_url": meta.source_url,
                        "source_file": str(path),
                        "page": extracted.page_number,
                        "year": meta.year,
                        "document_type": meta.document_type,
                        "topic": meta.topic,
                        "variables": (
                            ",".join(meta.variables)
                            if meta.variables
                            else None
                        ),
                        "location_scope": meta.location_scope,
                    },
                }
            )

    return records


_collection_cache = None


def get_collection():
    """Create (once) and reuse the Chroma collection and its embedding function.

    Cached at module level so the expensive SentenceTransformer model load
    and Chroma client creation happen only once per process, not on every
    call. main.py calls this once eagerly at application startup so that
    cost is paid during boot, not inside a request handler.
    """
    global _collection_cache

    if _collection_cache is not None:
        return _collection_cache

    print(
        "DARUKAA DEBUG: importing chromadb",
        flush=True,
    )

    import chromadb
    from chromadb.utils import embedding_functions

    print(
        "DARUKAA DEBUG: creating Chroma client",
        flush=True,
    )

    client = chromadb.PersistentClient(
        path=str(CHROMA_PATH)
    )

    print(
        "DARUKAA DEBUG: creating embedding function",
        flush=True,
    )

    embed_fn = embedding_functions.ONNXMiniLM_L6_V2()

    print(
        "DARUKAA DEBUG: getting collection",
        flush=True,
    )

    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    print(
        "DARUKAA DEBUG: collection ready",
        flush=True,
    )

    _collection_cache = collection
    return _collection_cache


def ingest_all(
    raw_dir: Path = RAW_DOCS_PATH,
) -> dict:
    """Walk raw_dir and ingest every supported source."""
    collection = get_collection()

    total_chunks = 0
    ingested_files: list[str] = []
    skipped_files: list[dict] = []

    for path in sorted(raw_dir.glob("*")):
        if path.suffix.lower() not in (
            ".pdf",
            ".txt",
        ):
            continue

        meta_path = path.with_suffix(
            path.suffix + ".meta.json"
        )

        try:
            meta = SourceMetadata.load(meta_path)
            records = build_records(
                path,
                meta,
            )

        except IngestionError as exc:
            skipped_files.append(
                {
                    "file": str(path),
                    "reason": str(exc),
                }
            )
            continue

        if records:
            metadatas = [
                {
                    k: v
                    for k, v in r["metadata"].items()
                    if v is not None
                }
                for r in records
            ]

            collection.upsert(
                ids=[
                    r["id"]
                    for r in records
                ],
                documents=[
                    r["text"]
                    for r in records
                ],
                metadatas=metadatas,
            )

            total_chunks += len(records)
            ingested_files.append(str(path))

    return {
        "ingested_files": ingested_files,
        "skipped_files": skipped_files,
        "total_chunks_upserted": total_chunks,
        "collection_count": collection.count(),
    }


if __name__ == "__main__":
    result = ingest_all()
    print(
        json.dumps(
            result,
            indent=2,
        )
    )