"""
RAG Ingest Pipeline
===================
Downloads three Kaggle datasets, splits them into chunks, embeds each chunk
with OpenAI's text-embedding-3-small via OpenRouter (1536-dim), and stores
the results in Supabase pgvector.

By default runs in SAMPLE_MODE: 50 support tickets. For full ingestion,
set SAMPLE_MODE = False in the script.

Prerequisites
-------------
1. Apply the migration:  migrations/001_rag.sql
2. Fill in .env:
       KAGGLE_USERNAME, KAGGLE_KEY      — from kaggle.com > Settings > API
       SUPABASE_URL, SUPABASE_SERVICE_KEY
       OPENROUTER_API_KEY               — from openrouter.ai > Settings > Keys

Run
---
    uv run python -m pipelines.ingest

Re-running appends duplicates. To start fresh:
    TRUNCATE rag.documents;   (run in Supabase SQL Editor)
"""

import csv
import os
import sys
from pathlib import Path
from typing import Generator

import kagglehub
from dotenv import load_dotenv
from openai import OpenAI
from supabase import create_client, Client

load_dotenv()

# ---------------------------------------------------------------------------
# Configuration — tune these for different quality / cost trade-offs
# ---------------------------------------------------------------------------

SAMPLE_MODE   = True       # Limit to a few examples for workshop/testing
CHUNK_SIZE    = 500    # characters per chunk (~75–100 words)
CHUNK_OVERLAP = 50     # characters shared between consecutive chunks
EMBED_MODEL   = "openai/text-embedding-3-small"  # 1536-dim, served via OpenRouter
EMBED_BATCH   = 50     # chunks per embedding batch

# ---------------------------------------------------------------------------
# Kaggle datasets to ingest
# ---------------------------------------------------------------------------

DATASETS = [
    {
        "slug": "tobiasbueck/multilingual-customer-support-tickets",
        "name": "support_tickets",
        "desc": "Multilingual customer support ticket records",
    },
]


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------

def split_text(text: str) -> list[str]:
    """Split text into overlapping character-based chunks."""
    text = text.strip()
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start : start + CHUNK_SIZE].strip()
        if chunk:
            chunks.append(chunk)
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ---------------------------------------------------------------------------
# Dataset reader — yields dicts ready for the documents table
# ---------------------------------------------------------------------------

def _pick(row: dict, *candidates: str) -> str:
    """Return the first non-empty value from a set of candidate column names."""
    for c in candidates:
        val = row.get(c, "").strip()
        if val:
            return val
    return ""


def read_csv(dataset_path: str, dataset_name: str) -> Generator[dict, None, None]:
    """Yield one chunk-dict per support ticket (subject + description)."""
    csv_files = list(Path(dataset_path).rglob("*.csv"))
    if not csv_files:
        print("  No CSV files found — skipping")
        return

    csv_path = csv_files[0]
    print(f"  Using {csv_path.name}")

    with open(csv_path, newline="", encoding="utf-8", errors="replace") as f:
        for row_idx, row in enumerate(csv.DictReader(f)):
            if SAMPLE_MODE and row_idx >= 50:
                break  # workshop: just 50 tickets

            subject = _pick(row, "subject", "Subject", "title", "Title")
            body    = _pick(row, "body", "Body", "description", "Description",
                            "ticket_description", "message", "text")
            lang    = _pick(row, "language", "Language", "lang")

            text = f"Subject: {subject}\n\n{body}" if subject else body
            if not text.strip():
                continue

            for chunk_idx, chunk in enumerate(split_text(text)):
                yield {
                    "dataset":     dataset_name,
                    "source":      f"ticket-{row_idx}",
                    "chunk_index": chunk_idx,
                    "content":     chunk,
                    "metadata":    {"row": row_idx, "language": lang},
                }


# ---------------------------------------------------------------------------
# Embedding — OpenAI text-embedding-3-small served via OpenRouter
# ---------------------------------------------------------------------------

def embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    """Return one 1536-dim embedding vector per text string."""
    response = client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

def store_batch(sb: Client, docs: list[dict], embeddings: list[list[float]]) -> None:
    rows = [
        {**doc, "embedding": emb}
        for doc, emb in zip(docs, embeddings)
    ]
    sb.schema("rag").table("documents").insert(rows).execute()


# ---------------------------------------------------------------------------
# Pipeline orchestrator
# ---------------------------------------------------------------------------

def run_pipeline(
    reader: Generator[dict, None, None],
    label:  str,
    client: OpenAI,
    sb:     Client,
) -> None:
    batch: list[dict] = []
    total = 0

    for doc in reader:
        batch.append(doc)
        if len(batch) >= EMBED_BATCH:
            embeddings = embed_batch(client, [d["content"] for d in batch])
            store_batch(sb, batch, embeddings)
            total += len(batch)
            print(f"    {label}: {total} chunks stored…")
            batch = []

    if batch:
        embeddings = embed_batch(client, [d["content"] for d in batch])
        store_batch(sb, batch, embeddings)
        total += len(batch)

    print(f"  {label}: done — {total} chunks total\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    missing = [v for v in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY", "OPENROUTER_API_KEY")
               if not os.getenv(v)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}\nSee .env.example")

    print(f"Embedding model: {EMBED_MODEL} (via OpenRouter)")

    # OpenAI client pointed at OpenRouter — same interface, different base URL
    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1",
    )

    sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

    for ds in DATASETS:
        print(f"\n{'='*60}")
        print(f"Dataset : {ds['name']}  ({ds['desc']})")
        print(f"Slug    : {ds['slug']}")
        print(f"{'='*60}")
        print("  Downloading from Kaggle…")

        try:
            path = kagglehub.dataset_download(ds["slug"])
        except Exception as e:
            print(f"  Download failed: {e}\n  Skipping.\n")
            continue

        run_pipeline(read_csv(path, ds["name"]), ds["name"], client, sb)

    print("All datasets ingested successfully.")


if __name__ == "__main__":
    main()
