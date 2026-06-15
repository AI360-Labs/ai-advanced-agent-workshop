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
    # A LIMIT inside a subquery must not satisfy the outer query's cap;
    # otherwise the outer SELECT runs unbounded.
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
    # Confirms validate_sql reads max_limit from get_config(), not a hardcoded
    # constant — changing the setting changes the enforced cap.
    monkeypatch.setattr(
        validate_sql_module,
        "get_config",
        lambda: SimpleNamespace(sql_max_limit=10),
    )

    sql = validate_sql("SELECT product_id FROM products")
    assert sql.rstrip().upper().endswith("LIMIT 10")

    with pytest.raises(SqlValidationError, match="between 1 and"):
        validate_sql("SELECT product_id FROM products LIMIT 50")
