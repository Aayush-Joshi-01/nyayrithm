from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.vector_db.base import SearchResult, VectorChunk

H = "user-a"


@pytest.fixture
def case_id(seed) -> str:
    return seed.case(H)


@pytest.fixture
def storage_root(db_path):
    return db_path.parent / "storage"


def upload(client, case, headers, name="note.txt", data=b"The witness saw a red car.",
           mime="text/plain", **params):
    return client.post(
        f"/api/v1/cases/{case}/evidence/", headers=headers, params=params,
        files={"file": (name, data, mime)},
    )


async def test_upload_stores_the_file_and_queues_ingestion(
    client, auth_headers, case_id, queued, storage_root
):
    r = await upload(client, case_id, auth_headers(H), title="Witness note")
    assert r.status_code == 201
    body = r.json()
    assert body["title"] == "Witness note" and body["status"] == "pending"
    assert body["evidence_type"] == "text" and body["modality"] == "text"
    assert body["file_size"] == len(b"The witness saw a red car.")

    stored = storage_root / body["file_path"]
    assert stored.read_bytes() == b"The witness saw a red car."
    queued["ingest"].assert_called_once_with(body["id"], case_id, body["file_path"], "text/plain")


async def test_title_defaults_to_the_filename(client, auth_headers, case_id, queued):
    r = await upload(client, case_id, auth_headers(H), name="statement.txt")
    assert r.json()["title"] == "statement.txt"


@pytest.mark.parametrize("name,mime,etype,modality", [
    ("report.pdf", "application/pdf", "pdf", "text"),
    ("photo.png", "image/png", "image", "image"),
    ("call.mp3", "audio/mpeg", "audio", "audio"),
    ("cctv.mp4", "video/mp4", "video", "video"),
    ("brief.docx",
     "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "docx", "text"),
])
async def test_evidence_type_follows_the_mime_type(
    client, auth_headers, case_id, queued, name, mime, etype, modality
):
    body = (await upload(client, case_id, auth_headers(H), name=name, mime=mime)).json()
    assert body["evidence_type"] == etype and body["modality"] == modality


@pytest.mark.parametrize("hostile", [
    "../../../etc/passwd",
    "..\\..\\windows\\system32\\config",
    "/absolute/path/evil.txt",
    "name with $pecial & <chars>.txt",
    ".hidden",
])
async def test_hostile_filenames_cannot_escape_the_storage_directory(
    client, auth_headers, case_id, queued, storage_root, hostile
):
    r = await upload(client, case_id, auth_headers(H), name=hostile)
    assert r.status_code == 201
    key = r.json()["file_path"]
    assert key.startswith(f"cases/{case_id}/evidence/")
    assert ".." not in key and "\\" not in key
    assert (storage_root / key).resolve().is_relative_to(storage_root.resolve())
    assert (storage_root / key).exists()


async def test_empty_upload_is_rejected(client, auth_headers, case_id, queued):
    r = await upload(client, case_id, auth_headers(H), data=b"")
    assert r.status_code == 422
    queued["ingest"].assert_not_called()


async def test_oversized_upload_is_rejected_before_it_is_stored(
    client, auth_headers, case_id, queued, storage_root, monkeypatch
):
    from app.config import get_settings

    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    get_settings.cache_clear()
    r = await upload(client, case_id, auth_headers(H), data=b"x" * (1024 * 1024 + 1))
    assert r.status_code == 413 and "1 MB" in r.json()["message"]
    queued["ingest"].assert_not_called()
    assert not any(storage_root.rglob("*.txt"))


async def test_upload_to_a_missing_case_is_404_and_stores_nothing(
    client, auth_headers, queued, storage_root
):
    r = await upload(client, "6f1c3a3e-0000-4000-8000-000000000000", auth_headers(H))
    assert r.status_code == 404
    queued["ingest"].assert_not_called()
    assert not storage_root.exists() or not any(storage_root.rglob("*.txt"))


async def test_list_get_and_paging(client, auth_headers, case_id, queued):
    h = auth_headers(H)
    ids = [(await upload(client, case_id, h, name=f"e{i}.txt")).json()["id"] for i in range(3)]
    page = (await client.get(f"/api/v1/cases/{case_id}/evidence/?size=2", headers=h)).json()
    assert page["total"] == 3 and len(page["items"]) == 2
    one = await client.get(f"/api/v1/cases/{case_id}/evidence/{ids[0]}", headers=h)
    assert one.status_code == 200 and one.json()["id"] == ids[0]


async def test_delete_removes_file_row_and_vector_chunks(
    client, auth_headers, case_id, queued, storage_root, monkeypatch
):
    store = MagicMock(delete=AsyncMock())
    monkeypatch.setattr("app.vector_db.factory.get_vector_store", lambda: store)
    h = auth_headers(H)
    body = (await upload(client, case_id, h)).json()
    path = storage_root / body["file_path"]
    assert path.exists()

    assert (await client.delete(f"/api/v1/cases/{case_id}/evidence/{body['id']}", headers=h)
            ).status_code == 204
    assert not path.exists()
    assert (await client.get(f"/api/v1/cases/{case_id}/evidence/{body['id']}", headers=h)
            ).status_code == 404


async def test_delete_still_succeeds_when_the_vector_store_is_down(
    client, auth_headers, case_id, queued, monkeypatch
):
    def boom():
        raise ConnectionError("qdrant unreachable")

    monkeypatch.setattr("app.vector_db.factory.get_vector_store", boom)
    h = auth_headers(H)
    ev = (await upload(client, case_id, h)).json()["id"]
    assert (await client.delete(f"/api/v1/cases/{case_id}/evidence/{ev}", headers=h)
            ).status_code == 204


async def test_reindex_resets_status_and_requeues(client, auth_headers, case_id, queued, seed):
    ev = seed.evidence(case_id, H, status="error")
    h = auth_headers(H)
    r = await client.post(f"/api/v1/cases/{case_id}/evidence/{ev}/reindex", headers=h)
    assert r.status_code == 202
    assert (await client.get(f"/api/v1/cases/{case_id}/evidence/{ev}", headers=h)
            ).json()["status"] == "pending"
    queued["ingest"].assert_called_once_with(ev, case_id, "cases/x/a.txt", "text/plain")


async def test_search_returns_titled_results(client, auth_headers, case_id, seed, monkeypatch):
    ev = seed.evidence(case_id, H)
    chunk = VectorChunk(id="c1", text="red car near the market",
                        embedding=[0.0], metadata={"evidence_id": ev, "chunk_index": 0})

    class FakeRetriever:
        def __init__(self, store):
            pass

        async def search_case(self, **kw):
            assert kw["top_k"] == 3 and kw["case_id"]
            return [SearchResult(chunk=chunk, score=0.91)]

    monkeypatch.setattr("app.rag.retriever.EvidenceRetriever", FakeRetriever)
    monkeypatch.setattr("app.vector_db.factory.get_vector_store", lambda: object())
    r = await client.post(f"/api/v1/cases/{case_id}/search", headers=auth_headers(H),
                          json={"query": "car", "top_k": 3})
    assert r.status_code == 200
    assert r.json() == [{
        "chunk_id": "c1", "evidence_id": ev, "evidence_title": "Exhibit A",
        "text": "red car near the market", "modality": "text", "score": 0.91,
        "metadata": {"evidence_id": ev, "chunk_index": 0},
    }]
