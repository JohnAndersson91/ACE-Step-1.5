"""Checks for note/chord validation and attenuation-only A/B matching."""
from pathlib import Path
import tempfile
import unittest

import gradio as gr
import numpy as np
import soundfile as sf

from acestep.score_editor import validate_notes
from acestep.chord_editor import apply_chords
from acestep.correction_lab import matched_pair


class CorrectionTests(unittest.TestCase):
    """Validate actual note/chord edits and matching without musical-quality assertions."""

    def test_note_values_and_invalid_rows(self):
        """Edits produce requested pitches/times, rejecting malformed rows."""
        score = validate_notes([["melody",0,1,"F#4",90]],2)
        note = score["melody"].instruments[0].notes[0]
        self.assertEqual((note.pitch,note.velocity,note.end),(66,90,1))
        for row in [["unknown",0,1,"C4",80],["bass",1,0,"C2",80],
                    ["melody",0,4,"C4",80],["melody",0,1,"bad",80]]:
            with self.assertRaises(gr.Error):
                validate_notes([row],2)

    def test_chords_replace_only_accompaniment(self):
        """An explicitly entered minor chord creates the requested triad."""
        original = validate_notes([["melody",0,1,"G4",90]],2)
        result = apply_chords(original,[[0,2,"Am"]],2)
        self.assertIs(result["melody"],original["melody"])
        notes = result["accompaniment"].instruments[0].notes
        self.assertEqual([n.pitch for n in notes],[57,60,64])
        with self.assertRaises(gr.Error):
            apply_chords(original,[[0,2,"not a chord"]],2)

    def test_matched_pair_never_amplifies(self):
        """Different source amplitudes become equal RMS without boosting the quieter file."""
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            first,second = folder/"one.wav",folder/"two.wav"
            sf.write(first,np.ones(8000)*0.4,8000,subtype="FLOAT")
            sf.write(second,np.ones(8000)*0.02,8000,subtype="FLOAT")
            paths = matched_pair(first,second,folder)
            audio = [sf.read(p)[0] for p in paths]
            levels = [float(np.sqrt(np.mean(x*x))) for x in audio]
            self.assertAlmostEqual(levels[0],levels[1],places=4)
            self.assertLessEqual(max(levels),0.0201)


if __name__ == "__main__":
    unittest.main()
