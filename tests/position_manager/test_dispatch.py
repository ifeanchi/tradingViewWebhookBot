from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from position_manager import PositionManager
from position_manager.events import PositionEvent


@dataclass(frozen=True)
class UnsupportedPositionEvent(PositionEvent):
    reason: str


def test_apply_rejects_unregistered_event_type():
    manager = PositionManager()

    event = UnsupportedPositionEvent(
        timestamp=datetime.now(timezone.utc),
        reason="test event",
    )

    with pytest.raises(
        TypeError,
        match="Unsupported position event: UnsupportedPositionEvent",
    ):
        manager.apply(event)