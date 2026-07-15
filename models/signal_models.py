from __future__ import annotations

from dataclasses import dataclass
from typing import Any


ALLOWED_ACTIONS = {
    "LONG",
    "SHORT",
    "LONG_ADD",
    "SHORT_ADD",
    "CLOSE_ALL",
}


@dataclass(frozen=True)
class NormalizedSignal:
    source: str
    action: str
    symbol: str
    timeframe: str
    price: float
    timestamp: str

    order_id: str | None = None
    order_comment: str | None = None

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
    ) -> "NormalizedSignal":
        required_fields = {
            "source",
            "action",
            "symbol",
            "timeframe",
            "price",
            "timestamp",
        }

        missing_fields = [
            field
            for field in required_fields
            if field not in data
        ]

        if missing_fields:
            raise ValueError(
                "Missing signal fields: "
                + ", ".join(sorted(missing_fields))
            )

        action = str(data["action"]).strip().upper()

        if action not in ALLOWED_ACTIONS:
            raise ValueError(
                f"Unsupported signal action: {action}"
            )

        try:
            price = float(data["price"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"Invalid signal price: {data['price']!r}"
            ) from exc

        if price <= 0:
            raise ValueError(
                "Signal price must be greater than zero."
            )

        return cls(
            source=str(data["source"]).strip(),
            action=action,
            symbol=str(data["symbol"]).strip(),
            timeframe=str(data["timeframe"]).strip(),
            price=price,
            timestamp=str(data["timestamp"]).strip(),
            order_id=(
                str(data["order_id"]).strip()
                if data.get("order_id") is not None
                else None
            ),
            order_comment=(
                str(data["order_comment"]).strip()
                if data.get("order_comment") is not None
                else None
            ),
        )