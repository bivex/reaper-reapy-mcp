import logging
import os
import sys
import time
import unittest

# Add the repository root to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController

# Constants to replace magic numbers
DEFAULT_MIDI_START_TIME = 0.0
DEFAULT_MIDI_LENGTH = 4.0
DEFAULT_MIDI_NOTE_PITCHES = [60, 64, 67]  # C, E, G (C major chord)
DEFAULT_MIDI_NOTE_LENGTH = 1.0
DEFAULT_MIDI_NOTE_VELOCITY = 100
DEFAULT_SECOND_MIDI_START_TIME = 4.0
DEFAULT_SECOND_MIDI_LENGTH = 2.0
DEFAULT_SECOND_MIDI_NOTE_PITCH = 72  # C an octave up
DEFAULT_SECOND_MIDI_NOTE_LEN = 0.5
DEFAULT_SECOND_MIDI_NOTE_VEL = 90
DEFAULT_SLEEP_TIME = 0.5


class TestMcpTemporary(unittest.TestCase):

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

    def test_midi_item_creation(self):
        self.logger.info("Testing MIDI and item operations...")
        midi_track_index = self.controller.create_track("MIDI Track")
        self.assertGreaterEqual(midi_track_index, 0, "Failed to create MIDI track.")
        self.logger.info(f"Created MIDI track {midi_track_index}")

        midi_item_id = self.controller.create_midi_item(midi_track_index, DEFAULT_MIDI_START_TIME, length=DEFAULT_MIDI_LENGTH)
        self.assertGreaterEqual(midi_item_id, 0, "Failed to create MIDI item.")
        self.logger.info(f"Created MIDI item with ID: {midi_item_id}")
        
        # Small delay to ensure item is fully created
        time.sleep(DEFAULT_SLEEP_TIME)
        
        # Add MIDI notes - C major chord
        self.logger.info(f"Adding MIDI notes to item ID: {midi_item_id}")
        note_result_c = self.controller.add_midi_note(midi_track_index, midi_item_id, DEFAULT_MIDI_NOTE_PITCHES[0], DEFAULT_MIDI_START_TIME, DEFAULT_MIDI_NOTE_LENGTH, DEFAULT_MIDI_NOTE_VELOCITY)  # C
        self.assertTrue(note_result_c, "Failed to add C note.")
        
        if note_result_c:
            self.assertTrue(self.controller.add_midi_note(midi_track_index, midi_item_id, DEFAULT_MIDI_NOTE_PITCHES[1], DEFAULT_MIDI_START_TIME, DEFAULT_MIDI_NOTE_LENGTH, DEFAULT_MIDI_NOTE_VELOCITY), "Failed to add E note.")  # E
            self.assertTrue(self.controller.add_midi_note(midi_track_index, midi_item_id, DEFAULT_MIDI_NOTE_PITCHES[2], DEFAULT_MIDI_START_TIME, DEFAULT_MIDI_NOTE_LENGTH, DEFAULT_MIDI_NOTE_VELOCITY), "Failed to add G note.")  # G
            self.logger.info("Added MIDI notes (C major chord)")
        else:
            self.logger.error("Failed to add first note, not attempting remaining notes")

        midi_item2_id = self.controller.create_midi_item(midi_track_index, DEFAULT_SECOND_MIDI_START_TIME, length=DEFAULT_SECOND_MIDI_LENGTH)
        self.assertGreaterEqual(midi_item2_id, 0, "Failed to create second MIDI item.")
        self.logger.info(f"Created second MIDI item with ID: {midi_item2_id}")
        
        time.sleep(DEFAULT_SLEEP_TIME)

        note2_result = self.controller.add_midi_note(midi_track_index, midi_item2_id, DEFAULT_SECOND_MIDI_NOTE_PITCH, DEFAULT_SECOND_MIDI_START_TIME, DEFAULT_SECOND_MIDI_NOTE_LEN, DEFAULT_SECOND_MIDI_NOTE_VEL)  # C an octave up
        self.assertTrue(note2_result, "Failed to add note to second MIDI item.")
        self.logger.info(f"Result of adding note to second item: {note2_result}")


if __name__ == "__main__":
    unittest.main()
