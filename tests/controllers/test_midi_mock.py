import unittest
from unittest.mock import patch, MagicMock

# Constants to replace magic numbers
DEFAULT_MIDI_LENGTH = 4.0
DEFAULT_MIDI_VELOCITY = 96
DEFAULT_MIDI_CHANNEL = 0
MAX_MIDI_PITCH = 127
MIN_MIDI_PITCH = 0
DEFAULT_TRACK_INDEX = 0
DEFAULT_ITEM_ID = 0
DEFAULT_POSITION = 0.0
DEFAULT_TAKE_COUNT = 1
DEFAULT_ACTIVE_TAKE = 0
DEFAULT_NEW_POSITION = 2.0
DEFAULT_NEW_LENGTH = 4.0
DEFAULT_AUDIO_START_TIME = 2.0
DEFAULT_AUDIO_LENGTH = 4.0
DEFAULT_MIDI_NOTE_COUNT = 3
DEFAULT_MIDI_NOTE_PITCHES = [60, 64, 67]  # C4, E4, G4
DEFAULT_MIDI_NOTE_LENGTH = 1.0
DEFAULT_MIDI_NOTE_VELOCITY = 100
DEFAULT_TIME_RANGE_START = 0.0
DEFAULT_TIME_RANGE_END = 10.0
DEFAULT_AUDIO_FILE_POSITION = 12.0
DEFAULT_AUDIO_ITEM_ID = 2

# Create a simplified ReaperController mock to use for testing
class MockReaperController:
    def __init__(self, debug=True):
        self.debug = debug
        self._test_midi_items = {}
        self.logger = MagicMock()

    def verify_connection(self):
        return True

    def create_track(self, name=None):
        return DEFAULT_TRACK_INDEX  # Return first track index
        
    def create_midi_item(self, track_index, start_time, length=DEFAULT_MIDI_LENGTH):
        item_id = DEFAULT_ITEM_ID  # Simple item ID for testing
        item_key = f"{track_index}:{item_id}"
        self._test_midi_items[item_key] = {
            'track_index': track_index,
            'item_id': item_id,
            'position': start_time,
            'length': length,
            'notes': []
        }
        return item_id
        
    def add_midi_note(self, track_index, item_id, pitch, start_time, length, velocity=DEFAULT_MIDI_VELOCITY, channel=DEFAULT_MIDI_CHANNEL):
        item_key = f"{track_index}:{item_id}"
        if item_key not in self._test_midi_items:
            self._test_midi_items[item_key] = {
                'track_index': track_index,
                'item_id': item_id,
                'notes': []
            }
        
        self._test_midi_items[item_key]['notes'].append({
            'pitch': pitch,
            'start_time': start_time,
            'end_time': start_time + length,
            'velocity': velocity,
            'channel': channel
        })
        return True
        
    def get_midi_notes(self, track_index, item_id):
        item_key = f"{track_index}:{item_id}"
        if item_key in self._test_midi_items:
            return self._test_midi_items[item_key]['notes']
        return []
        
    def find_midi_notes_by_pitch(self, pitch_min=MIN_MIDI_PITCH, pitch_max=MAX_MIDI_PITCH):
        found_notes = []
        for item_key, item_data in self._test_midi_items.items():
            for note in item_data['notes']:
                if pitch_min <= note['pitch'] <= pitch_max:
                    # Include track and item info with the note
                    found_note = note.copy()
                    found_note['track_index'] = item_data['track_index']
                    found_note['item_id'] = item_data['item_id']
                    found_notes.append(found_note)
        return found_notes
        
    def get_all_midi_items(self):
        return [
            {
                'track_index': data['track_index'],
                'item_id': data['item_id'],
                'position': data.get('position', DEFAULT_POSITION),
                'length': data.get('length', DEFAULT_MIDI_LENGTH),
                'name': f"MIDI Item {data['item_id']}"
            }
            for item_key, data in self._test_midi_items.items()
        ]
        
    def clear_midi_item(self, track_index, item_id):
        item_key = f"{track_index}:{item_id}"
        if item_key in self._test_midi_items:
            self._test_midi_items[item_key]['notes'] = []
        return True
        
    def get_item_properties(self, track_index, item_id):
        item_key = f"{track_index}:{item_id}"
        if item_key in self._test_midi_items:
            return {
                'track_index': track_index,
                'item_id': item_id,
                'position': self._test_midi_items[item_key].get('position', DEFAULT_POSITION),
                'length': self._test_midi_items[item_key].get('length', DEFAULT_MIDI_LENGTH),
                'name': f"MIDI Item {item_id}",
                'is_selected': False,
                'is_muted': False,
                'take_count': DEFAULT_TAKE_COUNT,
                'active_take': DEFAULT_ACTIVE_TAKE
            }
        return {
            'track_index': track_index,
            'item_id': item_id,
            'position': DEFAULT_POSITION,
            'length': DEFAULT_MIDI_LENGTH,
            'name': f"MIDI Item {item_id}",
            'is_selected': False,
            'is_muted': False, 
            'take_count': DEFAULT_TAKE_COUNT,
            'active_take': DEFAULT_ACTIVE_TAKE
        }
        
    def set_item_position(self, track_index, item_id, position):
        item_key = f"{track_index}:{item_id}"
        if item_key in self._test_midi_items:
            self._test_midi_items[item_key]['position'] = position
        return True
        
    def set_item_length(self, track_index, item_id, length):
        item_key = f"{track_index}:{item_id}"
        if item_key in self._test_midi_items:
            self._test_midi_items[item_key]['length'] = length
        return True
        
    def duplicate_item(self, track_index, item_id, new_position=None):
        item_key = f"{track_index}:{item_id}"
        new_item_id = 1  # For simplicity, use 1 as the duplicated item ID
        if item_key in self._test_midi_items:
            source_item = self._test_midi_items[item_key]
            new_key = f"{track_index}:{new_item_id}"
            self._test_midi_items[new_key] = {
                'track_index': track_index,
                'item_id': new_item_id,
                'position': new_position if new_position is not None else source_item.get('position', DEFAULT_POSITION),
                'length': source_item.get('length', DEFAULT_MIDI_LENGTH),
                'notes': [note.copy() for note in source_item.get('notes', [])]
            }
        return new_item_id
        
    def get_items_in_time_range(self, track_index, start_time, end_time):
        items = []
        for item_key, data in self._test_midi_items.items():
            if data['track_index'] == track_index:
                pos = data.get('position', DEFAULT_POSITION)
                length = data.get('length', DEFAULT_MIDI_LENGTH)
                # Check if item overlaps with time range
                if pos + length >= start_time and pos <= end_time:
                    items.append({
                        'track_index': track_index,
                        'item_id': data['item_id'],
                        'position': pos,
                        'length': length,
                        'name': f"MIDI Item {data['item_id']}"
                    })
        return items
        
    def delete_item(self, track_index, item_id):
        item_key = f"{track_index}:{item_id}"
        if item_key in self._test_midi_items:
            del self._test_midi_items[item_key]
        return True
        
    def insert_audio_item(self, track_index, file_path, start_time):
        audio_item_id = DEFAULT_AUDIO_ITEM_ID  # For simplicity use 2 as the audio item ID
        item_key = f"{track_index}:{audio_item_id}"
        self._test_midi_items[item_key] = {
            'track_index': track_index,
            'item_id': audio_item_id,
            'position': start_time,
            'length': DEFAULT_AUDIO_LENGTH,  # Default length
            'notes': [],
            'is_audio': True,
            'file_path': file_path
        }
        return audio_item_id

# Test class
class TestMIDIOperations(unittest.TestCase):
    
    def setUp(self):
        self.controller = MockReaperController(debug=True)
        
    def test_midi_operations(self):
        # Create a track
        track_index = self.controller.create_track("MIDI Test Track")
        
        # Create MIDI item
        start_time = DEFAULT_POSITION
        length = DEFAULT_MIDI_LENGTH
        midi_item_id = self.controller.create_midi_item(track_index, start_time, length)
        
        # Check if the MIDI item ID is valid - handle both string and integer IDs
        if isinstance(midi_item_id, str):
            self.assertTrue(midi_item_id, "MIDI item ID should not be empty")
        else:
            self.assertGreaterEqual(midi_item_id, 0, "MIDI item ID should be >= 0")
        
        # Add MIDI notes
        for pitch in DEFAULT_MIDI_NOTE_PITCHES:
            self.assertTrue(self.controller.add_midi_note(
                track_index, midi_item_id, pitch, DEFAULT_POSITION, 
                DEFAULT_MIDI_NOTE_LENGTH, DEFAULT_MIDI_NOTE_VELOCITY
            ))
        
        # Get all MIDI notes from the item
        midi_notes = self.controller.get_midi_notes(track_index, midi_item_id)
        self.assertEqual(len(midi_notes), DEFAULT_MIDI_NOTE_COUNT, "Should have retrieved 3 MIDI notes")
        
        # Verify notes have correct pitches
        pitches = sorted([note['pitch'] for note in midi_notes])
        self.assertEqual(pitches, DEFAULT_MIDI_NOTE_PITCHES, "Retrieved notes should have correct pitches")
        
        # Test finding notes by pitch
        c_notes = self.controller.find_midi_notes_by_pitch(60, 60)
        self.assertGreaterEqual(len(c_notes), 1, "Should find at least 1 C4 note")
        
        # Test getting all MIDI items
        midi_items = self.controller.get_all_midi_items()
        self.assertGreaterEqual(len(midi_items), 1, "Should find at least 1 MIDI item")
        
        # Clear MIDI item
        self.assertTrue(self.controller.clear_midi_item(track_index, midi_item_id))
        
        # Verify that the notes were cleared
        cleared_notes = self.controller.get_midi_notes(track_index, midi_item_id)
        self.assertEqual(len(cleared_notes), 0, "MIDI item should have no notes after clearing")
        
    def test_media_item_operations(self):
        # Create a track
        track_index = self.controller.create_track("Audio Test Track")
        
        # Create a MIDI item to test item operations (since we may not have an audio file)
        midi_item_id = self.controller.create_midi_item(track_index, DEFAULT_POSITION, DEFAULT_MIDI_LENGTH)
        
        # Check if the item ID is valid - handle both string and integer IDs
        if isinstance(midi_item_id, str):
            self.assertTrue(midi_item_id, "Item ID should not be empty")
        else:
            self.assertGreaterEqual(midi_item_id, 0, "Item ID should be >= 0")
        
        # Test item operations
        # Get item properties
        properties = self.controller.get_item_properties(track_index, midi_item_id)
        self.assertIsInstance(properties, dict)
        
        # Set item position
        new_position = DEFAULT_NEW_POSITION
        self.assertTrue(self.controller.set_item_position(track_index, midi_item_id, new_position))
        
        # Set item length
        new_length = DEFAULT_NEW_LENGTH
        self.assertTrue(self.controller.set_item_length(track_index, midi_item_id, new_length))
        
        # Duplicate item
        duplicated_id = self.controller.duplicate_item(track_index, midi_item_id)
        # Check duplicated ID - handle both string and integer IDs
        if isinstance(duplicated_id, str):
            self.assertTrue(duplicated_id, "Duplicated item ID should not be empty")
        else:
            self.assertGreaterEqual(duplicated_id, 0, "Duplicated item ID should be >= 0")
        
        # Get items in time range
        items = self.controller.get_items_in_time_range(track_index, 0.0, 10.0)
        self.assertGreaterEqual(len(items), 2)  # Should include both items
        
        # Delete the duplicated item
        self.assertTrue(self.controller.delete_item(track_index, duplicated_id))
        
        # Delete the original item
        self.assertTrue(self.controller.delete_item(track_index, midi_item_id))

if __name__ == '__main__':
    unittest.main()
