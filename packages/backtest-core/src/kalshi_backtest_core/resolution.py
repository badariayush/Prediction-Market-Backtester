from __future__ import annotations

from kalshi_backtest_core.events import SettlementPublished
from kalshi_backtest_core.portfolio import PortfolioEngine


class ResolutionEngine:
    def apply_settlement(self, portfolio: PortfolioEngine, event: SettlementPublished) -> None:
        count = portfolio.positions.pop(event.market_ticker, 0)
        if count == 0:
            return
        payout = event.yes_payout_cents or 0
        portfolio.cash_cents += count * payout
        portfolio.settled_pnl_cents = portfolio.cash_cents - portfolio.starting_cash_cents
