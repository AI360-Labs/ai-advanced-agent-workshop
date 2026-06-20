# Project Setup

Follow these guides in order to get a working environment for the workshop.

1. **[OpenRouter setup](openrouter/README.md)** — create an account, add
   credits, and generate the `OPENROUTER_API_KEY` used for chat and embeddings.
2. **[Supabase / Postgres setup](database/README.md)** — create the database,
   run the migrations, and populate it with the Northwind data and RAG reports.

Both keys end up in a single `.env` file in `Setup/database` (copied from
`Setup/database/.env.example`).
