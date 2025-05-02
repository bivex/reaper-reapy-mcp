import reapy
import logging
from typing import Optional, List, Dict, Any

class ReaperController:
    """Controller for interacting with Reaper using reapy."""
    
    def __init__(self, debug: bool = False):
        """
        Initialize the Reaper controller.
        
        Args:
            debug (bool): Enable debug logging
        """
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)
        
        # Connect to Reaper
        try:
            reapy.connect()
            self.logger.info("Connected to Reaper")
        except Exception as e:
            self.logger.error(f"Failed to connect to Reaper: {e}")
            raise

    def verify_connection(self) -> bool:
        """Verify connection to Reaper."""
        try:
            project = reapy.Project()
            print("Connected to project:", project.name)
            # TODO correct checker
            # return reapy.is_connected()
            return True
        except Exception as e:
            self.logger.error(f"Connection verification failed: {e}")
            return False

    def create_track(self, name: Optional[str] = None) -> int:
        """
        Create a new track in Reaper.
        
        Args:
            name (str, optional): Name for the new track
            
        Returns:
            int: Index of the created track
        """
        try:
            project = reapy.Project()
            track = project.add_track()
            if name:
                track.name = name
            return track.index
        except Exception as e:
            self.logger.error(f"Failed to create track: {e}")
            raise

    def rename_track(self, track_index: int, new_name: str) -> bool:
        """
        Rename an existing track.
        
        Args:
            track_index (int): Index of the track to rename
            new_name (str): New name for the track
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            track.name = new_name
            return True
        except Exception as e:
            self.logger.error(f"Failed to rename track: {e}")
            return False

    def get_track_count(self) -> int:
        """Get the number of tracks in the project."""
        try:
            project = reapy.Project()
            return len(project.tracks)
        except Exception as e:
            self.logger.error(f"Failed to get track count: {e}")
            return 0

    def set_tempo(self, bpm: float) -> bool:
        """
        Set the project tempo.
        
        Args:
            bpm (float): Tempo in beats per minute
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            project.bpm = bpm
            return True
        except Exception as e:
            self.logger.error(f"Failed to set tempo: {e}")
            return False

    def get_tempo(self) -> float:
        """Get the current project tempo."""
        try:
            project = reapy.Project()
            return project.bpm
        except Exception as e:
            self.logger.error(f"Failed to get tempo: {e}")
            return 0.0

    def set_track_color(self, track_index: int, color: str) -> bool:
        """
        Set the color of a track.
        
        Args:
            track_index (int): Index of the track
            color (str): Hex color code (e.g., "#FF0000")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            # Convert hex color to RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            track.color = (r, g, b)
            return True
        except Exception as e:
            self.logger.error(f"Failed to set track color: {e}")
            return False

    def get_track_color(self, track_index: int) -> str:
        """Get the color of a track."""
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            r, g, b = track.color
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception as e:
            self.logger.error(f"Failed to get track color: {e}")
            return ""

    def add_fx(self, track_index: int, fx_name: str) -> int:
        """
        Add an FX to a track.
        
        Args:
            track_index (int): Index of the track
            fx_name (str): Name of the FX to add
            
        Returns:
            int: Index of the added FX
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.add_fx(fx_name)
            return fx.index
        except Exception as e:
            self.logger.error(f"Failed to add FX: {e}")
            return -1

    def remove_fx(self, track_index: int, fx_index: int) -> bool:
        """
        Remove an FX from a track.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            track.remove_fx(fx_index)
            return True
        except Exception as e:
            self.logger.error(f"Failed to remove FX: {e}")
            return False

    def set_fx_param(self, track_index: int, fx_index: int, param_name: str, value: float) -> bool:
        """
        Set an FX parameter value.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            param_name (str): Name of the parameter
            value (float): Value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.fxs[fx_index]
            # Find parameter index by name
            for i, param in enumerate(fx.params):
                if param.name == param_name:
                    param.value = value
                    return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to set FX parameter: {e}")
            return False

    def get_fx_param(self, track_index: int, fx_index: int, param_name: str) -> float:
        """
        Get an FX parameter value.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            param_name (str): Name of the parameter
            
        Returns:
            float: Current value of the parameter
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.fxs[fx_index]
            # Find parameter by name
            for param in fx.params:
                if param.name == param_name:
                    return param.value
            return 0.0
        except Exception as e:
            self.logger.error(f"Failed to get FX parameter: {e}")
            return 0.0

    def toggle_fx(self, track_index: int, fx_index: int, enable: bool = None) -> bool:
        """
        Toggle or set the enable/disable state of an FX.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            enable (bool, optional): True to enable, False to disable, None to toggle
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            fx = track.fxs[fx_index]
            if enable is None:
                fx.enabled = not fx.enabled
            else:
                fx.enabled = enable
            return True
        except Exception as e:
            self.logger.error(f"Failed to toggle FX: {e}")
            return False

    def create_region(self, start_time: float, end_time: float, name: str) -> int:
        """
        Create a region in the project.
        
        Args:
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            name (str): Name of the region
            
        Returns:
            int: Index of the created region
        """
        try:
            project = reapy.Project()
            region = project.add_region(start_time, end_time, name)
            return region.index
        except Exception as e:
            self.logger.error(f"Failed to create region: {e}")
            return -1

    def delete_region(self, region_index: int) -> bool:
        """
        Delete a region from the project.
        
        Args:
            region_index (int): Index of the region to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            region = project.regions[region_index]
            region.delete()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete region: {e}")
            return False

    def create_marker(self, time: float, name: str) -> int:
        """
        Create a marker in the project.
        
        Args:
            time (float): Time position in seconds
            name (str): Name of the marker
            
        Returns:
            int: Index of the created marker
        """
        try:
            project = reapy.Project()
            marker = project.add_marker(time, name)
            return marker.index
        except Exception as e:
            self.logger.error(f"Failed to create marker: {e}")
            return -1

    def delete_marker(self, marker_index: int) -> bool:
        """
        Delete a marker from the project.
        
        Args:
            marker_index (int): Index of the marker to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            marker = project.markers[marker_index]
            marker.delete()
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete marker: {e}")
            return False

    def get_master_track(self) -> Dict[str, Any]:
        """Get information about the master track."""
        try:
            project = reapy.Project()
            master = project.master_track
            return {
                "volume": master.volume,
                "pan": master.pan,
                "mute": master.mute,
                "solo": master.solo
            }
        except Exception as e:
            self.logger.error(f"Failed to get master track info: {e}")
            return {}

    def set_master_volume(self, volume: float) -> bool:
        """
        Set the master track volume.
        
        Args:
            volume (float): Volume level (0.0 to 1.0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            master = project.master_track
            master.volume = volume
            return True
        except Exception as e:
            self.logger.error(f"Failed to set master volume: {e}")
            return False

    def set_master_pan(self, pan: float) -> bool:
        """
        Set the master track pan.
        
        Args:
            pan (float): Pan value (-1.0 to 1.0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            master = project.master_track
            master.pan = pan
            return True
        except Exception as e:
            self.logger.error(f"Failed to set master pan: {e}")
            return False

    def toggle_master_mute(self, mute: bool = None) -> bool:
        """
        Toggle or set the master track mute state.
        
        Args:
            mute (bool, optional): True to mute, False to unmute, None to toggle
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            master = project.master_track
            if mute is None:
                master.mute = not master.mute
            else:
                master.mute = mute
            return True
        except Exception as e:
            self.logger.error(f"Failed to toggle master mute: {e}")
            return False

    def toggle_master_solo(self, solo: bool = None) -> bool:
        """
        Toggle or set the master track solo state.
        
        Args:
            solo (bool, optional): True to solo, False to unsolo, None to toggle
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            master = project.master_track
            if solo is None:
                master.solo = not master.solo
            else:
                master.solo = solo
            return True
        except Exception as e:
            self.logger.error(f"Failed to toggle master solo: {e}")
            return False
