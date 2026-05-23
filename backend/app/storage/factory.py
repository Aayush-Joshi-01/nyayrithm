from __future__ import annotations

from functools import lru_cache

from app.config import get_settings
from app.storage.base import FileStorage


@lru_cache
def get_file_storage() -> FileStorage:
    settings = get_settings()
    backend = settings.STORAGE_BACKEND

    if backend == "local":
        from app.storage.local import LocalFileStorage
        return LocalFileStorage(root=settings.STORAGE_LOCAL_ROOT)

    if backend in ("s3", "minio"):
        from app.storage.s3 import S3FileStorage
        return S3FileStorage()

    raise NotImplementedError(f"Storage backend '{backend}' not implemented. "
                              f"Add a class to app/storage/ and register it here.")
