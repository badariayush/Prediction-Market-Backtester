from __future__ import annotations

from kalshi_backtest_core.events import ReplayEvent, event_sort_key


def is_chronological(events: list[ReplayEvent]) -> bool:
    return events == sorted(events, key=event_sort_key)
