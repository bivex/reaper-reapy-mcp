import reapy
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass

from src.utils.item_utils import get_item_by_id_or_index, get_item_properties
from src.utils.item_operations import select_item, delete_item

class MIDIController:
    """Controller for MIDI-related operations in Reaper."""

    # Constants to replace magic numbers
    DEFAULT_MIDI_LENGTH = 4.0
    DEFAULT_MIDI_VELOCITY = 96
    DEFAULT_MIDI_CHANNEL = 0
    MAX_MIDI_PITCH = 127
    MIN_MIDI_PITCH = 0
    MAX_MIDI_CHANNEL = 15
    DEFAULT_TRACK_INDEX = 0
    DEFAULT_POSITION = 0.0
    DEFAULT_ITEM_ID = 1
    DEFAULT_TAKE_COUNT = 1
    DEFAULT_MIDI_NOTE_PITCHES = [60, 64, 67]  # C, E, G - a C major chord
    DEFAULT_ACTIVE_TAKE = 0
    DEFAULT_MIDI_NOTE_LENGTH = 1.0
    DEFAULT_MIDI_NOTE_COUNT = 3  # Number of notes in DEFAULT_MIDI_NOTE_PITCHES
    DEFAULT_NEW_POSITION = 2.0
    DEFAULT_NEW_LENGTH = 2.0
    DEFAULT_TIME_RANGE_START = 0.0
    DEFAULT_TIME_RANGE_END = 10.0
    
    # Additional constants for tests
    DEFAULT_MIDI_START_TIME = 0.0
    DEFAULT_MIDI_NOTE_VELOCITY = 96
    DEFAULT_SECOND_MIDI_START_TIME = 4.0
    DEFAULT_SECOND_MIDI_LENGTH = 2.0
    DEFAULT_SECOND_MIDI_NOTE_PITCH = 72
    DEFAULT_SECOND_MIDI_NOTE_LEN = 0.5
    DEFAULT_SECOND_MIDI_NOTE_VEL = 90

    @dataclass
    class MIDIItemTarget:
        """Data class to hold MIDI item target parameters."""
        track_index: int
        item_id: Union[int, str]

    @dataclass
    class MIDINoteParams:
        """Data class to hold MIDI note parameters."""
        pitch: int
        start_time: float
        length: float
        velocity: int = 96  # DEFAULT_MIDI_VELOCITY
        channel: int = 0    # DEFAULT_MIDI_CHANNEL

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
            error_message = f"Failed to validate track index: {e}"
            self.logger.error(error_message)
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
            error_message = f"Failed to get track {track_index}: {e}"
            self.logger.error(error_message)
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
                         *, length: float = DEFAULT_MIDI_LENGTH) -> int:
        """
        Create an empty MIDI item on a track.
        
        Args:
            track_index (int): Index of the track to add the MIDI item to
            start_time (float): Start time in seconds
            length (float): Length of the MIDI item in seconds
            
        Returns:
            int: Index of the created MIDI item for direct use in add_midi_note
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
                f"Creating MIDI item on track {track_index} at position "
                f"{start_time} with length {length}"
            )
            
            # Create the item
            item = track.add_midi_item(start_time, start_time + length)
            if item is None:
                self.logger.error("Failed to create MIDI item")
                return -1
            
            # Find the index of the created item in the track's items list
            item_index = None
            for i, track_item in enumerate(track.items):
                if track_item.id == item.id:
                    item_index = i
                    break
            
            if item_index is None:
                self.logger.error("Failed to find created item index")
                return -1
                
            self.logger.info(f"Created MIDI item with ID: {item.id} at index {item_index}")
            return item_index
            
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
                     note_params: 'MIDIController.MIDINoteParams') -> bool:
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
                error_message = (
                    f"MIDI item {item_id} not found on track {track_index}"
                )
                self.logger.error(error_message)
                return False
            
            # Add the MIDI note
            take = item.active_take
            if take is None:
                self.logger.error("No active take found for MIDI item")
                return False
            
            # Add the note using the ReaScript API
            from reapy import reascript_api as RPR
            
            # Get the take ID
            take_id = take.id
            
            # Add the MIDI note using ReaScript API
            # MIDI_InsertNote(take, selected, muted, startppqpos, endppqpos, chan, pitch, vel)
            # We need to convert time to PPQ (pulses per quarter note)
            project = reapy.Project()
            start_ppq = RPR.TimeMap2_timeToQN(project.id, note_params.start_time)
            end_ppq = RPR.TimeMap2_timeToQN(project.id, note_params.start_time + note_params.length)
            
            result = RPR.MIDI_InsertNote(
                take_id, 
                False,  # selected
                False,  # muted
                start_ppq, 
                end_ppq, 
                note_params.channel, 
                note_params.pitch, 
                note_params.velocity,
                False   # noSortIn
            )
            
            if result == -1:
                self.logger.error("Failed to insert MIDI note using ReaScript API")
                return False
            
            self.logger.info(
                f"Added MIDI note: pitch={note_params.pitch}, "
                f"velocity={note_params.velocity}, channel={note_params.channel}"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add MIDI note: {e}")
            return False

    def add_midi_note_simple(self, midi_item_target: 'MIDIController.MIDIItemTarget', note_params: 'MIDIController.MIDINoteParams') -> bool:
        """
        Convenience method to add a MIDI note with individual parameters.
        
        Args:
            midi_item_target (MIDIItemTarget): Target MIDI item.
            note_params (MIDINoteParams): MIDI note parameters.
            
        Returns:
            bool: True if successful, False otherwise
        """
        return self.add_midi_note(midi_item_target.track_index, midi_item_target.item_id, note_params)

    def _validate_midi_note_params(self, pitch: int, velocity: int, channel: int) -> bool:
        """Validate MIDI note parameters."""
        if not (self.MIN_MIDI_PITCH <= pitch <= self.MAX_MIDI_PITCH):
            self.logger.error(f"Invalid pitch: {pitch}. Must be between {self.MIN_MIDI_PITCH} and {self.MAX_MIDI_PITCH}")
            return False
        
        if not (0 <= velocity <= 127):  # MIDI velocity range is 0-127
            self.logger.error(f"Invalid velocity: {velocity}. Must be between 0 and 127")
            return False
        
        if not (0 <= channel <= self.MAX_MIDI_CHANNEL):
            self.logger.error(f"Invalid channel: {channel}. Must be between 0 and {self.MAX_MIDI_CHANNEL}")
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
                error_message = (
                    f"MIDI item {item_id} not found on track {track_index}"
                )
                self.logger.error(error_message)
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
                error_message = (
                    f"MIDI item {item_id} not found on track {track_index}"
                )
                self.logger.error(error_message)
                return []
            
            # Get notes from the active take
            take = item.active_take
            if take is None:
                self.logger.error("No active take found for MIDI item")
                return []
            
            notes = []
            # Use the correct reapy API for MIDI notes
            try:
                # Try to get MIDI notes using the correct method
                midi_notes = take.notes if hasattr(take, 'notes') else []
                for note in midi_notes:
                    note_info = {
                        "pitch": note.pitch if hasattr(note, 'pitch') else 60,
                        "start": note.start if hasattr(note, 'start') else 0.0,
                        "end": note.end if hasattr(note, 'end') else 1.0,
                        "velocity": note.velocity if hasattr(note, 'velocity') else 96,
                        "channel": note.channel if hasattr(note, 'channel') else 0
                    }
                    notes.append(note_info)
            except Exception as e:
                self.logger.warning(f"Could not retrieve MIDI notes using standard method: {e}")
                # Return empty list if we can't get notes
                notes = []
            
            self.logger.info(f"Retrieved {len(notes)} MIDI notes from item {item_id}")
            return notes
            
        except Exception as e:
            self.logger.error(f"Failed to get MIDI notes: {e}")
            return []

    def find_midi_notes_by_pitch(self, pitch_min: int = None, 
                                pitch_max: int = None) -> List[Dict[str, Any]]:
        # Use default values if not provided
        if pitch_min is None:
            pitch_min = self.MIN_MIDI_PITCH
        if pitch_max is None:
            pitch_max = self.MAX_MIDI_PITCH
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
            error_message = f"Failed to find MIDI notes by pitch: {e}"
            self.logger.error(error_message)
            return []

    def _validate_pitch_range(self, pitch_min: int, pitch_max: int) -> bool:
        """Validate pitch range parameters."""
        if not (self.MIN_MIDI_PITCH <= pitch_min <= self.MAX_MIDI_PITCH):
            self.logger.error(f"Invalid pitch_min: {pitch_min}")
            return False
        
        if not (self.MIN_MIDI_PITCH <= pitch_max <= self.MAX_MIDI_PITCH):
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
            
            self.logger.info(
                f"Found {len(midi_items)} MIDI items in project"
            )
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
                    # Use the correct reapy API for item selection
                    try:
                        is_selected = item.is_selected if hasattr(item, 'is_selected') else False
                        if (is_selected and item.active_take and 
                            item.active_take.is_midi):
                            
                            item_info = {
                                "track_index": track_index,
                                "item_id": item.id,
                                "position": item.position,
                                "length": item.length
                            }
                            
                            self.logger.info(
                                f"Found selected MIDI item: track {track_index}, "
                                f"item {item.id}"
                            )
                            return item_info
                    except Exception as e:
                        self.logger.warning(f"Error checking item selection: {e}")
                        continue
            
            self.logger.info("No selected MIDI item found")
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get selected MIDI item: {e}")
            return None
