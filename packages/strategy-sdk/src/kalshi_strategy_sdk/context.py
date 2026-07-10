from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class OrderBookLevel:
    price: int
    count: int


@dataclass(frozen=True)
class OrderBook:
    yes_bids: list[OrderBookLevel]
    yes_asks: list[OrderBookLevel]


@dataclass(frozen=True)
class MarketState:
    ticker: str
    title: str = ""
    last_price: int | None = None
    status: str = "open"
    close_time: datetime | None = None
    resolution_time: datetime | None = None
