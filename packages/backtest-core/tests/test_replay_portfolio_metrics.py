from datetime import UTC, datetime

from kalshi_backtest_core.events import (
    BookLevel,
    OrderBookUpdated,
    PriceUpdated,
    SettlementPublished,
)
from kalshi_backtest_core.liquidity import FillAssumptionConfig, LiquidityAwareFillEngine
from kalshi_backtest_core.metrics import summarize_backtest
from kalshi_backtest_core.replay import ReplayEngine
from kalshi_strategy_sdk import KalshiReplayClient, LimitOrder


class BuyCheapStrategy:
    def on_event(self, client: KalshiReplayClient) -> list[LimitOrder]:
        if client.get_price("KXTEST-26") is not None and client.get_price("KXTEST-26") < 45:
            return [
                LimitOrder(market_ticker="KXTEST-26", side="yes", action="buy", count=10, price=42)
            ]
        return []


def test_replay_engine_updates_portfolio_and_metrics() -> None:
    events = [
        OrderBookUpdated(
            datetime(2026, 1, 1, 0, 0, tzinfo=UTC),
            1,
            "KXTEST-26",
            [BookLevel(price=40, count=20)],
            [BookLevel(price=42, count=20)],
        ),
        PriceUpdated(datetime(2026, 1, 1, 0, 0, tzinfo=UTC), 2, "KXTEST-26", last_price=41),
        PriceUpdated(datetime(2026, 1, 1, 0, 1, tzinfo=UTC), 3, "KXTEST-26", last_price=49),
        SettlementPublished(datetime(2026, 1, 2, tzinfo=UTC), 4, "KXTEST-26", result="yes"),
    ]
    engine = ReplayEngine(
        fill_engine=LiquidityAwareFillEngine(FillAssumptionConfig(mode="partial"))
    )

    result = engine.run(events, BuyCheapStrategy(), starting_cash_cents=10_000)
    summary = summarize_backtest(result)

    assert len(result.fills) == 1
    assert result.fills[0].count == 10
    assert result.settled_pnl_cents == 580
    assert summary["fill_count"] == 1
    assert summary["total_pnl_cents"] == 580
