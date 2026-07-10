from datetime import UTC, datetime

import pytest

from kalshi_backtest_core.event_store import LocalReplayEventStore
from kalshi_backtest_core.events import MarketStatusChanged


def test_event_store_writes_immutable_dataset_and_reads_in_order(tmp_path) -> None:
    store = LocalReplayEventStore(tmp_path)
    events = [
        MarketStatusChanged(datetime(2026, 1, 1, 0, 1, tzinfo=UTC), 2, "KXB", "open"),
        MarketStatusChanged(datetime(2026, 1, 1, 0, 0, tzinfo=UTC), 1, "KXA", "open"),
    ]

    manifest = store.create_dataset("dataset-1", events, source="fixture")
    loaded = store.load_events("dataset-1")

    assert manifest.event_count == 2
    assert [event.market_ticker for event in loaded] == ["KXA", "KXB"]

    with pytest.raises(FileExistsError):
        store.create_dataset("dataset-1", events, source="fixture")
