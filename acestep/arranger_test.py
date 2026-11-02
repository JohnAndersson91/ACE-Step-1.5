"""Verify enforced instrument layouts independently from transcription accuracy."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

import numpy as np
import pretty_midi
from acestep.arranger_render import render_arrangement, LAYOUTS


class ArrangerTests(unittest.TestCase):
    """Ensure piano/guitar are exclusively assigned and preserve the shared notes."""

    def test_instruments_are_enforced(self):
        """Rendering cannot substitute guitars/drums for piano or vice versa."""
        for layout,program in [("Piano",0),("Acoustic guitar",25)]:
            midi = pretty_midi.PrettyMIDI()
            track = pretty_midi.Instrument(0)
            track.notes.append(pretty_midi.Note(80,60,0.1,0.5))
            midi.instruments.append(track)
            score = {name:midi for name in ["melody","bass","accompaniment","drums"]}
            with tempfile.TemporaryDirectory() as directory, \
                 patch("acestep.arranger_render.render_notes",return_value=np.ones((44100,2),np.float32)*0.1) as render:
                result = Path(directory) / "test"
                audit = render_arrangement(score,"bank",1,layout,result)
                self.assertNotIn("drums",audit)
                self.assertEqual({item["program"] for item in audit.values()},{program})
                loaded = pretty_midi.PrettyMIDI(str(result)+".mid")
                self.assertEqual(len(loaded.instruments),3)
                self.assertTrue(all(i.program==program and not i.is_drum for i in loaded.instruments))
                self.assertTrue(all(i.notes[0].pitch==60 for i in loaded.instruments))

    def test_melody_can_be_excluded(self):
        """A backing-only arrangement need not double the user's singing melody."""
        midi = pretty_midi.PrettyMIDI()
        score = {name:midi for name in LAYOUTS["Piano"]}
        with tempfile.TemporaryDirectory() as directory, \
             patch("acestep.arranger_render.render_notes",return_value=np.ones((44100,2),np.float32)*0.1):
            audit = render_arrangement(score,"bank",1,"Piano",Path(directory)/"test",False)
            self.assertNotIn("melody",audit)


if __name__ == "__main__":
    unittest.main()
