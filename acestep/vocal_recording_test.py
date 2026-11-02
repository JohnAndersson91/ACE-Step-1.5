"""Verify persistent recordings and containment of saved-take selection."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gradio as gr
import numpy as np
import soundfile as sf

from acestep.vocal_recording import save_take, load_take


class RecordingTests(unittest.TestCase):
    """Exercise actual WAV conversion and invalid library selection."""

    def test_save_and_load(self):
        """A recorded file becomes a valid persistent, independently named WAV."""
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "recording.wav"
            sf.write(source, np.zeros(8000), 8000)
            with patch("acestep.vocal_recording.TAKES", Path(folder) / "takes"):
                saved, status = save_take(str(source))
                self.assertEqual(sf.info(saved).duration, 1)
                self.assertEqual(load_take(Path(saved).name), saved)
                self.assertIn("Saved", status)

    def test_rejects_bad_selection(self):
        """Missing recordings and traversal names never resolve as saved takes."""
        for name in [None, "../secret.wav", "missing.wav"]:
            with self.assertRaises(gr.Error):
                load_take(name)
        with self.assertRaises(gr.Error):
            save_take(None)


if __name__ == "__main__":
    unittest.main()
