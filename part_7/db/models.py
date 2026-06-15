"""Postgres ORM models for Northwind sales data and RAG report documents (read source).
"""
# SQLAlchemy ORM models for mandatory Northwind tables and report documents."""

from datetime import date
from uuid import UUID

from sqlalchemy import Date, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import UserDefinedType


class NorthwindBase(DeclarativeBase):
    pass


class Vector(UserDefinedType):
    """Minimal SQLAlchemy type shim for PostgreSQL pgvector columns."""

    cache_ok = True

    def get_col_spec(self, **kw: object) -> str:
        return "vector"


class Category(NorthwindBase):
    __tablename__ = "categories"

    category_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category_name: Mapped[str] = mapped_column(String(50))
    description: Mapped[str | None] = mapped_column(Text)


class Supplier(NorthwindBase):
    __tablename__ = "suppliers"

    supplier_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(100))
    contact_name: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(50))


class Product(NorthwindBase):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_name: Mapped[str] = mapped_column(String(100))
    supplier_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("suppliers.supplier_id")
    )
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.category_id")
    )
    quantity_per_unit: Mapped[str | None] = mapped_column(String(50))
    unit_price: Mapped[float | None] = mapped_column(Float)
    units_in_stock: Mapped[int | None] = mapped_column(Integer)
    units_on_order: Mapped[int | None] = mapped_column(Integer)
    reorder_level: Mapped[int | None] = mapped_column(Integer)
    discontinued: Mapped[int | None] = mapped_column(Integer)


class Customer(NorthwindBase):
    __tablename__ = "customers"

    customer_id: Mapped[str] = mapped_column(String(5), primary_key=True)
    company_name: Mapped[str] = mapped_column(String(100))
    contact_name: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(50))


class Employee(NorthwindBase):
    __tablename__ = "employees"

    employee_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_name: Mapped[str] = mapped_column(String(50))
    first_name: Mapped[str] = mapped_column(String(50))
    title: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(50))


class Shipper(NorthwindBase):
    __tablename__ = "shippers"

    shipper_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(100))
    phone: Mapped[str | None] = mapped_column(String(50))


class Order(NorthwindBase):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[str | None] = mapped_column(
        String(5), ForeignKey("customers.customer_id")
    )
    employee_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("employees.employee_id")
    )
    order_date: Mapped[date | None] = mapped_column(Date)
    shipper_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("shippers.shipper_id")
    )
    freight: Mapped[float | None] = mapped_column(Float)
    ship_country: Mapped[str | None] = mapped_column(String(50))


class OrderDetail(NorthwindBase):
    __tablename__ = "order_details"

    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.order_id"), primary_key=True
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.product_id"), primary_key=True
    )
    unit_price: Mapped[float | None] = mapped_column(Float)
    quantity: Mapped[int | None] = mapped_column(Integer)
    discount: Mapped[float | None] = mapped_column(Float)


class Report(NorthwindBase):
    """Business reports stored with embeddings for semantic search."""

    __tablename__ = "documents"
    __table_args__ = {"schema": "rag"}

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    dataset: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(Text)
    chunk_index: Mapped[int | None] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(), nullable=True)
