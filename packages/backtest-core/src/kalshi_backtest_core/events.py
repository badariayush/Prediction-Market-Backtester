from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal

MarketStatus = Literal["open", "paused", "closed", "determined", "settled"]
SettlementResult = Literal["yes", "no"]


def _ensure_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@dataclass(frozen=True)
class BookLevel:
    price: int
    count: int


@dataclass(frozen=True)
class MarketMetadataEvent:
    timestamp: datetime
    sequence: int
    market_ticker: str
    title: str
    close_time: datetime | None = None
    resolution_time: datetime | None = None
    source: str = "kalshi"
    schema_version: int = 1

    @property
    def event_type(self) -> str:
        return "market_metadata"

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _ensure_aware_utc(self.timestamp))
        if self.close_time is not None:
            object.__setattr__(self, "close_time", _ensure_aware_utc(self.close_time))
        if self.resolution_time is not None:
            object.__setattr__(self, "resolution_time", _ensure_aware_utc(self.resolution_time))


@dataclass(frozen=True)
class OrderBookUpdated:
    timestamp: datetime
    sequence: int
    market_ticker: str
    yes_bids: list[BookLevel]
    yes_asks: list[BookLevel]
    source: str = "kalshi"
    schema_version: int = 1

    @property
    def event_type(self) -> str:
        return "orderbook_updated"

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _ensure_aware_utc(self.timestamp))


@dataclass(frozen=True)
class PriceUpdated:
    timestamp: datetime
    sequence: int
    market_ticker: str
    last_price: int
    mark_price: int | None = None
    source: str = "kalshi"
    schema_version: int = 1

    @property
    def event_type(self) -> str:
        return "price_updated"

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _ensure_aware_utc(self.timestamp))


@dataclass(frozen=True)
class TradePrinted:
    timestamp: datetime
    sequence: int
    market_ticker: str
    price: int
    count: int
    taker_side: Literal["yes", "no"] | None = None
    source: str = "kalshi"
    schema_version: int = 1

    @property
    def event_type(self) -> str:
        return "trade_printed"

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _ensure_aware_utc(self.timestamp))


@dataclass(frozen=True)
class MarketStatusChanged:
    timestamp: datetime
    sequence: int
    market_ticker: str
    status: MarketStatus
    source: str = "kalshi"
    schema_version: int = 1

    @property
    def event_type(self) -> str:
        return "market_status_changed"

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _ensure_aware_utc(self.timestamp))


@dataclass(frozen=True)
class SettlementPublished:
    timestamp: datetime
    sequence: int
    market_ticker: str
    result: SettlementResult
    yes_payout_cents: int | None = None
    no_payout_cents: int | None = None
    source: str = "kalshi"
    schema_version: int = 1

    @property
    def event_type(self) -> str:
        return "settlement_published"

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _ensure_aware_utc(self.timestamp))
        if self.yes_payout_cents is None:
            object.__setattr__(self, "yes_payout_cents", 100 if self.result == "yes" else 0)
        if self.no_payout_cents is None:
            object.__setattr__(self, "no_payout_cents", 100 if self.result == "no" else 0)


ReplayEvent = (
    MarketMetadataEvent
    | OrderBookUpdated
    | PriceUpdated
    | TradePrinted
    | MarketStatusChanged
    | SettlementPublished
)


def event_sort_key(event: ReplayEvent) -> tuple[datetime, int, str, str]:
    return (event.timestamp, event.sequence, event.market_ticker, event.event_type)
