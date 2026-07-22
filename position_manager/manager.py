from position_manager.state import PositionState


class PositionManager:
    """
    GTAP Position Manager.

    Responsible for maintaining
    internal position state.
    """

    def __init__(self):
        self._state: PositionState | None = None

    @property
    def state(self):
        return self._state