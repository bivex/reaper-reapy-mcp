"""
Centralized REAPER API bridge for consistent reapy access across the application.
This module provides a single point of access to reapy instances to avoid
circular imports and duplicate initialization code.
"""

import logging
import importlib

logger = logging.getLogger(__name__)

_reapy_instance = None
_rpr_instance = None


def _is_rpr_alive(rpr) -> bool:
    """Check that reascript_api has real REAPER functions loaded."""
    return rpr is not None and hasattr(rpr, "EnumProjects")


def _try_reconnect(reapy_module) -> bool:
    """
    Attempt to reconnect reapy to REAPER.
    Returns True if connection is now alive.
    """
    try:
        # reapy.reconnect() re-registers machine and refreshes the socket
        reapy_module.reconnect()
        return _is_rpr_alive(reapy_module.reascript_api)
    except Exception as e:
        logger.debug(f"reapy reconnect attempt failed: {e}")
        return False


def get_reapy():
    """
    Get reapy instance with lazy initialization.

    Re-connects if the cached reascript_api has no REAPER functions
    (happens when the MCP server starts before REAPER's reapy socket
    is active).

    Returns:
        reapy module: The reapy module instance

    Raises:
        ImportError: If reapy cannot be imported
    """
    global _reapy_instance, _rpr_instance

    if _reapy_instance is None:
        try:
            reapy_module = importlib.import_module("reapy")
            _reapy_instance = reapy_module
            _rpr_instance = reapy_module.reascript_api
            logger.debug("Reapy module initialized successfully")
        except ImportError as e:
            logger.error(f"Failed to import reapy: {e}")
            raise

    # If reascript_api is empty (server started before REAPER socket was up),
    # try to reconnect on every call until it works.
    if not _is_rpr_alive(_rpr_instance):
        logger.warning("reascript_api has no REAPER functions — attempting reconnect")
        if _try_reconnect(_reapy_instance):
            _rpr_instance = _reapy_instance.reascript_api
            logger.info("reapy reconnected successfully")
        else:
            logger.warning("reapy reconnect failed — REAPER may not be running or reapy server not active")

    return _reapy_instance


def get_rpr():
    """
    Get reapy.reascript_api instance.

    Returns:
        ReaScript API instance for low-level REAPER operations
    """
    get_reapy()  # Ensure reapy is initialized
    return _rpr_instance


def reset_instances():
    """
    Reset the cached instances. Useful for testing.
    """
    global _reapy_instance, _rpr_instance
    _reapy_instance = None
    _rpr_instance = None
