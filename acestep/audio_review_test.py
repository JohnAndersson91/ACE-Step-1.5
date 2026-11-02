"""Verify volume matching and the preservation boundary of audio repairs."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gradio as gr
import numpy as np
import soundfile as sf

from acestep.audio_review import audio_metrics,compare_versions,splice_section


class AudioReviewTests(unittest.TestCase):
    """Test actual WAV samples rather than only UI wiring."""

    def test_comparison_attenuates_and_preserves_sources(self):
        """Two amplitudes match without boosting or modifying input files."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a,b = root/"a.wav",root/"b.wav"
            sf.write(a,np.ones(16000)*0.4,8000,subtype="FLOAT")
            sf.write(b,np.ones(16000)*0.02,8000,subtype="FLOAT")
            before = a.read_bytes()
            with patch("acestep.audio_review.ROOT",root/"out"):
                markup,report = compare_versions(str(a),str(b),0,2)
            previews = [sf.read(p)[0] for p in (root/"out").rglob("*.wav")]
            levels = [np.sqrt(np.mean(x*x)) for x in previews]
            self.assertAlmostEqual(levels[0],levels[1],places=6)
            self.assertLess(max(levels),0.02001)
            self.assertEqual(a.read_bytes(),before)
            self.assertIn("Version A",markup)
            self.assertIn("not measure tuning",report["note"])

    def test_repair_preserves_outside_and_crossfades_inside(self):
        """A selected replacement cannot move or overwrite surrounding samples."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source,repair = root/"source.wav",root/"repair.wav"
            audio = np.linspace(-0.1,0.1,32000,dtype=np.float32)
            sf.write(source,audio,8000,subtype="FLOAT")
            sf.write(repair,np.ones(32000)*0.2,8000,subtype="FLOAT")
            with patch("acestep.audio_review.ROOT",root/"out"):
                path,status = splice_section(str(source),str(repair),1,3,"Full song at the same timing",50)
            result,rate = sf.read(path,dtype="float32")
            np.testing.assert_array_equal(result[:8000],audio[:8000])
            np.testing.assert_array_equal(result[24000:],audio[24000:])
            self.assertEqual(len(result),len(audio))
            self.assertAlmostEqual(result[8000],audio[8000])
            self.assertAlmostEqual(result[23999],audio[23999])
            self.assertAlmostEqual(result[12000],0.2)

    def test_short_repair_rejected(self):
        """An undersized replacement cannot silently truncate the song."""
        with tempfile.TemporaryDirectory() as folder:
            a,b = Path(folder)/"a.wav",Path(folder)/"b.wav"
            sf.write(a,np.ones(32000)*0.1,8000)
            sf.write(b,np.ones(1000)*0.1,8000)
            with self.assertRaises(gr.Error):
                splice_section(str(a),str(b),1,3,"A clip starting at the repair",50)

    def test_metrics_flag_silence_and_full_scale(self):
        """Technical flags do not require an AI quality score."""
        audio = np.concatenate([np.ones(8000),np.zeros(8000)])[:,None]
        report = audio_metrics(audio,8000)
        self.assertEqual(report["samples_at_or_above_full_scale"],8000)
        self.assertEqual(report["possible_level_drop_seconds"],[1])


if __name__ == "__main__":
    unittest.main()
