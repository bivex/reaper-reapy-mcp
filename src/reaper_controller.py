# This file is now just a wrapper around the controllers package

import os
import sys
from typing import Optional, List, Dict, Any, Union

# Add necessary paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)  # Add script directory to path

# Import controllers using absolute imports from src package
from src.controllers.track.track_controller import TrackController
from src.controllers.fx.fx_controller import FXController
from src.controllers.marker.marker_controller import MarkerController
from src.controllers.midi.midi_controller import MIDIController
from src.controllers.audio.audio_controller import AudioController
from src.controllers.master.master_controller import MasterController
from src.controllers.project.project_controller import ProjectController

# Constants to replace magic numbers
DEFAULT_MIDI_VELOCITY = 100

# Create a combined controller that inherits from all controllers
class ReaperController:
    """Controller for interacting with Reaper using reapy.
    
    This class combines all controller functionality from specialized controllers.
    Acts as a facade that delegates operations to appropriate specialized controllers.
    """
    def __init__(self, debug=False):
        # Initialize other controllers as attributes
        self.track = TrackController(debug=debug)
        self.fx = FXController(debug=debug)
        self.marker = MarkerController(debug=debug)
        self.midi = MIDIController(debug=debug)
        self.audio = AudioController(debug=debug)
        self.master = MasterController(debug=debug)
        self.project = ProjectController(debug=debug)
        
        # Store debug setting for logging
        self.debug = debug
    
    def verify_connection(self) -> bool:
        """Verify connection to REAPER."""
        try:
            import reapy
            # Try to access REAPER project to verify connection
            project = reapy.Project()
            # Simple test to see if we can access project properties
            _ = len(project.tracks)
            return True
        except Exception:
            return False
    
    # Track operations
    def create_track(self, name: Optional[str] = None) -> int:
        """Create a new track in Reaper."""
        return self.track.create_track(name)
    
    def rename_track(self, track_index: int, new_name: str) -> bool:
        """Rename an existing track."""
        return self.track.rename_track(track_index, new_name)
    
    def get_track_count(self) -> int:
        """Get the number of tracks in the project."""
        return self.track.get_track_count()
    
    def set_track_color(self, track_index: int, color: str) -> bool:
        """Set the color of a track."""
        return self.track.set_track_color(track_index, color)
    
    def get_track_color(self, track_index: int) -> str:
        """Get the color of a track."""
        return self.track.get_track_color(track_index)
    
    # Project operations
    def get_project_info(self) -> Dict[str, Any]:
        """Get basic project information."""
        return self.project.get_project_info()
    
    def save_project(self, filepath: Optional[str] = None) -> bool:
        """Save the current project."""
        return self.project.save_project(filepath)
    
    # Marker operations
    def add_marker(self, position: float, name: str = "") -> bool:
        """Add a marker at the specified position."""
        return self.marker.add_marker(position, name)
    
    def get_markers(self) -> List[Dict[str, Any]]:
        """Get all markers in the project."""
        return self.marker.get_markers()
    
    # FX operations
    def add_fx_to_track(self, track_index: int, fx_name: str) -> bool:
        """Add an FX to a track."""
        return self.fx.add_fx_to_track(track_index, fx_name)
    
    def get_track_fx_list(self, track_index: int) -> List[str]:
        """Get list of FX on a track."""
        return self.fx.get_track_fx_list(track_index)
    
    # MIDI operations
    def create_midi_item(self, track_index: int, position: float, length: float) -> Optional[int]:
        """Create a MIDI item on a track."""
        return self.midi.create_midi_item(track_index, position, length)
    
    def add_midi_note(self, item_id: int, note: int, start: float, length: float, 
                     velocity: int = DEFAULT_MIDI_VELOCITY) -> bool:
        """Add a MIDI note to a MIDI item."""
        return self.midi.add_midi_note(item_id, note, start, length, velocity)
    
    # Audio operations
    def add_audio_item(self, track_index: int, file_path: str, position: float = 0.0) -> Optional[int]:
        """Add an audio item to a track."""
        return self.audio.add_audio_item(track_index, file_path, position)
    
    # Master operations
    def get_master_volume(self) -> float:
        """Get the master track volume."""
        return self.master.get_master_volume()
    
    def set_master_volume(self, volume: float) -> bool:
        """Set the master track volume."""
        return self.master.set_master_volume(volume)

# Re-export the ReaperController class for backward compatibility
__all__ = ['ReaperController']
