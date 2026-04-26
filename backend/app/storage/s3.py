from __future__ import annotations

from typing import BinaryIO

import aioboto3

from app.config import get_settings


class S3FileStorage:
    """AWS S3 (or S3-compatible: MinIO, GCS) file storage."""

    def __init__(self) -> None:
        settings = get_settings()
        self.bucket = settings.S3_BUCKET
        self.region = settings.AWS_REGION
        self.endpoint_url = settings.S3_ENDPOINT_URL
        self._session = aioboto3.Session(
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=self.region,
        )

    def _client(self):
        return self._session.client("s3", endpoint_url=self.endpoint_url)

    async def upload(self, key: str, file: BinaryIO, content_type: str) -> str:
        async with self._client() as s3:
            await s3.upload_fileobj(file, self.bucket, key, ExtraArgs={"ContentType": content_type})
        return f"s3://{self.bucket}/{key}"

    async def download(self, key: str) -> bytes:
        async with self._client() as s3:
            response = await s3.get_object(Bucket=self.bucket, Key=key)
            return await response["Body"].read()

    async def delete(self, key: str) -> None:
        async with self._client() as s3:
            await s3.delete_object(Bucket=self.bucket, Key=key)

    async def exists(self, key: str) -> bool:
        try:
            async with self._client() as s3:
                await s3.head_object(Bucket=self.bucket, Key=key)
            return True
        except Exception:
            return False

    async def get_url(self, key: str, expires_in: int = 3600) -> str:
        async with self._client() as s3:
            return await s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket, "Key": key},
                ExpiresIn=expires_in,
            )
