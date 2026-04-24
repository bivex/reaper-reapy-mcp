"""MCP tools package."""

from ._connection import _setup_connection_tools as setup_connection_tools
from ._track import _setup_track_tools as setup_track_tools
from ._project import _setup_project_tools as setup_project_tools
from ._midi import _setup_midi_tools as setup_midi_tools
from ._master import _setup_master_tools as setup_master_tools
from ._automation import _setup_automation_tools as setup_automation_tools
from ._analysis import _setup_analysis_tools as setup_analysis_tools
from ._fx import _setup_fx_tools as setup_fx_tools
from ._audio import (
    _setup_audio_tools as setup_audio_tools,
    _setup_advanced_item_tools as setup_advanced_item_tools,
)
from ._routing import _setup_routing_tools as setup_routing_tools


def setup_mcp_tools(mcp, controller) -> None:
    """Register all MCP tools with the server."""
    setup_connection_tools(mcp, controller)
    setup_track_tools(mcp, controller)
    setup_project_tools(mcp, controller)
    setup_midi_tools(mcp, controller)
    setup_master_tools(mcp, controller)
    setup_automation_tools(mcp, controller)
    setup_analysis_tools(mcp, controller)
    setup_fx_tools(mcp, controller)
    setup_audio_tools(mcp, controller)
    setup_advanced_item_tools(mcp, controller)
    setup_routing_tools(mcp, controller)


__all__ = [
    "setup_connection_tools",
    "setup_track_tools",
    "setup_project_tools",
    "setup_midi_tools",
    "setup_master_tools",
    "setup_automation_tools",
    "setup_analysis_tools",
    "setup_fx_tools",
    "setup_audio_tools",
    "setup_advanced_item_tools",
    "setup_routing_tools",
    "setup_mcp_tools",
]
