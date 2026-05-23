from __future__ import annotations

from app.ingestion.base import IngestionResult


class AudioIngester:
    supported_mime_types = ["audio/mpeg", "audio/wav", "audio/mp4", "audio/ogg", "audio/flac"]

    async def ingest(self, file_path: str) -> IngestionResult:
        import asyncio
        from faster_whisper import WhisperModel

        loop = asyncio.get_event_loop()
        model = WhisperModel("base", device="cpu", compute_type="int8")

        def _transcribe():
            segments, info = model.transcribe(file_path, beam_size=5)
            seg_list = []
            full_text_parts = []
            for seg in segments:
                seg_list.append({
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text.strip(),
                })
                full_text_parts.append(seg.text.strip())
            return seg_list, " ".join(full_text_parts), info

        segments, full_text, info = await loop.run_in_executor(None, _transcribe)

        return IngestionResult(
            raw_text=full_text,
            transcription=full_text,
            segments=segments,
            modality="audio",
            metadata={
                "language": info.language,
                "duration": info.duration,
                "segment_count": len(segments),
                "source": "audio",
            },
        )
