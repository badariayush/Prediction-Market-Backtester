from datetime import UTC, datetime

from kalshi_backtest_core.events import BookLevel, OrderBookUpdated
from kalshi_backtest_core.liquidity import FillAssumptionConfig, LiquidityAwareFillEngine
from kalshi_strategy_sdk import LimitOrder


def book() -> OrderBookUpdated:
    return OrderBookUpdated(
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        sequence=1,
        market_ticker="KXTEST-26",
        yes_bids=[BookLevel(price=40, count=20)],
        yes_asks=[BookLevel(price=42, count=30)],
    )


def test_sell_order_partially_fills_against_visible_bid_depth() -> None:
    engine = LiquidityAwareFillEngine(FillAssumptionConfig(mode="partial"))
    order = LimitOrder(market_ticker="KXTEST-26", side="yes", action="sell", count=100, price=40)

    result = engine.try_fill(order, book(), market_status="open")

    assert result.filled_count == 20
    assert result.remainder_count == 80
    assert result.fills[0].price == 40


def test_conservative_mode_no_fills_when_depth_is_insufficient() -> None:
    engine = LiquidityAwareFillEngine(FillAssumptionConfig(mode="conservative"))
    order = LimitOrder(market_ticker="KXTEST-26", side="yes", action="sell", count=100, price=40)

    result = engine.try_fill(order, book(), market_status="open")

    assert result.filled_count == 0
    assert result.remainder_count == 100
    assert result.fidelity_warnings


def test_no_fill_after_market_close() -> None:
    engine = LiquidityAwareFillEngine(FillAssumptionConfig(mode="partial"))
    order = LimitOrder(market_ticker="KXTEST-26", side="yes", action="buy", count=1, price=42)

    result = engine.try_fill(order, book(), market_status="closed")

    assert result.filled_count == 0
    assert "not open" in result.fidelity_warnings[0]
