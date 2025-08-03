import logging
import os
import sys
import unittest

# Add the parent directory to sys.path to import the reaper_controller module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController


class TestMidiItemClientOperations(unittest.TestCase):

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
