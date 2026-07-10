from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from kalshi_strategy_sdk.context import MarketState, OrderBook


@dataclass(frozen=True)
class KalshiReplayClient:
    now: datetime
    markets: dict[str, MarketState] = field(default_factory=dict)
    orderbooks: dict[str, OrderBook] = field(default_factory=dict)
    trades: dict[str, list[object]] = field(default_factory=dict)

    def get_market(self, ticker: str) -> MarketState | None:
        return self.markets.get(ticker)

    def get_markets(self) -> list[MarketState]:
        return list(self.markets.values())

    def get_orderbook(self, ticker: str) -> OrderBook:
        return self.orderbooks[ticker]

    def get_price(self, ticker: str) -> int | None:
        market = self.get_market(ticker)
        return None if market is None else market.last_price

    def get_trades(self, ticker: str) -> list[object]:
        return self.trades.get(ticker, [])

    def minutes_to_close(self, ticker: str) -> float | None:
        market = self.get_market(ticker)
        if market is None or market.close_time is None:
            return None
        return (market.close_time - self.now).total_seconds() / 60

    def minutes_to_resolution(self, ticker: str) -> float | None:
        market = self.get_market(ticker)
        if market is None or market.resolution_time is None:
            return None
        return (market.resolution_time - self.now).total_seconds() / 60
