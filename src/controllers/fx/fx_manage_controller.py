import logging
from typing import List, Dict, Any

from src.core.reapy_bridge import get_reapy


class FXManageController:
    def __init__(self, rpr, logger: logging.Logger | None = None):
        self._RPR = rpr
        self.logger = logger or logging.getLogger(__name__)

    def add_fx_to_track(self, track_index: int, fx_name: str) -> bool:
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            fx_id = self._RPR.TrackFX_AddByName(track.id, fx_name, False, 1)
            return fx_id >= 0
        except Exception as e:
            self.logger.error(
                f"Failed to add FX {fx_name} to track {track_index}: {e}")
            return False

    def add_fx(self, track_index: int, fx_name: str) -> int:
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]
            fx_id = self._RPR.TrackFX_AddByName(track.id, fx_name, False, 1)
            if fx_id >= 0:
                self.logger.info(
                    f"Added FX {fx_name} to track {track_index} at index {fx_id}")
            else:
                self.logger.error(
                    f"Failed to add FX {fx_name} to track {track_index}")
            return fx_id
        except Exception as e:
            self.logger.error(
                f"Failed to add FX {fx_name} to track {track_index}: {e}")
            return -1

    def remove_fx(self, track_index: int, fx_index: int) -> bool:
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]
            success = self._RPR.TrackFX_Delete(track.id, fx_index)
            if success:
                self.logger.info(
                    f"Removed FX {fx_index} from track {track_index}")
            else:
                self.logger.error(
                    f"Failed to remove FX {fx_index} from track {track_index}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to remove FX: {e}")
            return False

    def get_fx_list(self, track_index: int) -> List[Dict[str, Any]]:
        try:
            reapy = get_reapy()
            project = reapy.Project()
            track = project.tracks[track_index]

            fx_list: List[Dict[str, Any]] = []
            try:
                reapy_fx_list = track.fxs
                for i, fx in enumerate(reapy_fx_list):
                    fx_list.append({
                        "index": i,
                        "name": getattr(fx, "name", f"FX_{i}"),
                        "enabled": getattr(fx, "is_enabled", True),
                    })
                if fx_list:
                    self.logger.info(
                        "Retrieved %s FX for track %s using reapy",
                        len(fx_list), track_index)
                    return fx_list
            except Exception as reapy_error:
                self.logger.warning(f"Reapy method failed: {reapy_error}")

            fx_count = self._RPR.TrackFX_GetCount(track.id)
            for i in range(fx_count):
                fx_name = self._RPR.TrackFX_GetFXName(track.id, i, "")
                enabled = self._RPR.TrackFX_GetEnabled(track.id, i)
                fx_list.append({"index": i, "name": fx_name, "enabled": enabled})
            self.logger.info(
                "Retrieved %s FX for track %s using ReaScript API",
                len(fx_list), track_index)
            return fx_list
        except Exception as e:
            self.logger.error(
                f"Failed to get FX list for track {track_index}: {e}")
            return []

    def toggle_fx(self, track_index: int, fx_index: int, enable: bool | None = None) -> bool:
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]
            if enable is None:
                current_state = self._RPR.TrackFX_GetEnabled(track.id, fx_index)
                enable = not current_state
            self._RPR.TrackFX_SetEnabled(track.id, fx_index, enable)
            current_state = self._RPR.TrackFX_GetEnabled(track.id, fx_index)
            success = current_state == enable
            if success:
                state_str = "enabled" if enable else "disabled"
                self.logger.info(
                    f"{state_str.capitalize()} FX {fx_index} on track {track_index}")
                return True
            else:
                self.logger.error(
                    "Failed to toggle FX %s on track %s. Current state: %s, wanted: %s",
                    fx_index, track_index, current_state, enable)
                return False
        except Exception as e:
            self.logger.error(f"Failed to toggle FX: {e}")
            return False
