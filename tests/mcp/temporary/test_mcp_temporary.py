import logging
import os
import sys
import time
import unittest

# Add the repository root to the Python path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController
from src.mcp_tools import setup_mcp_tools
from src.controllers.midi.midi_controller import MIDIController

# Mock reapy objects and methods for testing
class MockReapyItem:
    def __init__(self, item_id, position=0.0, length=4.0):
        self.id = item_id
        self.position = position
        self.length = length
        self.selected = False
        self._midi_notes = []
        self.active_take = MockReapyTake(self._midi_notes)

    def set_selected(self, selected_state):
        self.selected = selected_state

class MockReapyTake:
    def __init__(self, midi_notes=None):
        self._midi_notes = midi_notes if midi_notes is not None else []
        self.is_midi = True

    def add_midi_note(self, pitch, start_time, end_time, velocity, channel):
        self._midi_notes.append({
            'pitch': pitch,
            'start': start_time,
            'end': end_time,
            'velocity': velocity,
            'channel': channel
        })

    def clear_midi_notes(self):
        self._midi_notes = []

    @property
    def midi_notes(self):
        return self._midi_notes


class MockReapyTrack:
    def __init__(self, index):
        self.index = index
        self.items = []

    def add_midi_item(self, start_time, end_time):
        item_id = len(self.items)
        item = MockReapyItem(item_id, position=start_time, length=end_time - start_time)
        self.items.append(item)
        return item


class MockReapyProject:
    def __init__(self):
        self.tracks = [MockReapyTrack(0), MockReapyTrack(1)]  # Two tracks for testing
        self.current_project = self

    def __len__(self):
        return len(self.tracks)

    def __getitem__(self, index):
        return self.tracks[index]


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

        # Create an item and select it
        midi_item_id = McpTools.create_midi_item(0, 0.0, length=MIDIController.DEFAULT_MIDI_LENGTH)['item_id']
        self.assertGreaterEqual(midi_item_id, 0, "Failed to create MIDI item.")
        self.logger.info(f"Created MIDI item with ID: {midi_item_id}")
        
        # Small delay to ensure item is fully created
        time.sleep(0.5) # Changed from DEFAULT_SLEEP_TIME to 0.5
        
        # Add MIDI notes - C major chord
        self.logger.info(f"Adding MIDI notes to item ID: {midi_item_id}")
        note_result_c = self.controller.add_midi_note(midi_track_index, midi_item_id, MIDIController.MIDINoteParams(pitch=60, start_time=0.0, length=1.0, velocity=100))  # C
        self.assertTrue(note_result_c, "Failed to add C note.")
        
        if note_result_c:
            self.assertTrue(self.controller.add_midi_note(midi_track_index, midi_item_id, MIDIController.MIDINoteParams(pitch=64, start_time=0.0, length=1.0, velocity=100)), "Failed to add E note.")  # E
            self.assertTrue(self.controller.add_midi_note(midi_track_index, midi_item_id, MIDIController.MIDINoteParams(pitch=67, start_time=0.0, length=1.0, velocity=100)), "Failed to add G note.")  # G
            self.logger.info("Added MIDI notes (C major chord)")
        else:
            self.logger.error("Failed to add first note, not attempting remaining notes")

        midi_item2_id = self.controller.create_midi_item(midi_track_index, 4.0, length=2.0)
        self.assertGreaterEqual(midi_item2_id, 0, "Failed to create second MIDI item.")
        self.logger.info(f"Created second MIDI item with ID: {midi_item2_id}")
        
        time.sleep(0.5) # Changed from DEFAULT_SLEEP_TIME to 0.5

        note2_result = self.controller.add_midi_note(midi_track_index, midi_item2_id, MIDIController.MIDINoteParams(pitch=72, start_time=4.0, length=0.5, velocity=90))  # C an octave up
        self.assertTrue(note2_result, "Failed to add note to second MIDI item.")
        self.logger.info(f"Result of adding note to second item: {note2_result}")


if __name__ == "__main__":
    unittest.main()
