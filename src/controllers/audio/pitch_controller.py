"""
Pitch and time-stretch controller for REAPER items.

Covers:
- Item pitch shift (semitones / cents)
- Item rate / timestretch
- Take pitch mode (elastique, soundtouch, etc.)
- Transpose all MIDI notes in an item
"""

import logging
from typing import Any, Dict, Optional

try:
    from src.core.reapy_bridge import get_reapy
except ImportError:
    from core.reapy_bridge import get_reapy

try:
    from src.item.core import get_item_by_id_or_index
except ImportError:
    from item.core import get_item_by_id_or_index


# REAPER pitch modes for takes (D_PITCHMODE item value)
PITCH_MODE_DEFAULT   = -1   # project default
PITCH_MODE_ELASTIQUE = 0    # zplane élastique Pro
PITCH_MODE_SOUNDTOUCH = 131072  # SoundTouch
PITCH_MODE_DIRAC     = 393216   # DIRAC LE
PITCH_MODE_SIMPLE    = 589824   # Simple windowed (no pitch)


class PitchController:
    """Controller for pitch shifting and time-stretching of audio/MIDI items."""

    def __init__(self, debug: bool = False):
        self.logger = logging.getLogger(__name__)
        if debug:
            self.logger.setLevel(logging.DEBUG)

    def _rpr(self):
        return get_reapy().reascript_api

    # ------------------------------------------------------------------
    # Item pitch (audio)
    # ------------------------------------------------------------------

    def set_item_pitch(
        self,
        track_index: int,
        item_id: int,
        semitones: float = 0.0,
    ) -> bool:
        """
        Set the pitch offset of an audio item in semitones.

        Args:
            track_index: Track index.
            item_id: Item index on the track.
            semitones: Pitch shift in semitones (can be fractional, e.g. 0.5 = 50 cents).

        Returns:
            True on success.
        """
        try:
            item = get_item_by_id_or_index(track_index, item_id)
            if item is None:
                self.logger.error(f"Item {item_id} not found on track {track_index}")
                return False
            RPR = self._rpr()
            RPR.SetMediaItemInfo_Value(item.id, "D_PITCH", float(semitones))
            RPR.UpdateArrange()
            self.logger.info(
                f"Set pitch track={track_index} item={item_id} → {semitones} semitones"
            )
            return True
        except Exception as e:
            self.logger.error(f"set_item_pitch failed: {e}")
            return False

    def get_item_pitch(self, track_index: int, item_id: int) -> Optional[float]:
        """Return the pitch offset of an item in semitones, or None on error."""
        try:
            item = get_item_by_id_or_index(track_index, item_id)
            if item is None:
                return None
            RPR = self._rpr()
            return RPR.GetMediaItemInfo_Value(item.id, "D_PITCH")
        except Exception as e:
            self.logger.error(f"get_item_pitch failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Item rate / time-stretch
    # ------------------------------------------------------------------

    def set_item_rate(
        self,
        track_index: int,
        item_id: int,
        rate: float = 1.0,
        preserve_pitch: bool = True,
    ) -> bool:
        """
        Set the playback rate (time-stretch factor) of an item.

        Args:
            track_index: Track index.
            item_id: Item index.
            rate: Playback rate (1.0 = normal, 2.0 = double speed, 0.5 = half speed).
            preserve_pitch: If True, pitch is locked while rate changes (élastique).

        Returns:
            True on success.
        """
        try:
            if rate <= 0:
                self.logger.error("Rate must be > 0")
                return False
            item = get_item_by_id_or_index(track_index, item_id)
            if item is None:
                return False
            RPR = self._rpr()
            RPR.SetMediaItemInfo_Value(item.id, "D_PLAYRATE", float(rate))
            # B_PPITCH: preserve pitch when rate changes
            RPR.SetMediaItemInfo_Value(
                item.id, "B_PPITCH", 1.0 if preserve_pitch else 0.0
            )
            RPR.UpdateArrange()
            self.logger.info(
                f"Set rate track={track_index} item={item_id} → {rate}x "
                f"(preserve_pitch={preserve_pitch})"
            )
            return True
        except Exception as e:
            self.logger.error(f"set_item_rate failed: {e}")
            return False

    def get_item_rate(self, track_index: int, item_id: int) -> Optional[float]:
        """Return the playback rate of an item, or None on error."""
        try:
            item = get_item_by_id_or_index(track_index, item_id)
            if item is None:
                return None
            return self._rpr().GetMediaItemInfo_Value(item.id, "D_PLAYRATE")
        except Exception as e:
            self.logger.error(f"get_item_rate failed: {e}")
            return None

    # ------------------------------------------------------------------
    # Take pitch mode (algorithm)
    # ------------------------------------------------------------------

    def set_take_pitch_mode(
        self,
        track_index: int,
        item_id: int,
        mode: int = PITCH_MODE_ELASTIQUE,
    ) -> bool:
        """
        Set the pitch/timestretch algorithm for the active take of an item.

        Args:
            track_index: Track index.
            item_id: Item index.
            mode: One of PITCH_MODE_* constants.

        Returns:
            True on success.
        """
        try:
            item = get_item_by_id_or_index(track_index, item_id)
            if item is None:
                return False
            take = item.active_take
            if take is None:
                self.logger.error("No active take")
                return False
            RPR = self._rpr()
            RPR.SetMediaItemTakeInfo_Value(take.id, "I_PITCHMODE", float(mode))
            RPR.UpdateArrange()
            self.logger.info(
                f"Set pitch mode track={track_index} item={item_id} → {mode}"
            )
            return True
        except Exception as e:
            self.logger.error(f"set_take_pitch_mode failed: {e}")
            return False

    # ------------------------------------------------------------------
    # MIDI transpose
    # ------------------------------------------------------------------

    def transpose_midi_item(
        self,
        track_index: int,
        item_id: int,
        semitones: int,
    ) -> bool:
        """
        Transpose all MIDI notes in an item by a number of semitones.

        Args:
            track_index: Track index.
            item_id: Item index.
            semitones: Number of semitones to shift (positive = up, negative = down).

        Returns:
            True on success.
        """
        try:
            item = get_item_by_id_or_index(track_index, item_id)
            if item is None:
                return False
            take = item.active_take
            if take is None or not take.is_midi:
                self.logger.error("Item has no MIDI take")
                return False

            RPR = self._rpr()
            note_count = RPR.MIDI_CountEvts(take.id, 0, 0, 0)[2]
            if note_count == 0:
                self.logger.info("No notes to transpose")
                return True

            for i in range(note_count):
                res = RPR.MIDI_GetNote(take.id, i, False, False, 0.0, 0.0, 0, 0, 0)
                # res: [retval, take_id, idx, selected, muted, startppq, endppq, chan, pitch, vel]
                sel, muted, start, end, chan, pitch, vel = (
                    res[3], res[4], res[5], res[6], res[7], res[8], res[9]
                )
                new_pitch = max(0, min(127, pitch + semitones))
                RPR.MIDI_SetNote(
                    take.id, i, sel, muted, start, end, chan, new_pitch, vel, False
                )

            RPR.MIDI_Sort(take.id)
            RPR.UpdateArrange()
            self.logger.info(
                f"Transposed {note_count} notes by {semitones} semitones "
                f"(track={track_index} item={item_id})"
            )
            return True
        except Exception as e:
            self.logger.error(f"transpose_midi_item failed: {e}")
            return False

    # ------------------------------------------------------------------
    # Track volume via envelope (automation-safe setter)
    # ------------------------------------------------------------------

    def set_track_volume_db(self, track_index: int, db: float) -> bool:
        """
        Set a track's volume in dB using SetMediaTrackInfo_Value (not reapy .volume).

        reapy's track.volume uses a 0-1 linear scale which is confusing for mixing.
        This method accepts dB and converts to the linear amplitude REAPER expects.

        Args:
            track_index: Track index.
            db: Volume in dBFS (0 dB = unity gain, -inf = silence).

        Returns:
            True on success.
        """
        try:
            import math
            linear = 0.0 if db <= -150 else 10 ** (db / 20.0)
            RPR = self._rpr()
            proj = get_reapy().Project()
            track = proj.tracks[track_index]
            RPR.SetMediaTrackInfo_Value(track.id, "D_VOL", linear)
            self.logger.info(f"Set track {track_index} volume → {db:.1f} dB ({linear:.4f} linear)")
            return True
        except Exception as e:
            self.logger.error(f"set_track_volume_db failed: {e}")
            return False

    def get_track_volume_db(self, track_index: int) -> Optional[float]:
        """Return the track volume in dBFS, or None on error."""
        try:
            import math
            RPR = self._rpr()
            proj = get_reapy().Project()
            track = proj.tracks[track_index]
            linear = RPR.GetMediaTrackInfo_Value(track.id, "D_VOL")
            if linear <= 0:
                return float("-inf")
            return 20.0 * math.log10(linear)
        except Exception as e:
            self.logger.error(f"get_track_volume_db failed: {e}")
            return None
