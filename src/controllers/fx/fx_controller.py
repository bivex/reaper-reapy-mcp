import reapy
import logging
import os
import re
from typing import List, Dict, Any, Optional
from reapy import reascript_api as RPR

# Constants to replace magic numbers
PLUGIN_NAME_INDEX = 2  # Index of plugin name in comma-separated format
MIN_PLUGIN_NAME_PARTS = 3  # Minimum parts needed for plugin name extraction

class FXController:
    """Controller for FX-related operations in Reaper."""
    
    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)

    def add_fx(self, track_index: int, fx_name: str) -> int:
        """
        Add an FX to a track.
        
        Args:
            track_index (int): Index of the track
            fx_name (str): Name of the FX to add
            
        Returns:
            int: Index of the added FX, or -1 if failed
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Try using reapy's built-in method first
            try:
                fx = track.add_fx(fx_name)
                if fx:
                    self.logger.info(
                        f"Added FX '{fx_name}' to track {track_index} using reapy method"
                    )
                    return 0  # Return 0 as the first FX index
            except Exception as reapy_error:
                self.logger.warning(f"Reapy method failed: {reapy_error}")
            
            # Fallback to ReaScript API method
            # First, try to select the track
            RPR.SetOnlyTrackSelected(track.id)
            
            # Add the FX using ReaScript API
            fx_index = RPR.TrackFX_AddByName(
                track.id, fx_name, False, 0
            )
            
            if fx_index >= 0:
                self.logger.info(
                    f"Added FX '{fx_name}' to track {track_index} at index {fx_index}"
                )
                return fx_index
            else:
                self.logger.error(
                    f"Failed to add FX '{fx_name}' to track {track_index}"
                )
                return -1
            
        except Exception as e:
            self.logger.error(f"Failed to add FX: {e}")
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
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Remove the FX using ReaScript API
            success = RPR.TrackFX_Delete(
                track.id, fx_index
            )
            
            if success:
                self.logger.info(
                    f"Removed FX {fx_index} from track {track_index}"
                )
            else:
                self.logger.error(
                    f"Failed to remove FX {fx_index} from track {track_index}"
                )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to remove FX: {e}")
            return False

    def set_fx_param(self, track_index: int, fx_index: int, param_name: str, 
                    value: float) -> bool:
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
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Get the parameter index by name
            param_count = RPR.TrackFX_GetNumParams(track.id, fx_index)
            
            for i in range(param_count):
                param_name_retrieved = RPR.TrackFX_GetParamName(
                    track.id, fx_index, i, ""
                )
                if param_name_retrieved == param_name:
                    # Set the parameter value
                    success = RPR.TrackFX_SetParam(track.id, fx_index, i, value)
                    if success:
                        self.logger.info(f"Set FX parameter '{param_name}' to {value}")
                    return success
            
            self.logger.error(
                f"Parameter '{param_name}' not found in FX {fx_index}"
            )
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
            project = reapy.Project()
            track = project.tracks[track_index]
            
            # Get the parameter index by name
            param_count = RPR.TrackFX_GetNumParams(track.id, fx_index)
            
            for i in range(param_count):
                param_name_retrieved = RPR.TrackFX_GetParamName(
                    track.id, fx_index, i, ""
                )
                if param_name_retrieved == param_name:
                    # Get the parameter value
                    value = RPR.TrackFX_GetParam(track.id, fx_index, i)
                    self.logger.info(f"Got FX parameter '{param_name}': {value}")
                    return value
            
            self.logger.error(
                f"Parameter '{param_name}' not found in FX {fx_index}"
            )
            return 0.0
            
        except Exception as e:
            error_message = f"Failed to get FX parameter '{param_name}': {e}"
            self.logger.error(error_message)
            return 0.0

    def get_fx_param_list(self, track_index: int, fx_index: int) -> List[Dict[str, Any]]:
        """
        Get a list of all parameters for an FX.
        
        Args:
            track_index (int): Index of the track
            fx_index (int): Index of the FX
            
        Returns:
            List[Dict[str, Any]]: List of parameter dictionaries
        """
        try:
            project = reapy.Project()
            track = project.tracks[track_index]
            
            param_list = []
            param_count = RPR.TrackFX_GetNumParams(track.id, fx_index)
            
            for i in range(param_count):
                param_name = RPR.TrackFX_GetParamName(
                    track.id, fx_index, i, ""
                )
                param_value = RPR.TrackFX_GetParam(track.id, fx_index, i)
                
                param_info = {
                    "index": i,
                    "name": param_name,
                    "value": param_value
                }
                param_list.append(param_info)
            
            self.logger.info(f"Retrieved {len(param_list)} parameters for FX {fx_index}")
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
            project = reapy.Project()
            track = project.tracks[track_index]
            
            fx_list = []
            
            # Try using reapy's built-in method first
            try:
                reapy_fx_list = track.fxs
                for i, fx in enumerate(reapy_fx_list):
                    fx_info = {
                        "index": i,
                        "name": fx.name if hasattr(fx, 'name') else f"FX_{i}",
                        "enabled": fx.is_enabled if hasattr(fx, 'is_enabled') else True
                    }
                    fx_list.append(fx_info)
                
                if fx_list:
                    self.logger.info(f"Retrieved {len(fx_list)} FX for track {track_index} using reapy")
                    return fx_list
                    
            except Exception as reapy_error:
                self.logger.warning(f"Reapy method failed: {reapy_error}")
            
            # Fallback to ReaScript API method
            fx_count = RPR.TrackFX_GetCount(track.id)
            
            for i in range(fx_count):
                fx_name = RPR.TrackFX_GetFXName(
                    track.id, i, ""
                )
                enabled = RPR.TrackFX_GetEnabled(track.id, i)
                
                fx_info = {
                    "index": i,
                    "name": fx_name,
                    "enabled": enabled
                }
                fx_list.append(fx_info)
            
            self.logger.info(f"Retrieved {len(fx_list)} FX for track {track_index} using ReaScript API")
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
                self.logger.info(
                    f"Retrieved {len(unique_fx_list)} unique FX plugins"
                )
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
        appdata = os.environ.get('APPDATA')
        if appdata:
            resource_paths.append(os.path.join(appdata, 'REAPER'))
        
        # Check if ReaperResourcePath is available through reapy
        try:
            resource_path = reapy.reascript_api.GetResourcePath()
            if resource_path:
                resource_paths.append(resource_path)
        except Exception as e:
            self.logger.warning(f"Failed to get Reaper resource path: {e}")
        
        return resource_paths

    def _parse_plugin_files(self, resource_path: str) -> List[str]:
        """Parse plugin database files in a resource path."""
        fx_list = []
        plugin_ini_files = [
            'reaper-plugs.ini', 
            'reaper-plugs64.ini', 
            'reaper-vstplugins.ini', 
            'reaper-vstplugins64.ini'
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
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    plugin_name = self._extract_plugin_name(line)
                    if plugin_name and plugin_name not in fx_list:
                        fx_list.append(plugin_name)
        except Exception as e:
            self.logger.warning(f"Failed to parse plugin file {file_path}: {e}")
        
        return fx_list

    def _extract_plugin_name(self, line: str) -> Optional[str]:
        """Extract plugin name from a database line."""
        if '=' not in line:
            return None
        
        parts = line.strip().split('=')
        if len(parts) <= 1:
            return None
        
        right_part = parts[1]
        
        # Try to extract names in the format: dll=ID,number,PluginName
        if ',' in right_part:
            comma_parts = right_part.split(',')
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
            project = reapy.Project()
            track = project.tracks[track_index]
            
            if enable is None:
                # Toggle the current state
                current_state = RPR.TrackFX_GetEnabled(track.id, fx_index)
                enable = not current_state
            
            # Set the enabled state
            success = RPR.TrackFX_SetEnabled(track.id, fx_index, enable)
            
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
