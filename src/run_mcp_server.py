import logging
import sys
from mcp.server.fastmcp import FastMCP
from .reaper_controller import ReaperController
from .mcp_tools import setup_mcp_tools


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
