from datetime import UTC, datetime

from kalshi_strategy_sdk import (
    KalshiReplayClient,
    LimitOrder,
    MarketState,
    OrderBook,
    OrderBookLevel,
    SignalMetadata,
)


def test_replay_client_exposes_current_multi_market_state_only() -> None:
    client = KalshiReplayClient(
        now=datetime(2026, 1, 1, 10, 5, tzinfo=UTC),
        markets={
            "KXA": MarketState(ticker="KXA", title="A", last_price=41, status="open"),
            "KXB": MarketState(ticker="KXB", title="B", last_price=62, status="open"),
        },
        orderbooks={
            "KXA": OrderBook(
                yes_bids=[OrderBookLevel(price=40, count=20)],
                yes_asks=[OrderBookLevel(price=42, count=30)],
            ),
        },
    )

    assert client.get_price("KXA") == 41
    assert {market.ticker for market in client.get_markets()} == {"KXA", "KXB"}
    assert client.get_orderbook("KXA").yes_asks[0].price == 42


def test_orders_and_signal_metadata_are_optional_strategy_outputs() -> None:
    order = LimitOrder(market_ticker="KXA", side="yes", action="buy", count=5, price=42)
    metadata = SignalMetadata(
        confidence=0.8, estimated_probability=0.55, expected_edge=0.03, notes="cheap"
    )

    assert order.count == 5
    assert metadata.estimated_probability == 0.55
