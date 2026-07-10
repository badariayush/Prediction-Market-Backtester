from pathlib import Path

from kalshi_backtester_api.services.migration_service import MigrationService


def test_migration_report_preserves_sources_and_flags_unsupported_calls(tmp_path: Path) -> None:
    strategy_file = tmp_path / "strategy.py"
    strategy_file.write_text(
        "from kalshi_python import KalshiClient\n\n"
        "def run(client):\n"
        "    price = client.get_price('KXTEST-26')\n"
        "    client.create_order(ticker='KXTEST-26', side='yes', count=1)\n"
        "    return price\n"
    )

    report = MigrationService().migrate_project(tmp_path)

    assert report.project_root == str(tmp_path)
    assert report.original_sources["strategy.py"].startswith("from kalshi_python")
    assert "kalshi_strategy_sdk" in report.migrated_sources["strategy.py"]
    assert "client.get_price('KXTEST-26')" in report.migrated_sources["strategy.py"]
    assert report.supported_calls[0].api_call == "get_price"
    assert report.unsupported_calls[0].filename == "strategy.py"
    assert report.unsupported_calls[0].line_number == 5
    assert "create_order" in report.unsupported_calls[0].explanation
    assert "diff --git" in report.diff


def test_project_scanner_ignores_generated_and_hidden_files(tmp_path: Path) -> None:
    (tmp_path / "main.py").write_text("print('ok')\n")
    (tmp_path / ".hidden.py").write_text("print('skip')\n")
    cache = tmp_path / "__pycache__"
    cache.mkdir()
    (cache / "generated.py").write_text("print('skip')\n")

    report = MigrationService().migrate_project(tmp_path)

    assert list(report.original_sources) == ["main.py"]
