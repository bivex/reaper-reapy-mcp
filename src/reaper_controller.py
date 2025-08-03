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
    
    # Additional project operations
    def set_tempo(self, bpm: float) -> bool:
        """Set the project tempo."""
        return self.project.set_tempo(bpm)
    
    def get_tempo(self) -> Optional[float]:
        """Get the current project tempo."""
        return self.project.get_tempo()
    
    # Additional master operations
    def get_master_track(self) -> Dict[str, Any]:
        """Get master track information."""
        return self.master.get_master_track()
    
    def set_master_pan(self, pan: float) -> bool:
        """Set the master track pan."""
        return self.master.set_master_pan(pan)
    
    def toggle_master_mute(self, mute: Optional[bool] = None) -> bool:
        """Toggle master track mute."""
        return self.master.toggle_master_mute(mute)
    
    def toggle_master_solo(self, solo: Optional[bool] = None) -> bool:
        """Toggle master track solo."""
        return self.master.toggle_master_solo(solo)
    
    # Additional FX operations
    def add_fx(self, track_index: int, fx_name: str) -> int:
        """Add an FX to a track."""
        return self.fx.add_fx(track_index, fx_name)
    
    def remove_fx(self, track_index: int, fx_index: int) -> bool:
        """Remove an FX from a track."""
        return self.fx.remove_fx(track_index, fx_index)
    
    def get_fx_list(self, track_index: int) -> List[str]:
        """Get list of FX on a track."""
        return self.fx.get_fx_list(track_index)
    
    def get_available_fx_list(self) -> List[str]:
        """Get list of available FX."""
        return self.fx.get_available_fx_list()
    
    def set_fx_param(self, track_index: int, fx_index: int, param_name: str, value: float) -> bool:
        """Set an FX parameter value."""
        return self.fx.set_fx_param(track_index, fx_index, param_name, value)
    
    def get_fx_param(self, track_index: int, fx_index: int, param_name: str) -> float:
        """Get an FX parameter value."""
        return self.fx.get_fx_param(track_index, fx_index, param_name)
    
    def get_fx_param_list(self, track_index: int, fx_index: int) -> List[str]:
        """Get list of FX parameters."""
        return self.fx.get_fx_param_list(track_index, fx_index)
    
    def toggle_fx(self, track_index: int, fx_index: int, enable: Optional[bool] = None) -> bool:
        """Toggle FX on/off."""
        return self.fx.toggle_fx(track_index, fx_index, enable)
    
    # Additional marker operations
    def create_region(self, start_time: float, end_time: float, name: str) -> bool:
        """Create a region in the project."""
        return self.marker.create_region(start_time, end_time, name)
    
    def delete_region(self, region_index: int) -> bool:
        """Delete a region from the project."""
        return self.marker.delete_region(region_index)
    
    def create_marker(self, time: float, name: str) -> bool:
        """Create a marker at the specified time."""
        return self.marker.create_marker(time, name)
    
    def delete_marker(self, marker_index: int) -> bool:
        """Delete a marker from the project."""
        return self.marker.delete_marker(marker_index)
    
    # Additional MIDI operations
    def create_midi_item(self, track_index: int, start_time: Optional[float] = None, length: float = 4.0) -> Optional[int]:
        """Create a MIDI item on a track."""
        if start_time is None:
            start_time = 0.0
        return self.midi.create_midi_item(track_index, start_time, length=length)
    
    def add_midi_note(self, track_index: int, item_id: int, pitch: int, start_time: float, length: float, velocity: int = 96) -> bool:
        """Add a MIDI note to a MIDI item."""
        from src.controllers.midi.midi_controller import MIDIController
        note_params = MIDIController.MIDINoteParams(
            pitch=pitch,
            start_time=start_time,
            length=length,
            velocity=velocity
        )
        return self.midi.add_midi_note(track_index, item_id, note_params)
    
    def clear_midi_item(self, track_index: int, item_id: int) -> bool:
        """Clear all MIDI notes from a MIDI item."""
        return self.midi.clear_midi_item(track_index, item_id)
    
    def get_midi_notes(self, track_index: int, item_id: int) -> List[Dict[str, Any]]:
        """Get all MIDI notes from a MIDI item."""
        return self.midi.get_midi_notes(track_index, item_id)
    
    def find_midi_notes_by_pitch(self, pitch_min: int = 0, pitch_max: int = 127) -> List[Dict[str, Any]]:
        """Find MIDI notes within a pitch range."""
        return self.midi.find_midi_notes_by_pitch(pitch_min, pitch_max)
    
    def get_selected_midi_item(self) -> Optional[Dict[str, Any]]:
        """Get the currently selected MIDI item."""
        return self.midi.get_selected_midi_item()
    
    # Additional audio operations
    def insert_audio_item(self, track_index: int, file_path: str, start_time: Optional[float] = None, start_measure: Optional[str] = None) -> Optional[int]:
        """Insert an audio file as an item on a track."""
        return self.audio.insert_audio_item(track_index, file_path, start_time, start_measure)
    
    def duplicate_item(self, track_index: int, item_id: int, new_time: Optional[float] = None, new_measure: Optional[str] = None) -> Optional[int]:
        """Duplicate an existing item."""
        return self.audio.duplicate_item(track_index, item_id, new_time, new_measure)
    
    def delete_item(self, track_index: int, item_id: int) -> bool:
        """Delete an item from a track."""
        return self.audio.delete_item(track_index, item_id)
    
    def get_item_properties(self, track_index: int, item_id: int) -> Dict[str, Any]:
        """Get properties of an item."""
        return self.audio.get_item_properties(track_index, item_id)
    
    def set_item_position(self, track_index: int, item_id: int, position_time: Optional[float] = None, position_measure: Optional[str] = None) -> bool:
        """Set the position of an item."""
        return self.audio.set_item_position(track_index, item_id, position_time, position_measure)
    
    def set_item_length(self, track_index: int, item_id: int, length: float) -> bool:
        """Set the length of an item."""
        return self.audio.set_item_length(track_index, item_id, length)
    
    def get_items_in_time_range(self, track_index: int, start_time: Optional[float] = None, end_time: Optional[float] = None, start_measure: Optional[str] = None, end_measure: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get items within a time range."""
        return self.audio.get_items_in_time_range(track_index, start_time, end_time, start_measure, end_measure)
    
    def get_selected_items(self) -> List[Dict[str, Any]]:
        """Get all selected items."""
        return self.audio.get_selected_items()

# Re-export the ReaperController class for backward compatibility
__all__ = ['ReaperController']
