"""Exercise screening against known synthetic signals without playing any audio."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import soundfile as sf

from acestep.audio_artifact_gate import checked_playback_path, scan_file, set_listening_hold
from acestep.audio_artifact_scan import scan_audio
from acestep.comparison_player import comparison_markup
from acestep.ui.gradio.events.results.audio_playback_updates import build_audio_slot_update


class ArtifactScreenTests(unittest.TestCase):
    """Known signals validate detection mechanics, not human hearing safety."""

    def setUp(self):
        """Make deterministic short signals with sub-full-scale peaks."""
        self.rate = 16000
        self.time = np.arange(self.rate*2)/self.rate
        self.low = (0.1*np.sin(2*np.pi*440*self.time)).astype(np.float32)
        self.high = (0.1*np.sin(2*np.pi*5000*self.time)).astype(np.float32)

    def test_high_tone_detected_even_with_opposite_stereo_phase(self):
        """Averaging stereo must not cancel a ringing-tone test signal."""
        report = scan_audio(np.column_stack([self.high, -self.high]), self.rate)
        tones = [event for event in report["events"] if event["kind"] == "narrow_upper_tone"]
        self.assertTrue(tones)
        self.assertAlmostEqual(tones[0]["frequency_hz"], 5000, delta=5)

    def test_silence_and_low_tone_not_called_high_frequency_artifacts(self):
        """An unflagged result must retain its non-certification limitation."""
        for audio in (np.zeros_like(self.low), self.low):
            report = scan_audio(audio, self.rate)
            self.assertFalse(report["review_required"])
            self.assertIn("Unflagged audio", report["limitations"])

    def test_quietening_does_not_hide_tonal_structure(self):
        """Turning a suspect file down cannot bypass the relative spectral screen."""
        first = scan_audio(self.high, self.rate)
        second = scan_audio(self.high*0.001, self.rate)
        self.assertEqual([event["kind"] for event in first["events"]],
                         [event["kind"] for event in second["events"]])

    def test_impulsive_change_and_nonfinite_samples(self):
        """A short broadband impulse flags; invalid samples cannot pass silently."""
        impulse = np.zeros_like(self.low)
        impulse[self.rate] = 0.9
        self.assertTrue(scan_audio(impulse, self.rate)["review_required"])
        impulse[0] = np.nan
        with self.assertRaises(ValueError):
            scan_audio(impulse, self.rate)

    def test_hold_and_spectral_flags_remove_playable_sources(self):
        """Both native generated players and embedded comparisons honor the pause."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            low, high = root/"low.wav", root/"high.wav"
            sf.write(low, self.low, self.rate)
            sf.write(high, self.high, self.rate)
            with patch("acestep.audio_artifact_gate.ROOT", root/"prefs"):
                set_listening_hold(True)
                self.assertIsNone(checked_playback_path(str(low))[0])
                markup = comparison_markup(str(low), str(high))
                self.assertNotIn("data:audio/", markup)
                self.assertIn("disabled", markup)
                fake_gr = type("FakeGr", (), {"update": staticmethod(lambda **kw: kw)})
                update = build_audio_slot_update(fake_gr, str(low))
                self.assertIsNone(update["value"])
                self.assertFalse(update["autoplay"])
                set_listening_hold(False)
                self.assertEqual(checked_playback_path(str(low))[0], str(low))
                self.assertIsNone(checked_playback_path(str(high))[0])

    def test_failed_scan_is_held_and_report_saved(self):
        """Unreadable audio fails closed; a readable file gets a persisted review report."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with patch("acestep.audio_artifact_gate.ROOT", root/"prefs"):
                set_listening_hold(False)
                self.assertIsNone(checked_playback_path(str(root/"missing.wav"))[0])
                path = root/"tone.wav"
                sf.write(path, self.low, self.rate)
                self.assertFalse(scan_file(str(path))["review_required"])
                self.assertTrue(path.with_suffix(".wav.soundcheck.json").is_file())

    def test_chunked_scan_preserves_late_event_timing(self):
        """Chunk boundaries cannot move or lose an isolated late tone event."""
        wave = np.zeros(self.rate*20, dtype=np.float32)
        wave[17*self.rate:18*self.rate] = self.high[:self.rate]
        direct = [event for event in scan_audio(wave, self.rate)["events"]
                  if event["kind"] == "narrow_upper_tone"]
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"long.wav"
            sf.write(path, wave, self.rate, subtype="FLOAT")
            chunked = [event for event in scan_file(str(path))["events"]
                       if event["kind"] == "narrow_upper_tone"]
        self.assertTrue(direct)
        self.assertTrue(chunked)
        self.assertAlmostEqual(direct[0]["start_seconds"], chunked[0]["start_seconds"], places=3)
        self.assertAlmostEqual(direct[0]["end_seconds"], chunked[0]["end_seconds"], places=3)


if __name__ == "__main__":
    unittest.main()
