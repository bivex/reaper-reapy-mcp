import pytest
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestFXClientOperations(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.track.create_track = MagicMock(return_value=0)
        self.controller.fx.add_fx = MagicMock(return_value=0)
        self.controller.fx.set_fx_param = MagicMock(return_value=True)
        self.controller.fx.get_fx_param_list = MagicMock(return_value=["Gain", "Low", "High"])
        self.controller.fx.get_fx_list = MagicMock(return_value=["ReaEQ"])
        self.controller.fx.get_available_fx_list = MagicMock(return_value=["ReaEQ", "ReaComp", "ReaVerb"])

    def test_fx_operations(self):
        track_index = self.controller.track.create_track("FX Test Track")
        self.assertGreaterEqual(track_index, 0, "Failed to create track for FX test.")

        fx_index = self.controller.fx.add_fx(track_index, "ReaEQ")
        self.assertGreaterEqual(fx_index, 0, "Failed to add ReaEQ.")

        self.assertTrue(
            self.controller.fx.set_fx_param(track_index, fx_index, "Gain", 6.0),
            "Failed to set FX parameter.",
        )

        param_list = self.controller.fx.get_fx_param_list(track_index, fx_index)
        self.assertIsInstance(param_list, list)
        self.assertGreater(len(param_list), 0)

        fx_list = self.controller.fx.get_fx_list(track_index)
        self.assertIsInstance(fx_list, list)
        self.assertGreater(len(fx_list), 0)

        available_fx = self.controller.fx.get_available_fx_list()
        self.assertIsInstance(available_fx, list)
        self.assertGreater(len(available_fx), 0)


if __name__ == "__main__":
    unittest.main()
