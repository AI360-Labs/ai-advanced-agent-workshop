"""
Northwind Seed
==============
Downloads pthom/northwind_psql SQL from GitHub, parses schema and data,
then upserts everything into the 'northwind' Supabase schema.

Prerequisites
-------------
1. Northwind schema applied in Supabase (pthom/northwind_psql SQL).
2. 'northwind' added to exposed schemas:
       Supabase > Settings > API > DB Schemas
3. SUPABASE_URL and SUPABASE_SERVICE_KEY set in .env.

Run
---
    uv run python -m pipelines.seed_northwind

Idempotent — safe to re-run.
"""

import os
import re
import sys
import urllib.request
from datetime import date
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SQL_URL = "https://raw.githubusercontent.com/pthom/northwind_psql/master/northwind.sql"
SCHEMA = "northwind"
BATCH_SIZE = 50
YEAR_SHIFT = 28  # moves 1996-1998 orders to 2024-2026

# FK-safe insertion order
TABLE_ORDER = [
    "us_states",
    "region",
    "territories",
    "customer_demographics",
    "categories",
    "suppliers",
    "shippers",
    "customers",
    "customer_customer_demo",
    "employees",          # self-referential FK; sorted below
    "employee_territories",
    "products",
    "orders",
    "order_details",
]

# Primary key(s) used for upsert conflict resolution
TABLE_PKS = {
    "us_states":              "state_id",
    "region":                 "region_id",
    "territories":            "territory_id",
    "customer_demographics":  "customer_type_id",
    "categories":             "category_id",
    "suppliers":              "supplier_id",
    "shippers":               "shipper_id",
    "customers":              "customer_id",
    "customer_customer_demo": "customer_id,customer_type_id",
    "employees":              "employee_id",
    "employee_territories":   "employee_id,territory_id",
    "products":               "product_id",
    "orders":                 "order_id",
    "order_details":          "order_id,product_id",
}

# ── Schema parsing ────────────────────────────────────────────────────────────

_CREATE_RE = re.compile(r"CREATE TABLE (\w+)\s*\((.+?)\);", re.DOTALL | re.IGNORECASE)
_COL_RE = re.compile(r"^\s*(\w+)\s+(\S+)")
_SKIP_KW = ("primary", "foreign", "unique", "check", "constraint")


def parse_schema(sql: str) -> dict[str, list[tuple[str, str]]]:
    """Return {table: [(col_name, col_type)]} from CREATE TABLE statements."""
    result = {}
    for m in _CREATE_RE.finditer(sql):
        cols = []
        for line in m.group(2).splitlines():
            line = line.strip().rstrip(",")
            if not line or any(line.lower().startswith(kw) for kw in _SKIP_KW):
                continue
            cm = _COL_RE.match(line)
            if cm:
                cols.append((cm.group(1), cm.group(2).lower()))
        result[m.group(1)] = cols
    return result


# ── Values parsing ────────────────────────────────────────────────────────────

_INSERT_RE = re.compile(
    r"^INSERT INTO (\w+)(?:\s*\([^)]+\))?\s*VALUES\s*\((.+)\);?$",
    re.IGNORECASE,
)


def _parse_values(raw: str) -> list:
    """Tokenise a SQL VALUES string into a typed Python list."""
    tokens: list[tuple[str, str]] = []
    i = 0
    while i < len(raw):
        while i < len(raw) and raw[i] in " \t\n\r":
            i += 1
        if i >= len(raw):
            break
        if raw[i] == "'":
            i += 1
            s = ""
            while i < len(raw):
                if raw[i] == "'" and i + 1 < len(raw) and raw[i + 1] == "'":
                    s += "'"
                    i += 2
                elif raw[i] == "'":
                    i += 1
                    break
                else:
                    s += raw[i]
                    i += 1
            tokens.append(("str", s))
        elif raw[i] == ",":
            i += 1
        else:
            j = i
            while j < len(raw) and raw[j] not in (",", "'"):
                j += 1
            lit = raw[i:j].strip()
            if lit:
                tokens.append(("lit", lit))
            i = j

    result = []
    for kind, val in tokens:
        if kind == "lit":
            result.append(_cast(val))
        else:
            if val.startswith("\\x"):   # PostgreSQL bytea hex literal
                result.append(None)
            else:
                result.append(val.replace("\\n", "\n").replace("\\t", "\t"))
    return result


def _cast(v: str):
    if v.upper() == "NULL":
        return None
    try:
        return int(v)
    except ValueError:
        pass
    try:
        return float(v)
    except ValueError:
        pass
    return v


# ── Date shifting ────────────────────────────────────────────────────────────

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _shift_date(val: str) -> str:
    """Shift a YYYY-MM-DD string forward by YEAR_SHIFT years."""
    d = date.fromisoformat(val)
    try:
        return d.replace(year=d.year + YEAR_SHIFT).isoformat()
    except ValueError:
        return d.replace(year=d.year + YEAR_SHIFT, day=28).isoformat()  # Feb 29 edge case


def _shift_dates(row: dict) -> dict:
    return {
        k: (_shift_date(v) if isinstance(v, str) and _DATE_RE.match(v) else v)
        for k, v in row.items()
    }


# ── INSERT parsing ────────────────────────────────────────────────────────────

def parse_inserts(
    sql: str, schema: dict[str, list[tuple[str, str]]]
) -> dict[str, list[dict]]:
    """Parse INSERT INTO statements into {table: [row_dict, ...]}."""
    tables: dict[str, list[dict]] = {}
    for line in sql.splitlines():
        line = line.strip()
        if not line.upper().startswith("INSERT"):
            continue
        m = _INSERT_RE.match(line.rstrip(";") + ";")
        if not m:
            continue
        table = m.group(1)
        cols = schema.get(table)
        if not cols:
            continue
        vals = _parse_values(m.group(2))
        if len(cols) != len(vals):
            continue
        row = {
            col: val
            for (col, typ), val in zip(cols, vals)
            if "bytea" not in typ   # drop binary image columns
        }
        tables.setdefault(table, []).append(_shift_dates(row))
    return tables


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    missing = [v for v in ("SUPABASE_URL", "SUPABASE_SERVICE_KEY") if not os.getenv(v)]
    if missing:
        sys.exit(f"Missing env vars: {', '.join(missing)}\nSee .env.example")

    print("Downloading Northwind SQL from GitHub…")
    with urllib.request.urlopen(SQL_URL) as r:
        sql = r.read().decode("utf-8")

    schema = parse_schema(sql)
    tables = parse_inserts(sql, schema)

    total = sum(len(v) for v in tables.values())
    found = [t for t in TABLE_ORDER if t in tables]
    print(f"Parsed {total} rows across {len(found)} tables\n")

    sb = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))
    nw = sb.schema(SCHEMA)

    for name in TABLE_ORDER:
        rows = tables.get(name)
        if not rows:
            continue

        # employees has a self-referential FK (reports_to → employee_id);
        # insert managers (reports_to IS NULL) before their direct reports.
        if name == "employees":
            rows = sorted(rows, key=lambda r: r.get("reports_to") is not None)

        pk = TABLE_PKS[name]
        for i in range(0, len(rows), BATCH_SIZE):
            nw.table(name).upsert(rows[i : i + BATCH_SIZE], on_conflict=pk).execute()
        print(f"  {name}: {len(rows)} rows")

    print("\nDone — Northwind data loaded.")


if __name__ == "__main__":
    main()
