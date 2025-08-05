import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import reapy
    print("Reapy imported successfully")
    
    # Try to enable distant API first
    try:
        reapy.config.enable_dist_api()
        print("Distant API enabled successfully")
    except Exception as e:
        print(f"Could not enable distant API: {e}")
    
    # Try to connect
    try:
        reapy.connect()
        print("Connected to REAPER")
        
        # Try to get project
        project = reapy.Project()
        print("Connected to project:", project.name)
        
        # Check if we can access project properties
        try:
            track_count = len(project.tracks)
            print(f"Project has {track_count} tracks")
            print("✅ Connection test PASSED - REAPER is accessible!")
        except Exception as e:
            print(f"Could not access project properties: {e}")
        
    except Exception as e:
        print(f"Connection failed: {e}")
        print("Please enable distant API in REAPER first")
        print("Run one of the enable scripts in REAPER as ReaScript")
        
except Exception as e:
    print(f"Failed to import or use reapy: {e}")
