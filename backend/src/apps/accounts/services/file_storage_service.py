import os
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile


class FileStorageService(ABC):
    """Abstract interface for file storage services."""

    @abstractmethod
    def save_file(self, file_content: UploadedFile, filename: str, user_id: int) -> str:
        """Save file and return storage path/key.

        Args:
            file_content: Uploaded file content.
            filename: Original filename.
            user_id: ID of the user uploading the file.

        Returns:
            Storage path/key that can be used to retrieve the file later.
        """
        raise NotImplementedError

    @abstractmethod
    def get_file_path(self, storage_path: str) -> str:
        """Get full path/URL to access file.

        Args:
            storage_path: Storage path/key returned by save_file.

        Returns:
            Full path or URL to access the file.
        """
        raise NotImplementedError

    @abstractmethod
    def delete_file(self, storage_path: str) -> None:
        """Delete file from storage.

        Args:
            storage_path: Storage path/key returned by save_file.
        """
        raise NotImplementedError


class LocalFileStorageService(FileStorageService):
    """Local filesystem implementation of FileStorageService."""

    def __init__(self) -> None:
        """Initialize local file storage service."""
        storage_dir = getattr(settings, "CSV_STORAGE_LOCAL_DIR", "files")
        self.storage_dir = Path(storage_dir)

        if not self.storage_dir.is_absolute():
            # Resolve BASE_DIR to absolute path to ensure consistency across different working directories
            base_dir = Path(settings.BASE_DIR).resolve().parent
            self.storage_dir = (base_dir / storage_dir).resolve()

        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_content: UploadedFile, filename: str, user_id: int) -> str:
        """Save file to local filesystem.

        Args:
            file_content: Uploaded file content.
            filename: Original filename.
            user_id: ID of the user uploading the file.

        Returns:
            Relative storage path.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = uuid.uuid4().hex[:8]
        safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
        unique_filename = f"{timestamp}_{user_id}_{unique_id}_{safe_filename}"
        file_path = self.storage_dir / unique_filename

        # Ensure filename is unique by checking existence and appending counter if needed
        counter = 1
        original_file_path = file_path
        while file_path.exists():
            stem = original_file_path.stem
            suffix = original_file_path.suffix
            unique_filename = f"{stem}_{counter}{suffix}"
            file_path = self.storage_dir / unique_filename
            counter += 1

        with open(file_path, "wb") as f:
            for chunk in file_content.chunks():
                f.write(chunk)

        return unique_filename

    def get_file_path(self, storage_path: str) -> str:
        """Get full path to access file.

        Args:
            storage_path: Storage path/key returned by save_file.

        Returns:
            Full absolute path to the file.
        """
        path = Path(storage_path)
        if path.is_absolute():
            return str(path.resolve())

        return str((self.storage_dir / storage_path).resolve())

    def delete_file(self, storage_path: str) -> None:
        """Delete file from local filesystem.

        Args:
            storage_path: Storage path returned by save_file.
        """
        file_path = Path(self.get_file_path(storage_path))
        if file_path.exists():
            os.unlink(file_path)


def get_file_storage_service() -> FileStorageService:
    """Get configured file storage service instance.

    Returns:
        FileStorageService instance based on CSV_STORAGE_BACKEND setting.
    """
    backend = getattr(settings, "CSV_STORAGE_BACKEND", "local")

    if backend == "local":
        return LocalFileStorageService()
    elif backend == "s3":
        raise NotImplementedError("S3 storage backend not yet implemented")
    else:
        raise ValueError(f"Unknown storage backend: {backend}")
