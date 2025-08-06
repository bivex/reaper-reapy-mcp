"""
REAPER Controller - Composition-based architecture for REAPER integration.

This module provides organized access to REAPER functionality through 
specialized controllers rather than a monolithic facade pattern.
"""
import os
import sys
import logging
from typing import Optional

# Add necessary paths for imports
script_dir = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(script_dir)
sys.path.insert(0, script_dir)  # Add script directory to path

# Import controllers using relative imports to avoid circular imports
from controllers.track.track_controller import TrackController
from controllers.fx.fx_controller import FXController
from controllers.marker.marker_controller import MarkerController
from controllers.midi.midi_controller import MIDIController
from controllers.audio.audio_controller import AudioController
from controllers.master.master_controller import MasterController
from controllers.project.project_controller import ProjectController
from controllers.routing.routing_controller import RoutingController
from controllers.routing.advanced_routing_controller import AdvancedRoutingController
from controllers.automation.automation_controller import AutomationController
from controllers.audio.advanced_item_controller import AdvancedItemController


class ReaperControllerFactory:
    """
    Factory for creating and managing REAPER controller instances.
    
    Provides organized access to REAPER functionality through specialized controllers
    instead of a monolithic facade. This improves modularity and maintainability.
    """
    
    def __init__(self, debug: bool = False):
        """
        Initialize the controller factory.
        
        Args:
            debug (bool): Enable debug logging for all controllers
        """
        self.debug = debug
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
        
        # Connection status
        self._connection_verified = None
        
        # Initialize controllers lazily
        self._controllers = {}
    
    def _get_controller(self, controller_type: str):
        """Get or create a controller instance with error handling."""
        if controller_type not in self._controllers:
            try:
                controller_class = {
                    'track': TrackController,
                    'fx': FXController,
                    'marker': MarkerController,
                    'midi': MIDIController,
                    'audio': AudioController,
                    'master': MasterController,
                    'project': ProjectController,
                    'routing': RoutingController,
                    'advanced_routing': AdvancedRoutingController,
                    'automation': AutomationController,
                    'advanced_items': AdvancedItemController,
                }[controller_type]
                
                self._controllers[controller_type] = controller_class(debug=self.debug)
                
            except Exception as e:
                self.logger.error(f"Failed to initialize {controller_type} controller: {e}")
                # Create placeholder that fails gracefully
                self._controllers[controller_type] = self._create_placeholder_controller(controller_type)
        
        return self._controllers[controller_type]
    
    def _create_placeholder_controller(self, controller_type: str):
        """Create a placeholder controller when initialization fails."""
        class PlaceholderController:
            def __init__(self, name: str):
                self.name = name
                self.logger = logging.getLogger(f"Placeholder{name}")
            
            def __getattr__(self, method_name: str):
                def method(*args, **kwargs):
                    self.logger.warning(f"REAPER not connected. {self.name}.{method_name}() unavailable.")
                    return None
                return method
        
        return PlaceholderController(controller_type.title() + "Controller")
    
    @property
    def track(self) -> TrackController:
        """Get the track controller for track operations."""
        return self._get_controller('track')
    
    @property
    def fx(self) -> FXController:
        """Get the FX controller for effects operations."""
        return self._get_controller('fx')
    
    @property
    def marker(self) -> MarkerController:
        """Get the marker controller for timeline operations."""
        return self._get_controller('marker')
    
    @property
    def midi(self) -> MIDIController:
        """Get the MIDI controller for MIDI operations."""
        return self._get_controller('midi')
    
    @property
    def audio(self) -> AudioController:
        """Get the audio controller for audio item operations."""
        return self._get_controller('audio')
    
    @property
    def master(self) -> MasterController:
        """Get the master controller for master track operations."""
        return self._get_controller('master')
    
    @property
    def project(self) -> ProjectController:
        """Get the project controller for project-level operations."""
        return self._get_controller('project')
    
    @property
    def routing(self) -> RoutingController:
        """Get the routing controller for send/receive operations."""
        return self._get_controller('routing')
    
    @property
    def advanced_routing(self) -> AdvancedRoutingController:
        """Get the advanced routing controller for complex routing operations."""
        return self._get_controller('advanced_routing')
    
    @property
    def automation(self) -> AutomationController:
        """Get the automation controller for automation operations."""
        return self._get_controller('automation')
    
    @property
    def advanced_items(self) -> AdvancedItemController:
        """Get the advanced items controller for complex item operations."""
        return self._get_controller('advanced_items')
    
    def verify_connection(self) -> bool:
        """Verify connection to REAPER."""
        if self._connection_verified is not None:
            return self._connection_verified
        
        try:
            import socket
            ports_to_try = [2306, 2307, 2308, 2309]
            
            for port in ports_to_try:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.0)
                    result = sock.connect_ex(('localhost', port))
                    sock.close()
                    
                    if result == 0:
                        self.logger.info(f"REAPER server found on port {port}")
                        self._connection_verified = True
                        return True
                        
                except Exception:
                    continue
            
            self.logger.warning("REAPER connection failed: No server found on common ports (2306-2309)")
            self._connection_verified = False
            return False
                    
        except Exception as e:
            self.logger.warning(f"REAPER connection test failed: {e}")
            self._connection_verified = False
            return False


# Backward compatibility: Create a factory instance that behaves like the old class
class ReaperController(ReaperControllerFactory):
    """
    Backward compatibility wrapper for ReaperControllerFactory.
    
    Maintains the same interface as before but uses the new composition-based architecture.
    """
    pass


# Factory function for creating controller instances
def create_reaper_controller(debug: bool = False) -> ReaperControllerFactory:
    """
    Create a new REAPER controller factory instance.
    
    Args:
        debug (bool): Enable debug logging
        
    Returns:
        ReaperControllerFactory: Factory instance for accessing controllers
    """
    return ReaperControllerFactory(debug=debug)


# Re-export for backward compatibility
__all__ = ['ReaperController', 'ReaperControllerFactory', 'create_reaper_controller']