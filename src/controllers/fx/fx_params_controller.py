import logging
from typing import List, Dict, Any, Optional

from src.core.reapy_bridge import get_reapy


class FXParamsController:
    def __init__(self, rpr, logger: logging.Logger | None = None):
        self._RPR = rpr
        self.logger = logger or logging.getLogger(__name__)

    def set_fx_param(self, track_index: int, fx_index: int, param_name: str, value: float) -> bool:
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]
            fx_name_buf = "\x00" * 256
            self._RPR.TrackFX_GetFXName(track.id, fx_index, fx_name_buf, 256)
            fx_name = (fx_name_buf or "").rstrip("\x00")
            mapped_index = self._map_param_name_to_index(fx_name, param_name)
            if mapped_index is not None:
                self._RPR.TrackFX_SetParam(track.id, fx_index, mapped_index, value)
                return True
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)
            for i in range(param_count):
                buf_size = 256
                name_buf = "\x00" * buf_size
                got = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, name_buf, buf_size)
                retrieved = name_buf.rstrip("\x00") if got else self._RPR.TrackFX_GetParamName(track.id, fx_index, i, "", 256)
                if not retrieved:
                    retrieved = self._generate_contextual_param_name(fx_name or "Unknown", i)
                if (param_name.lower() in retrieved.lower()) or (retrieved.lower() in param_name.lower()):
                    self._RPR.TrackFX_SetParam(track.id, fx_index, i, value)
                    return True
            return False
        except Exception as e:
            self.logger.error("Failed to set FX parameter: %s", e)
            return False

    def get_fx_param(self, track_index: int, fx_index: int, param_name: str) -> float:
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]
            fx_name_buf = "\x00" * 256
            self._RPR.TrackFX_GetFXName(track.id, fx_index, fx_name_buf, 256)
            fx_name = (fx_name_buf or "").rstrip("\x00")
            mapped_index = self._map_param_name_to_index(fx_name, param_name)
            if mapped_index is not None:
                return self._RPR.TrackFX_GetParam(track.id, fx_index, mapped_index)
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)
            for i in range(param_count):
                buf_size = 256
                name_buf = "\x00" * buf_size
                got = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, name_buf, buf_size)
                retrieved = name_buf.rstrip("\x00") if got else self._RPR.TrackFX_GetParamName(track.id, fx_index, i, "", 256)
                if not retrieved:
                    retrieved = self._generate_contextual_param_name(fx_name or "Unknown", i)
                if (param_name.lower() in retrieved.lower()) or (retrieved.lower() in param_name.lower()):
                    return self._RPR.TrackFX_GetParam(track.id, fx_index, i)
            return 0.0
        except Exception as e:
            self.logger.error("Failed to get FX parameter '%s': %s", param_name, e)
            return 0.0

    def get_fx_param_list(self, track_index: int, fx_index: int) -> List[Dict[str, Any]]:
        try:
            project = get_reapy().Project()
            track = project.tracks[track_index]
            param_list: List[Dict[str, Any]] = []
            param_count = self._RPR.TrackFX_GetNumParams(track.id, fx_index)
            fx_name_buf = "\x00" * 256
            self._RPR.TrackFX_GetFXName(track.id, fx_index, fx_name_buf, 256)
            fx_name = fx_name_buf.rstrip("\x00")
            for i in range(param_count):
                try:
                    param_name = ""
                    try:
                        buf_size = 256
                        param_name = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, "", buf_size)
                        if not param_name or len(param_name.strip()) == 0:
                            raise Exception("Empty parameter name")
                    except Exception:
                        try:
                            param_name_buf = "\x00" * 256
                            success = self._RPR.TrackFX_GetParamName(track.id, fx_index, i, param_name_buf, 256)
                            if success and param_name_buf:
                                param_name = param_name_buf.rstrip("\x00")
                                if not param_name:
                                    raise Exception("Empty buffer result")
                        except Exception:
                            param_name = self._generate_contextual_param_name(fx_name, i)
                    param_value = self._RPR.TrackFX_GetParam(track.id, fx_index, i)
                    formatted_value = ""
                    try:
                        format_buf = "\x00" * 256
                        success = self._RPR.TrackFX_GetFormattedParamValue(track.id, fx_index, i, format_buf, 256)
                        formatted_value = format_buf.rstrip("\x00") if (success and format_buf) else f"{param_value:.3f}"
                    except Exception:
                        formatted_value = f"{param_value:.3f}"
                    param_list.append({
                        "index": i,
                        "name": param_name or f"Param_{i}",
                        "value": param_value,
                        "formatted_value": formatted_value,
                    })
                except Exception as param_error:
                    self.logger.warning(f"Failed to get parameter {i}: {param_error}")
                    param_list.append({
                        "index": i,
                        "name": f"Param_{i}",
                        "value": 0.0,
                        "formatted_value": "0.000",
                    })
            return param_list
        except Exception as e:
            self.logger.error(
                f"Failed to get FX parameter list for FX {fx_index}: {e}")
            return []

    def _generate_contextual_param_name(self, fx_name: str, param_index: int) -> str:
        fx = (fx_name or "").lower()
        if "reacomp" in fx:
            mapping = self._reacomp_param_names()
            if 0 <= param_index < len(mapping):
                return mapping[param_index]
        if "realimit" in fx or "limit" in fx:
            mapping = [
                "Threshold",
                "Release",
                "Ceiling",
                "Brickwall limiter",
                "Advanced limiter",
                "Output gain",
                "Mix",
            ]
            if 0 <= param_index < len(mapping):
                return mapping[param_index]
        if "reaeq" in fx:
            if param_index == 0:
                return "HP Frequency"
            if param_index == 1:
                return "HP Enable"
            if param_index <= 21:
                band_num = ((param_index - 2) // 4) + 1
                idx = (param_index - 2) % 4
                param_type = ["Frequency", "Gain", "Q", "Type"][idx]
                return f"Band{band_num}_{param_type}"
            return f"EQ_Param_{param_index}"
        return f"Parameter_{param_index}"

    def _map_param_name_to_index(self, fx_name: str, param_name: str) -> Optional[int]:
        fx = (fx_name or "").lower()
        name = (param_name or "").lower()
        if "reacomp" in fx:
            names = self._reacomp_param_names()
            for idx, nm in enumerate(names):
                if name == nm.lower():
                    return idx
            for idx, nm in enumerate(names):
                nm_low = nm.lower()
                if name in nm_low or nm_low in name:
                    return idx
        if "realimit" in fx or "limit" in fx:
            names = [
                "Threshold",
                "Release",
                "Ceiling",
                "Brickwall limiter",
                "Advanced limiter",
                "Output gain",
                "Mix",
            ]
            for idx, nm in enumerate(names):
                if name == nm.lower():
                    return idx
            for idx, nm in enumerate(names):
                nm_low = nm.lower()
                if name in nm_low or nm_low in name:
                    return idx
        return None

    def _reacomp_param_names(self) -> List[str]:
        return [
            "Threshold",
            "Ratio",
            "Attack",
            "Release",
            "Knee",
            "Auto-release",
            "Makeup",
            "Dry",
            "Detector input",
            "RMS size",
            "Pre-comp",
            "Program dependent",
            "Adapt release",
            "Lookahead",
            "Auto-makeup",
            "Feedback",
            "Output gain",
            "Mix",
            "Detector HPF",
            "Detector LPF",
            "Saturate",
            "Log output",
            "Output meter",
            "Compressor",
        ]
