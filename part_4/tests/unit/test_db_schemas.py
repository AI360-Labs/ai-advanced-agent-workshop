from uuid import UUID

import pytest
from pydantic import ValidationError

from db.allowlist import ALLOWED_TABLES
from db.schemas import ProductRow, ReportMatch, SqlQueryResult


def test_allowlist_has_mandatory_tables() -> None:
    assert "products" in ALLOWED_TABLES
    assert "orders" in ALLOWED_TABLES
    assert "territories" not in ALLOWED_TABLES


def test_product_row_from_dict() -> None:
    row = ProductRow.model_validate(
        {
            "product_id": 1,
            "product_name": "Chai",
            "unit_price": 18.0,
            "units_in_stock": 39,
            "discontinued": 0,
        }
    )

    assert row.product_name == "Chai"


def test_product_row_rejects_missing_name() -> None:
    with pytest.raises(ValidationError):
        ProductRow.model_validate({"product_id": 1})


def test_report_match_accepts_uuid() -> None:
    match = ReportMatch.model_validate(
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Q2 Strategy",
            "content": "Expansion into EU markets.",
            "distance": 0.12,
        }
    )

    assert isinstance(match.id, UUID)


def test_sql_query_result_shape() -> None:
    result = SqlQueryResult.model_validate(
        {
            "sql": "SELECT product_id FROM products LIMIT 5",
            "rationale": "list ids",
            "row_count": 1,
            "rows": [{"product_id": 1}],
        }
    )

    assert result.row_count == 1
    assert result.rows[0]["product_id"] == 1
