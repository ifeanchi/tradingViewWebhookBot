from __future__ import annotations

import argparse
import asyncio
import csv
import json
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Allow this script to import modules from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from broker.mock import MockBroker
from config import settings
from models.signal_models import NormalizedSignal
from risk_engine import RiskEngine
from services.execution_service import ExecutionService


DEFAULT_INPUT_FILE = PROJECT_ROOT / "trade_signals.csv"
DEFAULT_OUTPUT_FILE = PROJECT_ROOT / "exports" / "signal_replay_report.json"


@dataclass
class ReplayEvent:
    row_number: int
    source: str
    action: str
    symbol: str
    timeframe: str
    price: float
    timestamp: str
    order_id: str | None
    order_comment: str | None
    status: str
    risk_code: str
    message: str
    fill_side: str | None
    fill_quantity: int | None
    fill_price: float | None


@dataclass
class ReplaySummary:
    input_file: str
    total_csv_rows: int
    parsed_signals: int
    skipped_rows: int
    filled_signals: int
    rejected_signals: int
    ignored_signals: int
    mock_orders: int
    open_positions: int
    rejection_codes: dict[str, int]
    action_counts: dict[str, int]


def clean_text(value: Any) -> str:
    if value is None:
        return ""

    return str(value).strip()


def parse_float(value: Any, field_name: str) -> float:
    text = clean_text(value)

    if not text:
        raise ValueError(f"{field_name} is empty.")

    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be numeric. Received: {value!r}"
        ) from exc


def parse_raw_payload(row: dict[str, Any]) -> dict[str, Any]:
    """
    Extracts the normalized payload stored in raw_payload.

    Expected structure:

    {
        "original_strategy_payload": {...},
        "normalized_bot_payload": {...}
    }
    """
    raw_value = row.get("raw_payload")

    if raw_value is None:
        return {}

    raw_text = clean_text(raw_value)

    if not raw_text:
        return {}

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        return {}

    if not isinstance(parsed, dict):
        return {}

    normalized = parsed.get("normalized_bot_payload")

    if isinstance(normalized, dict):
        return normalized

    return parsed


def get_first_value(
    *sources: dict[str, Any],
    field_names: tuple[str, ...],
) -> Any:
    for source in sources:
        for field_name in field_names:
            value = source.get(field_name)

            if value is not None and clean_text(value):
                return value

    return None


def normalize_action(value: Any) -> str:
    action = clean_text(value).upper()

    aliases = {
        "BUY": "LONG",
        "SELL": "SHORT",
        "FLAT": "CLOSE_ALL",
        "CLOSE": "CLOSE_ALL",
        "EXIT": "CLOSE_ALL",
    }

    return aliases.get(action, action)


def row_to_signal(
    row: dict[str, Any],
) -> NormalizedSignal:
    embedded_payload = parse_raw_payload(row)

    source = get_first_value(
        embedded_payload,
        row,
        field_names=("source",),
    )

    action = get_first_value(
        embedded_payload,
        row,
        field_names=("action",),
    )

    symbol = get_first_value(
        embedded_payload,
        row,
        field_names=("symbol",),
    )

    timeframe = get_first_value(
        embedded_payload,
        row,
        field_names=("timeframe", "interval"),
    )

    price = get_first_value(
        embedded_payload,
        row,
        field_names=("price", "order_price"),
    )

    timestamp = get_first_value(
        embedded_payload,
        row,
        field_names=(
            "timestamp",
            "alert_timestamp",
            "received_at",
        ),
    )

    order_id = get_first_value(
        embedded_payload,
        row,
        field_names=("order_id",),
    )

    order_comment = get_first_value(
        embedded_payload,
        row,
        field_names=("order_comment",),
    )

    normalized_data = {
        "source": clean_text(source),
        "action": normalize_action(action),
        "symbol": clean_text(symbol),
        "timeframe": clean_text(timeframe),
        "price": parse_float(price, "price"),
        "timestamp": clean_text(timestamp),
        "order_id": (
            clean_text(order_id)
            if order_id is not None
            else None
        ),
        "order_comment": (
            clean_text(order_comment)
            if order_comment is not None
            else None
        ),
    }

    return NormalizedSignal.from_dict(normalized_data)


def load_rows(
    input_file: Path,
) -> list[dict[str, Any]]:
    if not input_file.exists():
        raise FileNotFoundError(
            f"Input file was not found: {input_file}"
        )

    with input_file.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as csv_file:
        reader = csv.DictReader(csv_file)

        if reader.fieldnames is None:
            raise ValueError(
                "The CSV file does not contain a header row."
            )

        return list(reader)


async def run_replay(
    input_file: Path,
    output_file: Path,
    daily_pnl: float,
) -> dict[str, Any]:
    rows = load_rows(input_file)

    broker = MockBroker()
    risk_engine = RiskEngine(settings)

    service = ExecutionService(
        broker=broker,
        risk_engine=risk_engine,
    )

    await service.initialize()

    replay_events: list[ReplayEvent] = []
    skipped_rows: list[dict[str, Any]] = []

    status_counts: Counter[str] = Counter()
    rejection_codes: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()

    parsed_signals = 0

    for row_number, row in enumerate(
        rows,
        start=2,
    ):
        try:
            signal = row_to_signal(row)
            parsed_signals += 1
            action_counts[signal.action] += 1

            result = await service.execute_signal(
                signal=signal,
                current_daily_pnl=daily_pnl,
                execution_enabled=True,
            )

            status_counts[result.status] += 1

            if result.status == "rejected":
                rejection_codes[result.risk_code] += 1

            replay_events.append(
                ReplayEvent(
                    row_number=row_number,
                    source=signal.source,
                    action=signal.action,
                    symbol=signal.symbol,
                    timeframe=signal.timeframe,
                    price=signal.price,
                    timestamp=signal.timestamp,
                    order_id=signal.order_id,
                    order_comment=signal.order_comment,
                    status=result.status,
                    risk_code=result.risk_code,
                    message=result.message,
                    fill_side=(
                        result.fill.side
                        if result.fill is not None
                        else None
                    ),
                    fill_quantity=(
                        result.fill.quantity
                        if result.fill is not None
                        else None
                    ),
                    fill_price=(
                        result.fill.fill_price
                        if result.fill is not None
                        else None
                    ),
                )
            )

        except Exception as exc:
            skipped_rows.append(
                {
                    "row_number": row_number,
                    "reason": str(exc),
                    "row": row,
                }
            )

    accounts = await broker.get_accounts()
    positions = await broker.get_positions()
    orders = await broker.get_orders()

    summary = ReplaySummary(
        input_file=str(input_file),
        total_csv_rows=len(rows),
        parsed_signals=parsed_signals,
        skipped_rows=len(skipped_rows),
        filled_signals=status_counts["filled"],
        rejected_signals=status_counts["rejected"],
        ignored_signals=status_counts["ignored"],
        mock_orders=len(orders),
        open_positions=len(positions),
        rejection_codes=dict(rejection_codes),
        action_counts=dict(action_counts),
    )

    report = {
        "summary": asdict(summary),
        "accounts": [
            asdict(account)
            for account in accounts
        ],
        "ending_positions": [
            asdict(position)
            for position in positions
        ],
        "events": [
            asdict(event)
            for event in replay_events
        ],
        "skipped_rows": skipped_rows,
    }

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_file.open(
        "w",
        encoding="utf-8",
    ) as output:
        json.dump(
            report,
            output,
            indent=2,
            default=str,
        )

    return report


def print_summary(
    report: dict[str, Any],
    output_file: Path,
) -> None:
    summary = report["summary"]

    print()
    print("=" * 64)
    print("GREEDY MOCK BROKER SIGNAL REPLAY")
    print("=" * 64)

    print(f"Input file:       {summary['input_file']}")
    print(f"CSV rows:         {summary['total_csv_rows']}")
    print(f"Parsed signals:   {summary['parsed_signals']}")
    print(f"Skipped rows:     {summary['skipped_rows']}")
    print()

    print(f"Filled:           {summary['filled_signals']}")
    print(f"Rejected:         {summary['rejected_signals']}")
    print(f"Ignored:          {summary['ignored_signals']}")
    print(f"Mock orders:      {summary['mock_orders']}")
    print(f"Open positions:   {summary['open_positions']}")

    print()
    print("ACTION COUNTS")
    print("-" * 64)

    action_counts = summary["action_counts"]

    if action_counts:
        for action, count in sorted(
            action_counts.items()
        ):
            print(f"{action:<20} {count}")
    else:
        print("No actions were parsed.")

    print()
    print("REJECTION CODES")
    print("-" * 64)

    rejection_codes = summary["rejection_codes"]

    if rejection_codes:
        for code, count in sorted(
            rejection_codes.items()
        ):
            print(f"{code:<25} {count}")
    else:
        print("No signals were rejected.")

    print()
    print("ENDING POSITIONS")
    print("-" * 64)

    positions = report["ending_positions"]

    if not positions:
        print("FLAT — no open mock positions.")
    else:
        for position in positions:
            print(
                f"{position['symbol']} "
                f"{position['side']} "
                f"{position['quantity']} @ "
                f"{position['average_price']}"
            )

    print()
    print(f"Report saved to: {output_file}")
    print("=" * 64)


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Replay TradingView alert rows through "
            "RiskEngine, ExecutionService, and MockBroker."
        )
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT_FILE,
        help=(
            "Path to trade_signals.csv. "
            f"Default: {DEFAULT_INPUT_FILE}"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_FILE,
        help=(
            "Path for the generated JSON report. "
            f"Default: {DEFAULT_OUTPUT_FILE}"
        ),
    )

    parser.add_argument(
        "--daily-pnl",
        type=float,
        default=0.0,
        help=(
            "Daily P&L value supplied to the risk engine. "
            "Default: 0."
        ),
    )

    return parser


def main() -> None:
    parser = build_argument_parser()
    args = parser.parse_args()

    try:
        report = asyncio.run(
            run_replay(
                input_file=args.input.resolve(),
                output_file=args.output.resolve(),
                daily_pnl=args.daily_pnl,
            )
        )

        print_summary(
            report,
            args.output.resolve(),
        )

    except Exception as exc:
        print()
        print("Signal replay failed:")
        print(str(exc))
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()