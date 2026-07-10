from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile


class UnsafeArchiveError(ValueError):
    pass


class StrategyArchiveExtractor:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root
        self.upload_root = storage_root / "uploads"
        self.upload_root.mkdir(parents=True, exist_ok=True)

    def extract_zip(self, archive_path: Path, project_id: str) -> Path:
        destination = self.upload_root / project_id
        destination.mkdir(parents=True, exist_ok=True)
        with ZipFile(archive_path) as zip_file:
            for member in zip_file.infolist():
                target = destination / member.filename
                if not target.resolve().is_relative_to(destination.resolve()):
                    raise UnsafeArchiveError(f"unsafe archive path: {member.filename}")
                if member.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(zip_file.read(member))
        return destination
