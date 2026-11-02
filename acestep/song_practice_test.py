"""Focused checks for the caption builder and preparation count-in."""
import tempfile
import unittest
from pathlib import Path

import gradio as gr
import numpy as np
import soundfile as sf

from acestep.song_prompt import build_caption,load_preset
from acestep.practice_countin import count_in


class SongPracticeTests(unittest.TestCase):
    """Keep generation hints honest and preserve practice audio after the lead-in."""

    def test_instrumental_omits_voice_request(self):
        """An instrumental prompt must not retain the preset's female singer."""
        values = load_preset("Female melodic metal")
        caption,recipe = build_caption(*values[:-1],True)
        self.assertNotIn("female alto",caption)
        self.assertEqual(recipe["voice"],"")
        self.assertIn("instrumental accompaniment",caption)

    def test_voice_and_instruments_are_explicit(self):
        """The vocal recipe retains the requested voice and instrumentation."""
        caption,recipe = build_caption(*load_preset("Female melodic metal"))
        self.assertIn("female alto",caption)
        self.assertIn("distorted rhythm guitars",caption)
        with self.assertRaises(gr.Error):
            build_caption("","piano","","","","",True)

    def test_countin_preserves_backing(self):
        """Four clicks precede an otherwise unchanged source clip."""
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder)/"source.wav"
            audio = np.linspace(-0.1,0.1,8000,dtype=np.float32)
            sf.write(source,audio,8000,subtype="PCM_24")
            path,status = count_in(str(source),120)
            result,rate = sf.read(path,always_2d=True)
            self.assertEqual(result.shape,(24000,1))
            self.assertEqual(rate,8000)
            original,_ = sf.read(source,always_2d=True)
            np.testing.assert_allclose(result[16000:],original,atol=2e-7)
            self.assertLess(abs(result[:16000]).max(),0.061)
            Path(path).unlink()

    def test_countin_invalid(self):
        """Missing clips fail with a useful message."""
        with self.assertRaises(gr.Error):
            count_in(None,120)


if __name__ == "__main__":
    unittest.main()
