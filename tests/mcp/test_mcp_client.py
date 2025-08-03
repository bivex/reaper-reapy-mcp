import logging
import os
import sys
import unittest

# Add the parent directory to sys.path to import the reaper_controller module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestMcpClient(unittest.TestCase):

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

    def test_fx_operations(self):
        self.logger.info("Testing FX operations...")
        track_index = self.controller.create_track("FX Test Track")
        self.assertGreaterEqual(track_index, 0, "Failed to create track for FX test.")

        fx_name = "ReaEQ"
        fx_index = self.controller.add_fx(track_index, fx_name)
        self.assertGreaterEqual(fx_index, 0, f"Failed to add {fx_name}.")
        self.logger.info(f"Added {fx_name} to track {track_index} at index {fx_index}")

        self.assertTrue(self.controller.set_fx_param(track_index, fx_index, "Gain", 6.0), "Failed to set FX parameter.")
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

    def test_master_track_operations(self):
        self.logger.info("Testing master track operations...")
        self.assertTrue(self.controller.set_master_volume(0.8), "Failed to set master volume.")
        self.assertTrue(self.controller.set_master_pan(-0.5), "Failed to set master pan.")
        self.logger.info("Set master volume to 0.8 and pan to -0.5")

    def test_midi_and_item_operations(self):
        self.logger.info("Testing MIDI and item operations...")
        midi_track_index = self.controller.create_track("MIDI Track")
        self.assertGreaterEqual(midi_track_index, 0, "Failed to create MIDI track.")
        self.logger.info(f"Created MIDI track {midi_track_index}")

        midi_item_id = self.controller.create_midi_item(midi_track_index, 0.0, 4.0)
        self.assertGreaterEqual(midi_item_id, 0, "Failed to create MIDI item.")
        self.logger.info(f"Created MIDI item {midi_item_id}")

        self.assertTrue(self.controller.add_midi_note(midi_track_index, midi_item_id, 60, 0.0, 1.0, 100), "Failed to add C note.")
        self.assertTrue(self.controller.add_midi_note(midi_track_index, midi_item_id, 64, 0.0, 1.0, 100), "Failed to add E note.")
        self.assertTrue(self.controller.add_midi_note(midi_track_index, midi_item_id, 67, 0.0, 1.0, 100), "Failed to add G note.")
        self.logger.info("Added MIDI notes (C major chord)")

        midi_item2_id = self.controller.create_midi_item(midi_track_index, 4.0, 2.0)
        self.assertGreaterEqual(midi_item2_id, 0, "Failed to create second MIDI item.")
        self.logger.info(f"Created second MIDI item {midi_item2_id}")

        self.assertTrue(self.controller.add_midi_note(midi_track_index, midi_item2_id, 72, 0.0, 0.5, 90), "Failed to add note to second item.")
        self.logger.info("Added note to second MIDI item.")

        selected_items = self.controller.get_selected_items()
        self.assertIsInstance(selected_items, list, "Selected items is not a list.")
        self.assertGreater(len(selected_items), 0, "No items selected.")
        self.logger.info(f"Selected items: {len(selected_items)}")

        for item in selected_items:
            self.assertTrue(self.controller.delete_item(item['track_index'], item['item_id']), f"Failed to delete item {item['item_id']}.")
        self.logger.info("Deleted selected items.")


if __name__ == "__main__":
    unittest.main()
