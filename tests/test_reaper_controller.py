import unittest
import logging
from .reaper_controller import ReaperController

class TestReaperController(unittest.TestCase):
    """Test suite for ReaperController functionality."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        # Enable debug logging
        logging.basicConfig(level=logging.DEBUG)
        cls.logger = logging.getLogger(__name__)
        
        # Initialize controller with debug mode
        cls.controller = ReaperController(debug=True)
        
        # Verify connection
        if not cls.controller.verify_connection():
            raise Exception("Failed to connect to Reaper")

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
        test_tempo = 120.0
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
        
        # Add FX
        fx_name = "ReaEQ"
        fx_index = self.controller.add_fx(track_index, fx_name)
        self.assertGreaterEqual(fx_index, 0)
        
        # Set FX parameter
        param_name = "Band 1 Gain"
        param_value = 6.0
        self.assertTrue(self.controller.set_fx_param(track_index, fx_index, param_name, param_value))
        
        # Get FX parameter
        current_value = self.controller.get_fx_param(track_index, fx_index, param_name)
        self.assertEqual(current_value, param_value)
        
        # Toggle FX
        self.assertTrue(self.controller.toggle_fx(track_index, fx_index, False))
        self.assertTrue(self.controller.toggle_fx(track_index, fx_index, True))
        
        # Remove FX
        self.assertTrue(self.controller.remove_fx(track_index, fx_index))

    def test_regions_and_markers(self):
        """Test region and marker operations."""
        # Create region
        start_time = 0.0
        end_time = 10.0
        region_name = "Test Region"
        region_index = self.controller.create_region(start_time, end_time, region_name)
        self.assertGreaterEqual(region_index, 0)
        
        # Create marker
        marker_time = 5.0
        marker_name = "Test Marker"
        marker_index = self.controller.create_marker(marker_time, marker_name)
        self.assertGreaterEqual(marker_index, 0)
        
        # Delete region
        self.assertTrue(self.controller.delete_region(region_index))
        
        # Delete marker
        self.assertTrue(self.controller.delete_marker(marker_index))

    def test_master_track(self):
        """Test master track operations."""
        # Get master track info
        master_info = self.controller.get_master_track()
        self.assertIsInstance(master_info, dict)
        
        # Set master volume
        volume = 0.8
        self.assertTrue(self.controller.set_master_volume(volume))
        
        # Set master pan
        pan = 0.5
        self.assertTrue(self.controller.set_master_pan(pan))
        
        # Toggle master mute
        self.assertTrue(self.controller.toggle_master_mute(True))
        self.assertTrue(self.controller.toggle_master_mute(False))
        
        # Toggle master solo
        self.assertTrue(self.controller.toggle_master_solo(True))
        self.assertTrue(self.controller.toggle_master_solo(False))

if __name__ == '__main__':
    unittest.main() 