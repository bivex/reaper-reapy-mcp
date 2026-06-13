"""MIDI-related MCP tools."""

import logging
from typing import Dict, Any, Optional
from mcp.server.fastmcp import FastMCP, Context
from .tool_helpers import (
    _create_success_response,
    _create_error_response,
    _handle_controller_operation,
)
try:
    from src.time.conversion import parse_position
except ImportError:
    from time.conversion import parse_position

logger = logging.getLogger(__name__)

# Constants
DEFAULT_MIDI_LENGTH = 4.0
DEFAULT_MIDI_VELOCITY = 96
MAX_MIDI_PITCH = 127
MIN_MIDI_PITCH = 0


def _setup_midi_tools(mcp: FastMCP, controller) -> None:
    """Setup MIDI-related MCP tools."""

    @mcp.tool("create_midi_item")
    def create_midi_item(
        ctx: Context,
        track_index: int,
        start_time: Optional[float] = None,
        start_measure: Optional[str] = None,
        length: float = DEFAULT_MIDI_LENGTH,
    ) -> Dict[str, Any]:
        """
        Create a MIDI item.

        Args:
            track_index (int): Index of the track to create MIDI item on
            start_time (float, optional): Start time in seconds (use number, not string)
            start_measure (str, optional): Start measure (e.g., "1.1.0")
            length (float): Length of the MIDI item in seconds (use number, not string)
        """
        try:
            # Handle time conversion if measure is provided
            if start_measure:
                start_time = parse_position(start_measure)

            # Use 0.0 as default start time if none provided
            if start_time is None:
                start_time = 0.0

            item_id = controller.midi.create_midi_item(track_index, start_time, length)
            if item_id is not None and item_id >= 0:
                return _create_success_response(
                    f"Created MIDI item {item_id} on track {track_index}"
                )
            else:
                return _create_error_response(
                    f"Failed to create MIDI item on track {track_index}"
                )
        except Exception as e:
            error_message = f"Failed to create MIDI item: {str(e)}"
            logger.error(error_message)
            return _create_error_response(error_message)

    @mcp.tool("add_midi_note")
    def add_midi_note(
        ctx: Context,
        track_index: int,
        item_id: int,
        pitch: int,
        start_time: float,
        length: float,
        velocity: int = DEFAULT_MIDI_VELOCITY,
    ) -> Dict[str, Any]:
        """
        Add a MIDI note to a MIDI item.

        Args:
            track_index (int): Index of the track containing the MIDI item
            item_id (int): ID of the MIDI item
            pitch (int): MIDI pitch (0-127)
            start_time (float): Start time in seconds (use number, not string)
            length (float): Note length in seconds (use number, not string)
            velocity (int): Note velocity (0-127)
        """
        try:
            from src.controllers.midi.midi_controller import MIDIController

            note_params = MIDIController.MIDINoteParams(
                pitch=pitch, start_time=start_time, length=length, velocity=velocity
            )
            success = controller.midi.add_midi_note(track_index, item_id, note_params)
            if success:
                return _create_success_response(
                    f"Added MIDI note pitch {pitch} to item {item_id}"
                )
            return _create_error_response(
                f"Failed to add MIDI note pitch {pitch} to item {item_id}"
            )
        except Exception as e:
            logger.error(f"Failed to add MIDI note: {str(e)}")
            return _create_error_response(f"Failed to add MIDI note: {str(e)}")

    @mcp.tool("clear_midi_item")
    def clear_midi_item(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """Clear all MIDI notes from a MIDI item."""
        return _handle_controller_operation(
            f"Clear MIDI item {item_id} on track {track_index}",
            controller.midi.clear_midi_item,
            track_index,
            item_id,
        )

    @mcp.tool("get_midi_notes")
    def get_midi_notes(ctx: Context, track_index: int, item_id: int) -> Dict[str, Any]:
        """Get all MIDI notes from a MIDI item."""
        try:
            notes = controller.midi.get_midi_notes(track_index, item_id)
            return _create_success_response(f"MIDI notes in item {item_id}: {notes}")
        except Exception as e:
            logger.error(f"Failed to get MIDI notes: {str(e)}")
            return _create_error_response(f"Failed to get MIDI notes: {str(e)}")

    @mcp.tool("find_midi_notes_by_pitch")
    def find_midi_notes_by_pitch(
        ctx: Context, pitch_min: int = MIN_MIDI_PITCH, pitch_max: int = MAX_MIDI_PITCH
    ) -> Dict[str, Any]:
        """Find MIDI notes within a pitch range."""
        try:
            notes = controller.midi.find_midi_notes_by_pitch(pitch_min, pitch_max)
            return _create_success_response(
                f"MIDI notes in pitch range {pitch_min}-{pitch_max}: {notes}"
            )
        except Exception as e:
            logger.error(f"Failed to find MIDI notes: {str(e)}")
            return _create_error_response(f"Failed to find MIDI notes: {str(e)}")

    @mcp.tool("get_selected_midi_item")
    def get_selected_midi_item(ctx: Context) -> Dict[str, Any]:
        """Get the currently selected MIDI item."""
        try:
            item_info = controller.midi.get_selected_midi_item()
            return _create_success_response(f"Selected MIDI item: {item_info}")
        except Exception as e:
            logger.error(f"Failed to get selected MIDI item: {str(e)}")
            return _create_error_response(f"Failed to get selected MIDI item: {str(e)}")
