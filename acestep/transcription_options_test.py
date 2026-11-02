"""Test register fixes, note diagnostics and external MIDI routing."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gradio as gr
import numpy as np
import pretty_midi

from acestep.arrangement_register import fit_register
from acestep.external_midi import render_external_midi
from acestep.score_review import review_notes


class TranscriptionOptionsTests(unittest.TestCase):
    """Keep musical changes explicit and exercise the import boundary."""

    def test_register_preserves_pitch_class_and_timing(self):
        """Low bass notes move by octaves without changing the source score."""
        midi = pretty_midi.PrettyMIDI()
        track = pretty_midi.Instrument(25)
        track.notes = [pretty_midi.Note(80,p,0,1) for p in (25,40,60,100)]
        midi.instruments.append(track)
        fixed,count = fit_register(midi,40,88)
        self.assertEqual(count,2)
        for original,note in zip(track.notes,fixed.instruments[0].notes):
            self.assertTrue(40<=note.pitch<=88)
            self.assertEqual(note.pitch%12,original.pitch%12)
            self.assertEqual((note.start,note.end,note.velocity),(0,1,80))
        self.assertEqual([n.pitch for n in track.notes],[25,40,60,100])

    def test_diagnostics_are_flags_not_corrections(self):
        """Brief low notes are visible for review and remain unmodified."""
        rows = [["bass",0,0.1,"C2",80],["melody",1,2,"C4",80]]
        flags,figure,status = review_notes(rows,5)
        self.assertEqual(len(flags),1)
        self.assertIn("Very short",flags[0][3])
        self.assertIn("do not prove",status)
        self.assertEqual(rows[0][3],"C2")
        import matplotlib.pyplot as plt
        plt.close(figure)

    def test_import_routes_clips_and_excludes_voice(self):
        """Imported parts retain timing and explicit instrument choices."""
        midi = pretty_midi.PrettyMIDI()
        bass = pretty_midi.Instrument(33,name="bass")
        bass.notes = [pretty_midi.Note(90,28,1,3)]
        bass.pitch_bends = [pretty_midi.PitchBend(1000,0)]
        bass.control_changes = [pretty_midi.ControlChange(7,90,0)]
        voice = pretty_midi.Instrument(53,name="vocal")
        voice.notes = [pretty_midi.Note(80,60,1,3)]
        midi.instruments = [bass,voice]
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/"input.mid"
            midi.write(str(source))
            with patch("acestep.external_midi.render_notes",return_value=np.ones((220500,2),np.float32)*0.05) as render:
                wav,path,report,status = render_external_midi(str(source),"Acoustic guitar",2,5,True)
                result = pretty_midi.PrettyMIDI(path)
                self.assertEqual(len(result.instruments),1)
                track = result.instruments[0]
                self.assertEqual(track.program,25)
                self.assertEqual(track.notes[0].pitch,40)
                self.assertAlmostEqual(track.notes[0].start,0)
                self.assertAlmostEqual(track.notes[0].end,1)
                self.assertEqual(len(track.pitch_bends),0)
                self.assertEqual(track.control_changes[0].value,90)
                self.assertEqual(report[0][4],1)
                self.assertTrue(Path(wav).is_file())
                import shutil
                shutil.rmtree(Path(wav).parent)
            with patch("acestep.external_midi.render_notes",return_value=np.ones((220500,2),np.float32)*0.05):
                wav,path,report,status = render_external_midi(str(source),"Keep MIDI instrument assignments",2,5,True)
                track = pretty_midi.PrettyMIDI(path).instruments[0]
                self.assertEqual(track.program,33)
                self.assertEqual(track.notes[0].pitch,28)
                self.assertEqual(track.pitch_bends[0].pitch,1000)
                shutil.rmtree(Path(wav).parent)

    def test_invalid_input(self):
        """Missing imports fail before rendering work."""
        with self.assertRaises(gr.Error):
            render_external_midi(None,"Piano",0,25,True)


if __name__ == "__main__":
    unittest.main()
