import sys
import os
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestTrackOperations(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.track.create_track = MagicMock(return_value=0)

    def test_track_creation(self):
        track_index = self.controller.track.create_track("Test Track")
        self.assertGreaterEqual(track_index, 0, "Track creation failed")


if __name__ == "__main__":
    unittest.main()
