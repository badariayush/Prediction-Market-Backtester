from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

_IGNORED_DIRS = {".git", ".venv", "__pycache__", "node_modules", "dist", "build"}


@dataclass(frozen=True)
class SourceFile:
    relative_path: str
    content: str


class ProjectScanner:
    def scan_python_sources(self, project_root: Path) -> list[SourceFile]:
        if not project_root.exists() or not project_root.is_dir():
            raise FileNotFoundError(project_root)

        sources: list[SourceFile] = []
        for path in sorted(project_root.rglob("*.py")):
            relative_parts = path.relative_to(project_root).parts
            if any(part in _IGNORED_DIRS or part.startswith(".") for part in relative_parts):
                continue
            sources.append(
                SourceFile(
                    relative_path=str(path.relative_to(project_root)),
                    content=path.read_text(),
                )
            )
        return sources
