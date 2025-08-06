import logging
import os
import re
from typing import List, Dict, Any, Optional
import sys

# Add utils path for imports
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

from src.core.reapy_bridge import get_reapy

# Constants to replace magic numbers
PLUGIN_NAME_INDEX = 2  # Index of plugin name in comma-separated format
MIN_PLUGIN_NAME_PARTS = 3  # Minimum parts needed for plugin name extraction


class FXController:
    """Controller for FX-related operations in Reaper."""

    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)
        
        # Initialize RPR reference
        try:
            reapy = get_reapy()
            self._RPR = reapy.reascript_api
        except Exception as e:
            self.logger.error(f"Failed to initialize RPR: {e}")
            self._RPR = None

    def add_fx_to_track(self, track_index: int, fx_name: str) -> bool:
        """
        Add an FX to a track.

        Args:
            track_index (int): Index of the track
            fx_name (str): Name of the FX to add

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]

            # Add FX using ReaScript API
            fx_id = self._RPR.TrackFX_AddByName(track.id, fx_name, False, 1)
            return fx_id >= 0

        except Exception as e:
            error_message = f"Failed to add FX {fx_name} to track {track_index}: {e}"
            self.logger.error(error_message)
            return False

    def add_fx(self, track_index: int, fx_name: str) -> int:
        """
        Add an FX to a track and return the FX index.

        Args:
            track_index (int): Index of the track
            fx_name (str): Name of the FX to add

        Returns:
            int: FX index if successful, -1 otherwise
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]

            # Add FX using ReaScript API
            fx_id = self._RPR.TrackFX_AddByName(track.id, fx_name, False, 1)

            if fx_id >= 0:
                self.logger.info(
                    f"Added FX {fx_name} to track {track_index} at index {fx_id}"
                )
            else:
                self.logger.error(f"Failed to add FX {fx_name} to track {track_index}")

            return fx_id

        except Exception as e:
            error_message = f"Failed to add FX {fx_name} to track {track_index}: {e}"
            self.logger.error(error_message)
            return -1

    def remove_fx(self, track_index: int, fx_index: int) -> bool:
        """
        Remove an FX from a track.

        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX to remove

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]

            # Remove the FX using ReaScript API
            success = self._RPR.TrackFX_Delete(track.id, fx_index)

            if success:
                self.logger.info(f"Removed FX {fx_index} from track {track_index}")
            else:
                self.logger.error(
                    f"Failed to remove FX {fx_index} from track {track_index}"
                )

            return success

        except Exception as e:
            self.logger.error(f"Failed to remove FX: {e}")
            return False

    def set_fx_param(
        self, track_index: int, fx_index: int, param_name: str, value: float
    ) -> bool:
        """
        Set a parameter value for an FX.

        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            param_name (str): Name of the parameter
            value (float): Value to set

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if self._RPR is None:
                self.logger.error("RPR not initialized")
                return False
                
            project = get_reapy().Project()
            track = project.tracks[track_index]

            # Get the parameter index by name
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)

            for i in range(param_count):
                # Use proper buffer for parameter name retrieval
                buf_size = 256
                param_name_buf = "\x00" * buf_size
                retval = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, param_name_buf, buf_size)
                
                if retval:
                    param_name_retrieved = param_name_buf.rstrip('\x00')
                    
                    # Case-insensitive partial match to handle parameter name variations
                    if param_name.lower() in param_name_retrieved.lower() or param_name_retrieved.lower() in param_name.lower():
                        # Set the parameter value
                        self._RPR.TrackFX_SetParam(track.id, fx_index, i, value)
                        self.logger.info(f"Set FX parameter '{param_name_retrieved}' to {value}")
                        return True

            self.logger.error(f"Parameter '{param_name}' not found in FX {fx_index}")
            return False

        except Exception as e:
            self.logger.error(f"Failed to set FX parameter: {e}")
            return False

    def get_fx_param(self, track_index: int, fx_index: int, param_name: str) -> float:
        """
        Get a parameter value from an FX.

        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            param_name (str): Name of the parameter

        Returns:
            float: Parameter value, or 0.0 if failed
        """
        try:
            if self._RPR is None:
                self.logger.error("RPR not initialized")
                return 0.0
                
            project = get_reapy().Project()
            track = project.tracks[track_index]

            # Get the parameter index by name
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)

            for i in range(param_count):
                # Use proper buffer for parameter name retrieval
                buf_size = 256
                param_name_buf = "\x00" * buf_size
                retval = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, param_name_buf, buf_size)
                
                if retval:
                    param_name_retrieved = param_name_buf.rstrip('\x00')
                    
                    # Case-insensitive partial match
                    if param_name.lower() in param_name_retrieved.lower() or param_name_retrieved.lower() in param_name.lower():
                        # Get the parameter value
                        value = self._RPR.TrackFX_GetParam(track.id, fx_index, i)
                        self.logger.info(f"Got FX parameter '{param_name_retrieved}': {value}")
                        return value

            self.logger.error(f"Parameter '{param_name}' not found in FX {fx_index}")
            return 0.0

        except Exception as e:
            error_message = f"Failed to get FX parameter '{param_name}': {e}"
            self.logger.error(error_message)
            return 0.0

    def get_fx_param_list(
        self, track_index: int, fx_index: int
    ) -> List[Dict[str, Any]]:
        """
        Get a list of all parameters for an FX.

        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX

        Returns:
            List[Dict[str, Any]]: List of parameter dictionaries
        """
        try:
            if self._RPR is None:
                self.logger.error("RPR not initialized")
                return []
                
            project = get_reapy().Project()
            track = project.tracks[track_index]

            param_list = []
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)
            
            self.logger.info(f"FX {fx_index} has {param_count} parameters")

            for i in range(param_count):
                # Use proper buffer size for parameter name
                buf_size = 256
                param_name_buf = "\x00" * buf_size
                
                # Get parameter name with proper buffer
                retval = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, param_name_buf, buf_size)
                
                if retval:
                    # Clean the parameter name (remove null bytes)
                    param_name = param_name_buf.rstrip('\x00')
                else:
                    param_name = f"Param_{i}"
                
                # Get parameter value
                param_value = self._RPR.TrackFX_GetParam(track.id, fx_index, i)
                
                # Get formatted parameter value for display
                format_buf = "\x00" * buf_size
                self._RPR.TrackFX_GetFormattedParamValue(track.id, fx_index, i, format_buf, buf_size)
                formatted_value = format_buf.rstrip('\x00')

                param_info = {
                    "index": i, 
                    "name": param_name, 
                    "value": param_value,
                    "formatted_value": formatted_value
                }
                param_list.append(param_info)
                
                self.logger.debug(f"Parameter {i}: {param_name} = {param_value} ({formatted_value})")

            self.logger.info(
                f"Retrieved {len(param_list)} parameters for FX {fx_index}"
            )
            return param_list

        except Exception as e:
            error_message = f"Failed to get FX parameter list for FX {fx_index}: {e}"
            self.logger.error(error_message)
            return []

    def get_fx_list(self, track_index: int) -> List[Dict[str, Any]]:
        """
        Get a list of all FX on a track.

        Args:
            track_index (int): Index of the track

        Returns:
            List[Dict[str, Any]]: List of FX dictionaries
        """
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]

            fx_list = []

            # Try using reapy's built-in method first
            try:
                reapy_fx_list = track.fxs
                for i, fx in enumerate(reapy_fx_list):
                    fx_info = {
                        "index": i,
                        "name": fx.name if hasattr(fx, "name") else f"FX_{i}",
                        "enabled": fx.is_enabled if hasattr(fx, "is_enabled") else True,
                    }
                    fx_list.append(fx_info)

                if fx_list:
                    self.logger.info(
                        f"Retrieved {len(fx_list)} FX for track {track_index} using reapy"
                    )
                    return fx_list

            except Exception as reapy_error:
                self.logger.warning(f"Reapy method failed: {reapy_error}")

            # Fallback to ReaScript API method
            fx_count = self._RPR.TrackFX_GetCount(track.id)

            for i in range(fx_count):
                fx_name = self._RPR.TrackFX_GetFXName(track.id, i, "")
                enabled = self._RPR.TrackFX_GetEnabled(track.id, i)

                fx_info = {"index": i, "name": fx_name, "enabled": enabled}
                fx_list.append(fx_info)

            self.logger.info(
                f"Retrieved {len(fx_list)} FX for track {track_index} using ReaScript API"
            )
            return fx_list

        except Exception as e:
            error_message = f"Failed to get FX list for track {track_index}: {e}"
            self.logger.error(error_message)
            return []

    def get_available_fx_list(self) -> List[str]:
        """
        Get a list of all available FX plugins in Reaper.

        Returns:
            List[str]: List of available FX names
        """
        try:
            fx_list = []

            # Try to read Reaper's plugin database files
            fx_list.extend(self._read_plugin_database())

            # Deduplicate and sort the list
            if fx_list:
                unique_fx_list = sorted(list(set(fx_list)))
                self.logger.info(f"Retrieved {len(unique_fx_list)} unique FX plugins")
                return unique_fx_list
            else:
                self.logger.warning("No FX plugins found through any method")
                return []

        except Exception as e:
            error_message = f"Failed to get available FX list: {e}"
            self.logger.error(error_message)
            return []

    def _read_plugin_database(self) -> List[str]:
        """Read Reaper's plugin database files to extract FX names."""
        fx_list = []

        try:
            self.logger.info("Attempting to read Reaper plugin database files")
            resource_paths = self._get_reaper_resource_paths()

            for resource_path in resource_paths:
                self.logger.info(f"Checking resource path: {resource_path}")
                fx_list.extend(self._parse_plugin_files(resource_path))

        except Exception as e:
            self.logger.warning(f"Failed to read Reaper plugin database: {e}")

        return fx_list

    def _get_reaper_resource_paths(self) -> List[str]:
        """Get possible Reaper resource paths."""
        resource_paths = []

        # Check common Windows locations
        appdata = os.environ.get("APPDATA")
        if appdata:
            resource_paths.append(os.path.join(appdata, "REAPER"))

        # Check if ReaperResourcePath is available through reapy
        try:
            resource_path = self._RPR.GetResourcePath()
            if resource_path:
                resource_paths.append(resource_path)
        except Exception as e:
            self.logger.warning(f"Failed to get Reaper resource path: {e}")

        return resource_paths

    def _parse_plugin_files(self, resource_path: str) -> List[str]:
        """Parse plugin database files in a resource path."""
        fx_list = []
        plugin_ini_files = [
            "reaper-plugs.ini",
            "reaper-plugs64.ini",
            "reaper-vstplugins.ini",
            "reaper-vstplugins64.ini",
        ]

        for ini_file in plugin_ini_files:
            ini_path = os.path.join(resource_path, ini_file)
            if os.path.exists(ini_path):
                self.logger.info(f"Found plugin database at: {ini_path}")
                fx_list.extend(self._parse_plugin_file(ini_path))

        return fx_list

    def _parse_plugin_file(self, file_path: str) -> List[str]:
        """Parse a single plugin database file."""
        fx_list = []

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    plugin_name = self._extract_plugin_name(line)
                    if plugin_name and plugin_name not in fx_list:
                        fx_list.append(plugin_name)
        except Exception as e:
            self.logger.warning(f"Failed to parse plugin file {file_path}: {e}")

        return fx_list

    def _extract_plugin_name(self, line: str) -> Optional[str]:
        """Extract plugin name from a database line."""
        if "=" not in line:
            return None

        parts = line.strip().split("=")
        if len(parts) <= 1:
            return None

        right_part = parts[1]

        # Try to extract names in the format: dll=ID,number,PluginName
        if "," in right_part:
            comma_parts = right_part.split(",")
            if len(comma_parts) >= MIN_PLUGIN_NAME_PARTS:
                plugin_name = comma_parts[PLUGIN_NAME_INDEX].strip()
                if plugin_name:
                    return plugin_name

        # Try to extract names in quotes
        for part in parts:
            if part.strip() and '"' in part:
                name_match = re.search(r'"([^"]+)"', part)
                if name_match:
                    return name_match.group(1)

        return None

    def toggle_fx(self, track_index: int, fx_index: int, enable: bool = None) -> bool:
        """
        Toggle or set the enable/disable state of an FX.

        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            enable (bool, optional): True to enable, False to disable, None to toggle

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]

            if enable is None:
                # Toggle the current state
                current_state = self._RPR.TrackFX_GetEnabled(track.id, fx_index)
                enable = not current_state

            # Set the enabled state
            success = self._RPR.TrackFX_SetEnabled(track.id, fx_index, enable)

            if success:
                state_str = "enabled" if enable else "disabled"
                self.logger.info(
                    f"{state_str.capitalize()} FX {fx_index} on track {track_index}"
                )
            else:
                self.logger.error(
                    f"Failed to toggle FX {fx_index} on track {track_index}"
                )

            return success

        except Exception as e:
            error_message = f"Failed to toggle FX: {e}"
            self.logger.error(error_message)
            return False

    def set_compressor_params(
        self,
        track_index: int,
        fx_index: int,
        threshold: Optional[float] = None,
        ratio: Optional[float] = None,
        attack: Optional[float] = None,
        release: Optional[float] = None,
        makeup_gain: Optional[float] = None,
    ) -> bool:
        """
        Set common compressor parameters. Works with most compressor plugins.

        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            threshold (float, optional): Threshold in dB (typical range: -60 to 0)
            ratio (float, optional): Compression ratio (typical range: 1.0 to 20.0)
            attack (float, optional): Attack time in ms (typical range: 0.1 to 100)
            release (float, optional): Release time in ms (typical range: 10 to 1000)
            makeup_gain (float, optional): Makeup gain in dB (typical range: 0 to 20)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]

            # Common parameter names across different compressor plugins
            param_mappings = {
                "threshold": ["Threshold", "Thresh", "threshold", "thresh"],
                "ratio": ["Ratio", "ratio"],
                "attack": ["Attack", "attack", "Attack Time", "Att"],
                "release": ["Release", "release", "Release Time", "Rel"],
                "makeup_gain": [
                    "Makeup",
                    "Make-up",
                    "Gain",
                    "Output",
                    "makeup",
                    "make-up",
                ],
            }

            success = True
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)

            # Get all parameter names
            param_names = []
            for i in range(param_count):
                param_name = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, "")
                param_names.append((i, param_name))

            # Set parameters based on input values
            params_to_set = [
                ("threshold", threshold),
                ("ratio", ratio),
                ("attack", attack),
                ("release", release),
                ("makeup_gain", makeup_gain),
            ]

            for param_type, value in params_to_set:
                if value is not None:
                    param_found = False
                    for param_idx, param_name in param_names:
                        for mapping in param_mappings[param_type]:
                            if mapping.lower() in param_name.lower():
                                # Convert value to appropriate range (0.0 to 1.0 for most plugins)
                                normalized_value = self._normalize_compressor_param(
                                    param_type, value
                                )
                                self._RPR.TrackFX_SetParam(
                                    track.id, fx_index, param_idx, normalized_value
                                )
                                self.logger.info(
                                    f"Set {param_type} to {value} (normalized: {normalized_value})"
                                )
                                param_found = True
                                break
                        if param_found:
                            break

                    if not param_found:
                        self.logger.warning(
                            f"Parameter '{param_type}' not found in compressor"
                        )
                        success = False

            return success

        except Exception as e:
            self.logger.error(f"Failed to set compressor parameters: {e}")
            return False

    def _normalize_compressor_param(self, param_type: str, value: float) -> float:
        """
        Normalize compressor parameter values to 0.0-1.0 range.

        Args:
            param_type (str): Type of parameter
            value (float): Raw parameter value

        Returns:
            float: Normalized value (0.0 to 1.0)
        """
        if param_type == "threshold":
            # Threshold: -60dB to 0dB -> 0.0 to 1.0
            return max(0.0, min(1.0, (value + 60.0) / 60.0))
        elif param_type == "ratio":
            # Ratio: 1.0 to 20.0 -> 0.0 to 1.0
            return max(0.0, min(1.0, (value - 1.0) / 19.0))
        elif param_type == "attack":
            # Attack: 0.1ms to 100ms -> 0.0 to 1.0 (log scale)
            import math

            return max(
                0.0, min(1.0, math.log10(max(0.1, value) / 0.1) / math.log10(1000))
            )
        elif param_type == "release":
            # Release: 10ms to 1000ms -> 0.0 to 1.0 (log scale)
            import math

            return max(0.0, min(1.0, math.log10(max(10, value) / 10) / math.log10(100)))
        elif param_type == "makeup_gain":
            # Makeup gain: 0dB to 20dB -> 0.0 to 1.0
            return max(0.0, min(1.0, value / 20.0))
        else:
            return max(0.0, min(1.0, value))

    def set_limiter_params(
        self,
        track_index: int,
        fx_index: int,
        threshold: Optional[float] = None,
        ceiling: Optional[float] = None,
        release: Optional[float] = None,
    ) -> bool:
        """
        Set common limiter parameters. Works with most limiter plugins.

        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            threshold (float, optional): Threshold in dB (typical range: -20 to 0)
            ceiling (float, optional): Output ceiling in dB (typical range: -10 to 0)
            release (float, optional): Release time in ms (typical range: 1 to 100)

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]

            # Common parameter names across different limiter plugins
            param_mappings = {
                "threshold": ["Threshold", "Thresh", "threshold", "thresh", "Input"],
                "ceiling": ["Ceiling", "Output", "Limit", "ceiling", "output", "limit"],
                "release": ["Release", "release", "Release Time", "Rel"],
            }

            success = True
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)

            # Get all parameter names
            param_names = []
            for i in range(param_count):
                param_name = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, "")
                param_names.append((i, param_name))

            # Set parameters based on input values
            params_to_set = [
                ("threshold", threshold),
                ("ceiling", ceiling),
                ("release", release),
            ]

            for param_type, value in params_to_set:
                if value is not None:
                    param_found = False
                    for param_idx, param_name in param_names:
                        for mapping in param_mappings[param_type]:
                            if mapping.lower() in param_name.lower():
                                # Convert value to appropriate range
                                normalized_value = self._normalize_limiter_param(
                                    param_type, value
                                )
                                self._RPR.TrackFX_SetParam(
                                    track.id, fx_index, param_idx, normalized_value
                                )
                                self.logger.info(
                                    f"Set limiter {param_type} to {value} (normalized: {normalized_value})"
                                )
                                param_found = True
                                break
                        if param_found:
                            break

                    if not param_found:
                        self.logger.warning(
                            f"Parameter '{param_type}' not found in limiter"
                        )
                        success = False

            return success

        except Exception as e:
            self.logger.error(f"Failed to set limiter parameters: {e}")
            return False

    def _normalize_limiter_param(self, param_type: str, value: float) -> float:
        """
        Normalize limiter parameter values to 0.0-1.0 range.

        Args:
            param_type (str): Type of parameter
            value (float): Raw parameter value

        Returns:
            float: Normalized value (0.0 to 1.0)
        """
        if param_type == "threshold":
            # Threshold: -20dB to 0dB -> 0.0 to 1.0
            return max(0.0, min(1.0, (value + 20.0) / 20.0))
        elif param_type == "ceiling":
            # Ceiling: -10dB to 0dB -> 0.0 to 1.0
            return max(0.0, min(1.0, (value + 10.0) / 10.0))
        elif param_type == "release":
            # Release: 1ms to 100ms -> 0.0 to 1.0 (log scale)
            import math

            return max(0.0, min(1.0, math.log10(max(1, value)) / math.log10(100)))
        else:
            return max(0.0, min(1.0, value))

    def get_track_peak_level(self, track_index: int) -> Dict[str, float]:
        """
        Get the current peak levels for a track.

        Args:
            track_index (int): Index of the track

        Returns:
            Dict[str, float]: Peak levels in dB for left and right channels
        """
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]

            # Get peak levels using ReaScript API
            left_peak = self._RPR.Track_GetPeakInfo(track.id, 0)  # Left channel
            right_peak = self._RPR.Track_GetPeakInfo(track.id, 1)  # Right channel

            # Convert linear to dB
            import math
            from constants import (
                DB_CONVERSION_FACTOR,
                SILENCE_THRESHOLD_DB,
                MINIMUM_PEAK_VALUE,
            )

            left_db = (
                DB_CONVERSION_FACTOR * math.log10(max(MINIMUM_PEAK_VALUE, left_peak))
                if left_peak > 0
                else SILENCE_THRESHOLD_DB
            )
            right_db = (
                DB_CONVERSION_FACTOR * math.log10(max(MINIMUM_PEAK_VALUE, right_peak))
                if right_peak > 0
                else SILENCE_THRESHOLD_DB
            )

            return {
                "left_peak_db": left_db,
                "right_peak_db": right_db,
                "max_peak_db": max(left_db, right_db),
            }

        except Exception as e:
            self.logger.error(f"Failed to get track peak level: {e}")
            from constants import SILENCE_THRESHOLD_DB

            return {
                "left_peak_db": SILENCE_THRESHOLD_DB,
                "right_peak_db": SILENCE_THRESHOLD_DB,
                "max_peak_db": SILENCE_THRESHOLD_DB,
            }

    def get_master_peak_level(self) -> Dict[str, float]:
        """
        Get the current peak levels for the master track.

        Returns:
            Dict[str, float]: Peak levels in dB for left and right channels
        """
        try:
            project = get_reapy().Project()
            master_track = project.master_track

            # Get peak levels using ReaScript API
            left_peak = self._RPR.Track_GetPeakInfo(master_track.id, 0)  # Left channel
            right_peak = self._RPR.Track_GetPeakInfo(
                master_track.id, 1
            )  # Right channel

            # Convert linear to dB
            import math
            from constants import (
                DB_CONVERSION_FACTOR,
                SILENCE_THRESHOLD_DB,
                MINIMUM_PEAK_VALUE,
            )

            left_db = (
                DB_CONVERSION_FACTOR * math.log10(max(MINIMUM_PEAK_VALUE, left_peak))
                if left_peak > 0
                else SILENCE_THRESHOLD_DB
            )
            right_db = (
                DB_CONVERSION_FACTOR * math.log10(max(MINIMUM_PEAK_VALUE, right_peak))
                if right_peak > 0
                else SILENCE_THRESHOLD_DB
            )

            return {
                "left_peak_db": left_db,
                "right_peak_db": right_db,
                "max_peak_db": max(left_db, right_db),
            }

        except Exception as e:
            self.logger.error(f"Failed to get master peak level: {e}")
            from constants import SILENCE_THRESHOLD_DB

            return {
                "left_peak_db": SILENCE_THRESHOLD_DB,
                "right_peak_db": SILENCE_THRESHOLD_DB,
                "max_peak_db": SILENCE_THRESHOLD_DB,
            }
