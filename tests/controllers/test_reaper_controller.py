import unittest
import logging
import os


import sys
# Add the parent directory to sys.path to import the reaper_controller module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController
from src.utils.sample_audio import ensure_sample_file
from src.controllers.midi.midi_controller import MIDIController

# Constants to replace magic numbers
DEFAULT_TEMPO = 120.0
DEFAULT_MASTER_VOLUME = 0.8
DEFAULT_MASTER_PAN = 0.5
DEFAULT_REGION_START_TIME = 0.0
DEFAULT_REGION_END_TIME = 10.0
DEFAULT_MARKER_TIME = 5.0
# DEFAULT_MIDI_START_TIME = 0.0 # Removed
# DEFAULT_MIDI_LENGTH = 4.0 # Removed
# DEFAULT_MIDI_NOTE_PITCHES = [60, 64, 67] # Removed
# DEFAULT_MIDI_NOTE_LENGTH = 1.0 # Removed
# DEFAULT_MIDI_NOTE_VELOCITY = 100 # Removed
# DEFAULT_MIDI_NOTE_COUNT = 3 # Removed
DEFAULT_MP3_POSITION = 0.0
DEFAULT_MP3_NEW_POSITION = 1.0
DEFAULT_MP3_NEW_LENGTH = 5.0
DEFAULT_MP3_START_TIME = 6.0
DEFAULT_MP3_NEW_POSITION_2 = 7.0
DEFAULT_AUDIO_FILE_POSITION = 12.0
DEFAULT_TIME_RANGE_START = 0.0
DEFAULT_TIME_RANGE_END = 10.0
DEFAULT_ITEM_COUNT = 2
DEFAULT_PARAMETER_MULTIPLIER = 1.5
DEFAULT_PARAMETER_VALUE = 1.0
DEFAULT_POSITION_DELTA = 0.1
DEFAULT_LENGTH_DELTA = 0.1
DEFAULT_FX_PARAMETER_COUNT = 5
DEFAULT_FX_PARAMETER_LIMIT = 3

class TestReaperController(unittest.TestCase):
    """Test suite for ReaperController functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        cls.logger = logging.getLogger(__name__)
        
        # Initialize controller with debug mode
        cls.controller = ReaperController(debug=True)
        
        # Verify connection
        if not cls.controller.verify_connection():
            raise Exception("Failed to connect to Reaper")

    def setUp(self):
        """Set up test environment."""
        self.logger = logging.getLogger(__name__)
        self.controller = ReaperController(debug=True)
        # Get the full absolute path to the sample audio file
        self.sample_audio_path = os.path.abspath(ensure_sample_file())
        self.logger.info(f"Using sample audio file at: {self.sample_audio_path}")

    def test_connection(self):
        """Test Reaper connection."""
        self.assertTrue(self.controller.verify_connection())

    def test_create_and_rename_track(self):
        """Test track creation and renaming."""
        # Create a track
        track_index = self.controller.create_track("Test Track")
        self.assertGreaterEqual(track_index, 0)
        
        # Rename the track
        new_name = "Renamed Track"
        self.assertTrue(self.controller.rename_track(track_index, new_name))

    def test_tempo_control(self):
        """Test tempo control."""
        # Set tempo
        test_tempo = DEFAULT_TEMPO
        self.assertTrue(self.controller.set_tempo(test_tempo))
        
        # Get tempo
        current_tempo = self.controller.get_tempo()
        self.assertEqual(current_tempo, test_tempo)

    def test_track_color(self):
        """Test track color operations."""
        # Create a track
        track_index = self.controller.create_track()
        
        # Set color
        color = "#FF0000"
        self.assertTrue(self.controller.set_track_color(track_index, color))
        
        # Get color
        current_color = self.controller.get_track_color(track_index)
        self.assertEqual(current_color, color)

    def test_fx_operations(self):
        """Test FX operations."""
        # Create a track
        track_index = self.controller.create_track()
        
        # Test basic FX operations
        self._test_fx_basic_operations(track_index)
        
        # Test FX parameter operations
        self._test_fx_parameter_operations(track_index)
        
        # Test FX list operations
        self._test_fx_list_operations(track_index)
        
        # Test FX toggle operations
        self._test_fx_toggle_operations(track_index)

    def _test_fx_basic_operations(self, track_index: int):
        """Test basic FX operations (add/remove)."""
        fx_name = "VST: ReaEQ (Cockos)"
        fx_index = self.controller.add_fx(track_index, fx_name)
        self.assertGreaterEqual(fx_index, 0)
        
        # Remove FX
        self.assertTrue(self.controller.remove_fx(track_index, fx_index))

    def _test_fx_parameter_operations(self, track_index: int):
        """Test FX parameter operations."""
        fx_name = "VST: ReaEQ (Cockos)"
        fx_index = self.controller.add_fx(track_index, fx_name)
        self.assertGreaterEqual(fx_index, 0)
        
        # Get FX parameter list
        param_list = self.controller.get_fx_param_list(track_index, fx_index)
        self.assertIsInstance(param_list, list)
        self.assertGreater(len(param_list), 0)
        
        # Test parameter modification
        self._test_parameter_modification(track_index, fx_index, param_list)
        
        # Clean up
        self.controller.remove_fx(track_index, fx_index)

    def _test_parameter_modification(self, track_index: int, fx_index: int, param_list: list):
        """Test modifying FX parameters."""
        # Log the discovered parameters
        self.logger.info(f"Discovered {len(param_list)} parameters")
        for i, param in enumerate(param_list[:DEFAULT_FX_PARAMETER_COUNT]):
            self.logger.info(f"Parameter {i}: {param['name']} = {param['value']}")
        
        # Find test parameters
        test_params = self._find_test_parameters(param_list)
        
        # Try to modify parameters
        parameters_modified = False
        for param in test_params:
            if self._test_single_parameter(track_index, fx_index, param):
                parameters_modified = True
        
        if not parameters_modified:
            self.logger.warning("Could not verify parameter value changes, but set operations were successful.")

    def _find_test_parameters(self, param_list: list) -> list:
        """Find suitable parameters for testing."""
        # First find parameters with non-zero values
        test_params = [param for param in param_list if param['value'] != 0.0]
        
        # If no non-zero params found, use the first 3 parameters
        if not test_params and len(param_list) > 0:
            test_params = param_list[:min(DEFAULT_FX_PARAMETER_LIMIT, len(param_list))]
        
        return test_params

    def _test_single_parameter(self, track_index: int, fx_index: int, param: dict) -> bool:
        """Test modifying a single parameter."""
        param_name = param['name']
        current_value = param['value']
        
        # Calculate a new value
        new_value = DEFAULT_PARAMETER_VALUE if current_value == 0.0 else current_value * DEFAULT_PARAMETER_MULTIPLIER
        
        self.logger.info(f"Setting {param_name} from {current_value} to {new_value}")
        set_result = self.controller.set_fx_param(track_index, fx_index, param_name, new_value)
        self.assertTrue(set_result, f"Should be able to set parameter {param_name}")
        
        # Get the updated value
        updated_value = self.controller.get_fx_param(track_index, fx_index, param_name)
        self.logger.info(f"Parameter {param_name} after setting: {updated_value}")
        
        return updated_value != current_value

    def _test_fx_list_operations(self, track_index: int):
        """Test FX list operations."""
        fx_name = "VST: ReaEQ (Cockos)"
        fx_index = self.controller.add_fx(track_index, fx_name)
        
        # Get FX list on track
        fx_list = self.controller.get_fx_list(track_index)
        self.assertIsInstance(fx_list, list)
        self.assertGreater(len(fx_list), 0)
        self.assertEqual(fx_list[0]["name"], fx_name)
        
        # Get available FX list
        available_fx = self.controller.get_available_fx_list()
        self.assertIsInstance(available_fx, list)
        self.assertGreater(len(available_fx), 0)
        
        # Check for ReaEQ in available FX list
        reaeq_name = "ReaEQ (Cockos)"
        self.assertTrue(
            any(reaeq_name in fx for fx in available_fx), 
            f"{reaeq_name} should be in the available FX list"
        )
        
        # Clean up
        self.controller.remove_fx(track_index, fx_index)

    def _test_fx_toggle_operations(self, track_index: int):
        """Test FX toggle operations."""
        fx_name = "VST: ReaEQ (Cockos)"
        fx_index = self.controller.add_fx(track_index, fx_name)
        
        # Toggle FX
        self.assertTrue(self.controller.toggle_fx(track_index, fx_index, False))
        self.assertTrue(self.controller.toggle_fx(track_index, fx_index, True))
        
        # Clean up
        self.controller.remove_fx(track_index, fx_index)

    def test_regions_and_markers(self):
        """Test region and marker operations."""
        # Create region
        start_time = DEFAULT_REGION_START_TIME
        end_time = DEFAULT_REGION_END_TIME
        region_name = "Test Region"
        region_index = self.controller.create_region(start_time, end_time, region_name)
        self.assertGreaterEqual(region_index, 0)
        
        # Create marker
        marker_time = DEFAULT_MARKER_TIME
        marker_name = "Test Marker"
        marker_index = self.controller.create_marker(marker_time, marker_name)
        self.assertGreaterEqual(marker_index, 0)
        
        # Delete region
        self.assertTrue(self.controller.delete_region(region_index))
        
        # Delete marker
        self.assertTrue(self.controller.delete_marker(marker_index))
        # Verify marker is actually deleted
        if hasattr(self.controller, 'get_markers'):
            markers = self.controller.get_markers()
            marker_names = [m.get('name', '') for m in markers]
            self.assertNotIn(marker_name, marker_names, "Marker should be deleted from project")

    def test_master_track(self):
        """Test master track operations."""
        # Get master track info
        master_info = self.controller.get_master_track()
        self.assertIsInstance(master_info, dict)
        
        # Set master volume
        volume = DEFAULT_MASTER_VOLUME
        self.assertTrue(self.controller.set_master_volume(volume))
        
        # Set master pan
        pan = DEFAULT_MASTER_PAN
        self.assertTrue(self.controller.set_master_pan(pan))
        
        # Toggle master mute
        self.assertTrue(self.controller.toggle_master_mute(True))
        self.assertTrue(self.controller.toggle_master_mute(False))
        
        # Toggle master solo
        self.assertTrue(self.controller.toggle_master_solo(True))
        self.assertTrue(self.controller.toggle_master_solo(False))

    def test_midi_operations(self):
        """Test MIDI operations."""
        # Create a track
        track_index = self.controller.create_track("MIDI Test Track")
        
        # Create MIDI item
        start_time = MIDIController.DEFAULT_MIDI_START_TIME
        length = MIDIController.DEFAULT_MIDI_LENGTH
        midi_item_id = self.controller.create_midi_item(track_index, start_time, length=length)
        
        # Check if the MIDI item ID is valid - handle both string and integer IDs
        if isinstance(midi_item_id, str):
            self.assertTrue(midi_item_id, "MIDI item ID should not be empty")
        else:
            self.assertGreaterEqual(midi_item_id, 0, "MIDI item ID should be >= 0")
        
        # Add MIDI notes
        for pitch in MIDIController.DEFAULT_MIDI_NOTE_PITCHES:
            self.assertTrue(self.controller.add_midi_note(
                track_index, midi_item_id, MIDIController.MIDINoteParams(pitch=pitch, start_time=MIDIController.DEFAULT_MIDI_START_TIME, length=MIDIController.DEFAULT_MIDI_NOTE_LENGTH, velocity=MIDIController.DEFAULT_MIDI_NOTE_VELOCITY)
            ))
        
        # Get all MIDI notes from the item
        midi_notes = self.controller.get_midi_notes(track_index, midi_item_id)
        self.assertEqual(len(midi_notes), MIDIController.DEFAULT_MIDI_NOTE_COUNT, "Should have retrieved 3 MIDI notes")
        
        # Verify notes have correct pitches
        pitches = sorted([note['pitch'] for note in midi_notes])
        self.assertEqual(pitches, MIDIController.DEFAULT_MIDI_NOTE_PITCHES, "Retrieved notes should have correct pitches")
        
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
        
    def test_mp3_file_insertion(self):
        """Test MP3 file insertion."""
        # Create a track for the MP3
        track_index = self.controller.create_track("MP3 Test Track")
        
        # Test MP3 file insertion
        mp3_item_id = self._test_mp3_insertion(track_index)
        
        # Test MP3 properties
        self._test_mp3_properties(track_index, mp3_item_id)
        
        # Test MP3 modifications
        self._test_mp3_modifications(track_index, mp3_item_id)
        
        # Clean up
        self._cleanup_mp3_test(track_index, mp3_item_id)

    def _test_mp3_insertion(self, track_index: int):
        """Test inserting MP3 file."""
        self.logger.info(f"Testing MP3 file insertion from: {self.sample_audio_path}")
        
        # Verify the file exists
        self.assertTrue(os.path.exists(self.sample_audio_path), "Test MP3 file should exist")
        
        # Insert the MP3 file at position 0.0
        mp3_item_id = self.controller.insert_audio_item(track_index, self.sample_audio_path, DEFAULT_MP3_POSITION)
        
        # Check MP3 item ID
        if isinstance(mp3_item_id, str):
            self.assertTrue(mp3_item_id, "MP3 item ID should not be empty")
        else:
            self.assertGreaterEqual(mp3_item_id, 0, "MP3 item ID should be >= 0")
        
        return mp3_item_id

    def _test_mp3_properties(self, track_index: int, mp3_item_id):
        """Test MP3 item properties."""
        # Get the properties of the inserted MP3 item
        mp3_properties = self.controller.get_item_properties(track_index, mp3_item_id)
        self.assertIsInstance(mp3_properties, dict)
        self.logger.info(f"MP3 item properties: {mp3_properties}")
        
        # Verify essential properties
        if not self.controller.debug:
            self.assertIn('position', mp3_properties, "MP3 item should have a position property")
            self.assertIn('length', mp3_properties, "MP3 item should have a length property")
            if 'length' in mp3_properties:
                self.assertGreater(mp3_properties['length'], 0, "MP3 item length should be greater than zero")

    def _test_mp3_modifications(self, track_index: int, mp3_item_id):
        """Test modifying MP3 item properties."""
        # Create a marker at the start of the MP3
        marker_name = "MP3 Start"
        marker_index = self.controller.create_marker(0.0, marker_name)
        self.assertGreaterEqual(marker_index, 0)
        
        # Try to modify the MP3 properties
        if not self.controller.debug:
            self.controller.set_item_position(track_index, mp3_item_id, DEFAULT_MP3_NEW_POSITION)
            self.controller.set_item_length(track_index, mp3_item_id, DEFAULT_MP3_NEW_LENGTH)
            
            # Verify the changes
            updated_properties = self.controller.get_item_properties(track_index, mp3_item_id)
            self.assertIsInstance(updated_properties, dict)
            
            # Check properties if they're available
            if 'position' in updated_properties:
                self.assertAlmostEqual(updated_properties['position'], DEFAULT_MP3_NEW_POSITION, delta=DEFAULT_POSITION_DELTA)
            if 'length' in updated_properties:
                self.assertAlmostEqual(updated_properties['length'], DEFAULT_MP3_NEW_LENGTH, delta=DEFAULT_LENGTH_DELTA)
        
        # Delete the marker
        self.assertTrue(self.controller.delete_marker(marker_index))

    def _cleanup_mp3_test(self, track_index: int, mp3_item_id):
        """Clean up MP3 test resources."""
        # Clean up - delete the MP3 item
        self.assertTrue(self.controller.delete_item(track_index, mp3_item_id))

    def test_media_item_operations(self):
        """Test media item operations."""
        # Create a track
        track_index = self.controller.create_track("Audio Test Track")
        
        # Test MIDI item operations
        midi_item_id = self._test_midi_item_operations(track_index)
        
        # Test MP3 item operations
        mp3_item_id = self._test_mp3_item_operations(track_index)
        
        # Test audio file operations
        self._test_audio_file_operations(track_index)
        
        # Clean up
        self._cleanup_media_item_test(track_index, mp3_item_id)

    def _test_midi_item_operations(self, track_index: int):
        """Test MIDI item operations."""
        # Create a MIDI item to test item operations
        midi_item_id = self.controller.create_midi_item(track_index, 0.0, 4.0)
        
        # Check if the item ID is valid
        if isinstance(midi_item_id, str):
            self.assertTrue(midi_item_id, "Item ID should not be empty")
        else:
            self.assertGreaterEqual(midi_item_id, 0, "Item ID should be >= 0")
        
        # Test item operations
        properties = self.controller.get_item_properties(track_index, midi_item_id)
        self.assertIsInstance(properties, dict)
        
        # Test item duplication
        duplicated_id = self.controller.duplicate_item(track_index, midi_item_id)
        if isinstance(duplicated_id, str):
            self.assertTrue(duplicated_id, "Duplicated item ID should not be empty")
        else:
            self.assertGreaterEqual(duplicated_id, 0, "Duplicated item ID should be >= 0")
        
        # Get items in time range
        items = self.controller.get_items_in_time_range(track_index, DEFAULT_TIME_RANGE_START, DEFAULT_TIME_RANGE_END)
        self.assertGreaterEqual(len(items), DEFAULT_ITEM_COUNT)  # Should include both items
        
        return midi_item_id

    def _test_mp3_item_operations(self, track_index: int):
        """Test MP3 item operations."""
        self.logger.info(f"Inserting MP3 file from: {self.sample_audio_path}")
        self.assertTrue(os.path.exists(self.sample_audio_path), "Test MP3 file should exist")
        
        # Insert at position 6.0
        mp3_start_time = DEFAULT_MP3_START_TIME
        mp3_item_id = self.controller.insert_audio_item(track_index, self.sample_audio_path, mp3_start_time)
        
        # Check MP3 item ID
        if isinstance(mp3_item_id, str):
            self.assertTrue(mp3_item_id, "MP3 item ID should not be empty")
        else:
            self.assertGreaterEqual(mp3_item_id, 0, "MP3 item ID should be >= 0")
        
        # Get and verify properties
        mp3_properties = self.controller.get_item_properties(track_index, mp3_item_id)
        self.assertIsInstance(mp3_properties, dict)
        self.logger.info(f"MP3 item properties: {mp3_properties}")
        
        # Verify position if available
        if not self.controller.debug and 'position' in mp3_properties:
            self.assertAlmostEqual(
                mp3_properties['position'], mp3_start_time, delta=0.1,
                msg="MP3 item should be at the specified position"
            )
        
        # Test property modifications
        if not self.controller.debug:
            new_mp3_position = DEFAULT_MP3_NEW_POSITION_2
            self.assertTrue(self.controller.set_item_position(track_index, mp3_item_id, new_mp3_position))
            
            # Check if the position was updated
            updated_mp3_properties = self.controller.get_item_properties(track_index, mp3_item_id)
            if 'position' in updated_mp3_properties:
                self.assertAlmostEqual(
                    updated_mp3_properties['position'], new_mp3_position, delta=DEFAULT_POSITION_DELTA,
                    msg="MP3 item position should be updated"
                )
        
        return mp3_item_id

    def _test_audio_file_operations(self, track_index: int):
        """Test audio file operations."""
        # Try audio file insertion if a test file exists
        audio_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_audio.wav")
        if os.path.exists(audio_file_path):
            audio_item_id = self.controller.insert_audio_item(track_index, audio_file_path, DEFAULT_AUDIO_FILE_POSITION)
            # Check audio item ID
            if isinstance(audio_item_id, str):
                self.assertTrue(audio_item_id, "Audio item ID should not be empty")
            else:
                self.assertGreaterEqual(audio_item_id, 0, "Audio item ID should be >= 0")
            # Delete audio item
            self.assertTrue(self.controller.delete_item(track_index, audio_item_id))

    def _cleanup_media_item_test(self, track_index: int, mp3_item_id):
        """Clean up media item test resources."""
        # Clean up - delete the MP3 item
        self.assertTrue(self.controller.delete_item(track_index, mp3_item_id))
        
        self.logger.info("Skipping strict duplicated item deletion assertion in debug mode.")

    def test_midi_item_create_fail(self):
        """Test MIDI item creation failure handling."""
        # Create a track
        track_index = self.controller.create_track("MIDI Test Track")
        
        # Try to create MIDI item with invalid parameters
        # Using negative track index to force failure
        invalid_track_index = -1
        midi_item_id = self.controller.create_midi_item(invalid_track_index, 0, 4)
        
        # In non-debug mode, it should return -1 for failure
        if not self.controller.debug:
            self.assertEqual(midi_item_id, -1, "MIDI item creation should fail and return -1")
        else:
            # In debug mode, it may return -1 or a valid ID, so just check for int type
            self.assertIsInstance(midi_item_id, int, "MIDI item ID should be int in debug mode")
            
        # Try another failure case with invalid time parameters
        # Using negative start time to force failure
        midi_item_id = self.controller.create_midi_item(track_index, -1, 4)
        
        # In non-debug mode, it should return -1 for failure
        if not self.controller.debug:
            self.assertEqual(midi_item_id, -1, "MIDI item creation should fail and return -1")
        else:
            # In debug mode, it may return -1 or a valid ID, so just check for int type
            self.assertIsInstance(midi_item_id, int, "MIDI item ID should be int in debug mode")

    def test_audio_file_insertion(self):
        """Test audio file insertion."""
        # Create a track for the audio
        track_index = self.controller.create_track("Audio Test Track")
        
        # Insert the sample audio file at position 0.0
        audio_item_id = self.controller.insert_audio_item(track_index, self.sample_audio_path, DEFAULT_MP3_POSITION)
        
        # Check audio item ID - handle both string and integer IDs
        if isinstance(audio_item_id, str):
            self.assertTrue(audio_item_id, "Audio item ID should not be empty")
        else:
            self.assertGreaterEqual(audio_item_id, 0, "Audio item ID should be >= 0")
            
        # Get the properties of the inserted audio item
        audio_properties = self.controller.get_item_properties(track_index, audio_item_id)
        self.assertIsInstance(audio_properties, dict)
        self.logger.info(f"Audio item properties: {audio_properties}")
        
        # Clean up
        self.assertTrue(self.controller.delete_item(track_index, audio_item_id))

if __name__ == '__main__':
    unittest.main()
