"""Check local loudness measurement and distortion-free comparison playback."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

from acestep.audio_review import compare_versions
from acestep.loudness_comparison import comparison_gains, measure_loudness


class LoudnessComparisonTests(unittest.TestCase):
    """Exercise real audio as well as unavailable-analyzer fallback."""

    def test_real_measurement_and_constant_attenuation(self):
        """A louder copy matches its quieter twin without compression or source edits."""
        rate = 16000
        wave = np.sin(2*np.pi*440*np.arange(rate*3)/rate).astype(np.float32)
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            a, b = root/"a.wav", root/"b.wav"
            sf.write(a, wave*0.4, rate, subtype="FLOAT")
            sf.write(b, wave*0.1, rate, subtype="FLOAT")
            before = a.read_bytes(), b.read_bytes()
            with patch("acestep.audio_review.ROOT", root/"out"):
                _, report = compare_versions(str(a), str(b), 0, 3, True)
            self.assertEqual(report["playback_matching"], "Integrated LUFS")
            previews = [sf.read(path)[0] for path in sorted((root/"out").rglob("*.wav"))]
            levels = [float(np.sqrt(np.mean(audio*audio))) for audio in previews]
            # FFmpeg's gated histogram measurement has finite resolution (~0.1 LU).
            self.assertLess(abs(20*np.log10(levels[0]/levels[1])), 0.1)
            mask = np.abs(wave) > 0.1
            ratios = previews[0][mask]/wave[mask]
            self.assertLess(float(np.std(ratios)), 1e-6)
            self.assertLess(float(abs(previews[0]).max()), 0.1)
            self.assertEqual(before, (a.read_bytes(), b.read_bytes()))

    def test_unavailable_measurement_falls_back(self):
        """A missing analyzer leaves the existing comparison usable and reports fallback."""
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"sound.wav"
            sf.write(path, np.ones(16000)*0.1, 8000)
            with patch("acestep.audio_review.ROOT", Path(folder)/"out"), \
                 patch("acestep.loudness_comparison.measure_loudness", return_value=None):
                _, report = compare_versions(str(path), str(path), 0, 2, True)
            self.assertEqual(report["playback_matching"], "RMS")
            self.assertIn("unavailable", report["matching_notice"])

    def test_no_boost_and_true_peak_headroom(self):
        """A high-crest-factor excerpt attenuates both versions rather than limiting peaks."""
        values = [{"integrated_lufs": -40, "true_peak_dbtp": -1},
                  {"integrated_lufs": -30, "true_peak_dbtp": 1}]
        gains = comparison_gains(values)
        self.assertTrue(all(0 < gain <= 1 for gain in gains))
        outputs = [item["integrated_lufs"]+20*np.log10(gain)
                   for item, gain in zip(values, gains)]
        self.assertAlmostEqual(*outputs)
        for item, gain in zip(values, gains):
            self.assertLessEqual(item["true_peak_dbtp"]+20*np.log10(gain), -6+1e-9)

    def test_silence_is_not_a_valid_lufs_measurement(self):
        """Silence produces no finite integrated loudness."""
        self.assertIsNone(measure_loudness(np.zeros((16000, 1)), 8000))


if __name__ == "__main__":
    unittest.main()
