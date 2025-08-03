#!/usr/bin/env python
# Test script to verify the controller structure works correctly

import sys
import os
import logging
import unittest

# Add the repository root to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the ReaperController
from src.reaper_controller import ReaperController


class TestTrackOperations(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
        cls.controller = ReaperController(debug=True)

        if not cls.controller.verify_connection():
            raise Exception("Failed to connect to Reaper")

    def test_track_creation(self):
        self.logger.info("Testing track creation...")
        track_index = self.controller.create_track("Test Track")
        self.assertGreaterEqual(track_index, 0, "Track creation failed")
        self.logger.info(f"✓ Track created with index {track_index}")


if __name__ == "__main__":
    unittest.main()
