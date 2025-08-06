import logging
import os
import sys

from mcp.server.fastmcp import FastMCP

# Add necessary paths for imports - handle both direct execution and module execution
script_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)  # Add script directory to path
sys.path.insert(0, parent_dir)  # Add parent directory to path

# Try importing with different approaches for module vs direct execution
try:
    # Try relative imports first (when run as module)
    from .reaper_controller import ReaperController
    from .mcp_tools import setup_mcp_tools
except ImportError:
    try:
        # Try absolute imports from src package
        from src.reaper_controller import ReaperController
        from src.mcp_tools import setup_mcp_tools
    except ImportError:
        # Fall back to direct imports (when run directly)
        from reaper_controller import ReaperController
        from mcp_tools import setup_mcp_tools


def main():
    # Setup logging to stderr only (not stdout which is used for MCP JSON)
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
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

    except ImportError as e:
        logger.error(f"Import error in MCP server: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        import traceback

        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
