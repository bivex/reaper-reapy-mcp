"""
Controllers for interacting with Reaper using reapy.

This package contains specialized controllers for different aspects of Reaper functionality:
- TrackController: Track creation, renaming, and management
- FXController: Effects management
- MarkerController: Marker and region operations
- MIDIController: MIDI item creation and manipulation
- AudioController: Audio file insertion and media operations
- MasterController: Master track operations
- ProjectController: Project-level operations

The ReaperController class (defined in `reaper_controller.py`) combines all these controllers 
into a single, easy-to-use class using composition.
"""

# Import controllers so they can be imported from the controllers package
from .track.track_controller import TrackController
from .fx.fx_controller import FXController
from .marker.marker_controller import MarkerController
from .midi.midi_controller import MIDIController
from .audio.audio_controller import AudioController
from .master.master_controller import MasterController
from .project.project_controller import ProjectController
