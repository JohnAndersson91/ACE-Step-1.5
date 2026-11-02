"""Verify practice trimming and invalid input handling."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import gradio as gr
import numpy as np
import soundfile as sf
from acestep.practice_audio import trim_audio, split_audio, transcribe_lyrics


class PracticeTests(unittest.TestCase):
    """Check audio duration, fades, and empty input without model downloads."""

    def test_empty_inputs(self):
        """All practice actions reject missing audio before starting work."""
        for action, args in [(trim_audio, (None, 0, 1)),
                             (split_audio, (None,)), (transcribe_lyrics, (None,))]:
            with self.assertRaises(gr.Error):
                action(*args)

    def test_trim_and_fade(self):
        """Trimming retains the requested length and fades the ending."""
        with tempfile.TemporaryDirectory() as directory:
            source = str(Path(directory) / "input.wav")
            sf.write(source, np.full((16000, 2), 0.5), 8000)
            result = trim_audio(source, 0.5, 1.5)
            audio, rate = sf.read(result)
            self.assertEqual(len(audio), rate)
            self.assertAlmostEqual(float(audio[-1, 0]), 0, places=4)
            with self.assertRaises(gr.Error):
                trim_audio(source, 2, 1)


if __name__ == "__main__":
    unittest.main()
