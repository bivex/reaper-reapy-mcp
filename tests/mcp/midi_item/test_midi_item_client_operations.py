import pytest
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.reaper_controller import ReaperController
from src.controllers.midi.midi_controller import MIDIController


class TestMidiItemClientOperations(unittest.TestCase):

    def setUp(self):
        self.controller = ReaperController(debug=True)
        self.controller.track.create_track = MagicMock(return_value=0)
        self.controller.midi.create_midi_item = MagicMock(return_value=0)
        self.controller.midi.add_midi_note = MagicMock(return_value=True)
        self.controller.midi.get_selected_items = MagicMock(
            return_value=[{"track_index": 0, "item_id": 0}, {"track_index": 0, "item_id": 1}]
        )
        self.controller.audio.delete_item = MagicMock(return_value=True)

    def test_midi_and_item_operations(self):
        midi_track_index = self.controller.track.create_track("MIDI Track")
        self.assertGreaterEqual(midi_track_index, 0, "Failed to create MIDI track.")

        midi_item_id = self.controller.midi.create_midi_item(
            midi_track_index,
            MIDIController.DEFAULT_MIDI_START_TIME,
            length=MIDIController.DEFAULT_MIDI_LENGTH,
        )
        self.assertGreaterEqual(midi_item_id, 0, "Failed to create MIDI item.")

        for pitch in MIDIController.DEFAULT_MIDI_NOTE_PITCHES:
            self.assertTrue(
                self.controller.midi.add_midi_note(
                    midi_track_index,
                    midi_item_id,
                    MIDIController.MIDINoteParams(
                        pitch=pitch,
                        start_time=0.0,
                        length=MIDIController.DEFAULT_MIDI_NOTE_LENGTH,
                        velocity=MIDIController.DEFAULT_MIDI_NOTE_VELOCITY,
                    ),
                ),
                f"Failed to add note with pitch {pitch}.",
            )

        midi_item2_id = self.controller.midi.create_midi_item(
            midi_track_index,
            MIDIController.DEFAULT_SECOND_MIDI_START_TIME,
            length=MIDIController.DEFAULT_SECOND_MIDI_LENGTH,
        )
        self.assertGreaterEqual(midi_item2_id, 0, "Failed to create second MIDI item.")

        self.assertTrue(
            self.controller.midi.add_midi_note(
                midi_track_index,
                midi_item2_id,
                MIDIController.MIDINoteParams(
                    pitch=MIDIController.DEFAULT_SECOND_MIDI_NOTE_PITCH,
                    start_time=0.0,
                    length=MIDIController.DEFAULT_SECOND_MIDI_NOTE_LEN,
                    velocity=MIDIController.DEFAULT_SECOND_MIDI_NOTE_VEL,
                ),
            ),
            "Failed to add note to second item.",
        )

        selected_items = self.controller.midi.get_selected_items()
        self.assertIsInstance(selected_items, list)
        self.assertGreater(len(selected_items), 0)

        for item in selected_items:
            self.assertTrue(
                self.controller.audio.delete_item(item["track_index"], item["item_id"]),
                f"Failed to delete item {item['item_id']}.",
            )


if __name__ == "__main__":
    unittest.main()
