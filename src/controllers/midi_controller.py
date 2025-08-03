import reapy
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass

from .base_controller import BaseController
from src.utils.item_utils import get_item_by_id_or_index, get_item_properties
from src.utils.item_operations import select_item, delete_item

# Constants to replace magic numbers
DEFAULT_MIDI_LENGTH = 4.0
DEFAULT_MIDI_VELOCITY = 96
DEFAULT_MIDI_CHANNEL = 0
MAX_MIDI_PITCH = 127
MIN_MIDI_PITCH = 0
MAX_MIDI_CHANNEL = 15

@dataclass
class MIDINoteParams:
    """Data class to hold MIDI note parameters."""
    pitch: int
    start_time: float
    length: float
    velocity: int = DEFAULT_MIDI_VELOCITY
    channel: int = DEFAULT_MIDI_CHANNEL

class MIDIController:
    """Controller for MIDI-related operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)

    def _validate_track_index(self, track_index: int) -> bool:
        """
        Validate that a track index is within valid range.
        
        Args:
            track_index (int): The track index to validate
            
        Returns:
            bool: True if valid, False if invalid
        """
        try:
            track_index = int(track_index)
            if track_index < 0:
                return False
                
            project = reapy.Project()
            num_tracks = len(project.tracks)
            return track_index < num_tracks
        except Exception as e:
            self.logger.error(
                f"Failed to validate track index: {e}"
            )
            return False
            
    def _get_track(self, track_index: int) -> Optional[reapy.Track]:
        """
        Get a track by index with validation.
        
        Args:
            track_index (int): The track index to get
            
        Returns:
            Optional[reapy.Track]: The track if valid, None if invalid
        """
        if not self._validate_track_index(track_index):
            return None
            
        try:
            return reapy.Project().tracks[track_index]
        except Exception as e:
            self.logger.error(
                f"Failed to get track {track_index}: {e}"
            )
            return None

    def _select_item(self, item: reapy.Item) -> bool:
        """
        Helper function to select an item.
        
        Args:
            item (reapy.Item): The item to select
        
        Returns:
            bool: True if the selection was successful, False otherwise
        """
        return select_item(item)
    
    def create_midi_item(self, track_index: int, start_time: float, 
                        length: float = DEFAULT_MIDI_LENGTH) -> Union[int, str]:
        """
        Create an empty MIDI item on a track.
        
        Args:
            track_index (int): Index of the track to add the MIDI item to
            start_time (float): Start time in seconds
            length (float): Length of the MIDI item in seconds
            
        Returns:
            int or str: Index or ID of the created MIDI item for direct use in add_midi_note
            Returns -1 if creation fails
        """
        try:
            # Convert and validate parameters
            track_index, start_time, length = self._validate_midi_item_params(
                track_index, start_time, length
            )
            
            # Validate track index using base controller method
            track = self._get_track(track_index)
            if track is None:
                return -1
                
            self.logger.debug(
                f"Creating MIDI item on track {track_index} at position {start_time} "
                f"with length {length}"
            )
            
            # Create the item
            item = track.add_midi_item(start_time, start_time + length)
            if item is None:
                self.logger.error("Failed to create MIDI item")
                return -1
            
            self.logger.info(f"Created MIDI item with ID: {item.id}")
            return item.id
            
        except Exception as e:
            self.logger.error(f"Failed to create MIDI item: {e}")
            return -1

    def _validate_midi_item_params(self, track_index: int, start_time: float, 
                                  length: float) -> Tuple[int, float, float]:
        """Validate and convert MIDI item parameters."""
        try:
            track_index = int(track_index)
            start_time = float(start_time)
            length = float(length)
        except (ValueError, TypeError) as e:
            self.logger.error(f"Invalid parameter type: {e}")
            raise
        
        return track_index, start_time, length

    def add_midi_note(self, track_index: int, item_id: Union[int, str], 
                     note_params: MIDINoteParams) -> bool:
        """
        Add a MIDI note to a MIDI item.
        
        Args:
            track_index (int): Index of the track containing the MIDI item
            item_id (int or str): ID of the MIDI item
            note_params (MIDINoteParams): MIDI note parameters
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate parameters
            if not self._validate_midi_note_params(
                note_params.pitch, note_params.velocity, note_params.channel
            ):
                return False
            
            # Get the track and item
            track = self._get_track(track_index)
            if track is None:
                return False
            
            item = get_item_by_id_or_index(track, item_id)
            if item is None:
                self.logger.error(f"MIDI item {item_id} not found on track {track_index}")
                return False
            
            # Add the MIDI note
            take = item.active_take
            if take is None:
                self.logger.error("No active take found for MIDI item")
                return False
            
            # Add the note using the MIDI take
            take.add_midi_note(
                note_params.pitch, 
                note_params.start_time, 
                note_params.start_time + note_params.length, 
                note_params.velocity, 
                note_params.channel
            )
            
            self.logger.info(
                f"Added MIDI note: pitch={note_params.pitch}, "
                f"velocity={note_params.velocity}, channel={note_params.channel}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add MIDI note: {e}")
            return False

    def add_midi_note_simple(self, track_index: int, item_id: Union[int, str], pitch: int, 
                           start_time: float, length: float, 
                           velocity: int = DEFAULT_MIDI_VELOCITY, 
                           channel: int = DEFAULT_MIDI_CHANNEL) -> bool:
        """
        Convenience method to add a MIDI note with individual parameters.
        
        Args:
            track_index (int): Index of the track containing the MIDI item
            item_id (int or str): ID of the MIDI item
            pitch (int): MIDI pitch (0-127)
            start_time (float): Start time within the MIDI item in seconds
            length (float): Length of the note in seconds
            velocity (int): MIDI velocity (0-127)
            channel (int): MIDI channel (0-15)
            
        Returns:
            bool: True if successful, False otherwise
        """
        note_params = MIDINoteParams(
            pitch=pitch,
            start_time=start_time,
            length=length,
            velocity=velocity,
            channel=channel
        )
        return self.add_midi_note(track_index, item_id, note_params)

    def _validate_midi_note_params(self, pitch: int, velocity: int, channel: int) -> bool:
        """Validate MIDI note parameters."""
        if not (MIN_MIDI_PITCH <= pitch <= MAX_MIDI_PITCH):
            self.logger.error(f"Invalid pitch: {pitch}. Must be between {MIN_MIDI_PITCH} and {MAX_MIDI_PITCH}")
            return False
        
        if not (0 <= velocity <= MAX_MIDI_PITCH):
            self.logger.error(f"Invalid velocity: {velocity}. Must be between 0 and {MAX_MIDI_PITCH}")
            return False
        
        if not (0 <= channel <= MAX_MIDI_CHANNEL):
            self.logger.error(f"Invalid channel: {channel}. Must be between 0 and {MAX_MIDI_CHANNEL}")
            return False
        
        return True

    def clear_midi_item(self, track_index: int, item_id: Union[int, str]) -> bool:
        """
        Clear all MIDI notes from a MIDI item.
        
        Args:
            track_index (int): Index of the track containing the MIDI item
            item_id (int or str): ID of the MIDI item
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get the track and item
            track = self._get_track(track_index)
            if track is None:
                return False
            
            item = get_item_by_id_or_index(track, item_id)
            if item is None:
                self.logger.error(f"MIDI item {item_id} not found on track {track_index}")
                return False
            
            # Clear all notes from the active take
            take = item.active_take
            if take is None:
                self.logger.error("No active take found for MIDI item")
                return False
            
            # Clear all MIDI notes
            take.clear_midi_notes()
            
            self.logger.info(f"Cleared all MIDI notes from item {item_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear MIDI item: {e}")
            return False

    def get_midi_notes(self, track_index: int, item_id: Union[int, str]) -> List[Dict[str, Any]]:
        """
        Get all MIDI notes from a MIDI item.
        
        Args:
            track_index (int): Index of the track containing the MIDI item
            item_id (int or str): ID of the MIDI item
            
        Returns:
            List[Dict[str, Any]]: List of MIDI note dictionaries
        """
        try:
            # Get the track and item
            track = self._get_track(track_index)
            if track is None:
                return []
            
            item = get_item_by_id_or_index(track, item_id)
            if item is None:
                self.logger.error(f"MIDI item {item_id} not found on track {track_index}")
                return []
            
            # Get notes from the active take
            take = item.active_take
            if take is None:
                self.logger.error("No active take found for MIDI item")
                return []
            
            notes = []
            for note in take.midi_notes:
                note_info = {
                    "pitch": note.pitch,
                    "start": note.start,
                    "end": note.end,
                    "velocity": note.velocity,
                    "channel": note.channel
                }
                notes.append(note_info)
            
            self.logger.info(f"Retrieved {len(notes)} MIDI notes from item {item_id}")
            return notes
            
        except Exception as e:
            self.logger.error(f"Failed to get MIDI notes: {e}")
            return []

    def find_midi_notes_by_pitch(self, pitch_min: int = MIN_MIDI_PITCH, 
                                pitch_max: int = MAX_MIDI_PITCH) -> List[Dict[str, Any]]:
        """
        Find all MIDI notes within a specific pitch range across the project.
        
        Args:
            pitch_min (int): Minimum pitch (inclusive)
            pitch_max (int): Maximum pitch (inclusive)
            
        Returns:
            List[Dict[str, Any]]: List of MIDI notes with their track and item information
        """
        try:
            # Validate pitch range
            if not self._validate_pitch_range(pitch_min, pitch_max):
                return []
            
            # Get all MIDI items in the project
            midi_items = self.get_all_midi_items()
            matching_notes = []
            
            # Search through each MIDI item
            for item_info in midi_items:
                track_index = item_info["track_index"]
                item_id = item_info["item_id"]
                
                # Get notes from this item
                notes = self.get_midi_notes(track_index, item_id)
                
                # Filter notes by pitch range
                filtered_notes = self._filter_notes_by_pitch(notes, pitch_min, pitch_max)
                
                # Add track and item information to matching notes
                for note in filtered_notes:
                    note["track_index"] = track_index
                    note["item_id"] = item_id
                    matching_notes.append(note)
            
            self.logger.info(f"Found {len(matching_notes)} MIDI notes in pitch range {pitch_min}-{pitch_max}")
            return matching_notes
            
        except Exception as e:
            self.logger.error(f"Failed to find MIDI notes by pitch: {e}")
            return []

    def _validate_pitch_range(self, pitch_min: int, pitch_max: int) -> bool:
        """Validate pitch range parameters."""
        if not (MIN_MIDI_PITCH <= pitch_min <= MAX_MIDI_PITCH):
            self.logger.error(f"Invalid pitch_min: {pitch_min}")
            return False
        
        if not (MIN_MIDI_PITCH <= pitch_max <= MAX_MIDI_PITCH):
            self.logger.error(f"Invalid pitch_max: {pitch_max}")
            return False
        
        if pitch_min > pitch_max:
            self.logger.error(f"pitch_min ({pitch_min}) cannot be greater than pitch_max ({pitch_max})")
            return False
        
        return True

    def _filter_notes_by_pitch(self, notes: List[Dict[str, Any]], 
                              pitch_min: int, pitch_max: int) -> List[Dict[str, Any]]:
        """Filter notes by pitch range."""
        return [note for note in notes if pitch_min <= note["pitch"] <= pitch_max]

    def get_all_midi_items(self) -> List[Dict[str, Union[int, str, float]]]:
        """
        Get all MIDI items in the project.
        
        Returns:
            List[Dict[str, Union[int, str, float]]]: List of MIDI item information
        """
        try:
            project = reapy.Project()
            midi_items = []
            
            for track_index, track in enumerate(project.tracks):
                for item in track.items:
                    # Check if the item is a MIDI item
                    if item.active_take and item.active_take.is_midi:
                        item_info = {
                            "track_index": track_index,
                            "item_id": item.id,
                            "position": item.position,
                            "length": item.length
                        }
                        midi_items.append(item_info)
            
            self.logger.info(f"Found {len(midi_items)} MIDI items in project")
            return midi_items
            
        except Exception as e:
            self.logger.error(f"Failed to get all MIDI items: {e}")
            return []

    def get_selected_midi_item(self) -> Optional[Dict[str, int]]:
        """
        Get the first selected MIDI item in the project.
        
        Returns:
            Optional[Dict[str, int]]: Information about the selected MIDI item, or None if none found
        """
        try:
            project = reapy.Project()
            
            for track_index, track in enumerate(project.tracks):
                for item in track.items:
                    # Check if item is selected and is a MIDI item
                    if (item.selected and item.active_take and 
                        item.active_take.is_midi):
                        
                        item_info = {
                            "track_index": track_index,
                            "item_id": item.id,
                            "position": item.position,
                            "length": item.length
                        }
                        
                        self.logger.info(f"Found selected MIDI item: track {track_index}, item {item.id}")
                        return item_info
            
            self.logger.info("No selected MIDI item found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get selected MIDI item: {e}")
            return None
