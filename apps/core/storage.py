"""
StorageService: a thin abstraction over the active Django storage backend
(local FileSystemStorage in dev, S3Boto3Storage against Cloudflare R2 in
production, selected by STORAGE_BACKEND).

Keeping this abstraction separate from the models/views means that when we
later add true client-side presigned direct-uploads (browser -> R2, bypassing
the Django app for large PDF bodies), only this module and the upload views
need to change -- the DocumentRevision model and its serializers stay the
same, since they only ever deal with `file.url` / `file.name`.

Today, direct browser uploads to R2 are NOT implemented -- uploads go
through Django (`file` FileField on DocumentRevision) in both dev and prod.
`build_presigned_upload_url` below is a real, working method against R2's
S3-compatible API when STORAGE_BACKEND=r2, but no frontend flow calls it yet;
it exists so that wiring is additive, not a redesign.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from django.conf import settings
from django.core.files.storage import default_storage


@dataclass
class PresignedUpload:
    url: str
    fields: dict
    key: str
    expires_in: int


class StorageService:
    """Backend-agnostic helper for document/media file operations."""

    def __init__(self, storage=None):
        self.storage = storage or default_storage

    @property
    def backend_name(self) -> str:
        return getattr(settings, "STORAGE_BACKEND", "local")

    def build_key(self, folder: str, filename: str) -> str:
        ext = ""
        if "." in filename:
            ext = "." + filename.rsplit(".", 1)[-1]
        return f"{folder.strip('/')}/{uuid.uuid4().hex}{ext}"

    def url_for(self, name: str) -> str:
        return self.storage.url(name)

    def build_presigned_upload_url(self, folder: str, filename: str, content_type: str,
                                    expires_in: int = 3600) -> PresignedUpload:
        """Return a presigned POST for direct-to-R2 uploads.

        Only functional when STORAGE_BACKEND=r2 (needs boto3 + real R2
        credentials); raises NotImplementedError for the local backend since
        FileSystemStorage has no presigning concept. This is the stub the
        project spec asked for -- a real endpoint exists
        (`/api/v1/documents/presign-upload/`) and this is a working
        implementation for R2, but it is not yet wired into any frontend
        upload flow.
        """
        if self.backend_name != "r2":
            raise NotImplementedError(
                "Presigned direct uploads are only available when STORAGE_BACKEND=r2."
            )

        import boto3

        key = self.build_key(folder, filename)
        client = boto3.client(
            "s3",
            endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.R2_ACCESS_KEY_ID,
            aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
            region_name="auto",
        )
        presigned = client.generate_presigned_post(
            Bucket=settings.R2_BUCKET_NAME,
            Key=key,
            Fields={"Content-Type": content_type},
            Conditions=[{"Content-Type": content_type}],
            ExpiresIn=expires_in,
        )
        return PresignedUpload(
            url=presigned["url"],
            fields=presigned["fields"],
            key=key,
            expires_in=expires_in,
        )


storage_service = StorageService()
