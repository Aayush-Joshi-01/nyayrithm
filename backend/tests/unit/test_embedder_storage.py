from __future__ import annotations

import io

import pytest

from app.ingestion import vision
from app.rag.embedder import (
    GeminiEmbedder,
    OpenAIEmbedder,
    SentenceTransformerEmbedder,
    TextEmbeddingMixin,
    UnsupportedModalityError,
)
from app.storage.local import LocalFileStorage


class RecordingEmbedder(TextEmbeddingMixin):
    def __init__(self) -> None:
        self.embedded: list[str] = []

    async def embed_text(self, text: str) -> list[float]:
        self.embedded.append(text)
        return [float(len(text))]


async def test_image_is_embedded_through_its_transcript(monkeypatch):
    async def fake(image_bytes, mime_type, transcriber=None):
        return "stamp: RECEIVED 4 MAR", "ok"

    monkeypatch.setattr(vision, "transcribe_image", fake)
    e = RecordingEmbedder()
    assert await e.embed_image(b"png") == [21.0]
    assert e.embedded == ["stamp: RECEIVED 4 MAR"]


async def test_image_without_a_transcript_explains_what_to_configure(monkeypatch):
    async def fake(image_bytes, mime_type, transcriber=None):
        return None, "unavailable"

    monkeypatch.setattr(vision, "transcribe_image", fake)
    with pytest.raises(UnsupportedModalityError, match="API key"):
        await RecordingEmbedder().embed_image(b"png")


async def test_audio_is_directed_to_the_transcript_path():
    with pytest.raises(UnsupportedModalityError, match="transcribed during ingestion"):
        await RecordingEmbedder().embed_audio(b"wav")


async def test_multimodal_prefers_text_then_image(monkeypatch):
    async def fake(image_bytes, mime_type, transcriber=None):
        return "from image", "ok"

    monkeypatch.setattr(vision, "transcribe_image", fake)
    e = RecordingEmbedder()
    await e.embed_multimodal({"text": "from text", "image": b"x"})
    await e.embed_multimodal({"image": b"x"})
    assert e.embedded == ["from text", "from image"]
    with pytest.raises(UnsupportedModalityError):
        await e.embed_multimodal({})


@pytest.mark.parametrize("cls", [OpenAIEmbedder, GeminiEmbedder, SentenceTransformerEmbedder])
def test_every_embedder_has_the_full_modality_interface(cls):
    assert issubclass(cls, TextEmbeddingMixin)
    for method in ("embed_text", "embed_image", "embed_audio", "embed_multimodal"):
        assert callable(getattr(cls, method))


# ── local storage ─────────────────────────────────────────────────────────────
async def test_storage_roundtrip(tmp_path):
    store = LocalFileStorage(str(tmp_path))
    await store.upload("cases/1/a.txt", io.BytesIO(b"hello"), "text/plain")
    assert await store.exists("cases/1/a.txt")
    assert await store.download("cases/1/a.txt") == b"hello"
    assert (await store.localize("cases/1/a.txt")).endswith("a.txt")
    await store.delete("cases/1/a.txt")
    assert not await store.exists("cases/1/a.txt")
    await store.delete("cases/1/a.txt")  # deleting twice is harmless


@pytest.mark.parametrize("key", ["../outside.txt", "cases/../../outside.txt", "/etc/passwd"])
async def test_storage_refuses_path_traversal(tmp_path, key):
    store = LocalFileStorage(str(tmp_path / "root"))
    with pytest.raises(ValueError, match="traversal"):
        await store.upload(key, io.BytesIO(b"x"), "text/plain")
    assert not (tmp_path / "outside.txt").exists()


async def test_localizing_a_missing_file_is_an_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        await LocalFileStorage(str(tmp_path)).localize("nope.txt")
