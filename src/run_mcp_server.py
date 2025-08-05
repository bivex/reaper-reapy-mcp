import logging
import os
import sys

# Add necessary paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)  # Add script directory to path

from mcp.server.fastmcp import FastMCP
from mcp import StdioServerParameters

# Import directly from the same directory
from reaper_controller import ReaperController
from mcp_tools import setup_mcp_tools

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    print("Starting MCP server for Reaper...")
    
    try:
        # Create Reaper controller with connection check
        print("Initializing ReaperController...")
        controller = ReaperController(debug=True)
        
        # Check if REAPER connection is available
        if not controller.verify_connection():
            print("\n[WARNING] REAPER connection not available!")
            print("The MCP server will start, but REAPER operations will fail.")
            print("\nTo fix this:")
            print("1. Make sure REAPER is running")
            print("2. Run: python start_reapy_server_simple.py")
            print("3. Or enable the reapy remote API in REAPER")
            print()
        
        print("ReaperController initialized successfully.")
        
        # Create MCP server
        mcp = FastMCP("Reaper Control")
        
        # Setup MCP tools
        setup_mcp_tools(mcp, controller)
        
        # Run MCP server
        logger.info("Starting MCP server...")
        print("[SUCCESS] MCP server started successfully!")
        print("You can now use REAPER control tools through MCP.")
        mcp.run()
        
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        print(f"\n[ERROR] Failed to start MCP server: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: uv sync")
        print("2. Check if REAPER is running and accessible")
        print("3. Try running: python start_reapy_server_simple.py")
        raise

if __name__ == "__main__":
    main()
