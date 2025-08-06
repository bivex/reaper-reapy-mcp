import logging
from typing import List


class FXPresetsController:
    def __init__(self, rpr, logger: logging.Logger | None = None):
        self._RPR = rpr
        self.logger = logger or logging.getLogger(__name__)

    def get_available_fx_list(self) -> List[str]:
        from .fx_controller import FXController  # avoid circular on import time
        ctl = FXController()
        return ctl.get_available_fx_list()
