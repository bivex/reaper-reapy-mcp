import logging
from typing import Optional
import sys
import os

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from utils.reapy_utils import get_reapy


class TrackController:
    """Controller for track-related operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)

    def create_track(self, name: Optional[str] = None) -> int:
        """
        Create a new track in Reaper.
        
        Args:
            name (str, optional): Name for the new track
            
        Returns:
            int: Index of the created track
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.add_track()
            if name:
                track.name = name
            return track.index

        except Exception as e:
            error_message = f"Failed to create track: {e}"
            self.logger.error(error_message)
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
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            track.name = new_name
            return True

        except Exception as e:
            error_message = f"Failed to rename track: {e}"
            self.logger.error(error_message)
            return False

    def get_track_count(self) -> int:
        """Get the number of tracks in the project."""
        try:
            reapy = get_reapy()
            project = reapy.Project()
            return len(project.tracks)

        except Exception as e:
            self.logger.error(f"Failed to get track count: {e}")
            return 0
            
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
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            # Convert hex color to RGB
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            track.color = (r, g, b)
            return True

        except Exception as e:
            error_message = f"Failed to set track color: {e}"
            self.logger.error(error_message)
            return False

    def get_track_color(self, track_index: int) -> str:
        """Get the color of a track."""
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            r, g, b = track.color
            # Return uppercase hex color to match expected format in tests
            return f"#{r:02X}{g:02X}{b:02X}"
            
        except Exception as e:
            self.logger.error(f"Failed to get track color: {e}")
            return "#000000"

    def set_track_volume(self, track_index: int, volume_db: float) -> bool:
        """
        Set the volume of a track in dB.
        
        Args:
            track_index (int): Index of the track
            volume_db (float): Volume in dB (-inf to +12dB typical range)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Convert dB to linear volume (REAPER uses linear 0.0 to ~3.98 for +12dB)
            if volume_db <= -150:  # Treat as -inf dB
                linear_volume = 0.0
            else:
                linear_volume = 10 ** (volume_db / 20.0)
            
            # Set volume using ReaScript API for more precise control
            reapy.reascript_api.SetMediaTrackInfo_Value(track.id, "D_VOL", linear_volume)
            
            self.logger.info(f"Set track {track_index} volume to {volume_db} dB")
            return True
            
        except Exception as e:
            error_message = f"Failed to set track volume: {e}"
            self.logger.error(error_message)
            return False

    def get_track_volume(self, track_index: int) -> float:
        """
        Get the volume of a track in dB.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            float: Volume in dB
        """
        try:
            import math
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Get linear volume from ReaScript API
            linear_volume = reapy.reascript_api.GetMediaTrackInfo_Value(track.id, "D_VOL")
            
            # Convert linear to dB
            if linear_volume <= 0.0:
                volume_db = -150.0  # Represent -inf dB as -150
            else:
                volume_db = 20.0 * math.log10(linear_volume)
            
            return volume_db
            
        except Exception as e:
            self.logger.error(f"Failed to get track volume: {e}")
            return 0.0

    def set_track_pan(self, track_index: int, pan: float) -> bool:
        """
        Set the pan position of a track.
        
        Args:
            track_index (int): Index of the track
            pan (float): Pan position (-1.0 = hard left, 0.0 = center, 1.0 = hard right)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Clamp pan value to valid range
            pan = max(-1.0, min(1.0, pan))
            
            # Set pan using ReaScript API
            reapy.reascript_api.SetMediaTrackInfo_Value(track.id, "D_PAN", pan)
            
            self.logger.info(f"Set track {track_index} pan to {pan}")
            return True
            
        except Exception as e:
            error_message = f"Failed to set track pan: {e}"
            self.logger.error(error_message)
            return False

    def get_track_pan(self, track_index: int) -> float:
        """
        Get the pan position of a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            float: Pan position (-1.0 to 1.0)
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Get pan from ReaScript API
            pan = reapy.reascript_api.GetMediaTrackInfo_Value(track.id, "D_PAN")
            return pan
            
        except Exception as e:
            self.logger.error(f"Failed to get track pan: {e}")
            return 0.0

    def set_track_mute(self, track_index: int, mute: bool) -> bool:
        """
        Set the mute state of a track.
        
        Args:
            track_index (int): Index of the track
            mute (bool): True to mute, False to unmute
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Set mute using ReaScript API (1 = muted, 0 = unmuted)
            mute_value = 1 if mute else 0
            reapy.reascript_api.SetMediaTrackInfo_Value(track.id, "B_MUTE", mute_value)
            
            state = "muted" if mute else "unmuted"
            self.logger.info(f"Track {track_index} {state}")
            return True
            
        except Exception as e:
            error_message = f"Failed to set track mute: {e}"
            self.logger.error(error_message)
            return False

    def get_track_mute(self, track_index: int) -> bool:
        """
        Get the mute state of a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            bool: True if muted, False if not muted
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Get mute state from ReaScript API
            mute_value = reapy.reascript_api.GetMediaTrackInfo_Value(track.id, "B_MUTE")
            return bool(mute_value)
            
        except Exception as e:
            self.logger.error(f"Failed to get track mute state: {e}")
            return False

    def set_track_solo(self, track_index: int, solo: bool) -> bool:
        """
        Set the solo state of a track.
        
        Args:
            track_index (int): Index of the track
            solo (bool): True to solo, False to unsolo
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Set solo using ReaScript API (1 = soloed, 0 = not soloed)
            solo_value = 1 if solo else 0
            reapy.reascript_api.SetMediaTrackInfo_Value(track.id, "I_SOLO", solo_value)
            
            state = "soloed" if solo else "unsoloed"
            self.logger.info(f"Track {track_index} {state}")
            return True
            
        except Exception as e:
            error_message = f"Failed to set track solo: {e}"
            self.logger.error(error_message)
            return False

    def get_track_solo(self, track_index: int) -> bool:
        """
        Get the solo state of a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            bool: True if soloed, False if not soloed
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Get solo state from ReaScript API
            solo_value = reapy.reascript_api.GetMediaTrackInfo_Value(track.id, "I_SOLO")
            return bool(solo_value)
            
        except Exception as e:
            self.logger.error(f"Failed to get track solo state: {e}")
            return False

    def toggle_track_mute(self, track_index: int) -> bool:
        """
        Toggle the mute state of a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_mute = self.get_track_mute(track_index)
            return self.set_track_mute(track_index, not current_mute)
            
        except Exception as e:
            error_message = f"Failed to toggle track mute: {e}"
            self.logger.error(error_message)
            return False

    def toggle_track_solo(self, track_index: int) -> bool:
        """
        Toggle the solo state of a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            current_solo = self.get_track_solo(track_index)
            return self.set_track_solo(track_index, not current_solo)
            
        except Exception as e:
            error_message = f"Failed to toggle track solo: {e}"
            self.logger.error(error_message)
            return False

    def set_track_arm(self, track_index: int, arm: bool) -> bool:
        """
        Set the record arm state of a track.
        
        Args:
            track_index (int): Index of the track
            arm (bool): True to arm for recording, False to disarm
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Set record arm using ReaScript API (1 = armed, 0 = disarmed)
            arm_value = 1 if arm else 0
            reapy.reascript_api.SetMediaTrackInfo_Value(track.id, "I_RECARM", arm_value)
            
            state = "armed" if arm else "disarmed"
            self.logger.info(f"Track {track_index} record {state}")
            return True
            
        except Exception as e:
            error_message = f"Failed to set track record arm: {e}"
            self.logger.error(error_message)
            return False

    def get_track_arm(self, track_index: int) -> bool:
        """
        Get the record arm state of a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            bool: True if armed for recording, False if disarmed
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Get record arm state from ReaScript API
            arm_value = reapy.reascript_api.GetMediaTrackInfo_Value(track.id, "I_RECARM")
            return bool(arm_value)
            
        except Exception as e:
            self.logger.error(f"Failed to get track record arm state: {e}")
            return False
