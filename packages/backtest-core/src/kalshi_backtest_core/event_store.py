from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from kalshi_backtest_core.events import ReplayEvent, event_sort_key
from kalshi_backtest_core.serialization import event_from_dict, event_to_dict


@dataclass(frozen=True)
class ReplayDatasetManifest:
    dataset_id: str
    source: str
    event_count: int
    schema_version: int = 1


class LocalReplayEventStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def create_dataset(
        self,
        dataset_id: str,
        events: list[ReplayEvent],
        source: str,
    ) -> ReplayDatasetManifest:
        dataset_dir = self.root / dataset_id
        if dataset_dir.exists():
            raise FileExistsError(dataset_id)
        dataset_dir.mkdir(parents=True)
        ordered = sorted(events, key=event_sort_key)
        manifest = ReplayDatasetManifest(
            dataset_id=dataset_id, source=source, event_count=len(ordered)
        )
        (dataset_dir / "manifest.json").write_text(json.dumps(manifest.__dict__, indent=2))
        with (dataset_dir / "events.jsonl").open("w") as handle:
            for event in ordered:
                handle.write(json.dumps(event_to_dict(event), sort_keys=True) + "\n")
        return manifest

    def load_events(
        self,
        dataset_id: str,
        market_tickers: set[str] | None = None,
    ) -> list[ReplayEvent]:
        dataset_dir = self.root / dataset_id
        events_path = dataset_dir / "events.jsonl"
        if not events_path.exists():
            raise FileNotFoundError(dataset_id)
        events = [
            event_from_dict(json.loads(line)) for line in events_path.read_text().splitlines()
        ]
        if market_tickers is not None:
            events = [event for event in events if event.market_ticker in market_tickers]
        return sorted(events, key=event_sort_key)
