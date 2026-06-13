import pytest
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController
from src.controllers.midi.midi_controller import MIDIController


class TestMcpTemporary(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.track.create_track = MagicMock(return_value=0)
        self.controller.midi.create_midi_item = MagicMock(return_value=0)
        self.controller.midi.add_midi_note = MagicMock(return_value=True)

    def test_midi_item_creation(self):
        midi_track_index = self.controller.track.create_track("MIDI Track")
        self.assertGreaterEqual(midi_track_index, 0, "Failed to create MIDI track.")

        midi_item_id = self.controller.midi.create_midi_item(
            0, 0.0, length=MIDIController.DEFAULT_MIDI_LENGTH
        )
        self.assertGreaterEqual(midi_item_id, 0, "Failed to create MIDI item.")

        for pitch in [60, 64, 67]:
            result = self.controller.midi.add_midi_note(
                midi_track_index,
                midi_item_id,
                MIDIController.MIDINoteParams(
                    pitch=pitch, start_time=0.0, length=1.0, velocity=100
                ),
            )
            self.assertTrue(result, f"Failed to add note pitch={pitch}.")

        midi_item2_id = self.controller.midi.create_midi_item(
            midi_track_index, 4.0, length=2.0
        )
        self.assertGreaterEqual(midi_item2_id, 0, "Failed to create second MIDI item.")

        note2_result = self.controller.midi.add_midi_note(
            midi_track_index,
            midi_item2_id,
            MIDIController.MIDINoteParams(
                pitch=72, start_time=4.0, length=0.5, velocity=90
            ),
        )
        self.assertTrue(note2_result, "Failed to add note to second MIDI item.")


if __name__ == "__main__":
    unittest.main()
