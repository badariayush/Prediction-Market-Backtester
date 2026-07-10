from datetime import UTC, datetime

from kalshi_backtest_core.events import (
    BookLevel,
    MarketMetadataEvent,
    MarketStatusChanged,
    OrderBookUpdated,
    SettlementPublished,
    event_sort_key,
)
from kalshi_backtest_core.serialization import event_from_dict, event_to_dict


def test_replay_events_sort_deterministically_by_timestamp_and_sequence() -> None:
    late = MarketStatusChanged(
        timestamp=datetime(2026, 1, 1, 0, 1, tzinfo=UTC),
        sequence=1,
        market_ticker="KXTEST-26",
        status="open",
    )
    early_high_sequence = OrderBookUpdated(
        timestamp=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        sequence=2,
        market_ticker="KXTEST-26",
        yes_bids=[BookLevel(price=40, count=20)],
        yes_asks=[BookLevel(price=42, count=30)],
    )
    early_low_sequence = MarketMetadataEvent(
        timestamp=datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
        sequence=1,
        market_ticker="KXTEST-26",
        title="Test market",
        close_time=datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert sorted([late, early_high_sequence, early_low_sequence], key=event_sort_key) == [
        early_low_sequence,
        early_high_sequence,
        late,
    ]


def test_event_serialization_round_trips_concrete_type() -> None:
    event = SettlementPublished(
        timestamp=datetime(2026, 1, 2, tzinfo=UTC),
        sequence=9,
        market_ticker="KXTEST-26",
        result="yes",
    )

    restored = event_from_dict(event_to_dict(event))

    assert isinstance(restored, SettlementPublished)
    assert restored.result == "yes"
    assert restored.yes_payout_cents == 100
