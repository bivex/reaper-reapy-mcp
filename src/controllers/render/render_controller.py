"""
Render, bounce, freeze and stem export controller for REAPER.

Covers:
- Bounce/render project or time selection to file
- Freeze/unfreeze tracks
- Stem export (render each track separately)
- Region-based render
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

try:
    from src.core.reapy_bridge import get_reapy
except ImportError:
    from core.reapy_bridge import get_reapy


# REAPER render constants (from reaper_plugin_functions.h)
RENDER_TAIL_FLAG_NONE = 0
RENDER_BOUNDS_TIMELENGTH = 0   # full project length
RENDER_BOUNDS_TIMESEL = 1      # time selection
RENDER_BOUNDS_CUSTOM = 2       # custom start/end
RENDER_BOUNDS_PROJECT = 3      # project start to end
RENDER_BOUNDS_SELECTED_ITEMS = 4
RENDER_BOUNDS_SELECTED_REGIONS = 8

# Render format codes (GetSetProjectInfo_String "RENDER_FORMAT")
FMT_WAV  = "evaw"   # WAV  (reversed in REAPER's internal encoding)
FMT_AIFF = "ffia"
FMT_FLAC = "calf"
FMT_MP3  = "l3pm"


class RenderController:
    """Controller for render, bounce, freeze, and stem export operations."""

    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rpr(self):
        return get_reapy().reascript_api

    def _project_id(self):
        return get_reapy().Project().id

    # ------------------------------------------------------------------
    # Render / bounce
    # ------------------------------------------------------------------

    def render_project(
        self,
        output_path: str,
        start: float = 0.0,
        end: float = 0.0,
        sample_rate: int = 44100,
        channels: int = 2,
        bounds: int = RENDER_BOUNDS_PROJECT,
    ) -> bool:
        """
        Render the project (or a time range) to a file.

        Args:
            output_path: Absolute path for the output file (extension determines format).
            start: Start time in seconds (used when bounds=RENDER_BOUNDS_CUSTOM).
            end:   End time in seconds (used when bounds=RENDER_BOUNDS_CUSTOM).
            sample_rate: Output sample rate.
            channels: 1=mono, 2=stereo.
            bounds: One of the RENDER_BOUNDS_* constants.

        Returns:
            True on success.
        """
        try:
            RPR = self._rpr()
            proj = self._project_id()

            # Set render output file
            RPR.GetSetProjectInfo_String(proj, "RENDER_FILE", output_path, True)
            # Bounds
            RPR.GetSetProjectInfo(proj, "RENDER_BOUNDSFLAG", bounds, True)
            if bounds == RENDER_BOUNDS_CUSTOM:
                RPR.GetSetProjectInfo(proj, "RENDER_STARTPOS", start, True)
                RPR.GetSetProjectInfo(proj, "RENDER_ENDPOS", end, True)
            # Sample rate & channels
            RPR.GetSetProjectInfo(proj, "RENDER_SRATE", float(sample_rate), True)
            RPR.GetSetProjectInfo(proj, "RENDER_CHANNELS", float(channels), True)

            # Render (action 42230 = File: Render project to disk, using project render settings)
            RPR.Main_OnCommand(42230, 0)
            self.logger.info(f"Render started → {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"render_project failed: {e}")
            return False

    def render_time_selection(self, output_path: str, **kwargs) -> bool:
        """Render the current time selection to a file."""
        return self.render_project(
            output_path, bounds=RENDER_BOUNDS_TIMESEL, **kwargs
        )

    def bounce_track(
        self,
        track_index: int,
        output_path: str,
        start: float = 0.0,
        end: float = 0.0,
    ) -> bool:
        """
        Bounce (render in place) a single track to a file.

        Solos the track, renders the time selection, then restores solo state.
        """
        try:
            RPR = self._rpr()
            proj_obj = get_reapy().Project()
            track = proj_obj.tracks[track_index]

            # Remember solo states
            old_solos = {t.index: t.is_solo for t in proj_obj.tracks}

            # Solo only this track
            for t in proj_obj.tracks:
                t.is_solo = (t.index == track_index)

            # Set time selection if provided
            if end > start:
                RPR.GetSet_LoopTimeRange2(proj_obj.id, True, False, start, end, False)
                bounds = RENDER_BOUNDS_TIMESEL
            else:
                bounds = RENDER_BOUNDS_PROJECT

            ok = self.render_project(output_path, start=start, end=end, bounds=bounds)

            # Restore solo states
            for t in proj_obj.tracks:
                t.is_solo = old_solos[t.index]

            return ok
        except Exception as e:
            self.logger.error(f"bounce_track failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Freeze / unfreeze
    # ------------------------------------------------------------------

    def freeze_track(self, track_index: int, freeze_to_stereo: bool = True) -> bool:
        """
        Freeze a track (renders FX chain to audio, disables FX).

        Args:
            track_index: Index of the track to freeze.
            freeze_to_stereo: True = stereo freeze, False = mono.

        Returns:
            True on success.
        """
        try:
            RPR = self._rpr()
            proj = get_reapy().Project()
            track = proj.tracks[track_index]

            # Select only this track
            RPR.SetOnlyTrackSelected(track.id)
            # Action 41223 = Track: Freeze to stereo (render pre-fader, save/remove FX)
            # Action 41224 = Track: Freeze to mono
            action = 41223 if freeze_to_stereo else 41224
            RPR.Main_OnCommand(action, 0)
            self.logger.info(f"Freeze track {track_index} (stereo={freeze_to_stereo})")
            return True
        except Exception as e:
            self.logger.error(f"freeze_track failed: {e}")
            return False

    def unfreeze_track(self, track_index: int) -> bool:
        """Unfreeze a track (re-enables FX, removes freeze file)."""
        try:
            RPR = self._rpr()
            proj = get_reapy().Project()
            track = proj.tracks[track_index]

            RPR.SetOnlyTrackSelected(track.id)
            # Action 41225 = Track: Unfreeze tracks
            RPR.Main_OnCommand(41225, 0)
            self.logger.info(f"Unfreeze track {track_index}")
            return True
        except Exception as e:
            self.logger.error(f"unfreeze_track failed: {e}")
            return False

    def is_frozen(self, track_index: int) -> bool:
        """Return True if the track is currently frozen."""
        try:
            RPR = self._rpr()
            proj = get_reapy().Project()
            track = proj.tracks[track_index]
            # I_FREEZE: 0=not frozen, 1=frozen to stereo, 2=frozen to mono
            val = RPR.GetMediaTrackInfo_Value(track.id, "I_FREEZE")
            return int(val) != 0
        except Exception as e:
            self.logger.error(f"is_frozen failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Region-based render
    # ------------------------------------------------------------------

    def render_regions(self, output_dir: str, name_pattern: str = "$region") -> bool:
        """
        Render all regions in the project to separate files in output_dir.

        Args:
            output_dir: Directory to write rendered files.
            name_pattern: REAPER render pattern, e.g. "$region", "$tracknumber-$track".

        Returns:
            True on success.
        """
        try:
            RPR = self._rpr()
            proj = self._project_id()

            os.makedirs(output_dir, exist_ok=True)
            RPR.GetSetProjectInfo_String(proj, "RENDER_FILE", output_dir + "/", True)
            RPR.GetSetProjectInfo_String(proj, "RENDER_PATTERN", name_pattern, True)
            RPR.GetSetProjectInfo(
                proj, "RENDER_BOUNDSFLAG", float(RENDER_BOUNDS_SELECTED_REGIONS), True
            )
            # Action 42230 = render to disk using current settings
            RPR.Main_OnCommand(42230, 0)
            self.logger.info(f"Render regions → {output_dir}")
            return True
        except Exception as e:
            self.logger.error(f"render_regions failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Stem export
    # ------------------------------------------------------------------

    def export_stems(
        self,
        output_dir: str,
        track_indices: Optional[List[int]] = None,
        name_pattern: str = "$tracknumber-$track",
        start: float = 0.0,
        end: float = 0.0,
    ) -> Dict[int, str]:
        """
        Export each track as a separate stem file.

        Solos each track in turn, renders, then restores state.

        Args:
            output_dir: Directory to write stem files.
            track_indices: List of track indices to export (None = all tracks).
            name_pattern: Filename pattern (track name used when None).
            start: Render start in seconds (0 = project start).
            end: Render end in seconds (0 = project end).

        Returns:
            Dict mapping track_index → output file path for each stem rendered.
        """
        try:
            RPR = self._rpr()
            proj_obj = get_reapy().Project()
            os.makedirs(output_dir, exist_ok=True)

            tracks = proj_obj.tracks
            if track_indices is None:
                track_indices = list(range(len(tracks)))

            # Remember solo state
            old_solos = {t.index: t.is_solo for t in tracks}
            bounds = RENDER_BOUNDS_TIMESEL if end > start else RENDER_BOUNDS_PROJECT

            if end > start:
                RPR.GetSet_LoopTimeRange2(
                    proj_obj.id, True, False, start, end, False
                )

            results: Dict[int, str] = {}

            for idx in track_indices:
                if idx >= len(tracks):
                    self.logger.warning(f"Track index {idx} out of range, skipping")
                    continue

                track = tracks[idx]
                safe_name = (track.name or f"track_{idx}").replace("/", "_").replace("\\", "_")
                out_file = os.path.join(output_dir, f"{safe_name}.wav")

                # Solo only this track
                for t in tracks:
                    t.is_solo = (t.index == idx)

                ok = self.render_project(out_file, start=start, end=end, bounds=bounds)
                if ok:
                    results[idx] = out_file
                    self.logger.info(f"Stem rendered: track {idx} → {out_file}")
                else:
                    self.logger.error(f"Stem render failed for track {idx}")

            # Restore solo states
            for t in tracks:
                t.is_solo = old_solos[t.index]

            return results

        except Exception as e:
            self.logger.error(f"export_stems failed: {e}")
            return {}
