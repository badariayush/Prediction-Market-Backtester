from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from kalshi_backtest_core.liquidity import SimulatedFill


@dataclass(frozen=True)
class EquityPoint:
    timestamp: datetime
    equity_cents: int
    unrealized_pnl_cents: int
    exposure_cents: int


@dataclass
class PortfolioEngine:
    starting_cash_cents: int
    cash_cents: int = field(init=False)
    positions: dict[str, int] = field(default_factory=dict)
    average_entry: dict[str, int] = field(default_factory=dict)
    settled_pnl_cents: int = 0

    def __post_init__(self) -> None:
        self.cash_cents = self.starting_cash_cents

    def apply_fill(self, fill: SimulatedFill) -> None:
        signed = fill.count if fill.action == "buy" else -fill.count
        self.positions[fill.market_ticker] = self.positions.get(fill.market_ticker, 0) + signed
        self.average_entry.setdefault(fill.market_ticker, fill.price)
        self.cash_cents += -fill.notional_cents if fill.action == "buy" else fill.notional_cents
        self.cash_cents -= fill.fee_cents

    def mark_to_market(self, prices: dict[str, int], timestamp: datetime) -> EquityPoint:
        unrealized = 0
        exposure = 0
        for ticker, count in self.positions.items():
            price = prices.get(ticker, self.average_entry.get(ticker, 0))
            entry = self.average_entry.get(ticker, price)
            unrealized += count * (price - entry)
            exposure += abs(count * price)
        return EquityPoint(timestamp, self.cash_cents + unrealized, unrealized, exposure)
