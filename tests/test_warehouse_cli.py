from __future__ import annotations

from amazon_sales_analysis.cli import warehouse as warehouse_cli


def test_warehouse_cli_exports_category_revenue(monkeypatch, capsys, tmp_path) -> None:
    output_path = tmp_path / "warehouse_category_revenue.csv"
    monkeypatch.setattr(warehouse_cli, "configure_logging", lambda: None)
    monkeypatch.setattr(warehouse_cli, "get_settings", lambda: object())
    monkeypatch.setattr(
        warehouse_cli, "export_category_revenue_query", lambda settings: output_path
    )
    monkeypatch.setattr(
        warehouse_cli,
        "warehouse_query_metadata",
        lambda settings: {"warehouse_table": "gold_commercial_performance"},
    )
    monkeypatch.setattr(
        warehouse_cli,
        "build_parser",
        lambda: type(
            "Parser",
            (),
            {
                "parse_args": lambda self: type(
                    "Args",
                    (),
                    {
                        "export_category_revenue": True,
                        "show_run_history": False,
                        "compare_latest_runs": False,
                    },
                )()
            },
        )(),
    )

    warehouse_cli.main()

    assert str(output_path) in capsys.readouterr().out


def test_warehouse_cli_prints_metadata(monkeypatch, capsys) -> None:
    monkeypatch.setattr(warehouse_cli, "configure_logging", lambda: None)
    monkeypatch.setattr(warehouse_cli, "get_settings", lambda: object())
    monkeypatch.setattr(
        warehouse_cli,
        "warehouse_query_metadata",
        lambda settings: {"warehouse_table": "gold_commercial_performance"},
    )
    monkeypatch.setattr(
        warehouse_cli,
        "build_parser",
        lambda: type(
            "Parser",
            (),
            {
                "parse_args": lambda self: type(
                    "Args",
                    (),
                    {
                        "export_category_revenue": False,
                        "show_run_history": False,
                        "compare_latest_runs": False,
                    },
                )()
            },
        )(),
    )

    warehouse_cli.main()

    assert "warehouse_table" in capsys.readouterr().out
