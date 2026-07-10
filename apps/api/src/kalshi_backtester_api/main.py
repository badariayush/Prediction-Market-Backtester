from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from kalshi_backtest_core.liquidity import FillAssumptionConfig, LiquidityAwareFillEngine
from kalshi_backtest_core.metrics import summarize_backtest
from kalshi_backtest_core.replay import ReplayEngine
from kalshi_backtester_api.services.dataset_service import DatasetService
from kalshi_backtester_api.services.migration_service import MigrationService
from kalshi_backtester_api.services.upload_service import StrategyArchiveExtractor
from kalshi_historical_data.normalizer import KalshiDataAdapter
from kalshi_strategy_sdk import KalshiReplayClient, LimitOrder


class NormalizeRequest(BaseModel):
    payloads: list[dict[str, Any]]


class CreateDatasetRequest(BaseModel):
    dataset_id: str = Field(min_length=1)
    payloads: list[dict[str, Any]]
    source: str = "api-request"


class DemoBacktestRequest(BaseModel):
    payloads: list[dict[str, Any]]
    starting_cash_cents: int = Field(default=10_000, gt=0)


class DemoStrategy:
    def on_event(self, client: KalshiReplayClient) -> list[LimitOrder]:
        price = client.get_price("KXTEST-26")
        if price is not None and price < 45:
            return [
                LimitOrder(
                    market_ticker="KXTEST-26",
                    side="yes",
                    action="buy",
                    count=10,
                    price=42,
                )
            ]
        return []


def _event_type_names(payloads: list[dict[str, Any]]) -> list[str]:
    events = KalshiDataAdapter(source="api-request").normalize(payloads)
    return [event.event_type for event in events]


def create_app(storage_root: Path | None = None) -> FastAPI:
    app = FastAPI(title="Kalshi Strategy Backtester")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    resolved_storage_root = storage_root or Path(".data")
    dataset_service = DatasetService(resolved_storage_root)
    archive_extractor = StrategyArchiveExtractor(resolved_storage_root)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/datasets/normalize")
    def normalize_dataset(request: NormalizeRequest) -> dict[str, object]:
        event_types = _event_type_names(request.payloads)
        return {"event_count": len(event_types), "event_types": event_types}

    @app.post("/datasets")
    def create_dataset(request: CreateDatasetRequest) -> dict[str, object]:
        manifest = dataset_service.create_dataset(
            dataset_id=request.dataset_id,
            payloads=request.payloads,
            source=request.source,
        )
        return asdict(manifest)

    @app.get("/datasets")
    def list_datasets() -> dict[str, list[str]]:
        return {"datasets": dataset_service.list_dataset_ids()}

    @app.get("/datasets/{dataset_id}/events")
    def get_dataset_events(dataset_id: str) -> dict[str, object]:
        events = dataset_service.get_event_dicts(dataset_id)
        return {"event_count": len(events), "events": events}

    @app.post("/strategies/migrate")
    async def migrate_strategy_project(file: UploadFile) -> dict[str, object]:
        suffix = Path(file.filename or "strategy.zip").suffix or ".zip"
        with NamedTemporaryFile(suffix=suffix, delete=False) as handle:
            archive_path = Path(handle.name)
            handle.write(await file.read())
        project_root = archive_extractor.extract_zip(archive_path, project_id=uuid4().hex)
        return MigrationService().migrate_project(project_root).to_dict()

    @app.post("/backtests/run-demo")
    def run_demo_backtest(request: DemoBacktestRequest) -> dict[str, object]:
        events = KalshiDataAdapter(source="api-request").normalize(request.payloads)
        engine = ReplayEngine(
            fill_engine=LiquidityAwareFillEngine(FillAssumptionConfig(mode="partial"))
        )
        result = engine.run(events, DemoStrategy(), request.starting_cash_cents)
        fills = [asdict(fill) for fill in result.fills]
        return {
            "metrics": summarize_backtest(result),
            "fills": fills,
            "fidelity_warnings": result.fidelity_warnings,
        }

    return app


app = create_app()
