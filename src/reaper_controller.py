"""
REAPER Controller - Composition-based architecture for REAPER integration.

This module provides organized access to REAPER functionality through
specialized controllers rather than a monolithic facade pattern.
"""

from __future__ import annotations

import importlib
import logging
from typing import Optional

# No top-level controller imports to reduce coupling (lazy-loaded)


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

        self._connection_verified = None
        self._controllers = {}

    def _get_controller(self, controller_type: str):
        """Get or create a controller instance with lazy loading and error handling."""
        if controller_type not in self._controllers:
            try:
                # Lazy import to reduce module-level coupling
                mapping = {
                    "track": "controllers.track.track_controller.TrackController",
                    "fx": "controllers.fx.fx_controller.FXController",
                    "marker": "controllers.marker.marker_controller.MarkerController",
                    "midi": "controllers.midi.midi_controller.MIDIController",
                    "audio": "controllers.audio.audio_controller.AudioController",
                    "master": "controllers.master.master_controller.MasterController",
                    "project": "controllers.project.project_controller.ProjectController",
                    "routing": "controllers.routing.routing_controller.RoutingController",
                    "advanced_routing": "controllers.routing.advanced_routing_controller.AdvancedRoutingController",
                    "sidechain": "controllers.routing.sidechain_controller.SidechainController",
                    "automation": "controllers.automation.automation_controller.AutomationController",
                    "advanced_items": "controllers.audio.advanced_item_controller.AdvancedItemController",
                    "analysis": "controllers.analysis.analysis_controller.AnalysisController",
                }
                module_path, class_name = mapping[controller_type].rsplit(".", 1)
                module = importlib.import_module(module_path, package=__package__)
                controller_class = getattr(module, class_name)
                self._controllers[controller_type] = controller_class(debug=self.debug)
            except Exception as e:
                self.logger.error(
                    f"Failed to initialize {controller_type} controller: {e}"
                )
                self._controllers[controller_type] = (
                    self._create_placeholder_controller(controller_type)
                )
        return self._controllers[controller_type]

    def _create_placeholder_controller(self, controller_type: str):
        """Create a placeholder controller when initialization fails."""

        class PlaceholderController:
            def __init__(self, name: str):
                self.name = name
                self.logger = logging.getLogger(f"Placeholder{name}")

            def __getattr__(self, method_name: str):
                def method(*args, **kwargs):
                    self.logger.warning(
                        f"REAPER not connected. {self.name}.{method_name}() unavailable."
                    )
                    return None

                return method

        return PlaceholderController(controller_type.title() + "Controller")

    @property
    def track(self) -> TrackController:
        """Get the track controller for track operations."""
        return self._get_controller("track")

    @property
    def fx(self) -> FXController:
        """Get the FX controller for effects operations."""
        return self._get_controller("fx")

    @property
    def marker(self) -> MarkerController:
        """Get the marker controller for timeline operations."""
        return self._get_controller("marker")

    @property
    def midi(self) -> MIDIController:
        """Get the MIDI controller for MIDI operations."""
        return self._get_controller("midi")

    @property
    def audio(self) -> AudioController:
        """Get the audio controller for audio item operations."""
        return self._get_controller("audio")

    @property
    def master(self) -> MasterController:
        """Get the master controller for master track operations."""
        return self._get_controller("master")

    @property
    def project(self) -> ProjectController:
        """Get the project controller for project-level operations."""
        return self._get_controller("project")

    @property
    def routing(self) -> RoutingController:
        """Get the routing controller for send/receive operations."""
        return self._get_controller("routing")

    @property
    def advanced_routing(self) -> AdvancedRoutingController:
        """Get the advanced routing controller for complex routing operations."""
        return self._get_controller("advanced_routing")

    @property
    def sidechain(self) -> SidechainController:
        """Get the sidechain controller for sidechain and bus routing operations."""
        return self._get_controller("sidechain")

    @property
    def automation(self) -> AutomationController:
        """Get the automation controller for automation operations."""
        return self._get_controller("automation")

    @property
    def advanced_items(self) -> AdvancedItemController:
        """Get the advanced items controller for complex item operations."""
        return self._get_controller("advanced_items")

    @property
    def analysis(self) -> AnalysisController:
        """Get the analysis controller for loudness and spectrum analysis."""
        return self._get_controller("analysis")

    def verify_connection(self) -> bool:
        """Verify connection to REAPER."""
        if self._connection_verified is not None:
            return self._connection_verified

        try:
            import socket
            from constants import REAPER_DEFAULT_PORTS

            ports_to_try = REAPER_DEFAULT_PORTS

            for port in ports_to_try:
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1.0)
                    result = sock.connect_ex(("localhost", port))
                    sock.close()

                    if result == 0:
                        self.logger.info(f"REAPER server found on port {port}")
                        self._connection_verified = True
                        return True

                except Exception:
                    continue

            self.logger.warning(
                "REAPER connection failed: No server found on common ports (2306-2309)"
            )
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
__all__ = ["ReaperController", "ReaperControllerFactory", "create_reaper_controller"]
