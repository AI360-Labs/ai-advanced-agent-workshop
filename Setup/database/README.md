# Supabase / Postgres Setup

Complete walkthrough from account creation to a verified database ready for the workshop.

All shell commands in this guide are run from **this directory** (`Setup/database`).

---

## Prerequisites

You need one tool installed before running any pipeline commands:

**`uv`** — Python package and project manager (replaces pip + virtualenv).

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify: `uv --version`

You also need an **OpenRouter API key** for the RAG ingest step — see the
[OpenRouter setup guide](../openrouter/README.md).

---

## 1. Create an account

Go to [supabase.com](https://supabase.com) and sign up. A free-tier account is sufficient for the entire workshop.

---

## 2. Create a new project

1. From the Supabase dashboard, click **New project**.
2. Choose an **organisation** (your personal org is fine).
3. Fill in:
   - **Name** — e.g. `agentic-app`
   - **Database password** — save this somewhere; you will need it if you ever connect directly via `psql`
   - **Region** — pick the one closest to you
4. Click **Create new project** and wait ~2 minutes for provisioning.

---

## 3. Get your API credentials

Open your project dashboard and click the **Connect** button (top bar, next to the project name). This shows the project URL and all API keys in one place.

Alternatively, navigate to **Project Settings → API Keys** (left sidebar → Settings → API Keys).

You need two values:

| Value | Where to find it |
|---|---|
| **Project URL** | Looks like `https://abcdefgh.supabase.co` |
| **Secret key** | `sb_secret_...` on new projects, or the legacy `service_role` (`ey…`) key under the **Legacy API Keys** tab on older projects |

> **Use the secret / service_role key, not the publishable / anon key.** The secret key bypasses Row Level Security and is required for the pipelines to write data.
>
> Never expose the secret key in client-side code or commit it to git.

**Note on key formats:** Supabase introduced new key names in 2025. New projects use `sb_publishable_...` (≈ anon) and `sb_secret_...` (≈ service_role). Legacy JWT keys (`anon` / `service_role`) still work but will be deprecated by the end of 2026. Use whichever format your project shows.

---

## 4. Create your `.env` file

In **this directory** (`Setup/database`), copy the example file and fill in your credentials:

```bash
cp .env.example .env
```

Open `.env` in any text editor and set the values:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_KEY=sb_secret_...
OPENROUTER_API_KEY=sk-or-v1-...
```

The Kaggle variables are optional — leave them blank unless you plan to run the alternative Kaggle RAG ingest (`pipelines/ingest.py`).

---

## 5. Expose custom schemas in the Data API

The app uses two non-public schemas: `rag` and `northwind`. The Supabase Data API (PostgREST) only exposes `public` by default — add the others or API calls to those schemas will return a 404 or schema error.

1. Navigate to **Project Settings → Data API** (left sidebar → Settings → Data API).
2. Find the **Exposed schemas** field.
3. Add `rag` and `northwind` to the list (space- or comma-separated, alongside `public` and any existing entries).
4. Click **Save**.

> **New projects (created after May 2026):** Supabase changed the default so that tables are no longer automatically exposed to the Data API. If you see `PGRST106` errors after running migrations, go back to **Project Settings → Data API** and confirm that `public`, `rag`, and `northwind` are all listed under **Exposed schemas**, then save again to trigger a PostgREST reload.

---

## 6. Run the migrations

Open the [SQL Editor](https://supabase.com/dashboard/project/_/sql/new) (left sidebar → SQL Editor → **New query**).

For each of the two migrations below: **open the file** in your editor, **copy its entire contents**, **paste into the SQL Editor**, and click **Run**. Confirm it succeeds before moving to the next.

> **Row Level Security:** Every migration enables RLS on the tables it creates. With RLS on and no policies defined, only the `service_role` key (which bypasses RLS) can access the data — the anon / publishable key is locked out entirely. This is intentional: the workshop pipelines all use `SUPABASE_SERVICE_KEY`, so everything keeps working, and your data is not exposed to the public internet.

---

### Migration 1 — `migrations/001_rag.sql`

Enables the `pgvector` extension, creates the `rag` schema, the `documents` table, and the `match_documents` RPC used by the `rag_search` tool.

1. Open `migrations/001_rag.sql`.
2. Select all, copy.
3. Paste into the SQL Editor (open a **New query** first) and click **Run**.

**Verify:** In Table Editor, use the schema switcher (top-left dropdown) → select `rag` → you should see the `documents` table.

---

### Migration 2 — `migrations/002_northwind_schema.sql`

Creates the `northwind` schema with all Northwind tables (orders, products, customers, etc.). Data is populated later by the seed pipeline.

1. Open `migrations/002_northwind_schema.sql`.
2. Select all, copy.
3. Paste into the SQL Editor (**New query**) and click **Run**.

**Verify:** Table Editor → schema switcher → select `northwind` → you should see tables like `orders`, `products`, `customers`, `employees`.

---

## 7. Verify the schemas

Run this query in the SQL Editor to confirm both schemas are in place:

```sql
SELECT schema_name
FROM information_schema.schemata
WHERE schema_name IN ('rag', 'northwind')
ORDER BY schema_name;
```

Expected result — two rows: `northwind`, `rag`.

---

## 8. Populate the database

Run the following commands **from this directory** (`Setup/database`). Your `.env` must be filled in first. The first `uv run` automatically creates a virtual environment and installs dependencies.

```bash
# 1. Seed Northwind relational data (orders, products, customers, etc.)
#    Requires: SUPABASE_URL + SUPABASE_SERVICE_KEY, migration 002 applied.
uv run python -m pipelines.seed_northwind

# 2. Embed the pre-generated Northwind PDF reports (in reports/) into RAG.
#    Requires: SUPABASE_URL + SUPABASE_SERVICE_KEY + OPENROUTER_API_KEY, migration 001 applied.
uv run python -m pipelines.ingest_reports
```

Each command prints progress to the terminal. Wait for it to finish before running the next one.

> The PDF reports are committed in `reports/` — there is no separate generation step.

**Verify Northwind seed — in the SQL Editor:**

```sql
SELECT COUNT(*) FROM northwind.orders;
-- Expected: 830
```

**Verify RAG ingest — in the SQL Editor:**

```sql
SELECT dataset, COUNT(*) FROM rag.documents GROUP BY dataset;
-- Expected: one row, dataset = 'northwind_reports'
```

---

## Resetting data

| What to reset | SQL |
|---|---|
| All RAG documents | `TRUNCATE rag.documents;` |
| One dataset only | `DELETE FROM rag.documents WHERE dataset = 'northwind_reports';` |
| Northwind data | `TRUNCATE northwind.orders, northwind.order_details, northwind.products, northwind.customers, northwind.employees, northwind.suppliers, northwind.categories, northwind.shippers CASCADE;` |
