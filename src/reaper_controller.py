# This file is now just a wrapper around the controllers package

import os
import sys
from typing import Optional, List, Dict, Any, Union

# Add necessary paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)  # Add script directory to path

# Import controllers directly from the local directory
from controllers.track_controller import TrackController
from controllers.fx_controller import FXController
from controllers.marker_controller import MarkerController
from controllers.midi_controller import MIDIController
from controllers.audio_controller import AudioController
from controllers.master_controller import MasterController
from controllers.project_controller import ProjectController

# Create a combined controller that inherits from all controllers
class ReaperController:
    """Controller for interacting with Reaper using reapy.
    
    This class combines all controller functionality from specialized controllers.
    """
    def __init__(self, debug=False):
        # Initialize the base controller first
        
        # Initialize other controllers as attributes
        self.track = TrackController(debug=debug)
        self.fx = FXController(debug=debug)
        self.marker = MarkerController(debug=debug)
        self.midi = MIDIController(debug=debug)
        self.audio = AudioController(debug=debug)
        self.master = MasterController(debug=debug)
        self.project = ProjectController(debug=debug)

# Re-export the ReaperController class for backward compatibility
__all__ = ['ReaperController']
