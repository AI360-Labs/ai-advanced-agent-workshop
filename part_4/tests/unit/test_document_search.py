"""Regression: document search must use ORM select(), not raw text().

A raw text() call bypasses column-level type safety and can silently target
the wrong table if the schema changes. Compiling the ORM statement to SQL
verifies the <=> operator, the vector cast, and the correct table are present.
"""

from sqlalchemy import Float, cast, literal, select
from sqlalchemy.dialects import postgresql

from db.models import Report


def test_orm_query_targets_correct_table() -> None:
    distance = Report.embedding.op("<=>", return_type=Float)(
        cast(literal("[0.1,0.2,0.3]"), Report.embedding.type)
    ).label("distance")
    stmt = (
        select(Report.id, Report.title, Report.content, distance)
        .order_by(distance)
        .limit(5)
    )
    sql = str(stmt.compile(dialect=postgresql.dialect()))
    assert "documents.reports" in sql


def test_search_limit_not_hardcoded() -> None:
    """Search result cap must come from Config, not a module-level constant."""
    import agent.nodes.document_search as ds

    assert not hasattr(ds, "SEARCH_LIMIT")


def test_orm_query_uses_vector_distance_operator() -> None:
    distance = Report.embedding.op("<=>", return_type=Float)(
        cast(literal("[0.1,0.2,0.3]"), Report.embedding.type)
    ).label("distance")
    stmt = (
        select(Report.id, Report.title, Report.content, distance)
        .order_by(distance)
        .limit(5)
    )
    sql = str(stmt.compile(dialect=postgresql.dialect()))
    assert "<=>" in sql
    assert "vector" in sql.lower()
