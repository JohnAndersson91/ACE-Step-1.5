"""Regression tests for MP3 export on PCs without ffmpeg on PATH."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf
import torch

from acestep.ffmpeg_path import ffmpeg_executable
from acestep.audio_utils import AudioSaver


class FfmpegPathTests(unittest.TestCase):
    """Exercise discovery and a real short MP3 export using the installed encoder."""

    def test_system_encoder_preferred(self):
        """An existing system encoder remains the first choice."""
        with patch("acestep.ffmpeg_path.shutil.which",return_value="system-ffmpeg"):
            self.assertEqual(ffmpeg_executable(),"system-ffmpeg")

    def test_missing_encoder_has_clear_error(self):
        """Missing bundled files fail explicitly rather than running a guessed command."""
        with patch("acestep.ffmpeg_path.shutil.which",return_value=None), \
             patch("imageio_ffmpeg.get_ffmpeg_exe",return_value="not-an-existing-encoder.exe"):
            with self.assertRaises(FileNotFoundError):
                ffmpeg_executable()

    def test_real_mp3_without_system_path(self):
        """The exact missing-PATH failure is resolved by the existing bundled encoder."""
        audio = torch.from_numpy((0.1*np.sin(2*np.pi*440*np.arange(48000)/48000)).astype(np.float32))[None,:]
        with tempfile.TemporaryDirectory() as directory, \
             patch("acestep.ffmpeg_path.shutil.which",return_value=None):
            destination = Path(directory)/"test.mp3"
            AudioSaver().save_audio(audio,destination,sample_rate=48000,format="mp3")
            decoded,rate = sf.read(destination)
            self.assertEqual(rate,48000)
            self.assertAlmostEqual(len(decoded)/rate,1,places=2)
            self.assertGreater(abs(decoded).max(),0.01)


if __name__ == "__main__":
    unittest.main()
