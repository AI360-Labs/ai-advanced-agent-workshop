"""Tables the SQL agent is allowed to reference."""

ALLOWED_TABLES: frozenset[str] = frozenset(
    {
        "products",
        "categories",
        "customers",
        "orders",
        "order_details",
        "employees",
        "shippers",
        "suppliers",
    }
)
