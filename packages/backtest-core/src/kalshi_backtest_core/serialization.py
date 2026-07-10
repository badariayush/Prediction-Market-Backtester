from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any, cast

from kalshi_backtest_core.events import (
    BookLevel,
    MarketMetadataEvent,
    MarketStatusChanged,
    OrderBookUpdated,
    PriceUpdated,
    ReplayEvent,
    SettlementPublished,
    TradePrinted,
)


def _encode(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {key: _encode(item) for key, item in value.items()}
    return value


def event_to_dict(event: ReplayEvent) -> dict[str, Any]:
    payload = cast(dict[str, Any], _encode(asdict(event)))
    payload["event_type"] = event.event_type
    return payload


def _parse_dt(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(value)


def event_from_dict(payload: dict[str, Any]) -> ReplayEvent:
    data = dict(payload)
    event_type = data.pop("event_type")
    for key in ("timestamp", "close_time", "resolution_time"):
        if key in data:
            data[key] = _parse_dt(data[key])
    if "yes_bids" in data:
        data["yes_bids"] = [BookLevel(**level) for level in data["yes_bids"]]
    if "yes_asks" in data:
        data["yes_asks"] = [BookLevel(**level) for level in data["yes_asks"]]
    if event_type == "market_metadata":
        return MarketMetadataEvent(**data)
    if event_type == "orderbook_updated":
        return OrderBookUpdated(**data)
    if event_type == "price_updated":
        return PriceUpdated(**data)
    if event_type == "trade_printed":
        return TradePrinted(**data)
    if event_type == "market_status_changed":
        return MarketStatusChanged(**data)
    if event_type == "settlement_published":
        return SettlementPublished(**data)
    raise ValueError(f"unsupported event type: {event_type}")
