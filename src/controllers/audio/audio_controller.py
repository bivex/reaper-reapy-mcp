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
INSERTION_WAIT_TIME = (
    0.25  # Time to wait after media insertion (increased for reliability)
)
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

            # Defensive: clamp track_index
            if track_index < 0 or track_index >= len(project.tracks):
                self.logger.error("Track index out of range: %s", track_index)
                return None

            track = project.tracks[track_index]

            # Determine insertion position
            position = 0.0 if start_time is None else float(start_time)

            # Snapshot all items (track_id, item_index, position) before insertion
            before_snapshot = {
                (ti, idx)
                for ti, tr in enumerate(project.tracks)
                for idx, it in enumerate(tr.items)
            }

            # 1) Move edit cursor to position
            project.cursor_position = position

            # 2) Clear selection and select only the target track
            for t in project.tracks:
                try:
                    t.is_selected = False
                except Exception:
                    pass
            track.is_selected = True

            # 3) Primary attempt: insert media on selected track (mode=3)
            self._RPR.InsertMedia(file_path, 3)
            time.sleep(INSERTION_WAIT_TIME)
            self._RPR.UpdateArrange()

            # Create after snapshot
            after_snapshot = {
                (ti, idx)
                for ti, tr in enumerate(project.tracks)
                for idx, it in enumerate(tr.items)
            }

            # Find new items (could be on any track depending on REAPER prefs)
            new_pairs = sorted(list(after_snapshot - before_snapshot))
            if not new_pairs:
                # Fallback: try mode=0 (insert at edit cursor)
                self.logger.debug(
                    "InsertMedia mode=3 yielded no new items, fallback to mode=0"
                )
                self._RPR.InsertMedia(file_path, 0)
                time.sleep(INSERTION_WAIT_TIME)
                self._RPR.UpdateArrange()

                after_snapshot = {
                    (ti, idx)
                    for ti, tr in enumerate(project.tracks)
                    for idx, it in enumerate(tr.items)
                }
                new_pairs = sorted(list(after_snapshot - before_snapshot))

            if not new_pairs:
                self.logger.error("No new items detected after InsertMedia")
                return None

            # Prefer items at the intended position; otherwise take the first new item
            selected_pair = None
            for ti, idx in new_pairs:
                it = project.tracks[ti].items[idx]
                if abs((it.position or 0.0) - position) < POSITION_TOLERANCE:
                    selected_pair = (ti, idx)
                    break
            if selected_pair is None:
                selected_pair = new_pairs[-1]  # last created is often the inserted one

            src_ti, src_idx = selected_pair
            src_track = project.tracks[src_ti]
            inserted_item = src_track.items[src_idx]

            # If item landed on a different track, move it to the requested track
            if src_ti != track_index:
                try:
                    # ReaScript: SetMediaItemInfo_Value(item, "P_TRACK", track_id)
                    self._RPR.SetMediaItemInfo_Value(
                        inserted_item.id, "P_TRACK", track.id
                    )
                    time.sleep(INSERTION_WAIT_TIME)
                    self._RPR.UpdateArrange()
                    # After moving, re-bind 'track' reference
                    track = project.tracks[track_index]
                except Exception as move_err:
                    self.logger.error(
                        "Failed to move inserted item to track %s: %s",
                        track_index,
                        move_err,
                    )
                    return None

            # Ensure position is correct on the target track
            try:
                inserted_item.position = position
                time.sleep(INSERTION_WAIT_TIME)
                self._RPR.UpdateArrange()
            except Exception as pos_err:
                self.logger.warning(
                    "Failed to set position on inserted item: %s", pos_err
                )

            # Return the index of the inserted item on the target track (find by position or last index)
            # Prefer exact position match
            for idx, it in enumerate(track.items):
                if abs((it.position or 0.0) - position) < POSITION_TOLERANCE:
                    self.logger.info(
                        "Inserted audio item on track %s at index %s (pos=%s)",
                        track_index,
                        idx,
                        it.position,
                    )
                    return idx

            # Fallback: last item
            if track.items:
                last_idx = len(track.items) - 1
                self.logger.warning(
                    "Returning last index %s for inserted audio item on track %s",
                    last_idx,
                    track_index,
                )
                return last_idx

            self.logger.error("Inserted item not found on the target track after move")
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

    def create_blank_item_on_track(
        self,
        track_index: int,
        start_time: float,
        length: float = 1.0,
    ) -> int:
        """
        Create a blank media item on a track and return its index.

        Args:
            track_index (int): Destination track index
            start_time (float): Start time in seconds
            length (float): Item length in seconds (min 0.1s)

        Returns:
            int: Index of the created item on the track, or -1 on failure
        """
        try:
            if self._RPR is None:
                self.logger.error("RPR not initialized")
                return -1

            # Enforce minimal length
            length = max(0.1, float(length))
            start_time = float(start_time)

            reapy = get_reapy()
            project = reapy.Project()

            if track_index < 0 or track_index >= len(project.tracks):
                self.logger.error("Track index out of range: %s", track_index)
                return -1

            track = project.tracks[track_index]

            # Snapshot before
            before_count = len(track.items)

            # Move cursor and select only target track
            project.cursor_position = start_time
            for t in project.tracks:
                try:
                    t.is_selected = False
                except Exception:
                    pass
            track.is_selected = True

            # Insert empty item using REAPER action (40142)
            self._RPR.Main_OnCommand(40142, 0)
            time.sleep(INSERTION_WAIT_TIME)
            self._RPR.UpdateArrange()

            # Verify new item on the track
            after_count = len(track.items)
            if after_count <= before_count:
                self.logger.error(
                    "Failed to create blank item on track %s", track_index
                )
                return -1

            # New item should be last
            new_index = after_count - 1
            item = track.items[new_index]
            try:
                item.position = start_time
                item.length = length
                time.sleep(INSERTION_WAIT_TIME)
                self._RPR.UpdateArrange()
            except Exception as e:
                self.logger.warning("Failed to set blank item props: %s", e)

            # Prefer exact position match
            for idx, it in enumerate(track.items):
                if abs((it.position or 0.0) - start_time) < POSITION_TOLERANCE:
                    return idx

            return new_index
        except Exception as e:
            self.logger.error("Failed to create blank item: %s", e)
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
