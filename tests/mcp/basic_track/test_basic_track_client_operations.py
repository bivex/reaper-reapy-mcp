import logging
import os
import sys
import unittest

# Add the parent directory to sys.path to import the reaper_controller module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestBasicTrackClientOperations(unittest.TestCase):

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

    def test_basic_track_operations(self):
        self.logger.info("Testing basic track operations...")
        track_index = self.controller.create_track("Test Track")
        self.assertGreaterEqual(track_index, 0, "Failed to create track.")
        self.logger.info(f"Created track {track_index}")
        
        self.assertTrue(self.controller.set_track_color(track_index, "#FF0000"), "Failed to set track color.")
        self.logger.info(f"Set track {track_index} color to red")


if __name__ == "__main__":
    unittest.main()
