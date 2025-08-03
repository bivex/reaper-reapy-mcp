import logging
import os
import sys
import unittest

# Add the parent directory to sys.path to import the reaper_controller module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestProjectClientOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        cls.logger = logging.getLogger(__name__)
        cls.controller = ReaperController(debug=True)
        if not cls.controller.verify_connection():
            raise Exception("Failed to connect to Reaper for testing.")

    def test_project_operations(self):
        self.logger.info("Testing project operations...")
        self.assertTrue(self.controller.set_tempo(120.0), "Failed to set tempo.")
        self.logger.info("Set tempo to 120 BPM")

        region_index = self.controller.create_region(0.0, 10.0, "Test Region")
        self.assertGreaterEqual(region_index, 0, "Failed to create region.")
        self.logger.info(f"Created region {region_index}")

        marker_index = self.controller.create_marker(5.0, "Test Marker")
        self.assertGreaterEqual(marker_index, 0, "Failed to create marker.")
        self.logger.info(f"Created marker {marker_index}")


if __name__ == "__main__":
    unittest.main()
