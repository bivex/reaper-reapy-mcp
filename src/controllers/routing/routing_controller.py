import logging
from typing import Optional, List, Dict, Any, Union, TYPE_CHECKING

if TYPE_CHECKING:
    import reapy
from dataclasses import dataclass


@dataclass
class SendInfo:
    """Data class to hold send information."""
    send_id: int
    source_track: int
    destination_track: int
    volume: float
    pan: float
    mute: bool
    phase: bool
    channels: int


@dataclass
class ReceiveInfo:
    """Data class to hold receive information."""
    receive_id: int
    source_track: int
    destination_track: int
    volume: float
    pan: float
    mute: bool
    phase: bool
    channels: int


import logging
from typing import Optional, List, Dict, Any
import sys
import os

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from src.core.reapy_bridge import get_reapy


class RoutingController:
    """Controller for routing-related operations in Reaper."""

    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
        
        # Initialize RPR reference
        try:
            reapy = get_reapy()
            self._RPR = reapy.RPR
        except Exception as e:
            self.logger.error(f"Failed to initialize RPR: {e}")
            self._RPR = None
    def _validate_track_index(self, track_index: int) -> bool:
        """Validate that a track index is within valid range."""
        try:
            track_index = int(track_index)
            if track_index < 0:
                return False
                
            reapy = get_reapy()
            project = reapy.Project()
            num_tracks = len(project.tracks)
            return track_index < num_tracks
        except Exception as e:
            self.logger.error(f"Failed to validate track index: {e}")
            return False

    def _get_track(self, track_index: int) -> Optional['reapy.Track']:
        """Get a track by index with validation."""
        if not self._validate_track_index(track_index):
            return None
            
        try:
            reapy = get_reapy()
            return reapy.Project().tracks[track_index]
        except Exception as e:
            self.logger.error(f"Failed to get track {track_index}: {e}")
            return None

    def add_send(self, source_track: int, destination_track: int, 
                 volume: float = 0.0, pan: float = 0.0, 
                 mute: bool = False, phase: bool = False, 
                 channels: int = None) -> Optional[int]:
        """
        Add a send from source track to destination track.
        
        Args:
            source_track (int): Index of the source track
            destination_track (int): Index of the destination track
            volume (float): Send volume (dB)
            pan (float): Send pan (-1.0 to 1.0)
            mute (bool): Whether the send is muted
            phase (bool): Whether to invert phase
            channels (int): Number of channels (1=mono, 2=stereo)
            
        Returns:
            Optional[int]: Send ID if successful, None if failed
        """
        from ...constants import DEFAULT_STEREO_CHANNELS
        if channels is None:
            channels = DEFAULT_STEREO_CHANNELS
            
        try:
            source = self._get_track(source_track)
            destination = self._get_track(destination_track)
            
            if source is None or destination is None:
                self.logger.error(f"Failed to get tracks: source={source_track}, destination={destination_track}")
                return None

            self.logger.info(f"Attempting to add send from track {source_track} to track {destination_track}")
            self.logger.info(f"Source track: {source.name}, Destination track: {destination.name}")

            # Try using ReaScript API directly
            reapy = get_reapy()
            RPR = reapy.RPR
            
            # Add send using ReaScript API
            send_id = RPR.CreateTrackSend(source.id, destination.id)
            if send_id < 0:
                self.logger.error(f"Failed to create send using ReaScript API: {send_id}")
                return None

            # Configure send parameters using ReaScript API
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "D_VOL", volume)
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "D_PAN", pan)
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "B_MUTE", 1 if mute else 0)
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "B_PHASE", 1 if phase else 0)
            RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "I_SRCCHAN", channels)

            self.logger.info(f"Added send from track {source_track} to track {destination_track} with ID {send_id}")
            
            # Verify the send was created by immediately checking
            RPR.UpdateArrange()
            verify_count = RPR.GetTrackNumSends(source.id, 0)
            self.logger.info(f"After creation: Track {source_track} now has {verify_count} sends")
            
            # Try to read back the send we just created
            if send_id >= 0 and send_id < verify_count:
                verify_dest = RPR.GetTrackSendInfo_Value(source.id, 0, send_id, "P_DESTTRACK")
                verify_vol = RPR.GetTrackSendInfo_Value(source.id, 0, send_id, "D_VOL")
                self.logger.info(f"Verification - Send {send_id}: dest_ptr={verify_dest}, volume={verify_vol}")
            
            return send_id

        except Exception as e:
            self.logger.error(f"Failed to add send: {e}")
            return None

    def remove_send(self, source_track: int, send_id: int) -> bool:
        """
        Remove a send from a track.
        
        Args:
            source_track (int): Index of the source track
            send_id (int): ID of the send to remove
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source = self._get_track(source_track)
            if source is None:
                return False

            # Use ReaScript API to remove send
            reapy = get_reapy()
            RPR = reapy.RPR
            
            # Remove send using ReaScript API
            result = RPR.RemoveTrackSend(source.id, 0, send_id)  # 0 for sends, 1 for receives
            
            if result:
                self.logger.info(f"Removed send {send_id} from track {source_track}")
                return True
            else:
                self.logger.warning(f"Send {send_id} not found on track {source_track}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to remove send: {e}")
            return False

    def get_sends(self, track_index: int) -> List[SendInfo]:
        """
        Get all sends from a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            List[SendInfo]: List of send information
        """
        try:
            track = self._get_track(track_index)
            if track is None:
                return []

            # Use ReaScript API to get sends
            reapy = get_reapy()
            RPR = reapy.RPR
            
            # Force REAPER to update
            RPR.UpdateArrange()
            
            sends = []
            send_count = RPR.GetTrackNumSends(track.id, 0)  # 0 for sends, 1 for receives
            
            self.logger.info(f"Track {track_index} (ID: {track.id}): Found {send_count} sends")
            
            for i in range(send_count):
                try:
                    # Get destination track pointer
                    dest_track_pointer = RPR.GetTrackSendInfo_Value(track.id, 0, i, "P_DESTTRACK")
                    
                    # Get destination track index by scanning all tracks
                    dest_track_index = -1
                    
                    # Handle MediaTrack pointer format: "(MediaTrack*)0x0000000006D01200"
                    if isinstance(dest_track_pointer, str) and dest_track_pointer.startswith("(MediaTrack*)0x"):
                        # Extract hex value and convert to int
                        hex_value = dest_track_pointer.replace("(MediaTrack*)0x", "")
                        dest_track_ptr_int = int(hex_value, 16)
                    elif isinstance(dest_track_pointer, (int, float)):
                        dest_track_ptr_int = int(dest_track_pointer)
                    else:
                        dest_track_ptr_int = 0
                    
                    if dest_track_ptr_int != 0:
                        # Scan all tracks to find the matching one
                        reapy = get_reapy()
                        project = reapy.Project()
                        for idx, project_track in enumerate(project.tracks):
                            # Convert project track ID to int for comparison
                            project_track_id_int = 0
                            if isinstance(project_track.id, str) and project_track.id.startswith("(MediaTrack*)0x"):
                                hex_value = project_track.id.replace("(MediaTrack*)0x", "")
                                project_track_id_int = int(hex_value, 16)
                            elif isinstance(project_track.id, (int, float)):
                                project_track_id_int = int(project_track.id)
                            
                            if project_track_id_int == dest_track_ptr_int:
                                dest_track_index = idx
                                break
                    
                    # If we still don't have a valid index, use -1 (unknown)
                    if dest_track_index == -1:
                        self.logger.debug(f"Could not determine destination track index for send {i}, using -1")
                        dest_track_index = -1
                    
                    volume = RPR.GetTrackSendInfo_Value(track.id, 0, i, "D_VOL")
                    pan = RPR.GetTrackSendInfo_Value(track.id, 0, i, "D_PAN")
                    mute = bool(RPR.GetTrackSendInfo_Value(track.id, 0, i, "B_MUTE"))
                    phase = bool(RPR.GetTrackSendInfo_Value(track.id, 0, i, "B_PHASE"))
                    channels = int(RPR.GetTrackSendInfo_Value(track.id, 0, i, "I_SRCCHAN"))
                    
                    send_info = SendInfo(
                        send_id=i,
                        source_track=track_index,
                        destination_track=dest_track_index,
                        volume=volume,
                        pan=pan,
                        mute=mute,
                        phase=phase,
                        channels=channels
                    )
                    sends.append(send_info)
                    self.logger.debug(f"Send {i}: {track_index} -> {dest_track_index}, vol={volume}, pan={pan}, mute={mute}")
                    
                except Exception as send_error:
                    self.logger.error(f"Failed to get send {i}: {send_error}")

            self.logger.info(f"Successfully processed {len(sends)} sends on track {track_index}")
            return sends

        except Exception as e:
            self.logger.error(f"Failed to get sends: {e}")
            return []

    def get_receives(self, track_index: int) -> List[ReceiveInfo]:
        """
        Get all receives on a track by scanning all tracks for sends to this track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            List[ReceiveInfo]: List of receive information
        """
        try:
            target_track = self._get_track(track_index)
            if target_track is None:
                return []

            # Use ReaScript API
            reapy = get_reapy()
            RPR = reapy.RPR
            
            # Force REAPER to update
            RPR.UpdateArrange()
            
            receives = []
            reapy = get_reapy()
            project = reapy.Project()
            
            self.logger.info(f"Scanning all tracks for sends to track {track_index} (target track ID: {target_track.id})")
            
            # Convert target track ID to int for comparison
            target_track_id_int = 0
            if isinstance(target_track.id, str) and target_track.id.startswith("(MediaTrack*)0x"):
                hex_value = target_track.id.replace("(MediaTrack*)0x", "")
                target_track_id_int = int(hex_value, 16)
            elif isinstance(target_track.id, (int, float)):
                target_track_id_int = int(target_track.id)
            
            # Scan all tracks for sends to our target track
            for source_idx, source_track in enumerate(project.tracks):
                try:
                    send_count = RPR.GetTrackNumSends(source_track.id, 0)  # 0 for sends
                    
                    for send_idx in range(send_count):
                        try:
                            # Get destination track of this send
                            dest_track_pointer = RPR.GetTrackSendInfo_Value(source_track.id, 0, send_idx, "P_DESTTRACK")
                            
                            # Convert destination track pointer to int for comparison
                            dest_track_ptr_int = 0
                            if isinstance(dest_track_pointer, str) and dest_track_pointer.startswith("(MediaTrack*)0x"):
                                hex_value = dest_track_pointer.replace("(MediaTrack*)0x", "")
                                dest_track_ptr_int = int(hex_value, 16)
                            elif isinstance(dest_track_pointer, (int, float)):
                                dest_track_ptr_int = int(dest_track_pointer)
                            
                            # Check if this send goes to our target track
                            if dest_track_ptr_int == target_track_id_int:
                                # This is a receive for our target track
                                volume = RPR.GetTrackSendInfo_Value(source_track.id, 0, send_idx, "D_VOL")
                                pan = RPR.GetTrackSendInfo_Value(source_track.id, 0, send_idx, "D_PAN")
                                mute = bool(RPR.GetTrackSendInfo_Value(source_track.id, 0, send_idx, "B_MUTE"))
                                phase = bool(RPR.GetTrackSendInfo_Value(source_track.id, 0, send_idx, "B_PHASE"))
                                channels = int(RPR.GetTrackSendInfo_Value(source_track.id, 0, send_idx, "I_SRCCHAN"))
                                
                                receive_info = ReceiveInfo(
                                    receive_id=len(receives),  # Sequential receive ID
                                    source_track=source_idx,
                                    destination_track=track_index,
                                    volume=volume,
                                    pan=pan,
                                    mute=mute,
                                    phase=phase,
                                    channels=channels
                                )
                                receives.append(receive_info)
                                self.logger.debug(f"Found receive: Track {source_idx} -> Track {track_index}, vol={volume}, pan={pan}, mute={mute}")
                                
                        except Exception as send_error:
                            self.logger.debug(f"Error checking send {send_idx} on track {source_idx}: {send_error}")
                            
                except Exception as track_error:
                    self.logger.debug(f"Error scanning track {source_idx}: {track_error}")

            self.logger.info(f"Found {len(receives)} receives for track {track_index}")
            return receives

        except Exception as e:
            self.logger.error(f"Failed to get receives: {e}")
            return []

    def debug_track_routing(self, track_index: int) -> Dict[str, Any]:
        """
        Debug function to analyze track routing in detail.
        
        Args:
            track_index (int): Index of the track to debug
        
        Returns:
            Dict containing detailed routing information
        """
        try:
            track = self._get_track(track_index)
            if track is None:
                return {"error": f"Track {track_index} not found"}

            reapy = get_reapy()
            RPR = reapy.RPR
            
            # Force update
            RPR.UpdateArrange()
            
            debug_info = {
                "track_index": track_index,
                "track_id": track.id,
                "track_name": getattr(track, 'name', 'Unknown'),
                "sends": [],
                "receives": [],
                "raw_send_count": RPR.GetTrackNumSends(track.id, 0),
                "raw_receive_count": RPR.GetTrackNumSends(track.id, 1),
            }
            
            # Debug sends
            send_count = RPR.GetTrackNumSends(track.id, 0)
            self.logger.info(f"DEBUG: Track {track_index} has {send_count} sends (raw)")
            
            for i in range(send_count):
                try:
                    dest_ptr = RPR.GetTrackSendInfo_Value(track.id, 0, i, "P_DESTTRACK")
                    volume = RPR.GetTrackSendInfo_Value(track.id, 0, i, "D_VOL")
                    pan = RPR.GetTrackSendInfo_Value(track.id, 0, i, "D_PAN")
                    
                    send_debug = {
                        "send_id": i,
                        "dest_pointer": dest_ptr,
                        "dest_pointer_int": int(dest_ptr) if dest_ptr else 0,
                        "volume": volume,
                        "pan": pan
                    }
                    debug_info["sends"].append(send_debug)
                    
                except Exception as send_err:
                    debug_info["sends"].append({"send_id": i, "error": str(send_err)})
            
            return debug_info
            
        except Exception as e:
            return {"error": str(e)}

    def set_send_volume(self, source_track: int, send_id: int, volume: float) -> bool:
        """
        Set the volume of a send.
        
        Args:
            source_track (int): Index of the source track
            send_id (int): ID of the send
            volume (float): Volume in dB
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source = self._get_track(source_track)
            if source is None:
                return False

            # Use ReaScript API to set send volume
            reapy = get_reapy()
            RPR = reapy.RPR
            
            result = RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "D_VOL", volume)
            
            if result:
                self.logger.info(f"Set send {send_id} volume to {volume} dB")
                return True
            else:
                self.logger.warning(f"Send {send_id} not found on track {source_track}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to set send volume: {e}")
            return False

    def set_send_pan(self, source_track: int, send_id: int, pan: float) -> bool:
        """
        Set the pan of a send.
        
        Args:
            source_track (int): Index of the source track
            send_id (int): ID of the send
            pan (float): Pan value (-1.0 to 1.0)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source = self._get_track(source_track)
            if source is None:
                return False

            # Use ReaScript API to set send pan
            reapy = get_reapy()
            RPR = reapy.RPR
            
            result = RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "D_PAN", pan)
            
            if result:
                self.logger.info(f"Set send {send_id} pan to {pan}")
                return True
            else:
                self.logger.warning(f"Send {send_id} not found on track {source_track}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to set send pan: {e}")
            return False

    def toggle_send_mute(self, source_track: int, send_id: int, mute: Optional[bool] = None) -> bool:
        """
        Toggle or set the mute state of a send.
        
        Args:
            source_track (int): Index of the source track
            send_id (int): ID of the send
            mute (bool, optional): Mute state to set. If None, toggles current state
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            source = self._get_track(source_track)
            if source is None:
                return False

            # Use ReaScript API to toggle/set send mute
            reapy = get_reapy()
            RPR = reapy.RPR
            
            if mute is None:
                # Toggle current state
                current_mute = RPR.GetTrackSendInfo_Value(source.id, 0, send_id, "B_MUTE")
                mute = not bool(current_mute)
            
            result = RPR.SetTrackSendInfo_Value(source.id, 0, send_id, "B_MUTE", 1 if mute else 0)
            
            if result:
                self.logger.info(f"Set send {send_id} mute to {mute}")
                return True
            else:
                self.logger.warning(f"Send {send_id} not found on track {source_track}")
                return False

        except Exception as e:
            self.logger.error(f"Failed to toggle send mute: {e}")
            return False

    def get_track_routing_info(self, track_index: int) -> Dict[str, Any]:
        """
        Get comprehensive routing information for a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            Dict[str, Any]: Routing information including sends, receives, and track properties
        """
        try:
            track = self._get_track(track_index)
            if track is None:
                return {}

            sends = self.get_sends(track_index)
            receives = self.get_receives(track_index)

            routing_info = {
                "track_index": track_index,
                "track_name": track.name,
                "sends": [vars(send) for send in sends],
                "receives": [vars(receive) for receive in receives],
                "send_count": len(sends),
                "receive_count": len(receives)
            }

            self.logger.info(f"Retrieved routing info for track {track_index}")
            return routing_info

        except Exception as e:
            self.logger.error(f"Failed to get track routing info: {e}")
            return {}

    def clear_all_sends(self, track_index: int) -> bool:
        """
        Remove all sends from a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            track = self._get_track(track_index)
            if track is None:
                return False

            # Use ReaScript API to clear all sends
            reapy = get_reapy()
            RPR = reapy.RPR
            
            send_count = RPR.GetTrackNumSends(track.id, 0)  # 0 for sends
            
            # Remove sends in reverse order to avoid index shifting
            for i in range(send_count - 1, -1, -1):
                RPR.RemoveTrackSend(track.id, 0, i)

            self.logger.info(f"Cleared {send_count} sends from track {track_index}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear sends: {e}")
            return False

    def clear_all_receives(self, track_index: int) -> bool:
        """
        Remove all receives from a track.
        
        Args:
            track_index (int): Index of the track
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            track = self._get_track(track_index)
            if track is None:
                return False

            # Use ReaScript API to clear all receives
            reapy = get_reapy()
            RPR = reapy.RPR
            
            receive_count = RPR.GetTrackNumSends(track.id, 1)  # 1 for receives
            
            # Remove receives in reverse order to avoid index shifting
            for i in range(receive_count - 1, -1, -1):
                RPR.RemoveTrackSend(track.id, 1, i)

            self.logger.info(f"Cleared {receive_count} receives from track {track_index}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear receives: {e}")
            return False 
