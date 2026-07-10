from __future__ import annotations

from pathlib import Path

from kalshi_backtest_core.event_store import LocalReplayEventStore, ReplayDatasetManifest
from kalshi_backtest_core.serialization import event_to_dict
from kalshi_historical_data.normalizer import KalshiDataAdapter


class DatasetService:
    def __init__(self, storage_root: Path) -> None:
        self.storage_root = storage_root
        self.store = LocalReplayEventStore(storage_root / "datasets")

    def create_dataset(
        self,
        dataset_id: str,
        payloads: list[dict[str, object]],
        source: str,
    ) -> ReplayDatasetManifest:
        events = KalshiDataAdapter(source=source).normalize(payloads)
        return self.store.create_dataset(dataset_id=dataset_id, events=events, source=source)

    def list_dataset_ids(self) -> list[str]:
        root = self.storage_root / "datasets"
        if not root.exists():
            return []
        return sorted(path.name for path in root.iterdir() if path.is_dir())

    def get_event_dicts(self, dataset_id: str) -> list[dict[str, object]]:
        return [event_to_dict(event) for event in self.store.load_events(dataset_id)]
