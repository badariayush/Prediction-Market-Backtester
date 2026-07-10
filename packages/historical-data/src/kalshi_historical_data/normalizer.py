from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

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


def _parse_dt(value: str | datetime | None) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return datetime(1970, 1, 1, tzinfo=UTC)


class KalshiDataAdapter:
    def __init__(self, source: str = "kalshi") -> None:
        self.source = source

    def normalize(
        self, payloads: list[dict[str, Any]], now: datetime | None = None
    ) -> list[ReplayEvent]:
        events: list[ReplayEvent] = []
        sequence = 1
        current_time = now or datetime.now(UTC)
        for payload in payloads:
            kind = payload["type"]
            ticker = payload["ticker"]
            timestamp = _parse_dt(payload.get("ts") or payload.get("timestamp"))
            if kind == "market":
                close_time = (
                    _parse_dt(payload.get("close_time")) if payload.get("close_time") else None
                )
                events.append(
                    MarketMetadataEvent(
                        timestamp=timestamp,
                        sequence=sequence,
                        market_ticker=ticker,
                        title=payload.get("title", ticker),
                        close_time=close_time,
                        source=self.source,
                    )
                )
                sequence += 1
                if now is not None and close_time is not None and close_time <= current_time:
                    events.append(
                        MarketStatusChanged(
                            close_time, sequence, ticker, "closed", source=self.source
                        )
                    )
                    sequence += 1
                continue
            if kind == "orderbook":
                events.append(
                    OrderBookUpdated(
                        timestamp=timestamp,
                        sequence=sequence,
                        market_ticker=ticker,
                        yes_bids=[
                            BookLevel(price=int(price), count=int(count))
                            for price, count in payload.get("yes_bids", [])
                        ],
                        yes_asks=[
                            BookLevel(price=int(price), count=int(count))
                            for price, count in payload.get("yes_asks", [])
                        ],
                        source=self.source,
                    )
                )
            elif kind == "price":
                events.append(
                    PriceUpdated(
                        timestamp, sequence, ticker, int(payload["last_price"]), source=self.source
                    )
                )
            elif kind == "trade":
                events.append(
                    TradePrinted(
                        timestamp,
                        sequence,
                        ticker,
                        int(payload["price"]),
                        int(payload["count"]),
                        source=self.source,
                    )
                )
            elif kind == "status":
                events.append(
                    MarketStatusChanged(
                        timestamp, sequence, ticker, payload["status"], source=self.source
                    )
                )
            elif kind == "settlement":
                events.append(
                    SettlementPublished(
                        timestamp, sequence, ticker, payload["result"], source=self.source
                    )
                )
            else:
                raise ValueError(f"unsupported payload type: {kind}")
            sequence += 1
        return events
