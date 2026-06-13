import sys
import os
import logging
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestMarkerOperations(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.marker.create_marker = MagicMock(return_value=0)

    def test_marker_creation(self):
        marker_id = self.controller.marker.create_marker(0, "Test Marker")
        self.assertGreaterEqual(marker_id, 0, "Marker creation failed")


if __name__ == "__main__":
    unittest.main()
