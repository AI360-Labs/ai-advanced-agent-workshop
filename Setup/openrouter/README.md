# OpenRouter Setup

OpenRouter is a single, OpenAI-compatible API gateway in front of many model
providers (Anthropic, OpenAI, Google, and others). The workshop uses one
`OPENROUTER_API_KEY` for both chat/agent calls and for embedding the RAG
documents — so you only manage one key and one balance.

---

## 1. Create an account

Go to [openrouter.ai](https://openrouter.ai) and sign up (email, Google, or
GitHub). The account is free; you only pay for what the models cost.

---

## 2. Add credits

OpenRouter is pay-as-you-go — you need a small balance before any request will
succeed.

1. Open **[Settings → Credits](https://openrouter.ai/settings/credits)**.
2. Click **Add Credits** and add a small amount (e.g. **$5–10**) — more than
   enough for the entire workshop.

> Without a positive balance, API calls fail with a `402` / "insufficient
> credits" error.

---

## 3. Create an API key

1. Open **[Settings → Keys](https://openrouter.ai/settings/keys)**.
2. Click **Create Key**, give it a name (e.g. `agent-workshop`), and leave the
   credit limit blank (or set a cap if you prefer).
3. Copy the key immediately — it is shown **only once**. It starts with
   `sk-or-v1-...`.

> Treat the key like a password. Never commit it to git or paste it into
> client-side code.

---

## 4. Add the key to your `.env`

Add the key to the `.env` file you create during the
[database setup](../database/README.md) (in `Setup/database`):

```env
OPENROUTER_API_KEY=sk-or-v1-...
```

The pipelines and workshop code read this variable directly.

---

## 5. Verify it works

From `Setup/database` (where your `.env` lives), run:

```bash
uv run python -c "import os; from dotenv import load_dotenv; from openai import OpenAI; load_dotenv(); \
c = OpenAI(api_key=os.environ['OPENROUTER_API_KEY'], base_url='https://openrouter.ai/api/v1'); \
print(len(c.embeddings.create(model='openai/text-embedding-3-small', input='hello').data[0].embedding), 'dims')"
```

Expected output: `1536 dims`.

This confirms the key is valid, has credit, and that the OpenRouter
embeddings endpoint (used by `pipelines/ingest_reports.py`) is reachable.

---

## How it's used in the workshop

- **Embeddings** — `pipelines/ingest_reports.py` points an OpenAI client at
  `https://openrouter.ai/api/v1` and calls `text-embedding-3-small` (1536
  dims) to embed the PDF reports into the `rag.documents` table.
- **Chat / agents** — the workshop parts call chat models through the same
  base URL and key.

Because OpenRouter is OpenAI-compatible, the only differences from using OpenAI
directly are the `base_url` and the `OPENROUTER_API_KEY`.
