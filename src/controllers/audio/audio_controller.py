import reapy
import logging
import os
from typing import Union
import time
from reapy import reascript_api as RPR

from src.utils.item_utils import get_item_by_id_or_index, get_item_properties as get_item_props
from src.utils.item_operations import select_item, delete_item

# Constants to replace magic numbers
POSITION_TOLERANCE = 0.01
INSERTION_WAIT_TIME = 0.1
DEFAULT_DUPLICATE_OFFSET = 0.001

class AudioController:
    """Controller for audio-related operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)

    def insert_audio_item(self, track_index: int, file_path: str, 
                         start_time: float) -> Union[int, str]:
        """
        Insert an audio file as a media item on a track.
        
        Args:
            track_index (int): Index of the track to add the audio item to
            file_path (str): Path to the audio file
            start_time (float): Start time in seconds
            
        Returns:
            int or str: ID of the created item
        """
        try:
            if not os.path.exists(file_path):
                self.logger.error(f"Audio file does not exist: {file_path}")
                return -1
                
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Select the track and set cursor position
            self._prepare_track_for_insertion(track, start_time)
            
            # Store the number of items before insertion
            num_items_before = len(track.items)
            
            # Insert the media file (0 means "add media to selected tracks")
            RPR.InsertMedia(file_path, 0)
            
            # Wait for insertion to complete
            time.sleep(INSERTION_WAIT_TIME)
            
            # Find and return the newly inserted item
            return self._find_inserted_item(track, start_time, num_items_before)

        except Exception as e:
            error_message = f"Failed to insert audio item: {e}"
            self.logger.error(error_message)
            return -1

    def _prepare_track_for_insertion(self, track, start_time):
        """Prepare track for media insertion."""
        # Clear all track selections and select only this track
        RPR.SetOnlyTrackSelected(track.id)
        
        # Set the cursor to the start position
        project = reapy.Project()
        project.cursor_position = start_time

    def _find_inserted_item(self, track, start_time, num_items_before):
        """Find the newly inserted item after media insertion."""
        # Check if any new items were added
        if len(track.items) <= num_items_before:
            self.logger.error("No new items were added after media insertion")
            return -1
        
        # Find the newly inserted item (should be the last one)
        for i in range(len(track.items) - 1, -1, -1):
            item = track.items[i]
            if abs(item.position - start_time) < POSITION_TOLERANCE:
                self.logger.info(f"Found inserted audio item at position {item.position}, ID: {item.id}")
                return item.id
        
        # If we couldn't find the item at the exact position, return the last item
        if len(track.items) > num_items_before:
            last_item = track.items[-1]
            self.logger.info(f"Using last inserted item at position {last_item.position}, ID: {last_item.id}")
            return last_item.id
        
        self.logger.warning(f"Couldn't find the inserted audio item at position {start_time}")
        return -1
            
    def get_item_properties(self, track_index, item_id):
        """
        Get properties of a media item.
        """
        try:                
            # Find the item in the actual project
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Use shared utility to find the item
            item = get_item_by_id_or_index(track, item_id)
            if item is None:
                self.logger.warning(f"Item {item_id} not found on track {track_index}")
                return {}
            
            # Get properties using shared utility
            return get_item_props(item)
            
        except Exception as e:
            error_message = f"Failed to get properties for item {item_id}: {e}"
            self.logger.error(error_message)
            return {}

    def set_item_position(self, track_index, item_id, position):
        """
        Set the position of a media item.
        
        Args:
            track_index (int): Index of the track containing the item
            item_id (int or str): ID of the item
            position (float): New position in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            
            item = get_item_by_id_or_index(track, item_id)
            if item is None:
                self.logger.warning(f"Item {item_id} not found on track {track_index}")
                return False
            
            item.position = position
            self.logger.info(f"Set item {item_id} position to {position}")
            return True
            
        except Exception as e:
            error_message = f"Failed to set item {item_id} position to {position}: {e}"
            self.logger.error(error_message)
            return False

    def set_item_length(self, track_index, item_id, length):
        """
        Set the length of a media item.
        
        Args:
            track_index (int): Index of the track containing the item
            item_id (int or str): ID of the item
            length (float): New length in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            
            item = get_item_by_id_or_index(track, item_id)
            if item is None:
                self.logger.warning(f"Item {item_id} not found on track {track_index}")
                return False
            
            item.length = length
            self.logger.info(f"Set item {item_id} length to {length}")
            return True
            
        except Exception as e:
            error_message = f"Failed to set item {item_id} length to {length}: {e}"
            self.logger.error(error_message)
            return False

    def duplicate_item(self, track_index, item_id, new_position=None):
        """
        Duplicate an existing item on a track.
        
        Args:
            track_index (int): Index of the track containing the item
            item_id (int or str): ID of the item to duplicate
            new_position (float, optional): New position for the duplicated item
            
        Returns:
            int or str: ID of the duplicated item, or -1 if failed
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Get the original item
            original_item = get_item_by_id_or_index(track, item_id)
            if original_item is None:
                error_message = f"Item {item_id} not found on track {track_index}"
                self.logger.error(error_message)
                return -1
            
            # Calculate new position if not provided
            if new_position is None:
                new_position = self._calculate_duplicate_position(original_item)
            
            # Create the duplicate
            return self._create_item_duplicate(
                original_item, track, new_position
            )
            
        except Exception as e:
            self.logger.error(f"Failed to duplicate item: {e}")
            return -1

    def _calculate_duplicate_position(self, original_item):
        """Calculate the position for the duplicated item."""
        return original_item.position + original_item.length + DEFAULT_DUPLICATE_OFFSET

    def _create_item_duplicate(self, original_item, track, new_position):
        """Create a duplicate of the original item at the new position."""
        try:
            # Select the original item
            select_item(original_item)
            
            # Copy the item
            RPR.CopySelectedMediaItems()
            
            # Set cursor to new position
            project = reapy.Project()
            project.cursor_position = new_position
            
            # Paste the item
            RPR.PasteSelectedMediaItems()
            
            # Find the newly created item
            return self._find_duplicated_item(track, new_position)
            
        except Exception as e:
            self.logger.error(f"Failed to create item duplicate: {e}")
            return -1

    def _find_duplicated_item(self, track, new_position):
        """Find the newly duplicated item."""
        # Wait a moment for the paste operation to complete
        time.sleep(INSERTION_WAIT_TIME)
        
        # Find the item at the new position
        for item in track.items:
            if abs(item.position - new_position) < POSITION_TOLERANCE:
                self.logger.info(f"Found duplicated item at position {item.position}, ID: {item.id}")
                return item.id
        
        # If not found at exact position, return the last item
        if track.items:
            last_item = track.items[-1]
            self.logger.info(f"Using last item as duplicate: {last_item.id}")
            return last_item.id
        
        return -1

    def delete_item(self, track_index, item_id):
        """
        Delete a media item from a track.
        
        Args:
            track_index (int): Index of the track containing the item
            item_id (int or str): ID of the item to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            
            item = get_item_by_id_or_index(track, item_id)
            if item is None:
                return False
            
            # Use shared utility to delete the item
            return delete_item(item)
            
        except Exception as e:
            error_message = f"Failed to delete item {item_id}: {e}"
            self.logger.error(error_message)
            return False

    def get_items_in_time_range(self, track_index, start_time, end_time):
        """
        Get all items on a track within a time range.
        
        Args:
            track_index (int): Index of the track
            start_time (float): Start time in seconds
            end_time (float): End time in seconds
            
        Returns:
            list: List of item IDs within the time range
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            
            items_in_range = []
            for item in track.items:
                # Check if item overlaps with the time range
                item_start = item.position
                item_end = item.position + item.length
                
                # Item overlaps if it starts before the range ends and ends after the range starts
                if item_start < end_time and item_end > start_time:
                    items_in_range.append(item.id)
            
            self.logger.info(
                f"Found {len(items_in_range)} items in time range "
                f"{start_time}-{end_time}"
            )
            return items_in_range
            
        except Exception as e:
            self.logger.error(f"Failed to get items in time range: {e}")
            return []
    
    def get_selected_items(self):
        """
        Get all currently selected items across all tracks.
        
        Returns:
            list: List of dictionaries containing item information
        """
        try:
            project = reapy.Project()
            selected_items = []
            
            for track in project.tracks:
                for item in track.items:
                    if item.is_selected:
                        item_info = {
                            'track_index': track.index,
                            'item_id': item.id,
                            'position': item.position,
                            'length': item.length,
                            'name': item.name if hasattr(item, 'name') else f"Item {item.id}"
                        }
                        selected_items.append(item_info)
            
            self.logger.info(f"Found {len(selected_items)} selected items")
            return selected_items
            
        except Exception as e:
            self.logger.error(f"Failed to get selected items: {e}")
            return []
