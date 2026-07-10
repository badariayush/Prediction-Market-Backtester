from io import BytesIO
from zipfile import ZipFile

from fastapi.testclient import TestClient

from kalshi_backtester_api.main import create_app


def _payloads() -> list[dict[str, object]]:
    return [
        {
            "type": "orderbook",
            "ticker": "KXTEST-26",
            "ts": "2026-01-01T00:00:00+00:00",
            "yes_bids": [[40, 20]],
            "yes_asks": [[42, 20]],
        },
        {
            "type": "price",
            "ticker": "KXTEST-26",
            "ts": "2026-01-01T00:00:00+00:00",
            "last_price": 41,
        },
        {
            "type": "settlement",
            "ticker": "KXTEST-26",
            "ts": "2026-01-02T00:00:00+00:00",
            "result": "yes",
        },
    ]


def test_health_endpoint() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_dataset_normalization_endpoint_returns_replay_events() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/datasets/normalize",
        json={
            "payloads": [
                {
                    "type": "orderbook",
                    "ticker": "KXTEST-26",
                    "ts": "2026-01-01T00:00:00+00:00",
                    "yes_bids": [[40, 20]],
                    "yes_asks": [[42, 30]],
                },
                {
                    "type": "price",
                    "ticker": "KXTEST-26",
                    "ts": "2026-01-01T00:00:00+00:00",
                    "last_price": 41,
                },
            ]
        },
    )

    assert response.status_code == 200
    assert response.json()["event_count"] == 2
    assert response.json()["event_types"] == ["orderbook_updated", "price_updated"]


def test_dataset_create_list_and_get_round_trip(tmp_path) -> None:
    client = TestClient(create_app(storage_root=tmp_path))

    create_response = client.post(
        "/datasets",
        json={"dataset_id": "demo-dataset", "payloads": _payloads(), "source": "test"},
    )
    list_response = client.get("/datasets")
    get_response = client.get("/datasets/demo-dataset/events")

    assert create_response.status_code == 200
    assert create_response.json()["dataset_id"] == "demo-dataset"
    assert create_response.json()["event_count"] == 3
    assert list_response.json()["datasets"] == ["demo-dataset"]
    assert get_response.json()["event_count"] == 3
    assert get_response.json()["events"][0]["event_type"] == "orderbook_updated"


def test_demo_backtest_endpoint_runs_replay_engine() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/backtests/run-demo",
        json={"payloads": _payloads(), "starting_cash_cents": 10000},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["fill_count"] == 1
    assert body["metrics"]["total_pnl_cents"] == 580
    assert body["fills"][0]["count"] == 10


def test_strategy_project_zip_upload_returns_migration_report(tmp_path) -> None:
    client = TestClient(create_app(storage_root=tmp_path))
    archive = BytesIO()
    with ZipFile(archive, "w") as zip_file:
        zip_file.writestr(
            "strategy.py",
            "from kalshi_python import KalshiClient\n"
            "def run(client):\n"
            "    return client.get_price('KXTEST-26')\n",
        )
    archive.seek(0)

    response = client.post(
        "/strategies/migrate",
        files={"file": ("strategy.zip", archive.getvalue(), "application/zip")},
    )

    assert response.status_code == 200
    body = response.json()
    assert "strategy.py" in body["original_sources"]
    assert "kalshi_strategy_sdk" in body["migrated_sources"]["strategy.py"]
    assert body["supported_calls"][0]["api_call"] == "get_price"
