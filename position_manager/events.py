from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class PositionEvent:
    timestamp: datetime


@dataclass(frozen=True)
class PositionOpened(PositionEvent):
    symbol: str
    side: str
    quantity: int
    price: float


@dataclass(frozen=True)
class PositionAdded(PositionEvent):
    quantity: int
    price: float


@dataclass(frozen=True)
class PositionReduced(PositionEvent):
    quantity: int
    price: float


@dataclass(frozen=True)
class PositionClosed(PositionEvent):
    price: float