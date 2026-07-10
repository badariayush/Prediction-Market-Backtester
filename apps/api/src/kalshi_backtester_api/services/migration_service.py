from __future__ import annotations

import difflib
import re
from pathlib import Path

from kalshi_backtester_api.models.migration import CallDiagnostic, MigrationReport
from kalshi_backtester_api.services.project_scanner import ProjectScanner

_SUPPORTED_CALLS = {"get_market", "get_markets", "get_orderbook", "get_price", "get_trades"}
_UNSUPPORTED_CALLS = {"create_order", "place_order", "cancel_order", "get_balance"}
_CALL_PATTERN = re.compile(r"\.([a-zA-Z_][a-zA-Z0-9_]*)\(")
_IMPORT_REPLACEMENTS = {
    "from kalshi_python import KalshiClient": "from kalshi_strategy_sdk import KalshiReplayClient",
    "from kalshi import KalshiClient": "from kalshi_strategy_sdk import KalshiReplayClient",
}


class MigrationService:
    def __init__(self, scanner: ProjectScanner | None = None) -> None:
        self.scanner = scanner or ProjectScanner()

    def migrate_project(self, project_root: Path) -> MigrationReport:
        sources = self.scanner.scan_python_sources(project_root)
        original_sources = {source.relative_path: source.content for source in sources}
        migrated_sources: dict[str, str] = {}
        supported: list[CallDiagnostic] = []
        unsupported: list[CallDiagnostic] = []
        diff_chunks: list[str] = []

        for source in sources:
            migrated = self._migrate_imports(source.content)
            migrated_sources[source.relative_path] = migrated
            supported.extend(self._diagnostics_for(source.relative_path, source.content, True))
            unsupported.extend(self._diagnostics_for(source.relative_path, source.content, False))
            diff_chunks.extend(
                difflib.unified_diff(
                    source.content.splitlines(keepends=True),
                    migrated.splitlines(keepends=True),
                    fromfile=f"a/{source.relative_path}",
                    tofile=f"b/{source.relative_path}",
                )
            )

        diff = ""
        if diff_chunks:
            diff = "diff --git a/project b/project\n" + "".join(diff_chunks)

        return MigrationReport(
            project_root=str(project_root),
            original_sources=original_sources,
            migrated_sources=migrated_sources,
            supported_calls=supported,
            unsupported_calls=unsupported,
            diff=diff,
        )

    def _migrate_imports(self, content: str) -> str:
        migrated = content
        for old, new in _IMPORT_REPLACEMENTS.items():
            migrated = migrated.replace(old, new)
        return migrated

    def _diagnostics_for(
        self,
        filename: str,
        content: str,
        supported: bool,
    ) -> list[CallDiagnostic]:
        diagnostics: list[CallDiagnostic] = []
        call_set = _SUPPORTED_CALLS if supported else _UNSUPPORTED_CALLS
        for line_number, line in enumerate(content.splitlines(), start=1):
            for match in _CALL_PATTERN.finditer(line):
                api_call = match.group(1)
                if api_call not in call_set:
                    continue
                if supported:
                    explanation = f"{api_call} is supported by the replay compatibility layer."
                    replacement = f"Use KalshiReplayClient.{api_call} during replay."
                else:
                    explanation = f"{api_call} is not auto-migrated yet."
                    replacement = "Replace with a replay-safe order intent or SDK helper."
                diagnostics.append(
                    CallDiagnostic(
                        filename=filename,
                        line_number=line_number,
                        api_call=api_call,
                        explanation=explanation,
                        suggested_replacement=replacement,
                    )
                )
        return diagnostics
