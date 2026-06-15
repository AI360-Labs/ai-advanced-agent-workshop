"""Pydantic schemas mirroring ORM rows (API and node boundaries)."""

from db.queries import QueryName
from typing import Any

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProductRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    product_name: str
    category_id: int | None = None
    unit_price: float | None = None
    units_in_stock: int | None = None
    discontinued: int | None = None


class CategoryRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    category_name: str
    description: str | None = None


class CustomerRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: str
    company_name: str
    country: str | None = None


class OrderRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    customer_id: str | None = None
    order_date: date | None = None
    ship_country: str | None = None


class ReportMatch(BaseModel):
    """One semantic-search hit from rag.documents."""

    id: UUID
    source: str
    content: str
    distance: float  # cosine distance; lower is closer


class SqlGeneration(BaseModel):
    """LLM-produced SQL before validation."""

    sql: str
    rationale: str


class SqlQueryResult(BaseModel):
    """Output of the guarded SQL path."""

    sql: str
    rationale: str
    row_count: int
    rows: list[dict]


class QuerySelection(BaseModel):
    """LLM pick from the query catalog, or ``custom`` for ad-hoc SQL generation."""

    query_name: QueryName
    params: dict[str, Any] = {}
