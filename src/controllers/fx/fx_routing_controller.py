import logging

from src.core.reapy_bridge import get_reapy


class FXRoutingController:
    def __init__(self, rpr, logger: logging.Logger | None = None):
        self._RPR = rpr
        self.logger = logger or logging.getLogger(__name__)

    # Placeholder for future pin/routing helpers
    def noop(self) -> bool:
        return True
