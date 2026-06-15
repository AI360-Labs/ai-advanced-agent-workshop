# Part 4 — Retrieval nodes

Builds on Part 3. We add two ways to fetch information before the agent answers:
**SQL generation** over the Northwind database (parsed and validated with `sqlglot`
before read-only execution) and **semantic document search** over `documents.reports`
via pgvector embeddings. Both paths write typed results into graph state; full
routing lands in Part 5.

## Roadmap

1. Add `sql_gen` and `answer` tasks to `config/tasks.yaml`
2. Add the `SqlGeneration` output schema to `db/schemas.py`
3. Install `sqlglot` and create SQL validation guardrails in `db/validate_sql.py`
4. Define the schema prompt snippet in `db/schema_snippet.py`
5. Write the SQL generation prompt in `prompts/sql_generation.md`
6. Make `EMBEDDING_MODEL` required in `config/settings.py`
7. Update config unit-test fixtures in `tests/unit/test_config.py`
8. Add async embedding via `LLMClient.aembed` in `utils/llm_client.py` (uses `LiteLLMEmbeddings` from `langchain_litellm`)
9. Extend graph state in `agent/state.py` for retrieval outputs
10. Add the document-answer prompt stub in `prompts/document_answer.md` (used in Part 5)
11. Create the SQL query node in `agent/nodes/sql_query.py`
12. Create the document search node in `agent/nodes/document_search.py`
13. Remove the Part 3 DB connection integration test
14. Verify SQL validation with unit tests in `tests/unit/test_validate_sql.py`

## Layout (added to Part 3)

```text
part_4/
├── agent/
│   ├── state.py                # Updated with retrieval + thinking fields
│   └── nodes/
│       ├── document_search.py  # Semantic search query node
│       └── sql_query.py        # SQL generation & execution node
├── config/
│   ├── settings.py             # embedding_model now required (no default)
│   └── tasks.yaml              # sql_gen and answer tasks
├── db/
│   ├── schema_snippet.py       # Schema text for SQL prompting
│   ├── schemas.py              # SqlGeneration schema
│   └── validate_sql.py         # SQL validation using sqlglot
├── prompts/
│   ├── document_answer.md      # Prompt stub for Part 5 answer node
│   └── sql_generation.md       # Prompt for SQL generation
├── utils/
│   └── llm_client.py           # aembed class method
└── tests/unit/
    ├── test_config.py          # Fixtures include EMBEDDING_MODEL
    └── test_validate_sql.py    # SQL validation guardrail tests
```

## `config/tasks.yaml` — add `sql_gen` and `answer`

```yaml
  sql_gen:
    temperature: 0.0
    models:
      - google/gemma-3-12b-it
      - google/gemini-3.5-flash

  answer:
    temperature: 0.2
    models:
      - google/gemma-3-12b-it
      - google/gemini-3.5-flash
```

## `db/validate_sql.py` — forbidden keywords

```python
FORBIDDEN_KEYWORDS = frozenset(
    {"insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke"}
)
```

## `db/schema_snippet.py`

```python
SCHEMA_SNIPPET = """
Tables you may use (PostgreSQL, public schema unless noted):

- categories(category_id, category_name, description)
- suppliers(supplier_id, company_name, contact_name, country)
- products(product_id, product_name, supplier_id, category_id, unit_price,
  units_in_stock, units_on_order, reorder_level, discontinued)
- customers(customer_id, company_name, contact_name, country)
- employees(employee_id, last_name, first_name, title, country)
- shippers(shipper_id, company_name, phone)
- orders(order_id, customer_id, employee_id, order_date, shipper_id, freight, ship_country)
- order_details(order_id, product_id, unit_price, quantity, discount)

Join keys: orders.customer_id -> customers.customer_id;
order_details.order_id -> orders.order_id;
order_details.product_id -> products.product_id;
products.category_id -> categories.category_id;
products.supplier_id -> suppliers.supplier_id.
""".strip()
```

## Prompt — `prompts/sql_generation.md`

```markdown
You write PostgreSQL SELECT queries for the Northwind sales database.

{schema}

Rules:
- Output ONLY one SELECT statement. No markdown, no explanation outside JSON.
- Use only the tables listed above.
- Always include LIMIT (max {max_limit}).
- Never use INSERT, UPDATE, DELETE, DROP, or DDL.

Return JSON with exactly these fields:
- sql: the SELECT statement as a single string
- rationale: one short sentence explaining the query

User question:
{question}
```

## Prompt — `prompts/document_answer.md`

```markdown
You answer questions using excerpts from business report documents.

Report excerpts:
{excerpts}

User question:
{question}

Write a concise answer in plain text. If the excerpts do not contain the answer, say so.
```

## Config test fixtures — `tests/unit/test_config.py`

```python
DEV_ENV = """\
OPEN_ROUTER_API_KEY="test-key"
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/postgres"
EMBEDDING_MODEL="openai/text-embedding-3-small"
LOG_LEVEL=DEBUG
"""

PROD_ENV = """\
OPEN_ROUTER_API_KEY="test-key"
DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/postgres"
EMBEDDING_MODEL="openai/text-embedding-3-small"
LOG_LEVEL=INFO
"""
```

## Tests

### `tests/unit/test_validate_sql.py`

```python
from types import SimpleNamespace

import pytest

import db.validate_sql as validate_sql_module
from db.validate_sql import SqlValidationError, validate_sql


@pytest.fixture(autouse=True)
def mock_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        validate_sql_module,
        "get_config",
        lambda: SimpleNamespace(sql_max_limit=100),
    )


def test_accepts_simple_select() -> None:
    sql = validate_sql("SELECT product_id FROM products")

    assert "LIMIT" in sql.upper()


def test_rejects_drop() -> None:
    with pytest.raises(SqlValidationError, match="Forbidden"):
        validate_sql("DROP TABLE products")


def test_rejects_unknown_table() -> None:
    with pytest.raises(SqlValidationError, match="not allowed"):
        validate_sql("SELECT * FROM territories LIMIT 5")


def test_rejects_non_select() -> None:
    with pytest.raises(SqlValidationError):
        validate_sql("INSERT INTO products (product_name) VALUES ('x')")


def test_injects_limit_when_only_subquery_has_limit() -> None:
    # A LIMIT inside a subquery must not satisfy the outer query's cap.
    sql = validate_sql(
        "SELECT product_id FROM products "
        "WHERE category_id IN (SELECT category_id FROM categories LIMIT 5)"
    )

    assert sql.rstrip().upper().endswith("LIMIT 100")


def test_rejects_outer_limit_over_cap_with_subquery() -> None:
    with pytest.raises(SqlValidationError, match="between 1 and"):
        validate_sql(
            "SELECT product_id FROM products "
            "WHERE category_id IN (SELECT category_id FROM categories LIMIT 5) "
            "LIMIT 9999"
        )


def test_uses_settings_sql_max_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    # Confirms validate_sql reads max_limit from get_config(), not a hardcoded constant.
    monkeypatch.setattr(
        validate_sql_module,
        "get_config",
        lambda: SimpleNamespace(sql_max_limit=10),
    )

    sql = validate_sql("SELECT product_id FROM products")
    assert sql.rstrip().upper().endswith("LIMIT 10")

    with pytest.raises(SqlValidationError, match="between 1 and"):
        validate_sql("SELECT product_id FROM products LIMIT 50")
```
