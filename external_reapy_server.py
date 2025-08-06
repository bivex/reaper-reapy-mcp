#!/usr/bin/env python3
"""
External reapy server that runs outside REAPER
Run this with Python 3.x to start reapy server
"""

import sys
import time

# Check Python version
if sys.version_info[0] < 3:
    print("Error: This script requires Python 3.x")
    print("Current version:", sys.version)
    sys.exit(1)

try:
    import reapy

    print("Starting external reapy server...")

    # Configure reapy for external use
    reapy.config.configure_reaper()

    print("Reapy server configured successfully!")
    print("You can now use reapy from external applications.")
    print("Press Ctrl+C to stop the server.")

    # Keep the server running
    while True:
        time.sleep(1)

except ImportError:
    print("Error: reapy not installed.")
    print("Install with: pip install python-reapy")
    sys.exit(1)
except KeyboardInterrupt:
    print("\nServer stopped.")
except Exception as e:
    print("Error:", str(e))
    sys.exit(1)
