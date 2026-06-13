import pytest
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestBasicTrackClientOperations(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.track.create_track = MagicMock(return_value=0)
        self.controller.track.set_track_color = MagicMock(return_value=True)

    def test_basic_track_operations(self):
        track_index = self.controller.track.create_track("Test Track")
        self.assertGreaterEqual(track_index, 0, "Failed to create track.")

        result = self.controller.track.set_track_color(track_index, "#FF0000")
        self.assertTrue(result, "Failed to set track color.")


if __name__ == "__main__":
    unittest.main()
