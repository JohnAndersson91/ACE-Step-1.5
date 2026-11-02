"""Focused checks for reconstruction validation and actual instrument rendering."""
from pathlib import Path
import unittest
from unittest.mock import patch

import gradio as gr
import numpy as np

from acestep.reconstruction_ui import rebuild


class ReconstructionTests(unittest.TestCase):
    """Reject unsupported inputs and verify optional synthesis when installed."""

    def test_input_validation(self):
        """Bad inputs fail before transcription or subprocess work."""
        for args in [(None,0,25,"Guitar"),("file.wav",-1,25,"Guitar"),
                     ("file.wav",0,100,"Guitar"),("file.wav",0,25,"Unknown")]:
            with self.assertRaises(gr.Error), patch("subprocess.run") as run:
                rebuild(*args)
                run.assert_not_called()

    def test_start_outside_song(self):
        """A start beyond the recording cannot launch reconstruction."""
        with patch("acestep.reconstruction_ui.sf.info") as info:
            info.return_value.duration = 5
            with self.assertRaises(gr.Error):
                rebuild("file.wav",10,25,"Guitar")

    def test_render_single_note(self):
        """The local sample renderer creates finite non-silent stereo output."""
        bank = Path(__file__).resolve().parents[1] / "checkpoints/reconstruction/florestan-subset.sf2"
        if not bank.exists():
            self.skipTest("Optional sample bank not installed")
        import pretty_midi
        from acestep.reconstruction_render import render_notes
        midi = pretty_midi.PrettyMIDI()
        instrument = pretty_midi.Instrument(program=24)
        instrument.notes.append(pretty_midi.Note(80,60,0,0.5))
        midi.instruments.append(instrument)
        audio = render_notes(midi,str(bank),1,24)
        self.assertEqual(audio.shape,(44100,2))
        self.assertTrue(np.isfinite(audio).all())
        self.assertGreater(float(abs(audio).max()),0)


if __name__ == "__main__":
    unittest.main()
