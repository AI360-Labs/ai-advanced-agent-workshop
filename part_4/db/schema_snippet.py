"""Compact schema text injected into the SQL generation prompt."""

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
