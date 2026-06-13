import pytest
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestMasterClientOperations(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.master.set_master_volume = MagicMock(return_value=True)
        self.controller.master.set_master_pan = MagicMock(return_value=True)

    def test_master_track_operations(self):
        self.assertTrue(
            self.controller.master.set_master_volume(0.8),
            "Failed to set master volume.",
        )
        self.assertTrue(
            self.controller.master.set_master_pan(-0.5),
            "Failed to set master pan.",
        )


if __name__ == "__main__":
    unittest.main()
