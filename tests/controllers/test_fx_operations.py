import sys
import os
import logging
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestFXOperations(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.track.create_track = MagicMock(return_value=0)
        self.controller.fx.add_fx = MagicMock(return_value=0)

    def test_fx_addition(self):
        track_index = self.controller.track.create_track("FX Test Track")
        self.assertGreaterEqual(track_index, 0, "Failed to create track for FX test")

        fx_index = self.controller.fx.add_fx(track_index, "ReaEQ")
        self.assertGreaterEqual(fx_index, 0, "FX addition failed")


if __name__ == "__main__":
    unittest.main()
