from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from django.conf import settings
from django.utils import timezone

from apps.common.exceptions import ExternalServiceException, ValidationException


class FileStorageService:
    """File storage abstraction with a local backend and extension points for cloud providers."""

    LOCAL_BACKEND = "local"
    AZURE_BLOB_BACKEND = "azure_blob"
    S3_BACKEND = "s3"

    _ALLOWED_BACKENDS = {LOCAL_BACKEND, AZURE_BLOB_BACKEND, S3_BACKEND}

    def __init__(
        self,
        *,
        backend: str | None = None,
        base_directory: Path | None = None,
    ) -> None:
        configured_backend = str(
            backend
            or getattr(settings, "DOCUMENT_STORAGE_BACKEND", self.LOCAL_BACKEND)
        ).strip().lower()
        if configured_backend not in self._ALLOWED_BACKENDS:
            raise ValidationException(
                detail=f"Unsupported storage backend '{configured_backend}'."
            )

        self.backend = configured_backend
        self.base_directory = Path(base_directory or getattr(settings, "MEDIA_ROOT", "."))

    @staticmethod
    def _sanitize_file_name(file_name: str) -> str:
        candidate = Path((file_name or "").strip()).name
        candidate = re.sub(r"[^A-Za-z0-9._-]", "_", candidate)
        candidate = candidate.strip("._")
        if not candidate:
            raise ValidationException(detail="A valid file_name is required.")
        return candidate

    @staticmethod
    def _ensure_content(content: bytes | bytearray | memoryview) -> bytes:
        if content is None:
            raise ValidationException(detail="File content is required.")
        if isinstance(content, bytes):
            payload = content
        elif isinstance(content, bytearray):
            payload = bytes(content)
        elif isinstance(content, memoryview):
            payload = content.tobytes()
        else:
            raise ValidationException(detail="File content must be bytes-like.")

        if not payload:
            raise ValidationException(detail="File content cannot be empty.")
        return payload

    def _save_local(
        self,
        *,
        content: bytes,
        file_name: str,
        subdirectory: str,
    ) -> dict[str, Any]:
        date_partition = timezone.now().strftime("%Y/%m/%d")
        relative_path = Path(subdirectory) / date_partition / file_name
        absolute_path = self.base_directory / relative_path

        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(content)

        checksum = hashlib.sha256(content).hexdigest()
        return {
            "storage_backend": self.LOCAL_BACKEND,
            "file_name": file_name,
            "relative_path": relative_path.as_posix(),
            "absolute_path": str(absolute_path),
            "file_size": len(content),
            "checksum": checksum,
        }

    @staticmethod
    def _save_azure_blob(**kwargs):
        raise ExternalServiceException(
            detail=(
                "Azure Blob backend is not configured yet. "
                "Set DOCUMENT_STORAGE_BACKEND=local or implement Azure provider settings."
            )
        )

    @staticmethod
    def _save_s3(**kwargs):
        raise ExternalServiceException(
            detail=(
                "S3 backend is not configured yet. "
                "Set DOCUMENT_STORAGE_BACKEND=local or implement S3 provider settings."
            )
        )

    def save_bytes(
        self,
        *,
        content: bytes | bytearray | memoryview,
        file_name: str,
        subdirectory: str = "generated-documents",
    ) -> dict[str, Any]:
        payload = self._ensure_content(content)
        normalized_name = self._sanitize_file_name(file_name)
        normalized_subdirectory = str(Path(subdirectory)).strip("/\\") or "generated-documents"

        if self.backend == self.LOCAL_BACKEND:
            return self._save_local(
                content=payload,
                file_name=normalized_name,
                subdirectory=normalized_subdirectory,
            )

        if self.backend == self.AZURE_BLOB_BACKEND:
            return self._save_azure_blob(
                content=payload,
                file_name=normalized_name,
                subdirectory=normalized_subdirectory,
            )

        return self._save_s3(
            content=payload,
            file_name=normalized_name,
            subdirectory=normalized_subdirectory,
        )
