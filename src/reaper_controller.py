# This file is now just a wrapper around the controllers package

import os
import sys
import logging
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
from src.controllers.routing.routing_controller import RoutingController
from src.controllers.routing.advanced_routing_controller import AdvancedRoutingController
from src.controllers.automation.automation_controller import AutomationController
from src.controllers.audio.advanced_item_controller import AdvancedItemController

# Constants to replace magic numbers
DEFAULT_MIDI_VELOCITY = 100

# Create a combined controller that inherits from all controllers
class ReaperController:
    """Controller for interacting with Reaper using reapy.
    
    This class combines all controller functionality from specialized controllers.
    Acts as a facade that delegates operations to appropriate specialized controllers.
    """
    def __init__(self, debug=False):
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
        
        # Store debug setting for logging
        self.debug = debug
        
        # Initialize controllers with lazy reapy import
        self._initialize_controllers()
        
        # Test connection
        if not self.verify_connection():
            self.logger.warning("REAPER connection not available. Some operations may fail.")
    
    def _initialize_controllers(self):
        """Initialize all controllers with proper error handling."""
        try:
            self.track = TrackController(debug=self.debug)
            self.fx = FXController(debug=self.debug)
            self.marker = MarkerController(debug=self.debug)
            self.midi = MIDIController(debug=self.debug)
            self.audio = AudioController(debug=self.debug)
            self.master = MasterController(debug=self.debug)
            self.project = ProjectController(debug=self.debug)
            self.routing = RoutingController(debug=self.debug)
            self.advanced_routing = AdvancedRoutingController(debug=self.debug)
            self.automation = AutomationController(debug=self.debug)
            self.advanced_items = AdvancedItemController(debug=self.debug)
        except Exception as e:
            self.logger.error(f"Failed to initialize controllers: {e}")
            # Create placeholder controllers that will fail gracefully
            self._create_placeholder_controllers()
    
    def _create_placeholder_controllers(self):
        """Create placeholder controllers when reapy is not available."""
        class PlaceholderController:
            def __init__(self, name, debug=False):
                self.name = name
                self.logger = logging.getLogger(f"Placeholder{name}")
                if debug:
                    self.logger.setLevel(logging.INFO)
            
            def __getattr__(self, name):
                def method(*args, **kwargs):
                    self.logger.warning(f"REAPER not connected. {self.name}.{name}() unavailable.")
                    return None
                return method
        
        self.track = PlaceholderController("TrackController", self.debug)
        self.fx = PlaceholderController("FXController", self.debug)
        self.marker = PlaceholderController("MarkerController", self.debug)
        self.midi = PlaceholderController("MIDIController", self.debug)
        self.audio = PlaceholderController("AudioController", self.debug)
        self.master = PlaceholderController("MasterController", self.debug)
        self.project = PlaceholderController("ProjectController", self.debug)
        self.routing = PlaceholderController("RoutingController", self.debug)
        self.advanced_routing = PlaceholderController("AdvancedRoutingController", self.debug)
        self.automation = PlaceholderController("AutomationController", self.debug)
        self.advanced_items = PlaceholderController("AdvancedItemController", self.debug)
    
    def verify_connection(self) -> bool:
        """Verify connection to REAPER."""
        try:
            # Simple TCP connection test to check if REAPER is listening
            import socket
            
            # Try common reapy ports
            ports_to_try = [2306, 2307, 2308, 2309]
            
            for port in ports_to_try:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.0)  # 1 second timeout
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    
                    if result == 0:
                        self.logger.info(f"REAPER server found and listening on port {port}")
                        return True
                        
                except Exception as e:
                    continue
            
            self.logger.warning("REAPER connection failed: No server found on common ports (2306-2309)")
            return False
                    
        except Exception as e:
            self.logger.warning(f"REAPER connection test failed: {e}")
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
    
    def clear_project(self) -> bool:
        """Clear all items from all tracks in the project."""
        return self.project.clear_project()
    
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
    
    def add_midi_note(self, track_index: int, item_id: int, note_params) -> bool:
        """Add a MIDI note to a MIDI item."""
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

    # Routing operations
    def add_send(self, source_track: int, destination_track: int, 
                 volume: float = 0.0, pan: float = 0.0, 
                 mute: bool = False, phase: bool = False, 
                 channels: int = 2) -> Optional[int]:
        """Add a send from source track to destination track."""
        return self.routing.add_send(source_track, destination_track, volume, pan, mute, phase, channels)
    
    def remove_send(self, source_track: int, send_id: int) -> bool:
        """Remove a send from a track."""
        return self.routing.remove_send(source_track, send_id)
    
    def get_sends(self, track_index: int) -> List[Dict[str, Any]]:
        """Get all sends from a track."""
        sends = self.routing.get_sends(track_index)
        return [vars(send) for send in sends]
    
    def get_receives(self, track_index: int) -> List[Dict[str, Any]]:
        """Get all receives on a track."""
        receives = self.routing.get_receives(track_index)
        return [vars(receive) for receive in receives]
    
    def set_send_volume(self, source_track: int, send_id: int, volume: float) -> bool:
        """Set the volume of a send."""
        return self.routing.set_send_volume(source_track, send_id, volume)
    
    def set_send_pan(self, source_track: int, send_id: int, pan: float) -> bool:
        """Set the pan of a send."""
        return self.routing.set_send_pan(source_track, send_id, pan)
    
    def toggle_send_mute(self, source_track: int, send_id: int, mute: Optional[bool] = None) -> bool:
        """Toggle or set the mute state of a send."""
        return self.routing.toggle_send_mute(source_track, send_id, mute)
    
    def get_track_routing_info(self, track_index: int) -> Dict[str, Any]:
        """Get comprehensive routing information for a track."""
        return self.routing.get_track_routing_info(track_index)
    
    def debug_track_routing(self, track_index: int) -> Dict[str, Any]:
        """Debug track routing information for troubleshooting."""
        return self.routing.debug_track_routing(track_index)
    
    def clear_all_sends(self, track_index: int) -> bool:
        """Remove all sends from a track."""
        return self.routing.clear_all_sends(track_index)
    
    def clear_all_receives(self, track_index: int) -> bool:
        """Remove all receives from a track."""
        return self.routing.clear_all_receives(track_index)

    # Advanced Routing & Bussing operations
    def create_folder_track(self, name: str = "Folder Track") -> int:
        """Create a folder track that can contain other tracks."""
        return self.advanced_routing.create_folder_track(name)

    def create_bus_track(self, name: str = "Bus Track") -> int:
        """Create a bus track for grouping and processing multiple tracks."""
        return self.advanced_routing.create_bus_track(name)

    def set_track_parent(self, child_track_index: int, parent_track_index: int) -> bool:
        """Set a track's parent folder track."""
        return self.advanced_routing.set_track_parent(child_track_index, parent_track_index)

    def get_track_children(self, parent_track_index: int) -> List[int]:
        """Get all child tracks of a parent track."""
        return self.advanced_routing.get_track_children(parent_track_index)

    def set_track_folder_depth(self, track_index: int, depth: int) -> bool:
        """Set the folder depth of a track."""
        return self.advanced_routing.set_track_folder_depth(track_index, depth)

    def get_track_folder_depth(self, track_index: int) -> int:
        """Get the folder depth of a track."""
        return self.advanced_routing.get_track_folder_depth(track_index)

    # Automation & Modulation operations
    def create_automation_envelope(self, track_index: int, envelope_name: str) -> int:
        """Create an automation envelope on a track."""
        return self.automation.create_automation_envelope(track_index, envelope_name)

    def add_automation_point(self, track_index: int, envelope_name: str, time: float, value: float, shape: int = 0) -> bool:
        """Add an automation point to an envelope."""
        return self.automation.add_automation_point(track_index, envelope_name, time, value, shape)

    def get_automation_points(self, track_index: int, envelope_name: str) -> List[Dict[str, Any]]:
        """Get all automation points from an envelope."""
        return self.automation.get_automation_points(track_index, envelope_name)

    def set_automation_mode(self, track_index: int, mode: str) -> bool:
        """Set the automation mode for a track."""
        return self.automation.set_automation_mode(track_index, mode)

    def get_automation_mode(self, track_index: int) -> str:
        """Get the current automation mode for a track."""
        return self.automation.get_automation_mode(track_index)

    def delete_automation_point(self, track_index: int, envelope_name: str, point_index: int) -> bool:
        """Delete an automation point from an envelope."""
        return self.automation.delete_automation_point(track_index, envelope_name, point_index)

    # Advanced Item Operations
    def split_item(self, track_index: int, item_index: int, split_time: float) -> List[int]:
        """Split an item at a specific time."""
        return self.advanced_items.split_item(track_index, item_index, split_time)

    def glue_items(self, track_index: int, item_indices: List[int]) -> int:
        """Glue multiple items together into a single item."""
        return self.advanced_items.glue_items(track_index, item_indices)

    def fade_in(self, track_index: int, item_index: int, fade_length: float, fade_curve: int = 0) -> bool:
        """Add a fade-in to an item."""
        return self.advanced_items.fade_in(track_index, item_index, fade_length, fade_curve)

    def fade_out(self, track_index: int, item_index: int, fade_length: float, fade_curve: int = 0) -> bool:
        """Add a fade-out to an item."""
        return self.advanced_items.fade_out(track_index, item_index, fade_length, fade_curve)

    def crossfade_items(self, track_index: int, item1_index: int, item2_index: int, crossfade_length: float) -> bool:
        """Create a crossfade between two items."""
        return self.advanced_items.crossfade_items(track_index, item1_index, item2_index, crossfade_length)



    def reverse_item(self, track_index: int, item_index: int) -> bool:
        """Reverse an item."""
        return self.advanced_items.reverse_item(track_index, item_index)

    def get_item_fade_info(self, track_index: int, item_index: int) -> Dict[str, Any]:
        """Get fade information for an item."""
        return self.advanced_items.get_item_fade_info(track_index, item_index)

    # Track Mixing Controls
    def set_track_volume(self, track_index: int, volume_db: float) -> bool:
        """Set the volume of a track in dB."""
        return self.track.set_track_volume(track_index, volume_db)

    def get_track_volume(self, track_index: int) -> float:
        """Get the volume of a track in dB."""
        return self.track.get_track_volume(track_index)

    def set_track_pan(self, track_index: int, pan: float) -> bool:
        """Set the pan position of a track."""
        return self.track.set_track_pan(track_index, pan)

    def get_track_pan(self, track_index: int) -> float:
        """Get the pan position of a track."""
        return self.track.get_track_pan(track_index)

    def set_track_mute(self, track_index: int, mute: bool) -> bool:
        """Set the mute state of a track."""
        return self.track.set_track_mute(track_index, mute)

    def get_track_mute(self, track_index: int) -> bool:
        """Get the mute state of a track."""
        return self.track.get_track_mute(track_index)

    def set_track_solo(self, track_index: int, solo: bool) -> bool:
        """Set the solo state of a track."""
        return self.track.set_track_solo(track_index, solo)

    def get_track_solo(self, track_index: int) -> bool:
        """Get the solo state of a track."""
        return self.track.get_track_solo(track_index)

    def toggle_track_mute(self, track_index: int) -> bool:
        """Toggle the mute state of a track."""
        return self.track.toggle_track_mute(track_index)

    def toggle_track_solo(self, track_index: int) -> bool:
        """Toggle the solo state of a track."""
        return self.track.toggle_track_solo(track_index)

    def set_track_arm(self, track_index: int, arm: bool) -> bool:
        """Set the record arm state of a track."""
        return self.track.set_track_arm(track_index, arm)

    def get_track_arm(self, track_index: int) -> bool:
        """Get the record arm state of a track."""
        return self.track.get_track_arm(track_index)

    # Dynamics Processing Controls
    def set_compressor_params(self, track_index: int, fx_index: int, 
                             threshold: Optional[float] = None,
                             ratio: Optional[float] = None,
                             attack: Optional[float] = None,
                             release: Optional[float] = None,
                             makeup_gain: Optional[float] = None) -> bool:
        """Set common compressor parameters."""
        return self.fx.set_compressor_params(track_index, fx_index, threshold, ratio, attack, release, makeup_gain)

    def set_limiter_params(self, track_index: int, fx_index: int,
                          threshold: Optional[float] = None,
                          ceiling: Optional[float] = None,
                          release: Optional[float] = None) -> bool:
        """Set common limiter parameters."""
        return self.fx.set_limiter_params(track_index, fx_index, threshold, ceiling, release)

    # Meter Reading
    def get_track_peak_level(self, track_index: int) -> Dict[str, float]:
        """Get the current peak levels for a track."""
        return self.fx.get_track_peak_level(track_index)

    def get_master_peak_level(self) -> Dict[str, float]:
        """Get the current peak levels for the master track."""
        return self.fx.get_master_peak_level()

# Re-export the ReaperController class for backward compatibility
__all__ = ['ReaperController']
