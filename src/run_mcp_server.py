import logging
import sys
import os

# Support both direct execution and module execution
# When run as `python3 /path/to/run_mcp_server.py`, relative imports fail.
# Fix by inserting the project root into sys.path.
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
if _root not in sys.path:
    sys.path.insert(0, _root)
if _here not in sys.path:
    sys.path.insert(0, _here)

from mcp.server.fastmcp import FastMCP

# Use absolute imports when run as script, relative when run as module
try:
    from .reaper_controller import ReaperController
    from .mcp_tools import setup_mcp_tools
except ImportError:
    from reaper_controller import ReaperController  # type: ignore[no-redef]
    from mcp_tools import setup_mcp_tools  # type: ignore[no-redef]


def main():
    logging.basicConfig(
        level=logging.ERROR,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    logger = logging.getLogger(__name__)

    try:
        controller = ReaperController(debug=False)
        mcp = FastMCP("Reaper Control")
        setup_mcp_tools(mcp, controller)
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
