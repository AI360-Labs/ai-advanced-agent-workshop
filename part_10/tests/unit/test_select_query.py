import asyncio

import pytest

import agent.nodes.select_query as select_module
from db.schemas import QuerySelection


def test_select_query_uses_catalog_match(monkeypatch: pytest.MonkeyPatch) -> None:
    selection = QuerySelection(
        query_name="count_orders_for_customer",
        params={"customer_id": "ALFKI"},
    )

    class FakeClient:
        async def astructured(
            self, prompt: str, variables: dict, schema: type
        ) -> QuerySelection:
            return selection

    monkeypatch.setattr(select_module, "client", FakeClient())

    update = asyncio.run(
        select_module.select_query({"question": "How many orders did ALFKI place?"})
    )

    assert update["query_selection"] is not None
    assert update["query_selection"].query_name == "count_orders_for_customer"
    assert update["query_selection"].params == {"customer_id": "ALFKI"}


def test_select_query_custom_falls_back(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeClient:
        async def astructured(
            self, prompt: str, variables: dict, schema: type
        ) -> QuerySelection:
            return QuerySelection(query_name="custom", params={})

    monkeypatch.setattr(select_module, "client", FakeClient())

    update = asyncio.run(select_module.select_query({"question": "Something novel"}))

    assert update["query_selection"] is None


def test_select_query_invalid_params_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeClient:
        async def astructured(
            self, prompt: str, variables: dict, schema: type
        ) -> QuerySelection:
            return QuerySelection(
                query_name="count_orders_for_customer",
                params={},
            )

    monkeypatch.setattr(select_module, "client", FakeClient())

    update = asyncio.run(select_module.select_query({"question": "How many orders?"}))

    assert update["query_selection"] is None
