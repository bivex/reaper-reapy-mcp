import logging
import os
import re
from typing import List, Dict, Any, Optional
import sys

from src.core.reapy_bridge import get_reapy
from .fx_manage_controller import FXManageController
from .fx_params_controller import FXParamsController
from .fx_presets_controller import FXPresetsController
from .fx_routing_controller import FXRoutingController

# Add utils path for imports (kept for backward-compat if needed by other modules)
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Constants to replace magic numbers
PLUGIN_NAME_INDEX = 2
MIN_PLUGIN_NAME_PARTS = 3


class FXController:
    """Controller for FX-related operations in Reaper."""

    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.INFO)

        try:
            reapy = get_reapy()
            self._RPR = reapy.reascript_api
        except Exception as e:
            self.logger.error(f"Failed to initialize RPR: {e}")
            self._RPR = None
        self.manage = FXManageController(self._RPR, self.logger)
        self.params = FXParamsController(self._RPR, self.logger)
        self.presets = FXPresetsController(self._RPR, self.logger)
        self.routing = FXRoutingController(self._RPR, self.logger)

    def add_fx_to_track(self, track_index: int, fx_name: str) -> bool:
        return self.manage.add_fx_to_track(track_index, fx_name)

    def add_fx(self, track_index: int, fx_name: str) -> int:
        return self.manage.add_fx(track_index, fx_name)

    def remove_fx(self, track_index: int, fx_index: int) -> bool:
        return self.manage.remove_fx(track_index, fx_index)

    def set_fx_param(
        self, track_index: int, fx_index: int, param_name: str, value: float
    ) -> bool:
        return self.params.set_fx_param(track_index, fx_index, param_name, value)

    def get_fx_param(self, track_index: int, fx_index: int, param_name: str) -> float:
        return self.params.get_fx_param(track_index, fx_index, param_name)

    def get_fx_param_list(self, track_index: int, fx_index: int) -> List[Dict[str, Any]]:
        return self.params.get_fx_param_list(track_index, fx_index)

    def _generate_contextual_param_name(self, fx_name: str, param_index: int) -> str:
        return self.params._generate_contextual_param_name(fx_name, param_index)

    def _map_param_name_to_index(self, fx_name: str, param_name: str) -> Optional[int]:
        return self.params._map_param_name_to_index(fx_name, param_name)

    def _reacomp_param_names(self) -> List[str]:
        return self.params._reacomp_param_names()

    def get_fx_list(self, track_index: int) -> List[Dict[str, Any]]:
        return self.manage.get_fx_list(track_index)

    def get_available_fx_list(self) -> List[str]:
        try:
            fx_list = []
            fx_list.extend(self._read_plugin_database())
            if fx_list:
                unique_fx_list = sorted(list(set(fx_list)))
                self.logger.info(f"Retrieved {len(unique_fx_list)} unique FX plugins")
                return unique_fx_list
            else:
                self.logger.warning("No FX plugins found through any method")
                return []
        except Exception as e:
            self.logger.error(f"Failed to get available FX list: {e}")
            return []

    def _read_plugin_database(self) -> List[str]:
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
        resource_paths = []
        appdata = os.environ.get("APPDATA")
        if appdata:
            resource_paths.append(os.path.join(appdata, "REAPER"))
        try:
            resource_path = self._RPR.GetResourcePath()
            if resource_path:
                resource_paths.append(resource_path)
        except Exception as e:
            self.logger.warning(f"Failed to get Reaper resource path: {e}")
        return resource_paths

    def _parse_plugin_files(self, resource_path: str) -> List[str]:
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
        fx_list: List[str] = []
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
        if "=" not in line:
            return None
        parts = line.strip().split("=")
        if len(parts) <= 1:
            return None
        right_part = parts[1]
        if "," in right_part:
            comma_parts = right_part.split(",")
            if len(comma_parts) >= MIN_PLUGIN_NAME_PARTS:
                plugin_name = comma_parts[PLUGIN_NAME_INDEX].strip()
                if plugin_name:
                    return plugin_name
        for part in parts:
            if part.strip() and '"' in part:
                import re as _re
                name_match = _re.search(r'"([^"]+)"', part)
                if name_match:
                    return name_match.group(1)
        return None

    def toggle_fx(self, track_index: int, fx_index: int, enable: bool | None = None) -> bool:
        return self.manage.toggle_fx(track_index, fx_index, enable)

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
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]
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
            param_names = []
            for i in range(param_count):
                param_name = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, "")
                param_names.append((i, param_name))
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
                                normalized_value = self._normalize_compressor_param(
                                    param_type, value
                                )
                                self._RPR.TrackFX_SetParam(
                                    track.id, fx_index, param_idx, normalized_value
                                )
                                self.logger.info(
                                    "Set %s to %s (normalized: %s)",
                                    param_type,
                                    value,
                                    normalized_value,
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
        if param_type == "threshold":
            return max(0.0, min(1.0, (value + 60.0) / 60.0))
        elif param_type == "ratio":
            return max(0.0, min(1.0, (value - 1.0) / 19.0))
        elif param_type == "attack":
            import math
            return max(
                0.0, min(1.0, math.log10(max(0.1, value) / 0.1) / math.log10(1000))
            )
        elif param_type == "release":
            import math
            return max(0.0, min(1.0, math.log10(max(10, value) / 10) / math.log10(100)))
        elif param_type == "makeup_gain":
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
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]
            param_mappings = {
                "threshold": ["Threshold", "Thresh", "threshold", "thresh", "Input"],
                "ceiling": ["Ceiling", "Output", "Limit", "ceiling", "output", "limit"],
                "release": ["Release", "release", "Release Time", "Rel"],
            }
            success = True
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)
            param_names = []
            for i in range(param_count):
                param_name = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, "")
                param_names.append((i, param_name))
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
                                normalized_value = self._normalize_limiter_param(
                                    param_type, value
                                )
                                self._RPR.TrackFX_SetParam(
                                    track.id, fx_index, param_idx, normalized_value
                                )
                                self.logger.info(
                                    "Set limiter %s to %s (normalized: %s)",
                                    param_type,
                                    value,
                                    normalized_value,
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
        if param_type == "threshold":
            return max(0.0, min(1.0, (value + 20.0) / 20.0))
        elif param_type == "ceiling":
            return max(0.0, min(1.0, (value + 10.0) / 10.0))
        elif param_type == "release":
            import math
            return max(0.0, min(1.0, math.log10(max(1, value)) / math.log10(100)))
        else:
            return max(0.0, min(1.0, value))

    def get_track_peak_level(self, track_index: int) -> Dict[str, float]:
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]
            left_peak = self._RPR.Track_GetPeakInfo(track.id, 0)
            right_peak = self._RPR.Track_GetPeakInfo(track.id, 1)
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
        try:
            project = get_reapy().Project()
            master_track = project.master_track
            left_peak = self._RPR.Track_GetPeakInfo(master_track.id, 0)
            right_peak = self._RPR.Track_GetPeakInfo(master_track.id, 1)
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
