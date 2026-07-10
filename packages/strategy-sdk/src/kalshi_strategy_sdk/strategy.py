from __future__ import annotations

from typing import Protocol

from kalshi_strategy_sdk.client import KalshiReplayClient
from kalshi_strategy_sdk.orders import LimitOrder


class Strategy(Protocol):
    def on_event(self, client: KalshiReplayClient) -> list[LimitOrder]: ...
