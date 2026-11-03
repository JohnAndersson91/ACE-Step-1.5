"""Verify saved sound experiments cannot be mistaken for automatic generation upgrades."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import gradio as gr
import numpy as np
import soundfile as sf

from acestep.comparison_player import build_comparison_player
from acestep.quality_auditions import available_auditions, compare_saved_audition


class QualityAuditionsTests(unittest.TestCase):
    """Check completed-file discovery and the real comparison path."""

    def test_requires_baseline_and_only_lists_wavs(self):
        """A partial render cannot expose a misleading baseline comparison."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/"B - sampler.wav").touch()
            with patch("acestep.quality_auditions.ROOT", root):
                self.assertEqual(available_auditions(), {})
                (root/"A - current settings.wav").touch()
                (root/"settings.json").touch()
                self.assertEqual(len(available_auditions()), 2)

    def test_real_saved_comparison_preserves_files(self):
        """The in-program test button produces matched playback without editing masters."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            wave = np.sin(2*np.pi*440*np.arange(32000)/16000).astype(np.float32)*0.1
            first, second = root/"A - current settings.wav", root/"B - sampler.wav"
            sf.write(first, wave, 16000, subtype="FLOAT")
            sf.write(second, wave*2, 16000, subtype="FLOAT")
            before = first.read_bytes(), second.read_bytes()
            with patch("acestep.quality_auditions.ROOT", root), \
                 patch("acestep.audio_review.ROOT", root/"previews"):
                update, report = compare_saved_audition("B - sampler", 0, 2)
                self.assertTrue(update["visible"])
                self.assertIn("data:audio/wav;base64", update["value"])
                self.assertEqual(report["playback_matching"], "Integrated LUFS")
                with self.assertRaises(gr.Error):
                    compare_saved_audition("../outside", 0, 2)
            self.assertEqual(before, (first.read_bytes(), second.read_bytes()))

    def test_custom_player_labels_do_not_change_existing_callers(self):
        """Other comparison tools retain their existing player defaults."""
        self.assertIn("Piano from current notes", build_comparison_player().value)
        player = build_comparison_player(labels=("Current settings", "Selected test"), visible=False)
        self.assertIn("Selected test", player.value)
        self.assertFalse(player.visible)


if __name__ == "__main__":
    unittest.main()
