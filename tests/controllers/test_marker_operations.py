import sys
import os
import logging
import unittest
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController



@pytest.mark.reaper
class TestMarkerOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
        cls.controller = ReaperController(debug=True)

        if not cls.controller.verify_connection():
            raise Exception("Failed to connect to Reaper")

    def test_marker_creation(self):
        self.logger.info("Testing marker creation...")
        marker_id = self.controller.marker.create_marker(0, "Test Marker")
        self.assertGreaterEqual(marker_id, 0, "Marker creation failed")
        self.logger.info(f"Marker created with ID {marker_id}")


if __name__ == "__main__":
    unittest.main()
