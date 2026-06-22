-- Enable pgvector (run once per Supabase project — safe to re-run)
CREATE EXTENSION IF NOT EXISTS vector;

CREATE SCHEMA IF NOT EXISTS rag;
SET search_path = rag, extensions, public;

-- Drop table if re-running from scratch
DROP TABLE IF EXISTS documents;

-- Document chunks with embeddings (BAAI/bge-small-en-v1.5 via fastembed → 384 dims)
CREATE TABLE documents (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset     TEXT        NOT NULL,           -- e.g. 'northwind_reports', 'support_tickets'
    source      TEXT        NOT NULL,           -- filename or row identifier
    chunk_index INT         NOT NULL,
    content     TEXT        NOT NULL,
    embedding   VECTOR(1536),
    metadata    JSONB       DEFAULT '{}',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- No vector index for workshop scale (<1 000 rows); sequential scan is accurate and fast.
-- Add an IVFFlat index (lists ≈ sqrt(rows)) once the table grows beyond ~1 000 rows.

CREATE INDEX documents_dataset_idx ON documents (dataset);

ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Grant access to Supabase built-in roles (service_role bypasses RLS but still needs USAGE)
GRANT USAGE ON SCHEMA rag TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA rag TO anon, authenticated, service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA rag TO anon, authenticated, service_role;
GRANT ALL ON ALL ROUTINES IN SCHEMA rag TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA rag GRANT ALL ON TABLES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA rag GRANT ALL ON SEQUENCES TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA rag GRANT ALL ON ROUTINES TO anon, authenticated, service_role;

-- RPC called by the rag_search agent tool
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding VECTOR(1536),
    match_count     INT  DEFAULT 5,
    filter_dataset  TEXT DEFAULT NULL
)
RETURNS TABLE (
    id         UUID,
    dataset    TEXT,
    source     TEXT,
    content    TEXT,
    metadata   JSONB,
    similarity FLOAT
)
LANGUAGE SQL STABLE AS $$
    SELECT
        id,
        dataset,
        source,
        content,
        metadata,
        1 - (embedding <=> query_embedding) AS similarity
    FROM documents
    WHERE filter_dataset IS NULL OR dataset = filter_dataset
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
