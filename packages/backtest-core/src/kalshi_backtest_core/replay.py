from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from kalshi_backtest_core.events import (
    MarketMetadataEvent,
    MarketStatusChanged,
    OrderBookUpdated,
    PriceUpdated,
    ReplayEvent,
    SettlementPublished,
    event_sort_key,
)
from kalshi_backtest_core.liquidity import FillResult, LiquidityAwareFillEngine, SimulatedFill
from kalshi_backtest_core.portfolio import EquityPoint, PortfolioEngine
from kalshi_backtest_core.resolution import ResolutionEngine
from kalshi_strategy_sdk import (
    KalshiReplayClient,
    LimitOrder,
    MarketState,
    OrderBook,
    OrderBookLevel,
)


class ReplayStrategy(Protocol):
    def on_event(self, client: KalshiReplayClient) -> list[LimitOrder]: ...


@dataclass(frozen=True)
class BacktestResult:
    starting_cash_cents: int
    ending_cash_cents: int
    fills: list[SimulatedFill]
    equity_curve: list[EquityPoint]
    settled_pnl_cents: int
    fidelity_warnings: list[str] = field(default_factory=list)

    @property
    def total_pnl_cents(self) -> int:
        return self.ending_cash_cents - self.starting_cash_cents


class ReplayEngine:
    def __init__(self, fill_engine: LiquidityAwareFillEngine) -> None:
        self.fill_engine = fill_engine
        self.resolution_engine = ResolutionEngine()

    def run(
        self,
        events: list[ReplayEvent],
        strategy: ReplayStrategy,
        starting_cash_cents: int,
    ) -> BacktestResult:
        markets: dict[str, MarketState] = {}
        orderbooks: dict[str, OrderBook] = {}
        raw_books: dict[str, OrderBookUpdated] = {}
        statuses: dict[str, str] = {}
        prices: dict[str, int] = {}
        portfolio = PortfolioEngine(starting_cash_cents)
        fills: list[SimulatedFill] = []
        equity_curve: list[EquityPoint] = []
        warnings: list[str] = []

        for event in sorted(events, key=event_sort_key):
            if isinstance(event, MarketMetadataEvent):
                existing = markets.get(event.market_ticker, MarketState(ticker=event.market_ticker))
                markets[event.market_ticker] = MarketState(
                    ticker=event.market_ticker,
                    title=event.title,
                    last_price=existing.last_price,
                    status=existing.status,
                    close_time=event.close_time,
                    resolution_time=event.resolution_time,
                )
            elif isinstance(event, OrderBookUpdated):
                raw_books[event.market_ticker] = event
                orderbooks[event.market_ticker] = OrderBook(
                    yes_bids=[OrderBookLevel(level.price, level.count) for level in event.yes_bids],
                    yes_asks=[OrderBookLevel(level.price, level.count) for level in event.yes_asks],
                )
            elif isinstance(event, PriceUpdated):
                prices[event.market_ticker] = event.last_price
                old = markets.get(event.market_ticker, MarketState(ticker=event.market_ticker))
                markets[event.market_ticker] = MarketState(
                    ticker=event.market_ticker,
                    title=old.title,
                    last_price=event.last_price,
                    status=statuses.get(event.market_ticker, old.status),
                    close_time=old.close_time,
                    resolution_time=old.resolution_time,
                )
            elif isinstance(event, MarketStatusChanged):
                statuses[event.market_ticker] = event.status
                old = markets.get(event.market_ticker, MarketState(ticker=event.market_ticker))
                markets[event.market_ticker] = MarketState(
                    ticker=event.market_ticker,
                    title=old.title,
                    last_price=old.last_price,
                    status=event.status,
                    close_time=old.close_time,
                    resolution_time=old.resolution_time,
                )
            elif isinstance(event, SettlementPublished):
                self.resolution_engine.apply_settlement(portfolio, event)
                statuses[event.market_ticker] = "settled"

            client = KalshiReplayClient(event.timestamp, dict(markets), dict(orderbooks))
            for order in strategy.on_event(client):
                result: FillResult = self.fill_engine.try_fill(
                    order,
                    raw_books.get(order.market_ticker),
                    statuses.get(order.market_ticker, "open"),
                )
                warnings.extend(result.fidelity_warnings)
                for fill in result.fills:
                    fills.append(fill)
                    portfolio.apply_fill(fill)

            equity_curve.append(portfolio.mark_to_market(prices, event.timestamp))

        return BacktestResult(
            starting_cash_cents=starting_cash_cents,
            ending_cash_cents=portfolio.cash_cents,
            fills=fills,
            equity_curve=equity_curve,
            settled_pnl_cents=portfolio.settled_pnl_cents,
            fidelity_warnings=warnings,
        )
