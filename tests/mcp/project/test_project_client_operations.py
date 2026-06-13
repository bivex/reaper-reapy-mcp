import pytest
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestProjectClientOperations(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.project.set_tempo = MagicMock(return_value=True)
        self.controller.marker.create_region = MagicMock(return_value=0)
        self.controller.marker.create_marker = MagicMock(return_value=0)

    def test_project_operations(self):
        self.assertTrue(
            self.controller.project.set_tempo(120.0),
            "Failed to set tempo.",
        )

        region_index = self.controller.marker.create_region(0.0, 10.0, "Test Region")
        self.assertGreaterEqual(region_index, 0, "Failed to create region.")

        marker_index = self.controller.marker.create_marker(5.0, "Test Marker")
        self.assertGreaterEqual(marker_index, 0, "Failed to create marker.")


if __name__ == "__main__":
    unittest.main()
