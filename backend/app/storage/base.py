from __future__ import annotations

from typing import BinaryIO, Protocol, runtime_checkable


@runtime_checkable
class FileStorage(Protocol):
    """Abstract file storage. Implementations: local, s3, gcs, azure_blob, minio."""

    async def upload(self, key: str, file: BinaryIO, content_type: str) -> str:
        """Upload file and return its canonical URI/path."""
        ...

    async def download(self, key: str) -> bytes: ...

    async def delete(self, key: str) -> None: ...

    async def exists(self, key: str) -> bool: ...

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        """Return a pre-signed or direct URL for the file."""
        ...
