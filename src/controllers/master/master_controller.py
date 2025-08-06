import logging
from typing import Dict, Any, Optional


import logging
from typing import Optional, List, Dict, Any
import sys
import os

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from src.core.reapy_bridge import get_reapy


class MasterController:
    """Controller for master track operations in Reaper."""

    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)

    def get_master_track(self) -> Dict[str, Any]:
        """Get information about the master track."""
        try:
            reapy = get_reapy()
            project = reapy.Project()
            master = project.master_track

            # Use send methods to get volume and pan instead of direct attributes
            # For master track, these are accessed differently in the reapy API
            volume = master.get_info_value("D_VOL")  # Get master volume
            pan = master.get_info_value("D_PAN")  # Get master pan

            # For mute and solo, use the appropriate API calls
            mute = bool(master.get_info_value("B_MUTE"))
            solo = bool(master.get_info_value("I_SOLO"))

            return {"volume": volume, "pan": pan, "mute": mute, "solo": solo}
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
            reapy = get_reapy()
            project = reapy.Project()
            master = project.master_track
            master.volume = volume
            return True
        except Exception as e:
            error_message = f"Failed to set master volume: {e}"
            self.logger.error(error_message)
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
            reapy = get_reapy()
            project = reapy.Project()
            master = project.master_track
            master.pan = pan
            return True
        except Exception as e:
            error_message = f"Failed to set master pan: {e}"
            self.logger.error(error_message)
            return False

    def toggle_master_mute(self, mute: Optional[bool] = None) -> bool:
        """
        Toggle or set the master track mute state.

        Args:
            mute (bool, optional): True to mute, False to unmute, None to toggle

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            master = project.master_track
            if mute is None:
                master.mute = not master.mute
            else:
                master.mute = mute
            return True
        except Exception as e:
            error_message = f"Failed to toggle master mute: {e}"
            self.logger.error(error_message)
            return False

    def toggle_master_solo(self, solo: Optional[bool] = None) -> bool:
        """
        Toggle or set the master track solo state.

        Args:
            solo (bool, optional): True to solo, False to unsolo, None to toggle

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            master = project.master_track
            if solo is None:
                master.solo = not master.solo
            else:
                master.solo = solo
            return True
        except Exception as e:
            error_message = f"Failed to toggle master solo: {e}"
            self.logger.error(error_message)
            return False
