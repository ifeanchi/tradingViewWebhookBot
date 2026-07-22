class PositionManagerError(Exception):
    """Base class."""


class IllegalTransition(PositionManagerError):
    """Illegal state transition."""


class PositionAlreadyOpen(PositionManagerError):
    """Position already exists."""


class PositionNotOpen(PositionManagerError):
    """No active position."""


class QuantityMismatch(PositionManagerError):
    """Invalid quantity."""


class InvalidAveragePrice(PositionManagerError):
    """Average price invalid."""