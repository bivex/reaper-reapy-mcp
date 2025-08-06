import logging
from typing import Dict, Any, List, Optional, Tuple


import logging
from typing import Optional, List, Dict, Any
import sys
import os

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from src.core.reapy_bridge import get_reapy


class AutomationController:
    """Controller for automation and modulation operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
    def create_automation_envelope(self, track_index: int, envelope_name: str) -> int:
        """
        Create an automation envelope on a track.
        
        Args:
            track_index (int): Index of the track
            envelope_name (str): Name of the envelope (e.g., "Volume", "Pan", "Mute")
            
        Returns:
            int: Envelope index, or -1 if failed
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return -1
            
            track = project.tracks[track_index]
            
            # Map envelope names to REAPER envelope types
            envelope_map = {
                "volume": "VOLENV",
                "pan": "PANENV", 
                "mute": "MUTEENV",
                "width": "WIDTHENV",
                "send_volume": "SENDVOLENV",
                "send_pan": "SENDPANENV"
            }
            
            envelope_type = envelope_map.get(envelope_name.lower(), "VOLENV")
            
            # Create the envelope using the correct API function
            # First try to get existing envelope
            envelope_index = self._RPR.GetTrackEnvelopeByName(track.id, envelope_type)
            
            if envelope_index == -1:
                # Create new envelope if it doesn't exist
                envelope_index = self._RPR.InsertEnvelope(track.id, envelope_type, True, True, 0, 0, 0)
            
            self.logger.info(f"Created automation envelope '{envelope_name}' on track {track_index}")
            return envelope_index
            
        except Exception as e:
            self.logger.error(f"Failed to create automation envelope: {e}")
            return -1

    def add_automation_point(self, track_index: int, envelope_name: str, time: float, value: float, shape: int = 0) -> bool:
        """
        Add an automation point to an envelope.
        
        Args:
            track_index (int): Index of the track
            envelope_name (str): Name of the envelope
            time (float): Time position in seconds
            value (float): Automation value
            shape (int): Point shape (0=linear, 1=square, 2=slow start/end, 3=fast start, 4=fast end, 5=bezier)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return False
            
            track = project.tracks[track_index]
            
            # Get envelope
            envelope_map = {
                "volume": "VOLENV",
                "pan": "PANENV", 
                "mute": "MUTEENV",
                "width": "WIDTHENV",
                "send_volume": "SENDVOLENV",
                "send_pan": "SENDPANENV"
            }
            
            envelope_type = envelope_map.get(envelope_name.lower(), "VOLENV")
            envelope = self._RPR.GetTrackEnvelopeByName(track.id, envelope_type)
            
            if envelope == -1:
                self.logger.error(f"Envelope '{envelope_name}' not found on track {track_index}")
                return False
            
            # Add automation point using the correct API function
            point_index = self._RPR.InsertEnvelopePoint(envelope, time, value, shape, 0, False, True)
            
            self.logger.info(f"Added automation point at {time}s with value {value} on track {track_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add automation point: {e}")
            return False

    def get_automation_points(self, track_index: int, envelope_name: str) -> List[Dict[str, Any]]:
        """
        Get all automation points from an envelope.
        
        Args:
            track_index (int): Index of the track
            envelope_name (str): Name of the envelope
            
        Returns:
            List[Dict[str, Any]]: List of automation points with time, value, and shape
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return []
            
            track = project.tracks[track_index]
            
            # Get envelope
            envelope_map = {
                "volume": "VOLENV",
                "pan": "PANENV", 
                "mute": "MUTEENV",
                "width": "WIDTHENV",
                "send_volume": "SENDVOLENV",
                "send_pan": "SENDPANENV"
            }
            
            envelope_type = envelope_map.get(envelope_name.lower(), "VOLENV")
            envelope = self._RPR.GetTrackEnvelopeByName(track.id, envelope_type)
            
            if envelope == -1:
                self.logger.error(f"Envelope '{envelope_name}' not found on track {track_index}")
                return []
            
            points = []
            point_count = self._RPR.CountEnvelopePoints(envelope)
            
            for i in range(point_count):
                retval, time, value, shape, tension, selected = self._RPR.GetEnvelopePoint(envelope, i)
                
                if retval:
                    points.append({
                        "index": i,
                        "time": time,
                        "value": value,
                        "shape": shape,
                        "tension": tension,
                        "selected": selected
                    })
            
            self.logger.info(f"Retrieved {len(points)} automation points from track {track_index}")
            return points
            
        except Exception as e:
            self.logger.error(f"Failed to get automation points: {e}")
            return []

    def set_automation_mode(self, track_index: int, mode: str) -> bool:
        """
        Set the automation mode for a track.
        
        Args:
            track_index (int): Index of the track
            mode (str): Automation mode ("read", "write", "touch", "latch", "trim")
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return False
            
            track = project.tracks[track_index]
            
            # Map mode names to REAPER automation modes
            mode_map = {
                "read": 0,
                "write": 1,
                "touch": 2,
                "latch": 3,
                "trim": 4
            }
            
            automation_mode = mode_map.get(mode.lower(), 0)
            
            # Set automation mode
            self._RPR.SetTrackAutomationMode(track.id, automation_mode)
            
            self.logger.info(f"Set automation mode to '{mode}' on track {track_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set automation mode: {e}")
            return False

    def get_automation_mode(self, track_index: int) -> str:
        """
        Get the current automation mode for a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            str: Current automation mode
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return "read"
            
            track = project.tracks[track_index]
            
            # Get automation mode
            mode = self._RPR.GetTrackAutomationMode(track.id)
            
            # Map mode numbers to names
            mode_names = ["read", "write", "touch", "latch", "trim"]
            mode_name = mode_names[mode] if 0 <= mode < len(mode_names) else "read"
            
            return mode_name
            
        except Exception as e:
            self.logger.error(f"Failed to get automation mode: {e}")
            return "read"

    def delete_automation_point(self, track_index: int, envelope_name: str, point_index: int) -> bool:
        """
        Delete an automation point from an envelope.
        
        Args:
            track_index (int): Index of the track
            envelope_name (str): Name of the envelope
            point_index (int): Index of the point to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return False
            
            track = project.tracks[track_index]
            
            # Get envelope
            envelope_map = {
                "volume": "VOLENV",
                "pan": "PANENV", 
                "mute": "MUTEENV",
                "width": "WIDTHENV",
                "send_volume": "SENDVOLENV",
                "send_pan": "SENDPANENV"
            }
            
            envelope_type = envelope_map.get(envelope_name.lower(), "VOLENV")
            envelope = self._RPR.GetTrackEnvelopeByName(track.id, envelope_type)
            
            if envelope == -1:
                self.logger.error(f"Envelope '{envelope_name}' not found on track {track_index}")
                return False
            
            # Delete the point using the correct API function
            success = self._RPR.DeleteEnvelopePointEx(envelope, 0, point_index)  # Use DeleteEnvelopePointEx instead of DeleteEnvelopePoint
            
            if success:
                self.logger.info(f"Deleted automation point {point_index} from track {track_index}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to delete automation point: {e}")
            return False 
        
