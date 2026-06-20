"""
RAG Ingest — Northwind PDF Reports
====================================
Reads the synthetic PDF reports in reports/, splits them into chunks, embeds
each chunk using OpenRouter (openai/text-embedding-3-small), and stores the
results in the 'documents' Supabase table alongside any existing data.

Prerequisites
-------------
1. Apply migrations/001_rag.sql (pgvector + documents table + match_documents RPC).
2. Fill in .env:
      SUPABASE_URL
      SUPABASE_SERVICE_KEY
      OPENROUTER_API_KEY

Run
---
    uv run python -m pipelines.ingest_reports

Re-running appends duplicates. To clear only the reports dataset:
    DELETE FROM documents WHERE dataset = 'northwind_reports';
"""

import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from supabase import Client, create_client

load_dotenv()

# --- Configuration -----------------------------------------------------------

CHUNK_SIZE  = 500   # soft max characters per chunk (~75–100 words)
EMBED_MODEL = "openai/text-embedding-3-small"  # served via OpenRouter
EMBED_BATCH = 50    # how many chunks to embed in one API call
DATASET     = "northwind_reports"
REPORTS_DIR = Path(__file__).parent.parent / "reports"

# Lines matching these patterns appear as boilerplate at the top of every page.
# Stripping them keeps this noise out of every chunk.
_BOILERPLATE = (
    re.compile(r"Northwind Traders\s+·"),  # "Northwind Traders  ·  Internal Document"
    re.compile(r"^Page \d+$"),             # standalone page-number line
)

# --- Text helpers ------------------------------------------------------------

def clean_page_text(text: str) -> str:
    """Strip the repeated page header that appears at the top of every PDF page."""
    lines = text.strip().splitlines()
    return "\n".join(
        line for line in lines
        if not any(pat.search(line.strip()) for pat in _BOILERPLATE)
    ).strip()


def split_text(text: str) -> list[str]:
    """Group text into chunks up to CHUNK_SIZE characters.

    Prefers splitting on blank lines (paragraph/section breaks). When pypdf
    omits blank lines — which is common — falls back to line-by-line grouping
    so table rows and sentences still stay intact within a chunk.
    """
    # Try paragraph-level splits first (blank lines)
    units = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    # pypdf often strips blank lines — fall back to single-line units
    if len(units) == 1:
        units = [line.strip() for line in text.splitlines() if line.strip()]

    chunks: list[str] = []
    current = ""

    for unit in units:
        candidate = (current + "\n" + unit).strip() if current else unit
        if current and len(candidate) > CHUNK_SIZE:
            chunks.append(current)
            current = unit
        else:
            current = candidate

    if current:
        chunks.append(current)

    return chunks


def read_pdf(path: Path):
    """Yield one dict per text chunk extracted from the PDF.

    Each dict will later be enriched with an 'embedding' key before being
    inserted into Supabase.
    """
    reader = PdfReader(str(path))
    chunk_idx = 0
    for page_num, page in enumerate(reader.pages, start=1):
        text = clean_page_text(page.extract_text() or "")
        for chunk in split_text(text):
            yield {
                "dataset":     DATASET,
                "source":      path.name,
                "chunk_index": chunk_idx,
                "content":     chunk,
                "metadata":    {"page": page_num},
            }
            chunk_idx += 1

# --- Embedding ---------------------------------------------------------------

def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Call the OpenRouter embeddings endpoint and return a list of vectors."""
    response = client.embeddings.create(model=EMBED_MODEL, input=texts)
    # The API returns results sorted by index, so we can zip them directly.
    return [item.embedding for item in response.data]

# --- Storage -----------------------------------------------------------------

def store_batch(sb: Client, docs: list[dict], embeddings: list[list[float]]) -> None:
    """Attach embeddings to each chunk dict and insert the batch into Supabase."""
    rows = [{**doc, "embedding": emb} for doc, emb in zip(docs, embeddings)]
    sb.schema("rag").table("documents").insert(rows).execute()

# --- Pipeline ----------------------------------------------------------------

def run_pipeline(pdf_path: Path, openai_client: OpenAI, sb: Client) -> None:
    """Process one PDF: chunk → embed → store, flushing every EMBED_BATCH chunks."""
    batch: list[dict] = []
    total = 0

    for doc in read_pdf(pdf_path):
        batch.append(doc)
        if len(batch) >= EMBED_BATCH:
            store_batch(sb, batch, embed_batch(openai_client, [d["content"] for d in batch]))
            total += len(batch)
            batch = []

    # Flush any remaining chunks that didn't fill a full batch
    if batch:
        store_batch(sb, batch, embed_batch(openai_client, [d["content"] for d in batch]))
        total += len(batch)

    print(f"  {pdf_path.name}: {total} chunks")


def main() -> None:
    # Fail early if any required environment variables are missing
    required = ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "OPENROUTER_API_KEY")
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}\nSee .env.example")

    pdfs = sorted(REPORTS_DIR.glob("*.pdf"))
    if not pdfs:
        sys.exit(f"No PDFs found in {REPORTS_DIR}")

    # OpenAI client pointed at OpenRouter — same interface, different base URL
    openai_client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

    sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    print(f"Ingesting {len(pdfs)} reports from {REPORTS_DIR}")
    print(f"Embedding model: {EMBED_MODEL}\n")

    for pdf in pdfs:
        run_pipeline(pdf, openai_client, sb)

    print("\nDone — all reports ingested.")


if __name__ == "__main__":
    main()
