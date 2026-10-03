from __future__ import annotations

import pytest
from qdrant_client.http.exceptions import UnexpectedResponse

from app.vector_db.qdrant import QdrantVectorStore


def make_store(exists_after_failure: bool, status: int):
    store = QdrantVectorStore.__new__(QdrantVectorStore)
    calls = {"create": 0, "exists": 0}

    class Client:
        async def get_collection(self, name):
            calls["exists"] += 1
            # the first existence check says "no"; later ones depend on the scenario
            if calls["exists"] == 1 or not exists_after_failure:
                raise RuntimeError("not found")

        async def create_collection(self, **kw):
            calls["create"] += 1
            raise UnexpectedResponse(status, "x", b'{"status":{"error":"already exists"}}', {})

    store.client = Client()
    return store, calls


async def test_losing_the_collection_creation_race_is_not_an_error():
    store, calls = make_store(exists_after_failure=True, status=409)
    await store.create_collection("case-1", 768)  # must not raise
    assert calls["create"] == 1


async def test_a_409_is_tolerated_even_if_the_recheck_is_flaky():
    store, _ = make_store(exists_after_failure=False, status=409)
    await store.create_collection("case-1", 768)


async def test_genuine_failures_still_surface():
    store, _ = make_store(exists_after_failure=False, status=500)
    with pytest.raises(UnexpectedResponse):
        await store.create_collection("case-1", 768)


async def test_existing_collection_is_left_alone():
    store = QdrantVectorStore.__new__(QdrantVectorStore)

    class Client:
        async def get_collection(self, name):
            return object()

        async def create_collection(self, **kw):
            raise AssertionError("must not recreate")

    store.client = Client()
    await store.create_collection("case-1", 768)
