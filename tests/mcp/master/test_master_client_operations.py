import logging
import os
import sys
import unittest

# Add the parent directory to sys.path to import the reaper_controller module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestMasterClientOperations(unittest.TestCase):

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

    def test_master_track_operations(self):
        self.logger.info("Testing master track operations...")
        self.assertTrue(self.controller.set_master_volume(0.8), "Failed to set master volume.")
        self.assertTrue(self.controller.set_master_pan(-0.5), "Failed to set master pan.")
        self.logger.info("Set master volume to 0.8 and pan to -0.5")


if __name__ == "__main__":
    unittest.main()
