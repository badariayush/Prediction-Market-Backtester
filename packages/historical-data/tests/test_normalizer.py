from datetime import UTC, datetime

from kalshi_backtest_core.events import MarketStatusChanged, OrderBookUpdated, SettlementPublished
from kalshi_historical_data.normalizer import KalshiDataAdapter


def test_kalshi_adapter_normalizes_payloads_into_replay_events() -> None:
    adapter = KalshiDataAdapter(source="fixture")
    raw_payloads = [
        {
            "type": "market",
            "ticker": "KXTEST-26",
            "title": "Test",
            "close_time": "2026-01-02T00:00:00+00:00",
        },
        {
            "type": "orderbook",
            "ticker": "KXTEST-26",
            "ts": "2026-01-01T00:00:00+00:00",
            "yes_bids": [[40, 20]],
            "yes_asks": [[42, 30]],
        },
        {
            "type": "status",
            "ticker": "KXTEST-26",
            "ts": "2026-01-01T00:01:00+00:00",
            "status": "closed",
        },
        {
            "type": "settlement",
            "ticker": "KXTEST-26",
            "ts": "2026-01-02T00:00:00+00:00",
            "result": "yes",
        },
    ]

    events = adapter.normalize(raw_payloads)

    assert isinstance(events[1], OrderBookUpdated)
    assert events[1].yes_bids[0].count == 20
    assert isinstance(events[2], MarketStatusChanged)
    assert isinstance(events[3], SettlementPublished)
    assert [event.sequence for event in events] == [1, 2, 3, 4]


def test_adapter_infers_conservative_closed_status_from_metadata() -> None:
    adapter = KalshiDataAdapter(source="fixture")

    events = adapter.normalize(
        [
            {
                "type": "market",
                "ticker": "KXTEST-26",
                "title": "Test",
                "close_time": "2026-01-01T00:00:00+00:00",
            },
        ],
        now=datetime(2026, 1, 2, tzinfo=UTC),
    )

    assert any(
        isinstance(event, MarketStatusChanged) and event.status == "closed" for event in events
    )
