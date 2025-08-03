import reapy
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

from .base_controller import BaseController
from src.utils.item_utils import get_item_by_id_or_index, get_item_properties, select_item, delete_item

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
        except Exception:
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
        except Exception:
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
    
    def create_midi_item(self, track_index: int, start_time: float, length: float = 4.0) -> Union[int, str]:
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
            try:
                track_index = int(track_index)
                start_time = float(start_time)
                length = float(length)
            except (ValueError, TypeError) as e:
                self.logger.error(f"Invalid parameter type: {e}")
                return -1
            
            # Validate track index using base controller method
            track = self._get_track(track_index)
            if track is None:
                return -1
                
            self.logger.debug(f"Creating MIDI item on track {track_index} at position {start_time} with length {length}")
            
            # Create the item
            item = track.add_midi_item(start_time, start_time + length)
            if item is None:
                self.logger.error("Failed to create MIDI item - track.add_midi_item returned None")
                return -1
                
            take = item.active_take
            if take is None:
                take = item.add_take()
                if take is None:
                    self.logger.error("Failed to add take to MIDI item")
                    return -1
                self.logger.debug("Added new take to item")
            
            self.logger.debug("Take configured for MIDI")
            
            project = reapy.Project()
            project.select_all_items(False)
            try:
                self._select_item(item)
                self.logger.debug("Selected the newly created item")
            except Exception as e:
                self.logger.warning(f"Failed to select item, but continuing: {e}")
            
            # Find the index of this item in the track's items collection
            # This is more reliable for later operations than using the ID
            for i, track_item in enumerate(track.items):
                if track_item.id == item.id:
                    self.logger.info(f"Created MIDI item at index {i} with actual ID: {item.id}")
                    return i
            
            # Fallback to returning the raw ID if we couldn't find the index
            self.logger.info(f"Created MIDI item with ID: {item.id}, returning as string")
            return item.id

        except Exception as e:
            self.logger.error(f"Failed to create MIDI item: {e}")
            return -1
    
    def add_midi_note(self, track_index: int, item_id: Union[int, str], pitch: int, 
                     start_time: float, length: float, velocity: int = 96, channel: int = 0) -> bool:
        """
        Add a MIDI note to a MIDI item.
        
        Args:
            track_index (int): Index of the track containing the MIDI item
            item_id (int or str): ID of the MIDI item
            pitch (int): MIDI note pitch (0-127)
            start_time (float): Start time of the note within the MIDI item in seconds
            length (float): Length of the note in seconds
            velocity (int): Note velocity (0-127)
            channel (int): MIDI channel (0-15)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            item = get_item_by_id_or_index(reapy.Project().tracks[track_index], item_id)
            if item is None:
                self.logger.error(f"MIDI item with ID {item_id} not found on track {track_index}")
                return False

            # Ensure the item is a MIDI item and has an active take
            if not item.is_midi or not item.active_take:
                self.logger.error(f"Item {item_id} on track {track_index} is not a valid MIDI item or has no active take.")
                return False

            midi_take = item.active_take
            
            # Add note
            midi_take.add_note(
                pitch=pitch,
                start_time=start_time,
                length=length,
                velocity=velocity,
                channel=channel
            )
            
            self.logger.info(f"Added MIDI note: pitch={pitch}, start={start_time}, length={length}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to add MIDI note: {e}")
            return False

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
            item = get_item_by_id_or_index(reapy.Project().tracks[track_index], item_id)
            if item is None:
                self.logger.error(f"MIDI item with ID {item_id} not found on track {track_index}")
                return False

            if not item.is_midi or not item.active_take:
                self.logger.error(f"Item {item_id} on track {track_index} is not a valid MIDI item or has no active take.")
                return False

            midi_take = item.active_take
            midi_take.clear_notes()
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
            List[Dict[str, Any]]: List of dictionaries, each representing a MIDI note
        """
        try:
            item = get_item_by_id_or_index(reapy.Project().tracks[track_index], item_id)
            if item is None:
                self.logger.error(f"MIDI item with ID {item_id} not found on track {track_index}")
                return []

            if not item.is_midi or not item.active_take:
                self.logger.error(f"Item {item_id} on track {track_index} is not a valid MIDI item or has no active take.")
                return []

            midi_take = item.active_take
            notes_data = []
            for note in midi_take.notes:
                notes_data.append({
                    "pitch": note.pitch,
                    "start_time": note.start_time,
                    "length": note.length,
                    "velocity": note.velocity,
                    "channel": note.channel,
                })
            return notes_data
        except Exception as e:
            self.logger.error(f"Failed to get MIDI notes: {e}")
            return []

    def find_midi_notes_by_pitch(self, pitch_min: int = 0, pitch_max: int = 127) -> List[Dict[str, Any]]:
        """
        Find all MIDI notes within a pitch range across all MIDI items in the current project.
        
        Args:
            pitch_min (int): Minimum pitch to search for (inclusive, 0-127)
            pitch_max (int): Maximum pitch to search for (inclusive, 0-127)
            
        Returns:
            List[Dict[str, Any]]: A list of dictionaries, each representing a MIDI note found,
                                  including its track index and item ID.
        """
        found_notes = []
        project = reapy.Project()
        for track_index, track in enumerate(project.tracks):
            for item in track.items:
                if item.is_midi and item.active_take:
                    midi_take = item.active_take
                    for note in midi_take.notes:
                        if pitch_min <= note.pitch <= pitch_max:
                            found_notes.append({
                                "track_index": track_index,
                                "item_id": item.id,
                                "pitch": note.pitch,
                                "start_time": note.start_time,
                                "length": note.length,
                                "velocity": note.velocity,
                                "channel": note.channel,
                            })
        return found_notes

    def get_all_midi_items(self) -> List[Dict[str, Union[int, str, float]]]:
        """
        Get information about all MIDI items in the current project.
        
        Returns:
            List[Dict[str, Union[int, str, float]]]: A list of dictionaries, each representing a MIDI item,
                                                      including its track index, item ID, position, and length.
        """
        all_midi_items = []
        project = reapy.Project()
        for track_index, track in enumerate(project.tracks):
            for item in track.items:
                if item.is_midi:
                    all_midi_items.append({
                        "track_index": track_index,
                        "item_id": item.id,
                        "position": item.position,
                        "length": item.length,
                        "name": item.active_take.name if item.active_take else ""
                    })
        return all_midi_items
    
    def get_selected_midi_item(self) -> Optional[Dict[str, int]]:
        """
        Get the currently selected MIDI item, if any.

        Returns:
            Optional[Dict[str, int]]: A dictionary containing the track index and item ID of the selected MIDI item,
                                      or None if no MIDI item is selected.
        """
        project = reapy.Project()
        for track_index, track in enumerate(project.tracks):
            for item in track.items:
                if item.selected and item.is_midi:
                    return {"track_index": track_index, "item_id": item.id}
        return None
