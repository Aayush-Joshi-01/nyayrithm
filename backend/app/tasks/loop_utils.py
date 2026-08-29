from __future__ import annotations

"""Helpers for Celery tasks that run their own ``asyncio.run()`` loop.

Every Celery task here spins up a fresh event loop. Async clients cached with
``@lru_cache`` (DB engine/pool, Qdrant, embedder HTTP clients) bind to whatever
loop first created them, so a later task reusing them raises
``RuntimeError: Event loop is closed`` / "Future attached to a different loop".
Clear the caches at the start of each task so every run gets fresh clients.
"""


def clear_loop_bound_caches() -> None:
    from app.db.session import _make_engine, _make_session_factory
    from app.rag.embedder_factory import get_embedder
    from app.vector_db.factory import get_vector_store

    for fn in (_make_engine, _make_session_factory, get_vector_store, get_embedder):
        try:
            fn.cache_clear()
        except AttributeError:
            pass
