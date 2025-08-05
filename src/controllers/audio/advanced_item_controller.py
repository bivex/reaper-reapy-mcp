import logging
from typing import Dict, Any, List, Optional, Tuple


import logging
from typing import Optional, List, Dict, Any
import sys
import os

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from utils.reapy_utils import get_reapy


class AdvancedItemController:
    """Controller for advanced item operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
    def split_item(self, track_index: int, item_index: int, split_time: float) -> List[int]:
        """
        Split an item at a specific time.
        
        Args:
            track_index (int): Index of the track
            item_index (int): Index of the item to split
            split_time (float): Time position to split at (in seconds)
            
        Returns:
            List[int]: List of resulting item indices
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return []
            
            track = project.tracks[track_index]
            
            if item_index >= len(track.items):
                self.logger.error("Invalid item index")
                return []
            
            item = track.items[item_index]
            
            # Select the item
            self._RPR.SetMediaItemSelected(item.id, True)
            
            # Split at the specified time
            self._RPR.SplitMediaItem(item.id, split_time)
            
            # Get the resulting items
            new_items = []
            for i, new_item in enumerate(track.items):
                if new_item.position >= split_time or new_item.position + new_item.length > split_time:
                    new_items.append(i)
            
            self.logger.info(f"Split item {item_index} at {split_time}s, created {len(new_items)} new items")
            return new_items
            
        except Exception as e:
            self.logger.error(f"Failed to split item: {e}")
            return []

    def glue_items(self, track_index: int, item_indices: List[int]) -> int:
        """
        Glue multiple items together into a single item.
        
        Args:
            track_index (int): Index of the track
            item_indices (List[int]): List of item indices to glue
            
        Returns:
            int: Index of the resulting glued item, or -1 if failed
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return -1
            
            track = project.tracks[track_index]
            
            # Select the items to glue
            for item_idx in item_indices:
                if item_idx < len(track.items):
                    self._RPR.SetMediaItemSelected(track.items[item_idx].id, True)
            
            # Glue the selected items
            self._RPR.Main_OnCommand(40362, 0)  # Glue items action
            
            # Find the resulting item
            for i, item in enumerate(track.items):
                if self._RPR.IsMediaItemSelected(item.id):
                    self.logger.info(f"Glued {len(item_indices)} items into item {i}")
                    return i
            
            return -1
            
        except Exception as e:
            self.logger.error(f"Failed to glue items: {e}")
            return -1

    def fade_in(self, track_index: int, item_index: int, fade_length: float, fade_curve: int = 0) -> bool:
        """
        Add a fade-in to an item.
        
        Args:
            track_index (int): Index of the track
            item_index (int): Index of the item
            fade_length (float): Length of the fade in seconds
            fade_curve (int): Fade curve type (0=linear, 1=square, 2=slow start/end, 3=fast start, 4=fast end)
            
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
            
            if item_index >= len(track.items):
                self.logger.error("Invalid item index")
                return False
            
            item = track.items[item_index]
            
            # Set fade-in length
            self._RPR.SetMediaItemInfo_Value(item.id, "D_FADEOUTLEN", 0)  # Clear fade-out first
            self._RPR.SetMediaItemInfo_Value(item.id, "D_FADEINLEN", fade_length)
            
            # Set fade-in curve
            self._RPR.SetMediaItemInfo_Value(item.id, "C_FADEINLEN", fade_curve)
            
            self.logger.info(f"Added {fade_length}s fade-in to item {item_index} on track {track_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add fade-in: {e}")
            return False

    def fade_out(self, track_index: int, item_index: int, fade_length: float, fade_curve: int = 0) -> bool:
        """
        Add a fade-out to an item.
        
        Args:
            track_index (int): Index of the track
            item_index (int): Index of the item
            fade_length (float): Length of the fade in seconds
            fade_curve (int): Fade curve type (0=linear, 1=square, 2=slow start/end, 3=fast start, 4=fast end)
            
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
            
            if item_index >= len(track.items):
                self.logger.error("Invalid item index")
                return False
            
            item = track.items[item_index]
            
            # Set fade-out length
            self._RPR.SetMediaItemInfo_Value(item.id, "D_FADEINLEN", 0)  # Clear fade-in first
            self._RPR.SetMediaItemInfo_Value(item.id, "D_FADEOUTLEN", fade_length)
            
            # Set fade-out curve
            self._RPR.SetMediaItemInfo_Value(item.id, "C_FADEOUTLEN", fade_curve)
            
            self.logger.info(f"Added {fade_length}s fade-out to item {item_index} on track {track_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add fade-out: {e}")
            return False

    def crossfade_items(self, track_index: int, item1_index: int, item2_index: int, crossfade_length: float) -> bool:
        """
        Create a crossfade between two items.
        
        Args:
            track_index (int): Index of the track
            item1_index (int): Index of the first item
            item2_index (int): Index of the second item
            crossfade_length (float): Length of the crossfade in seconds
            
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
            
            if item1_index >= len(track.items) or item2_index >= len(track.items):
                self.logger.error("Invalid item index")
                return False
            
            item1 = track.items[item1_index]
            item2 = track.items[item2_index]
            
            # Select both items
            self._RPR.SetMediaItemSelected(item1.id, True)
            self._RPR.SetMediaItemSelected(item2.id, True)
            
            # Create crossfade
            self._RPR.Main_OnCommand(40312, 0)  # Crossfade items action
            
            self.logger.info(f"Created crossfade between items {item1_index} and {item2_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create crossfade: {e}")
            return False

    def reverse_item(self, track_index: int, item_index: int) -> bool:
        """
        Reverse an item.
        
        Args:
            track_index (int): Index of the track
            item_index (int): Index of the item
            
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
            
            if item_index >= len(track.items):
                self.logger.error("Invalid item index")
                return False
            
            item = track.items[item_index]
            
            # Select the item
            self._RPR.SetMediaItemSelected(item.id, True)
            
            # Reverse the item
            self._RPR.Main_OnCommand(41051, 0)  # Reverse items action
            
            self.logger.info(f"Reversed item {item_index} on track {track_index}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reverse item: {e}")
            return False

    def get_item_fade_info(self, track_index: int, item_index: int) -> Dict[str, Any]:
        """
        Get fade information for an item.
        
        Args:
            track_index (int): Index of the track
            item_index (int): Index of the item
            
        Returns:
            Dict[str, Any]: Fade information including lengths and curves
        """
        try:
            reapy = get_reapy()


            project = reapy.Project()
            
            if track_index >= len(project.tracks):
                self.logger.error("Invalid track index")
                return {}
            
            track = project.tracks[track_index]
            
            if item_index >= len(track.items):
                self.logger.error("Invalid item index")
                return {}
            
            item = track.items[item_index]
            
            # Get fade information
            fade_in_len = self._RPR.GetMediaItemInfo_Value(item.id, "D_FADEINLEN")
            fade_out_len = self._RPR.GetMediaItemInfo_Value(item.id, "D_FADEOUTLEN")
            fade_in_curve = self._RPR.GetMediaItemInfo_Value(item.id, "C_FADEINLEN")
            fade_out_curve = self._RPR.GetMediaItemInfo_Value(item.id, "C_FADEOUTLEN")
            
            return {
                "fade_in_length": fade_in_len,
                "fade_out_length": fade_out_len,
                "fade_in_curve": fade_in_curve,
                "fade_out_curve": fade_out_curve
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get item fade info: {e}")
            return {} 
        
