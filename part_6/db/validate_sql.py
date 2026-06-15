"""Guardrails for LLM-generated SQL before execution."""

import sqlglot
from sqlglot import exp

from config.settings import get_config
from db.allowlist import ALLOWED_TABLES
from utils.logger import get_logger

logger = get_logger(__name__)

FORBIDDEN_KEYWORDS = frozenset(
    {
        "insert",
        "update",
        "delete",
        "drop",
        "alter",
        "truncate",
        "create",
        "grant",
        "revoke",
    }
)


class SqlValidationError(ValueError):
    """Raised when generated SQL fails safety checks."""


def normalize_sql(sql: str) -> str:
    return sql.strip().rstrip(";")


def validate_sql(sql: str, *, max_limit: int | None = None) -> str:
    """Return safe SQL or raise ``SqlValidationError``.

    Rules:
    - single ``SELECT`` statement only
    - only allowlisted tables
    - must include ``LIMIT`` (injected if missing)
    - no forbidden keywords anywhere in the text
    """
    if max_limit is None:
        max_limit = get_config().sql_max_limit
    cleaned = normalize_sql(sql)
    lowered = cleaned.lower()

    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in lowered:
            raise SqlValidationError(f"Forbidden keyword in SQL: {keyword}")

    try:
        expression = sqlglot.parse_one(cleaned, dialect="postgres")
    except sqlglot.errors.ParseError as exc:
        raise SqlValidationError(f"SQL parse error: {exc}") from exc

    if not isinstance(expression, exp.Select):
        raise SqlValidationError("Only SELECT statements are allowed")

    tables = {t.name.lower() for t in expression.find_all(exp.Table)}
    unknown = tables - ALLOWED_TABLES
    if unknown:
        raise SqlValidationError(f"Tables not allowed: {sorted(unknown)}")

    if expression.args.get("limit") is None:
        cleaned = f"{cleaned} LIMIT {max_limit}"
        expression = sqlglot.parse_one(cleaned, dialect="postgres")

    limit_node = expression.args.get("limit")
    if limit_node is not None:
        try:
            value = int(limit_node.expression.this)  # type: ignore[union-attr]
        except (AttributeError, ValueError, TypeError):
            raise SqlValidationError("LIMIT must be a positive integer") from None
        if value <= 0 or value > max_limit:
            raise SqlValidationError(f"LIMIT must be between 1 and {max_limit}")

    logger.info(f"SQL validated ({len(tables)} tables): {cleaned[:120]}")
    return cleaned
