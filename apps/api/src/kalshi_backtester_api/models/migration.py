from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass(frozen=True)
class CallDiagnostic:
    filename: str
    line_number: int
    api_call: str
    explanation: str
    suggested_replacement: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class MigrationReport:
    project_root: str
    original_sources: dict[str, str]
    migrated_sources: dict[str, str]
    supported_calls: list[CallDiagnostic] = field(default_factory=list)
    unsupported_calls: list[CallDiagnostic] = field(default_factory=list)
    diff: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "project_root": self.project_root,
            "original_sources": self.original_sources,
            "migrated_sources": self.migrated_sources,
            "supported_calls": [call.to_dict() for call in self.supported_calls],
            "unsupported_calls": [call.to_dict() for call in self.unsupported_calls],
            "diff": self.diff,
        }
