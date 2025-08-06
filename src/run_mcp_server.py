import logging
import os
import sys

from mcp.server.fastmcp import FastMCP
from reaper_controller import ReaperController
from mcp_tools import setup_mcp_tools

# Add necessary paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)  # Add script directory to path


def main():
    # Setup logging to stderr only (not stdout which is used for MCP JSON)
    logging.basicConfig(
        level=logging.ERROR,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )
    logger = logging.getLogger(__name__)

    try:
        # Create Reaper controller with connection check
        controller = ReaperController(debug=False)

        # Create MCP server
        mcp = FastMCP("Reaper Control")

        # Setup MCP tools
        setup_mcp_tools(mcp, controller)

        # Run MCP server (this will handle stdio communication)
        mcp.run()

    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
