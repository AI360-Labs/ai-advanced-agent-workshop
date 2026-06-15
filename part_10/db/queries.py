"""Parameterized ORM query catalog for common Northwind questions."""

from collections.abc import Awaitable, Callable
from typing import Any, Literal, TypeAlias, get_args

from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import (
    Category,
    Customer,
    Employee,
    Order,
    OrderDetail,
    Product,
    Supplier,
)


class CustomerParams(BaseModel):
    customer_id: str


class LimitParams(BaseModel):
    limit: int = Field(default=10, ge=1, le=100)


class ThresholdParams(BaseModel):
    threshold: int = Field(default=10, ge=0)


class CategoryParams(BaseModel):
    category_name: str
    limit: int = Field(default=20, ge=1, le=100)


class CountryParams(BaseModel):
    country: str


class SupplierCountryParams(BaseModel):
    country: str
    limit: int = Field(default=20, ge=1, le=100)


class CustomersInCountryParams(BaseModel):
    country: str
    limit: int = Field(default=50, ge=1, le=100)


def _line_total():
    return OrderDetail.unit_price * OrderDetail.quantity * (1 - OrderDetail.discount)


async def count_orders_for_customer(
    session: AsyncSession, params: CustomerParams
) -> list[dict[str, Any]]:
    stmt = (
        select(func.count())
        .select_from(Order)
        .where(Order.customer_id == params.customer_id)
    )
    count = (await session.execute(stmt)).scalar_one()
    return [{"customer_id": params.customer_id, "order_count": count}]


async def top_products_by_revenue(
    session: AsyncSession, params: LimitParams
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            func.sum(_line_total()).label("revenue"),
        )
        .join(OrderDetail, OrderDetail.product_id == Product.product_id)
        .group_by(Product.product_id, Product.product_name)
        .order_by(func.sum(_line_total()).desc())
        .limit(params.limit)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def revenue_by_category(
    session: AsyncSession, params: LimitParams
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Category.category_name,
            func.sum(_line_total()).label("revenue"),
        )
        .join(Product, Product.category_id == Category.category_id)
        .join(OrderDetail, OrderDetail.product_id == Product.product_id)
        .group_by(Category.category_name)
        .order_by(func.sum(_line_total()).desc())
        .limit(params.limit)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def top_customers_by_order_count(
    session: AsyncSession, params: LimitParams
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Customer.customer_id,
            Customer.company_name,
            func.count(Order.order_id).label("order_count"),
        )
        .join(Order, Order.customer_id == Customer.customer_id)
        .group_by(Customer.customer_id, Customer.company_name)
        .order_by(func.count(Order.order_id).desc())
        .limit(params.limit)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def low_stock_products(
    session: AsyncSession, params: ThresholdParams
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            Product.units_in_stock,
        )
        .where(
            or_(Product.discontinued == 0, Product.discontinued.is_(None)),
            Product.units_in_stock < params.threshold,
        )
        .order_by(Product.units_in_stock)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def products_in_category(
    session: AsyncSession, params: CategoryParams
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            Category.category_name,
        )
        .join(Category, Category.category_id == Product.category_id)
        .where(Category.category_name.ilike(params.category_name))
        .order_by(Product.product_name)
        .limit(params.limit)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def orders_by_ship_country(
    session: AsyncSession, params: CountryParams
) -> list[dict[str, Any]]:
    stmt = (
        select(func.count())
        .select_from(Order)
        .where(Order.ship_country.ilike(params.country))
    )
    count = (await session.execute(stmt)).scalar_one()
    return [{"ship_country": params.country, "order_count": count}]


async def orders_per_employee(
    session: AsyncSession, params: LimitParams
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Employee.employee_id,
            Employee.first_name,
            Employee.last_name,
            func.count(Order.order_id).label("order_count"),
        )
        .join(Order, Order.employee_id == Employee.employee_id)
        .group_by(
            Employee.employee_id,
            Employee.first_name,
            Employee.last_name,
        )
        .order_by(func.count(Order.order_id).desc())
        .limit(params.limit)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def products_by_supplier_country(
    session: AsyncSession, params: SupplierCountryParams
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Product.product_id,
            Product.product_name,
            Supplier.company_name,
            Supplier.country,
        )
        .join(Supplier, Supplier.supplier_id == Product.supplier_id)
        .where(Supplier.country.ilike(params.country))
        .order_by(Product.product_name)
        .limit(params.limit)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


async def customers_in_country(
    session: AsyncSession, params: CustomersInCountryParams
) -> list[dict[str, Any]]:
    stmt = (
        select(
            Customer.customer_id,
            Customer.company_name,
            Customer.country,
        )
        .where(Customer.country.ilike(params.country))
        .order_by(Customer.company_name)
        .limit(params.limit)
    )
    rows = (await session.execute(stmt)).mappings().all()
    return [dict(row) for row in rows]


class CatalogQuery(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    name: str
    description: str
    param_model: type[BaseModel]
    handler: Callable[[AsyncSession, BaseModel], Awaitable[list[dict[str, Any]]]]


QUERY_CATALOG: dict[str, CatalogQuery] = {
    "count_orders_for_customer": CatalogQuery(
        name="count_orders_for_customer",
        description=(
            "Count orders placed by one customer. "
            "params: customer_id (5-letter code, e.g. ALFKI)."
        ),
        param_model=CustomerParams,
        handler=count_orders_for_customer,
    ),
    "top_products_by_revenue": CatalogQuery(
        name="top_products_by_revenue",
        description=(
            "Top products ranked by total revenue. params: limit (int, default 10)."
        ),
        param_model=LimitParams,
        handler=top_products_by_revenue,
    ),
    "revenue_by_category": CatalogQuery(
        name="revenue_by_category",
        description=(
            "Total revenue grouped by product category. params: limit (int, default 10)."
        ),
        param_model=LimitParams,
        handler=revenue_by_category,
    ),
    "top_customers_by_order_count": CatalogQuery(
        name="top_customers_by_order_count",
        description=(
            "Customers with the most orders. params: limit (int, default 10)."
        ),
        param_model=LimitParams,
        handler=top_customers_by_order_count,
    ),
    "low_stock_products": CatalogQuery(
        name="low_stock_products",
        description=(
            "Non-discontinued products below a stock threshold. "
            "params: threshold (int, default 10)."
        ),
        param_model=ThresholdParams,
        handler=low_stock_products,
    ),
    "products_in_category": CatalogQuery(
        name="products_in_category",
        description=(
            "Products in a named category. "
            "params: category_name (str), limit (int, default 20)."
        ),
        param_model=CategoryParams,
        handler=products_in_category,
    ),
    "orders_by_ship_country": CatalogQuery(
        name="orders_by_ship_country",
        description="Order count shipped to a country. params: country (str).",
        param_model=CountryParams,
        handler=orders_by_ship_country,
    ),
    "orders_per_employee": CatalogQuery(
        name="orders_per_employee",
        description=(
            "Order count grouped by employee. params: limit (int, default 10)."
        ),
        param_model=LimitParams,
        handler=orders_per_employee,
    ),
    "products_by_supplier_country": CatalogQuery(
        name="products_by_supplier_country",
        description=(
            "Products supplied from a given country. "
            "params: country (str), limit (int, default 20)."
        ),
        param_model=SupplierCountryParams,
        handler=products_by_supplier_country,
    ),
    "customers_in_country": CatalogQuery(
        name="customers_in_country",
        description=(
            "Customers located in a given country. "
            "params: country (str), limit (int, default 50)."
        ),
        param_model=CustomersInCountryParams,
        handler=customers_in_country,
    ),
}


CatalogQueryName: TypeAlias = Literal[
    "count_orders_for_customer",
    "top_products_by_revenue",
    "revenue_by_category",
    "top_customers_by_order_count",
    "low_stock_products",
    "products_in_category",
    "orders_by_ship_country",
    "orders_per_employee",
    "products_by_supplier_country",
    "customers_in_country",
]

CUSTOM_QUERY_NAME: Literal["custom"] = "custom"

QueryName: TypeAlias = CatalogQueryName | Literal["custom"]

assert frozenset(QUERY_CATALOG) == frozenset(get_args(CatalogQueryName))


def catalog_descriptions() -> str:
    return "\n".join(f"- {q.name}: {q.description}" for q in QUERY_CATALOG.values())
