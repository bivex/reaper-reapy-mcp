import logging
import os
import sys
import unittest

# Add the parent directory to sys.path to import the reaper_controller module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestFXClientOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        cls.logger = logging.getLogger(__name__)
        cls.controller = ReaperController(debug=True)
        if not cls.controller.verify_connection():
            raise Exception("Failed to connect to Reaper for testing.")

    def test_fx_operations(self):
        self.logger.info("Testing FX operations...")
        track_index = self.controller.create_track("FX Test Track")
        self.assertGreaterEqual(track_index, 0, "Failed to create track for FX test.")

        fx_name = "ReaEQ"
        fx_index = self.controller.add_fx(track_index, fx_name)
        self.assertGreaterEqual(fx_index, 0, f"Failed to add {fx_name}.")
        self.logger.info(f"Added {fx_name} to track {track_index} at index {fx_index}")

        self.assertTrue(
            self.controller.set_fx_param(track_index, fx_index, "Gain", 6.0),
            "Failed to set FX parameter.",
        )
        self.logger.info(f"Set ReaEQ gain to 6.0")

        param_list = self.controller.get_fx_param_list(track_index, fx_index)
        self.assertIsInstance(param_list, list, "FX parameter list is not a list.")
        self.assertGreater(len(param_list), 0, "FX parameter list is empty.")
        self.logger.info(f"Got FX parameter list with {len(param_list)} parameters")

        fx_list = self.controller.get_fx_list(track_index)
        self.assertIsInstance(fx_list, list, "FX list is not a list.")
        self.assertGreater(len(fx_list), 0, "FX list is empty.")
        self.logger.info(f"Track {track_index} has {len(fx_list)} FX plugins")

        available_fx = self.controller.get_available_fx_list()
        self.assertIsInstance(available_fx, list, "Available FX list is not a list.")
        self.assertGreater(len(available_fx), 0, "Available FX list is empty.")
        self.logger.info(f"Found {len(available_fx)} available FX plugins in Reaper")


if __name__ == "__main__":
    unittest.main()
