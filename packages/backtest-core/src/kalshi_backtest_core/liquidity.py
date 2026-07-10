from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from kalshi_backtest_core.events import OrderBookUpdated
from kalshi_strategy_sdk import LimitOrder


@dataclass(frozen=True)
class FillAssumptionConfig:
    mode: Literal["partial", "conservative", "optimistic"] = "partial"
    slippage_cents: int = 0


@dataclass(frozen=True)
class SimulatedFill:
    market_ticker: str
    action: str
    side: str
    count: int
    price: int
    fee_cents: int = 0

    @property
    def notional_cents(self) -> int:
        return self.count * self.price


@dataclass(frozen=True)
class FillResult:
    fills: list[SimulatedFill] = field(default_factory=list)
    remainder_count: int = 0
    fidelity_warnings: list[str] = field(default_factory=list)

    @property
    def filled_count(self) -> int:
        return sum(fill.count for fill in self.fills)


class LiquidityAwareFillEngine:
    def __init__(self, config: FillAssumptionConfig) -> None:
        self.config = config

    def try_fill(
        self,
        order: LimitOrder,
        book: OrderBookUpdated | None,
        market_status: str,
    ) -> FillResult:
        if market_status != "open":
            return FillResult(
                remainder_count=order.count, fidelity_warnings=[f"market not open: {market_status}"]
            )
        if book is None or book.market_ticker != order.market_ticker:
            return FillResult(
                remainder_count=order.count, fidelity_warnings=["no visible liquidity"]
            )

        levels = book.yes_asks if order.action == "buy" else book.yes_bids
        if not levels:
            return FillResult(remainder_count=order.count, fidelity_warnings=["empty book side"])

        best = levels[0]
        crosses = order.price >= best.price if order.action == "buy" else order.price <= best.price
        if not crosses:
            return FillResult(remainder_count=order.count)

        available = best.count
        if self.config.mode == "conservative" and available < order.count:
            return FillResult(
                remainder_count=order.count,
                fidelity_warnings=["visible depth insufficient for conservative full fill"],
            )

        fill_count = (
            order.count if self.config.mode == "optimistic" else min(order.count, available)
        )
        price = (
            best.price + self.config.slippage_cents
            if order.action == "buy"
            else best.price - self.config.slippage_cents
        )
        fill = SimulatedFill(order.market_ticker, order.action, order.side, fill_count, price)
        warnings = [] if fill_count == order.count else ["partial fill due to visible depth"]
        return FillResult([fill], order.count - fill_count, warnings)
