import asyncio
import csv
import json
from pathlib import Path

from tools.signal_replay import run_replay


def test_signal_replay_long_and_close(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "signals.csv"
    output_file = tmp_path / "report.json"

    rows = [
        {
            "id": "1",
            "received_at": "2026-07-16T15:00:01Z",
            "source": "Greedy Futures Strategy",
            "action": "LONG",
            "symbol": "MNQ1!",
            "price": "30000",
            "timeframe": "15",
            "exchange": "CME_MINI",
            "alert_timestamp": "2026-07-16T15:00:00Z",
            "raw_payload": "",
        },
        {
            "id": "2",
            "received_at": "2026-07-16T15:15:01Z",
            "source": "Greedy Futures Strategy",
            "action": "CLOSE_ALL",
            "symbol": "MNQ1!",
            "price": "30020",
            "timeframe": "15",
            "exchange": "CME_MINI",
            "alert_timestamp": "2026-07-16T15:15:00Z",
            "raw_payload": "",
        },
    ]

    with input_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)

    report = asyncio.run(
        run_replay(
            input_file=input_file,
            output_file=output_file,
            daily_pnl=0.0,
        )
    )

    summary = report["summary"]

    assert summary["total_csv_rows"] == 2
    assert summary["parsed_signals"] == 2
    assert summary["skipped_rows"] == 0
    assert summary["filled_signals"] == 2
    assert summary["rejected_signals"] == 0
    assert summary["mock_orders"] == 2
    assert summary["open_positions"] == 0

    assert output_file.exists()

    saved_report = json.loads(
        output_file.read_text(
            encoding="utf-8",
        )
    )

    assert (
        saved_report["summary"]["filled_signals"]
        == 2
    )


def test_signal_replay_rejects_one_minute(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "signals.csv"
    output_file = tmp_path / "report.json"

    rows = [
        {
            "source": "Greedy Futures Strategy",
            "action": "LONG",
            "symbol": "MNQ1!",
            "price": "30000",
            "timeframe": "1",
            "alert_timestamp": "2026-07-16T15:00:00Z",
            "raw_payload": "",
        }
    ]

    with input_file.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(rows[0].keys()),
        )

        writer.writeheader()
        writer.writerows(rows)

    report = asyncio.run(
        run_replay(
            input_file=input_file,
            output_file=output_file,
            daily_pnl=0.0,
        )
    )

    summary = report["summary"]

    assert summary["parsed_signals"] == 1
    assert summary["filled_signals"] == 0
    assert summary["rejected_signals"] == 1

    assert (
        summary["rejection_codes"][
            "TIMEFRAME_NOT_ALLOWED"
        ]
        == 1
    )