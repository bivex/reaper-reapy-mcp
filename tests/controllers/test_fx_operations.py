import sys
import os
import logging
import unittest
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController



@pytest.mark.reaper
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
        track_index = self.controller.track.create_track("FX Test Track")
        self.assertGreaterEqual(track_index, 0, "Failed to create track for FX test")

        fx_index = self.controller.fx.add_fx(track_index, "ReaEQ")
        self.assertGreaterEqual(fx_index, 0, "FX addition failed")
        self.logger.info(f"FX added with index {fx_index}")


if __name__ == "__main__":
    unittest.main()
