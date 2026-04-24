"""Internal helpers for MCP tool registration."""

from mcp.server.fastmcp import FastMCP, Context
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# MIDI constants
DEFAULT_MIDI_LENGTH = 4.0
DEFAULT_MIDI_VELOCITY = 96
MAX_MIDI_PITCH = 127
MIN_MIDI_PITCH = 0


def _create_success_response(message: str) -> Dict[str, Any]:
    """Create a standardized success response."""
    return {"status": "success", "message": message}


def _create_error_response(message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {"status": "error", "message": message}


def _handle_controller_operation(
    operation_name: str, operation_func, *args, **kwargs
) -> Dict[str, Any]:
    """Generic handler for controller operations with proper error handling."""
    try:
        result = operation_func(*args, **kwargs)
        if result is True or (isinstance(result, (int, float)) and result >= 0):
            return _create_success_response(f"{operation_name} completed successfully")
        elif result is False or (isinstance(result, (int, float)) and result < 0):
            return _create_error_response(f"Failed to {operation_name.lower()}")
        elif result is not None:
            return _create_success_response(f"{operation_name} completed successfully")
        else:
            return _create_error_response(f"Failed to {operation_name.lower()}")
    except Exception as e:
        logger.error(f"Controller operation failed: {operation_name} - {str(e)}")
        return _create_error_response(f"Failed to {operation_name.lower()}: {str(e)}")
