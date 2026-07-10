from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class LimitOrder:
    market_ticker: str
    side: Literal["yes", "no"]
    action: Literal["buy", "sell"]
    count: int
    price: int
