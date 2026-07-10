from __future__ import annotations

from kalshi_backtest_core.replay import BacktestResult


def summarize_backtest(result: BacktestResult) -> dict[str, int | float]:
    peak = result.starting_cash_cents
    max_drawdown = 0
    for point in result.equity_curve:
        peak = max(peak, point.equity_cents)
        max_drawdown = max(max_drawdown, peak - point.equity_cents)
    partial_or_warning_count = len(result.fidelity_warnings)
    return {
        "starting_cash_cents": result.starting_cash_cents,
        "ending_cash_cents": result.ending_cash_cents,
        "total_pnl_cents": result.total_pnl_cents,
        "return_pct": round((result.total_pnl_cents / result.starting_cash_cents) * 100, 10),
        "fill_count": len(result.fills),
        "max_drawdown_cents": max_drawdown,
        "replay_fidelity_warning_count": partial_or_warning_count,
    }
