FROM python:3.11-slim

# ffmpeg/ffprobe as static binaries: the apt package drags in ~200 GPU/codec libraries.
COPY --from=mwader/static-ffmpeg:7.1 /ffmpeg /usr/local/bin/ffmpeg
COPY --from=mwader/static-ffmpeg:7.1 /ffprobe /usr/local/bin/ffprobe

WORKDIR /app

RUN pip install --no-cache-dir uv

# Optional extras, e.g. --build-arg EXTRAS=local-embeddings for offline embeddings (adds PyTorch).
ARG EXTRAS=""

COPY pyproject.toml .
RUN if [ -n "$EXTRAS" ]; then uv pip install --system --no-cache -e ".[${EXTRAS}]"; \
    else uv pip install --system --no-cache -e .; fi

COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
