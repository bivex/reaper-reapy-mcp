import sys
import os
import logging
import unittest

# Add the repository root to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the ReaperController
from src.reaper_controller import ReaperController


class TestFXOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
        cls.controller = ReaperController(debug=True)

        if not cls.controller.verify_connection():
            raise Exception("Failed to connect to Reaper")

    def test_fx_addition(self):
        self.logger.info("Testing FX addition...")
        # Create a track for the FX
        track_index = self.controller.create_track("FX Test Track")
        self.assertGreaterEqual(track_index, 0, "Failed to create track for FX test")
        
        fx_index = self.controller.add_fx(track_index, "ReaEQ")
        self.assertGreaterEqual(fx_index, 0, "FX addition failed")
        self.logger.info(f"✓ FX added with index {fx_index}")


if __name__ == "__main__":
    unittest.main()
