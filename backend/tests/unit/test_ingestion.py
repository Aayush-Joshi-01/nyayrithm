from __future__ import annotations

import base64
import io
from pathlib import Path

import httpx
import pytest
from PIL import Image

from app.config import get_settings
from app.ingestion import vision
from app.ingestion.image import ImageIngester
from app.ingestion.pdf import PDFIngester
from app.ingestion.vision import (
    AnthropicVision,
    GeminiVision,
    OpenAIVision,
    get_vision_transcriber,
    normalize_image,
    transcribe_image,
)


class FakeTranscriber:
    name = "fake"

    def __init__(self, reply: str | Exception = "TRANSCRIPT: FIR No. 42\n---\nA torn page.") -> None:
        self.reply = reply
        self.calls: list[tuple[int, str]] = []

    async def transcribe(self, image_bytes: bytes, mime_type: str) -> str:
        self.calls.append((len(image_bytes), mime_type))
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def png_bytes(size=(64, 48), mode="RGB") -> bytes:
    buf = io.BytesIO()
    Image.new(mode, size, "white").save(buf, format="PNG")
    return buf.getvalue()


@pytest.fixture
def png_file(tmp_path: Path) -> Path:
    path = tmp_path / "scan.png"
    path.write_bytes(png_bytes())
    return path


# ── image ingester ────────────────────────────────────────────────────────────
async def test_image_text_comes_from_the_vision_transcript(png_file):
    t = FakeTranscriber()
    result = await ImageIngester(t).ingest(str(png_file))
    assert result.raw_text == "TRANSCRIPT: FIR No. 42\n---\nA torn page."
    assert result.transcription == result.raw_text and result.modality == "image"
    assert result.metadata["ocr_status"] == "ok"
    assert (result.metadata["width"], result.metadata["height"], result.metadata["format"]) == (
        64, 48, "PNG")
    assert len(t.calls) == 1 and t.calls[0][1] == "image/png"


async def test_image_without_a_vision_provider_is_still_indexable(png_file, monkeypatch):
    monkeypatch.setattr(vision, "get_vision_transcriber", lambda: None)
    result = await ImageIngester().ingest(str(png_file))
    assert result.metadata["ocr_status"] == "unavailable"
    assert "64x48" in result.raw_text and "text not extracted" in result.raw_text


async def test_a_vision_failure_degrades_instead_of_failing_the_ingestion(png_file):
    result = await ImageIngester(FakeTranscriber(RuntimeError("quota exceeded"))).ingest(
        str(png_file))
    assert result.metadata["ocr_status"] == "failed"
    assert "text not extracted" in result.raw_text


async def test_an_empty_transcript_counts_as_a_failure(png_file):
    result = await ImageIngester(FakeTranscriber("  ")).ingest(str(png_file))
    assert result.metadata["ocr_status"] == "failed"


async def test_unsupported_formats_are_converted_before_sending(tmp_path):
    path = tmp_path / "scan.tiff"
    Image.new("RGBA", (30, 30), (255, 0, 0, 128)).save(path, format="TIFF")
    t = FakeTranscriber()
    await ImageIngester(t).ingest(str(path))
    assert t.calls[0][1] == "image/png"


def test_large_scans_are_downscaled_and_normalised():
    data, mime = normalize_image(png_bytes((5000, 3000), "RGBA"), "image/png")
    with Image.open(io.BytesIO(data)) as img:
        assert max(img.size) == 2000 and img.mode == "RGB"
    assert mime == "image/png"


# ── PDF ingester ──────────────────────────────────────────────────────────────
def make_pdf(path: Path, pages: list[str | None]) -> Path:
    """A PDF whose pages are text (str) or an image-only scan (None)."""
    import fitz

    doc = fitz.open()
    for text in pages:
        page = doc.new_page()
        if text is None:
            page.insert_image(page.rect, stream=png_bytes((200, 200)))
        else:
            page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()
    return path


LONG_TEXT = "The accused was seen near the market at nine in the evening."


async def test_text_pdf_needs_no_ocr(tmp_path):
    t = FakeTranscriber()
    result = await PDFIngester(t).ingest(str(make_pdf(tmp_path / "a.pdf", [LONG_TEXT, LONG_TEXT])))
    assert t.calls == []
    assert result.metadata["ocr_status"] == "not_needed" and result.metadata["page_count"] == 2
    assert LONG_TEXT in result.raw_text


async def test_scanned_pages_are_ocred_and_merged_in_page_order(tmp_path):
    t = FakeTranscriber("SCANNED PAGE TEXT")
    path = make_pdf(tmp_path / "mixed.pdf", [LONG_TEXT, None, LONG_TEXT])
    result = await PDFIngester(t).ingest(str(path))
    assert len(t.calls) == 1
    pages = result.raw_text.split("\n\n")
    assert pages[0].startswith("The accused") and pages[1] == "SCANNED PAGE TEXT"
    assert result.metadata["scanned_pages"] == 1 and result.metadata["ocr_pages"] == 1
    assert result.metadata["ocr_status"] == "ok"


async def test_scanned_pdf_without_a_provider_reports_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(vision, "get_vision_transcriber", lambda: None)
    path = make_pdf(tmp_path / "scan.pdf", [None, None, None])
    result = await PDFIngester().ingest(str(path))
    assert result.metadata["scanned_pages"] == 3 and result.metadata["ocr_pages"] == 0
    assert result.metadata["ocr_status"] == "unavailable"


async def test_one_failed_page_does_not_lose_the_rest(tmp_path):
    class Flaky(FakeTranscriber):
        async def transcribe(self, image_bytes, mime_type):
            self.calls.append((0, mime_type))
            if len(self.calls) == 1:
                raise RuntimeError("transient")
            return "second page text"

    t = Flaky()
    result = await PDFIngester(t).ingest(str(make_pdf(tmp_path / "s.pdf", [None, None])))
    assert result.metadata["ocr_pages"] == 1 and "second page text" in result.raw_text


# ── provider selection ────────────────────────────────────────────────────────
def with_keys(monkeypatch, default="gemini", **keys):
    for name in ("GEMINI_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        monkeypatch.setenv(name, keys.get(name, ""))
    monkeypatch.setenv("LLM_DEFAULT_PROVIDER", default)
    get_settings.cache_clear()


def test_no_keys_means_no_transcriber(monkeypatch):
    with_keys(monkeypatch)
    assert get_vision_transcriber() is None


def test_default_provider_wins_when_it_has_a_key(monkeypatch):
    with_keys(monkeypatch, default="openai", OPENAI_API_KEY="o", GEMINI_API_KEY="g")
    assert isinstance(get_vision_transcriber(), OpenAIVision)


def test_falls_back_to_any_provider_that_has_a_key(monkeypatch):
    with_keys(monkeypatch, default="openai", ANTHROPIC_API_KEY="a")
    assert isinstance(get_vision_transcriber(), AnthropicVision)


async def test_transcribe_image_status_codes(monkeypatch):
    with_keys(monkeypatch)
    assert await transcribe_image(png_bytes(), "image/png") == (None, "unavailable")
    ok = await transcribe_image(png_bytes(), "image/png", FakeTranscriber("hello"))
    assert ok == ("hello", "ok")
    assert (await transcribe_image(b"not an image", "image/png", FakeTranscriber()))[1] == "failed"


# ── provider wire formats (HTTP is stubbed) ───────────────────────────────────
@pytest.fixture
def http(monkeypatch):
    sent: list[dict] = []

    def install(payload: dict):
        async def fake_post(self, url, **kw):
            sent.append({"url": str(url), **kw})
            return httpx.Response(200, json=payload, request=httpx.Request("POST", str(url)))

        monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
        return sent

    return install


async def test_gemini_request_and_response(http):
    sent = http({"candidates": [{"content": {"parts": [{"text": "line one"}, {"text": " two"}]}}]})
    out = await GeminiVision("KEY").transcribe(b"imgbytes", "image/png")
    assert out == "line one two"
    call = sent[0]
    assert "generateContent" in call["url"] and call["params"] == {"key": "KEY"}
    part = call["json"]["contents"][0]["parts"][1]["inline_data"]
    assert part["mime_type"] == "image/png" and base64.b64decode(part["data"]) == b"imgbytes"
    assert "Devanagari" in call["json"]["contents"][0]["parts"][0]["text"]


async def test_openai_request_and_response(http):
    sent = http({"choices": [{"message": {"content": " hello "}}]})
    assert await OpenAIVision("sk-x").transcribe(b"img", "image/png") == "hello"
    call = sent[0]
    assert call["headers"]["Authorization"] == "Bearer sk-x"
    image = call["json"]["messages"][0]["content"][1]["image_url"]["url"]
    assert image.startswith("data:image/png;base64,")


async def test_anthropic_request_and_response(http):
    sent = http({"content": [{"type": "text", "text": "page text"}]})
    assert await AnthropicVision("ak").transcribe(b"img", "image/png") == "page text"
    call = sent[0]
    assert call["headers"]["x-api-key"] == "ak" and "anthropic-version" in call["headers"]
    assert call["json"]["messages"][0]["content"][0]["source"]["media_type"] == "image/png"
