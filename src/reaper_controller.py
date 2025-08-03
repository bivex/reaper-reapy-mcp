# This file is now just a wrapper around the controllers package

import os
import sys
from typing import Optional, List, Dict, Any, Union

# Add necessary paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)  # Add script directory to path

# Import controllers directly from the local directory
from controllers.track_controller import TrackController
from controllers.fx_controller import FXController
from controllers.marker_controller import MarkerController
from controllers.midi_controller import MIDIController
from controllers.audio_controller import AudioController
from controllers.master_controller import MasterController
from controllers.project_controller import ProjectController

# Create a combined controller that inherits from all controllers
class ReaperController:
    """Controller for interacting with Reaper using reapy.
    
    This class combines all controller functionality from specialized controllers.
    """
    def __init__(self, debug=False):
        # Initialize the base controller first
        
        # Initialize other controllers as attributes
        self.track = TrackController(debug=debug)
        self.fx = FXController(debug=debug)
        self.marker = MarkerController(debug=debug)
        self.midi = MIDIController(debug=debug)
        self.audio = AudioController(debug=debug)
        self.master = MasterController(debug=debug)
        self.project = ProjectController(debug=debug)

    def verify_connection(self) -> bool:
        """Delegates to BaseController.verify_connection."""
        return self.base_controller.verify_connection()

    def get_selected_items(self):
        """Delegates to BaseController.get_selected_items."""
        return self.base_controller.get_selected_items()

    def create_track(self, name: Optional[str] = None) -> int:
        """Delegates to TrackController.create_track."""
        return self.track.create_track(name)

    def rename_track(self, track_index: int, new_name: str) -> bool:
        """Delegates to TrackController.rename_track."""
        return self.track.rename_track(track_index, new_name)

    def get_track_count(self) -> int:
        """Delegates to TrackController.get_track_count."""
        return self.track.get_track_count()

    def set_track_color(self, track_index: int, color: str) -> bool:
        """Delegates to TrackController.set_track_color."""
        return self.track.set_track_color(track_index, color)

    def get_track_color(self, track_index: int) -> str:
        """Delegates to TrackController.get_track_color."""
        return self.track.get_track_color(track_index)

    def add_fx(self, track_index: int, fx_name: str) -> int:
        """Delegates to FXController.add_fx."""
        return self.fx.add_fx(track_index, fx_name)

    def remove_fx(self, track_index: int, fx_index: int) -> bool:
        """Delegates to FXController.remove_fx."""
        return self.fx.remove_fx(track_index, fx_index)

    def set_fx_param(self, track_index: int, fx_index: int, param_name: str, value: float) -> bool:
        """Delegates to FXController.set_fx_param."""
        return self.fx.set_fx_param(track_index, fx_index, param_name, value)

    def get_fx_param(self, track_index: int, fx_index: int, param_name: str) -> float:
        """Delegates to FXController.get_fx_param."""
        return self.fx.get_fx_param(track_index, fx_index, param_name)

    def get_fx_param_list(self, track_index: int, fx_index: int) -> List[Dict[str, Any]]:
        """Delegates to FXController.get_fx_param_list."""
        return self.fx.get_fx_param_list(track_index, fx_index)

    def get_fx_list(self, track_index: int) -> List[Dict[str, Any]]:
        """Delegates to FXController.get_fx_list."""
        return self.fx.get_fx_list(track_index)

    def get_available_fx_list(self) -> List[str]:
        """Delegates to FXController.get_available_fx_list."""
        return self.fx.get_available_fx_list()

    def toggle_fx(self, track_index: int, fx_index: int, enable: bool = None) -> bool:
        """Delegates to FXController.toggle_fx."""
        return self.fx.toggle_fx(track_index, fx_index, enable)

    def create_region(self, start_time: float, end_time: float, name: str) -> int:
        """Delegates to MarkerController.create_region."""
        return self.marker.create_region(start_time, end_time, name)

    def delete_region(self, region_index: int) -> bool:
        """Delegates to MarkerController.delete_region."""
        return self.marker.delete_region(region_index)

    def create_marker(self, time: float, name: str) -> int:
        """Delegates to MarkerController.create_marker."""
        return self.marker.create_marker(time, name)

    def delete_marker(self, marker_index: int) -> bool:
        """Delegates to MarkerController.delete_marker."""
        return self.marker.delete_marker(marker_index)

    def create_midi_item(self, track_index: int, start_time: float, length: float = 4.0) -> Union[int, str]:
        """Delegates to MIDIController.create_midi_item."""
        return self.midi.create_midi_item(track_index, start_time, length)

    def add_midi_note(self, track_index: int, item_id: Union[int, str], pitch: int, 
                     start_time: float, length: float, velocity: int = 96, channel: int = 0) -> bool:
        """Delegates to MIDIController.add_midi_note."""
        return self.midi.add_midi_note(track_index, item_id, pitch, start_time, length, velocity, channel)

    def clear_midi_item(self, track_index, item_id):
        """Delegates to MIDIController.clear_midi_item."""
        return self.midi.clear_midi_item(track_index, item_id)

    def get_midi_notes(self, track_index, item_id):
        """Delegates to MIDIController.get_midi_notes."""
        return self.midi.get_midi_notes(track_index, item_id)

    def find_midi_notes_by_pitch(self, pitch_min=0, pitch_max=127):
        """Delegates to MIDIController.find_midi_notes_by_pitch."""
        return self.midi.find_midi_notes_by_pitch(pitch_min, pitch_max)

    def get_all_midi_items(self):
        """Delegates to MIDIController.get_all_midi_items."""
        return self.midi.get_all_midi_items()

    def get_selected_midi_item(self) -> Optional[Dict[str, int]]:
        """Delegates to MIDIController.get_selected_midi_item."""
        return self.midi.get_selected_midi_item()

    def insert_audio_item(self, track_index: int, file_path: str, start_time: float) -> Union[int, str]:
        """Delegates to AudioController.insert_audio_item."""
        return self.audio.insert_audio_item(track_index, file_path, start_time)

    def get_item_properties(self, track_index, item_id):
        """Delegates to AudioController.get_item_properties."""
        return self.audio.get_item_properties(track_index, item_id)

    def set_item_position(self, track_index, item_id, position):
        """Delegates to AudioController.set_item_position."""
        return self.audio.set_item_position(track_index, item_id, position)

    def set_item_length(self, track_index, item_id, length):
        """Delegates to AudioController.set_item_length."""
        return self.audio.set_item_length(track_index, item_id, length)

    def duplicate_item(self, track_index, item_id, new_position=None):
        """Delegates to AudioController.duplicate_item."""
        return self.audio.duplicate_item(track_index, item_id, new_position)

    def delete_item(self, track_index, item_id):
        """Delegates to AudioController.delete_item."""
        return self.audio.delete_item(track_index, item_id)

    def get_items_in_time_range(self, track_index, start_time, end_time):
        """Delegates to AudioController.get_items_in_time_range."""
        return self.audio.get_items_in_time_range(track_index, start_time, end_time)

    def get_master_track(self) -> Dict[str, Any]:
        """Delegates to MasterController.get_master_track."""
        return self.master.get_master_track()

    def set_master_volume(self, volume: float) -> bool:
        """Delegates to MasterController.set_master_volume."""
        return self.master.set_master_volume(volume)

    def set_master_pan(self, pan: float) -> bool:
        """Delegates to MasterController.set_master_pan."""
        return self.master.set_master_pan(pan)

    def toggle_master_mute(self, mute: Optional[bool] = None) -> bool:
        """Delegates to MasterController.toggle_master_mute."""
        return self.master.toggle_master_mute(mute)

    def toggle_master_solo(self, solo: Optional[bool] = None) -> bool:
        """Delegates to MasterController.toggle_master_solo."""
        return self.master.toggle_master_solo(solo)

    def set_tempo(self, bpm: float) -> bool:
        """Delegates to ProjectController.set_tempo."""
        return self.project.set_tempo(bpm)

    def get_tempo(self) -> Optional[float]:
        """Delegates to ProjectController.get_tempo."""
        return self.project.get_tempo()

# Re-export the ReaperController class for backward compatibility
__all__ = ['ReaperController']
