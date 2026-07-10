from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ReplayDatasetManifest:
    dataset_id: str
    source: str
    event_count: int
    market_tickers: list[str] = field(default_factory=list)
    schema_version: int = 1
    fidelity_warnings: list[str] = field(default_factory=list)
