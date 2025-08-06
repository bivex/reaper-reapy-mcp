import logging
import os
from typing import Optional, List, Dict, Any
import time
import sys

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from src.core.reapy_bridge import get_reapy
from src.item.utils import (
    get_item_by_id_or_index,
    get_item_properties as get_item_props,
)
from src.item.operations import delete_item, verify_item_deletion, select_item

# Constants
INSERTION_WAIT_TIME = 0.1  # Time to wait after media insertion
POSITION_TOLERANCE = 0.001  # Tolerance for position matching
DEFAULT_DUPLICATE_OFFSET = 0.1  # Default offset for duplicated items


class AudioController:
    # Public API expected by MCP layer
    # insert_audio_item is referenced from mcp_tools -> controller.audio.insert_audio_item
    """Controller for audio-related operations in Reaper."""

    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)

        # Initialize RPR reference
        try:
            reapy = get_reapy()
            self._RPR = reapy.reascript_api
        except Exception as e:
            self.logger.error(f"Failed to initialize RPR: {e}")
            self._RPR = None

    def add_audio_item(
        self, track_index: int, file_path: str, position: float = 0.0
    ) -> Optional[int]:
        """
        Add an audio file to a track.

        Args:
            track_index (int): Index of the track
            file_path (str): Path to the audio file
            position (float): Position in seconds where to place the item

        Returns:
            Optional[int]: Item ID if successful, None otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]

            # Add audio item using ReaScript API
            item_id = self._RPR.AddMediaItem(track.id)
            if item_id >= 0:
                # Set item position
                self._RPR.SetMediaItemInfo_Value(item_id, "D_POSITION", position)

                # Create take and set source
                take_id = self._RPR.AddTakeToMediaItem(item_id)
                if take_id >= 0:
                    # Set the source file
                    self._RPR.SetMediaItemTake_Source(take_id, file_path)
                    return item_id

            return None

        except Exception as e:
            error_message = (
                f"Failed to add audio item {file_path} to track {track_index}: {e}"
            )
            self.logger.error(error_message)
            return None

    def insert_audio_item(
        self,
        track_index: int,
        file_path: str,
        start_time: Optional[float] = None,
        start_measure: Optional[str] = None,
    ) -> Optional[int]:
        """
        Insert an audio file as a media item on the specified track.

        Args:
            track_index (int): Index of the destination track
            file_path (str): Absolute path to the audio file
            start_time (float, optional): Start time in seconds. Defaults to 0.0
            start_measure (str, optional): Not used here (conversion handled in higher layer)

        Returns:
            Optional[int]: Index of the newly inserted item on the track, or None on failure
        """
        try:
            if self._RPR is None:
                self.logger.error("RPR not initialized")
                return None

            if not file_path or not os.path.exists(file_path):
                self.logger.error("Audio file does not exist: %s", file_path)
                return None

            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]

            # Determine insertion position
            position = 0.0 if start_time is None else float(start_time)

            # Snapshot count before insertion
            count_before = len(track.items)

            # 1) Move edit cursor to position
            project.cursor_position = position

            # 2) Clear selection and select only the target track
            for t in project.tracks:
                try:
                    t.is_selected = False
                except Exception:
                    pass
            track.is_selected = True

            # 3) Try to insert media explicitly on the selected track (mode=3 is more reliable)
            #    If mode=3 fails to yield an item on the track, fall back to mode=0.
            self._RPR.InsertMedia(file_path, 3)
            time.sleep(0.25)  # slightly longer to ensure media is realized
            self._RPR.UpdateArrange()

            # Determine new item index by comparing counts or searching by position
            count_after = len(track.items)
            if count_after <= count_before:
                # Fallback attempt with mode=0 at edit cursor
                self.logger.debug("Fallback to InsertMedia mode=0")
                self._RPR.InsertMedia(file_path, 0)
                time.sleep(0.25)
                self._RPR.UpdateArrange()
                count_after = len(track.items)

            if count_after > count_before:
                # The new item is typically appended to the end
                new_index = count_after - 1
                inserted = track.items[new_index]
                if abs((inserted.position or 0.0) - position) < POSITION_TOLERANCE:
                    self.logger.info(
                        "Inserted audio item on track %s at index %s (pos=%s)",
                        track_index,
                        new_index,
                        inserted.position,
                    )
                    return new_index

                # Search on the same track by position
                for idx, it in enumerate(track.items):
                    if abs((it.position or 0.0) - position) < POSITION_TOLERANCE:
                        self.logger.info(
                            "Inserted audio item found by search at index %s (pos=%s)",
                            idx,
                            it.position,
                        )
                        return idx

                # As a final fallback return last index on this track
                self.logger.warning(
                    "Inserted audio item position check failed; returning last index %s",
                    new_index,
                )
                return new_index

            # As a diagnostic fallback, search across all tracks at the target position
            found_idx: Optional[int] = None
            found_track_idx: Optional[int] = None
            for ti, tr in enumerate(project.tracks):
                for idx, it in enumerate(tr.items):
                    if abs((it.position or 0.0) - position) < POSITION_TOLERANCE:
                        found_idx = idx
                        found_track_idx = ti
                        break
                if found_idx is not None:
                    break

            if found_idx is not None:
                self.logger.warning(
                    "Item inserted on different track %s at index %s; consider moving it programmatically",
                    found_track_idx,
                    found_idx,
                )
                # For now, report failure to respect contract: should appear on requested track
                return None

            self.logger.error(
                "No new item detected after InsertMedia (before=%s, after=%s)",
                count_before,
                count_after,
            )
            return None

        except Exception as e:
            self.logger.error("Failed to insert audio item: %s", e)
            return None

    def get_audio_items(self, track_index: int) -> List[Dict[str, Any]]:
        """
        Get all audio items on a track.

        Args:
            track_index (int): Index of the track

        Returns:
            List[Dict[str, Any]]: List of audio item information
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]

            audio_items = []
            for item in track.items:
                # Check if item has audio takes
                for take in item.takes:
                    if not take.is_midi:
                        audio_items.append(
                            {
                                "id": item.id,
                                "position": item.position,
                                "length": item.length,
                                "file_path": (
                                    take.source.filename
                                    if hasattr(take.source, "filename")
                                    else ""
                                ),
                                "muted": item.muted,
                                "selected": item.selected,
                            }
                        )
                        break  # Only count each item once

            return audio_items

        except Exception as e:
            self.logger.error(f"Failed to get audio items for track {track_index}: {e}")
            return []

    def get_item_properties(self, track_index, item_id):
        """
        Get properties of a media item.
        """
        try:
            # Find the item in the actual project
            project = get_reapy().Project()
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
            project = get_reapy().Project()
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
            project = get_reapy().Project()
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
            int: Index of the duplicated item, or -1 if failed
        """
        try:
            if self._RPR is None:
                self.logger.error("RPR not initialized")
                return -1

            project = get_reapy().Project()
            track = project.tracks[track_index]

            # Count items before duplication
            item_count_before = len(track.items)
            self.logger.info(
                f"Track {track_index} has {item_count_before} items before duplication"
            )

            # Get the original item by ID or index
            original_item = get_item_by_id_or_index(track, item_id)
            if original_item is None:
                error_message = f"Item {item_id} not found on track {track_index}"
                self.logger.error(error_message)
                return -1

            # Calculate new position if not provided
            if new_position is None:
                new_position = self._calculate_duplicate_position(original_item)

            self.logger.info(f"Duplicating item {item_id} to position {new_position}")

            # Simple duplication approach
            try:
                # Use reapy's copy method
                duplicate_item = original_item.copy()
                if duplicate_item:
                    # Set the new position
                    duplicate_item.position = new_position

                    # Update the arrangement
                    self._RPR.UpdateArrange()

                    # Verify duplication by checking item count
                    item_count_after = len(track.items)
                    if item_count_after > item_count_before:
                        new_index = item_count_after - 1  # Last item is the new one
                        # Double-check by position
                        if (
                            abs(track.items[new_index].position - new_position)
                            < POSITION_TOLERANCE
                        ):
                            self.logger.info(
                                f"Successfully duplicated item to index {new_index}"
                            )
                            return new_index
                        else:
                            # Search for the correct item by position
                            for idx, item in enumerate(track.items):
                                if (
                                    abs(item.position - new_position)
                                    < POSITION_TOLERANCE
                                ):
                                    self.logger.info(
                                        f"Found duplicated item at index {idx} by position"
                                    )
                                    return idx

                    self.logger.error(
                        f"Item count didn't increase after duplication (before: {item_count_before}, after: {item_count_after})"
                    )
                    return -1
                else:
                    self.logger.error("Failed to create duplicate using reapy copy()")
                    return -1
            except Exception as reapy_error:
                self.logger.error(f"Reapy duplication failed: {reapy_error}")
                return -1

        except Exception as e:
            self.logger.error(f"Failed to duplicate item: {e}")
            return -1

    def _calculate_duplicate_position(self, original_item):
        """Calculate the position for the duplicated item."""
        return original_item.position + original_item.length + DEFAULT_DUPLICATE_OFFSET

    def _create_item_duplicate(self, original_item, track, new_position):
        """Create a duplicate of the original item at the new position."""
        try:
            if self._RPR is None:
                self.logger.error("RPR not initialized")
                return -1

            # Count items before duplication to determine new item index
            item_count_before = len(track.items)

            # Method 1: Use reapy high-level API for duplication
            try:
                duplicate_item = original_item.copy()
                if duplicate_item:
                    duplicate_item.position = new_position

                    # Update arrange to reflect changes
                    self._RPR.UpdateArrange()

                    # The new item should be at the end of the items list
                    new_index = item_count_before

                    # Verify the item exists at this index
                    if new_index < len(track.items):
                        verify_item = track.items[new_index]
                        if (
                            abs(verify_item.position - new_position)
                            < POSITION_TOLERANCE
                        ):
                            self.logger.info(f"Duplicated item to index {new_index}")
                            return new_index

                    # Fallback: search for the item by position
                    return self._find_duplicated_item_index(track, new_position)

            except (AttributeError, TypeError, Exception) as reapy_error:
                self.logger.warning(
                    f"Reapy duplication failed, trying ReaScript: {reapy_error}"
                )

                # Method 2: Fallback to ReaScript copy-paste method
                try:
                    # Select the original item
                    select_item(original_item)

                    # Copy the item using ReaScript command
                    self._RPR.Main_OnCommand(40698, 0)  # Edit: Copy items

                    # Set cursor to new position
                    project = get_reapy().Project()
                    project.cursor_position = new_position

                    # Paste the item
                    self._RPR.Main_OnCommand(40914, 0)  # Edit: Paste items

                    # Update arrange
                    self._RPR.UpdateArrange()

                    # Find the newly created item index
                    return self._find_duplicated_item_index(track, new_position)

                except Exception as reascript_error:
                    self.logger.error(
                        f"ReaScript duplication also failed: {reascript_error}"
                    )
                    return -1

        except Exception as e:
            self.logger.error(f"Failed to create item duplicate: {e}")
            return -1

    def _find_duplicated_item_index(self, track, new_position):
        """Find the index of the newly duplicated item."""
        # Wait a moment for the operation to complete
        time.sleep(INSERTION_WAIT_TIME)

        # Find the item at the new position and return its index
        for idx, item in enumerate(track.items):
            if abs(item.position - new_position) < POSITION_TOLERANCE:
                self.logger.info(
                    f"Found duplicated item at position {item.position}, index: {idx}"
                )
                return idx

        # If not found at exact position, check the last item
        if track.items:
            last_index = len(track.items) - 1
            last_item = track.items[last_index]
            self.logger.info(
                f"Using last item as duplicate at index {last_index}, position: {last_item.position}"
            )
            return last_index

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
            project = get_reapy().Project()
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

    def get_items_in_time_range(
        self,
        track_index,
        start_time=None,
        end_time=None,
        start_measure=None,
        end_measure=None,
    ):
        """
        Get all items on a track within a time range.

        Args:
            track_index (int): Index of the track
            start_time (float): Start time in seconds (optional)
            end_time (float): End time in seconds (optional)
            start_measure (str): Start measure (optional, not used)
            end_measure (str): End measure (optional, not used)

        Returns:
            list: List of item IDs within the time range
        """
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]

            # Set default time range if not provided
            if start_time is None:
                start_time = 0.0
            if end_time is None:
                end_time = float("inf")  # Get all items

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
            project = get_reapy().Project()
            selected_items = []

            for track in project.tracks:
                for item in track.items:
                    if item.is_selected:
                        item_info = {
                            "track_index": track.index,
                            "item_id": item.id,
                            "position": item.position,
                            "length": item.length,
                            "name": (
                                item.name
                                if hasattr(item, "name")
                                else f"Item {item.id}"
                            ),
                        }
                        selected_items.append(item_info)

            self.logger.info(f"Found {len(selected_items)} selected items")
            return selected_items

        except Exception as e:
            self.logger.error(f"Failed to get selected items: {e}")
            return []
