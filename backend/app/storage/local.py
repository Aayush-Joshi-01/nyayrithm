from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO


class LocalFileStorage:
    """Stores files in a local directory. Good for development and air-gapped deployments."""

    def __init__(self, root: str) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise ValueError(f"Path traversal attempt: {key}")
        return p

    async def upload(self, key: str, file: BinaryIO, content_type: str) -> str:
        dest = self._path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(file.read())
        return str(dest)

    async def download(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    async def delete(self, key: str) -> None:
        p = self._path(key)
        if p.exists():
            p.unlink()

    async def exists(self, key: str) -> bool:
        return self._path(key).exists()

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        return f"/storage/{key}"
