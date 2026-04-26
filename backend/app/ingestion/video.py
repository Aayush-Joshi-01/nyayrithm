from __future__ import annotations

import os
import tempfile

from app.ingestion.base import IngestionResult


class VideoIngester:
    supported_mime_types = ["video/mp4", "video/mpeg", "video/quicktime", "video/x-msvideo", "video/webm"]

    async def ingest(self, file_path: str) -> IngestionResult:
        import asyncio
        import ffmpeg
        from faster_whisper import WhisperModel

        loop = asyncio.get_event_loop()

        # Extract audio track to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            audio_path = tmp.name

        try:
            await loop.run_in_executor(
                None,
                lambda: (
                    ffmpeg
                    .input(file_path)
                    .output(audio_path, ac=1, ar="16000", format="wav")
                    .overwrite_output()
                    .run(quiet=True)
                )
            )

            model = WhisperModel("base", device="cpu", compute_type="int8")

            def _transcribe():
                segs, info = model.transcribe(audio_path, beam_size=5)
                seg_list = []
                texts = []
                for s in segs:
                    seg_list.append({"start": s.start, "end": s.end, "text": s.text.strip()})
                    texts.append(s.text.strip())
                return seg_list, " ".join(texts), info

            segments, full_text, info = await loop.run_in_executor(None, _transcribe)

        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)

        return IngestionResult(
            raw_text=full_text,
            transcription=full_text,
            segments=segments,
            modality="video",
            metadata={
                "language": info.language,
                "duration": info.duration,
                "segment_count": len(segments),
                "source": "video",
            },
        )
