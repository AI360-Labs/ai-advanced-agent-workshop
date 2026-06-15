# Database schema (training reference)

The agent may access **only** the tables listed below. Everything else in the
Northwind database exists for the training demo but is out of bounds for the agent.

## Northwind (`public` schema) — mandatory tables

| Table | Purpose |
|-------|---------|
| `products` | Product catalogue (price, stock, category) |
| `categories` | Product categories |
| `customers` | Customer master data |
| `orders` | Order headers (dates, customer, shipper) |
| `order_details` | Line items per order |
| `employees` | Staff records |
| `shippers` | Delivery companies |
| `suppliers` | Product suppliers |

## Report documents (`documents` schema)

| Table | Purpose |
|-------|---------|
| `documents.reports` | Business report text with a pgvector embedding for semantic search |

Columns:

- `id` — `uuid`, primary key
- `title` — `text`
- `content` — `text`
- `embedding` — `vector(1536)` (same dimension as `openai/text-embedding-3-small`)

Semantic search uses the pgvector distance operator `<=>` (cosine distance).

## Application tables (persistence, Part 7)

| Table | Purpose |
|-------|---------|
| `conversations` | One row per chat thread (`session_id`, `title`) |
| `messages` | Messages in a thread (`role`, `content`, optional `steps` jsonb) |
