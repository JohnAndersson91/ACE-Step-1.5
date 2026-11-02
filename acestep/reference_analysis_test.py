"""Reference analysis input, review, and offline-process regression checks."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import gradio as gr
import numpy as np
import soundfile as sf

from acestep.reference_analysis import (
    analyze_reference, apply_reference, prepare_reference, valid_tempo,
)


class ReferenceAnalysisTests(unittest.TestCase):
    """Check bounded real audio and explicit application without live models."""

    def test_tempo_rejects_invalid_predictions(self):
        for value in (None, "unknown", float("nan"), float("inf"), 29, 241):
            self.assertIsNone(valid_tempo(value))
        self.assertEqual(valid_tempo("155"), 155)

    def test_apply_preserves_existing_request_and_skips_unselected_controls(self):
        result = apply_reference("Female singing", "Harmonized guitars", 155, False, None, False)
        self.assertIn("Female singing", result[0])
        self.assertIn("Harmonized guitars", result[0])
        self.assertEqual(result[1:4], (gr.skip(), gr.skip(), gr.skip()))
        self.assertEqual(apply_reference(result[0], "Harmonized guitars", 155, False,
            None, False)[0], result[0])

    def test_explicit_tempo_and_clip_application(self):
        with tempfile.NamedTemporaryFile(suffix=".wav") as clip:
            result = apply_reference("My song", "Guitar", 155, True, clip.name, True)
            self.assertEqual(result[1:4], (155, False, clip.name))
            guided = apply_reference("Female singing", "", None, False, clip.name, True)
            self.assertEqual(guided[0], "Female singing")
            self.assertEqual(guided[3], clip.name)

    def test_no_empty_description_or_missing_clip(self):
        with self.assertRaises(gr.Error):
            apply_reference("Original", "", 155, True, None, False)
        with self.assertRaises(gr.Error):
            apply_reference("Original", "Guitar", 155, True, None, True)

    def test_experimental_description_is_off_by_default(self):
        from acestep.reference_analysis_ui import build_reference_analysis
        with gr.Blocks() as demo:
            custom = dict(captions=gr.Textbox(), reference_audio=gr.Audio(type="filepath"))
            options = dict(bpm=gr.Number(), bpm_auto=gr.Checkbox())
            build_reference_analysis(custom, options, MagicMock())
        components = demo.config["components"]
        flags = {item["props"].get("label"): item["props"].get("value")
            for item in components if item["type"] == "checkbox"}
        self.assertFalse(flags["Try experimental automatic description · can misidentify instruments"])
        self.assertTrue(flags["Use this clip as sound guidance"])
        self.assertTrue(any(item["type"] == "group" and item["props"].get("visible") is False
            for item in components))

    def test_invalid_clip_bounds_rejected_before_decoder(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.wav"
            source.touch()
            for start, duration in ((-1, 15), (float("nan"), 15), (0, 31), (0, 9)):
                with self.assertRaises(gr.Error):
                    prepare_reference(source, start, duration, Path(tmp))

    def test_real_decoder_crops_without_changing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            source = folder / "source.wav"
            rate = 8000
            sf.write(source, np.sin(np.arange(14 * rate) * .2) * .1, rate)
            before = source.read_bytes()
            clip = prepare_reference(source, 2, 10, folder)
            self.assertAlmostEqual(sf.info(clip).duration, 10, places=2)
            self.assertEqual(source.read_bytes(), before)

    @patch("acestep.reference_analysis.prepare_reference")
    @patch("acestep.reference_analysis.subprocess.run")
    @patch("acestep.lyric_memory.release_idle_music_gpu")
    def test_worker_offline_and_real_codes_required(self, release, run, prepare):
        with tempfile.TemporaryDirectory() as tmp, patch("acestep.reference_analysis.ROOT", Path(tmp)):
            root = Path(tmp)
            model = root / "checkpoints/acestep-5Hz-lm-1.7B/model.safetensors"
            model.parent.mkdir(parents=True)
            model.touch()
            prepare.return_value = root / "clip.wav"
            handler = MagicMock()
            handler.convert_src_audio_to_codes.return_value = ""
            with self.assertRaises(gr.Error):
                analyze_reference("source", 0, 10, handler)
            run.assert_not_called()
            handler.convert_src_audio_to_codes.return_value = "<|audio_code_123|>"

            def finish(args, **kwargs):
                self.assertEqual(kwargs["env"]["HF_HUB_OFFLINE"], "1")
                Path(args[-1]).write_text(json.dumps(dict(caption="Guitars", bpm=155, key="E minor")))

            run.side_effect = finish
            result = analyze_reference("source", 0, 10, handler)
            self.assertEqual(result[1:3], ("Guitars", 155))
            release.assert_called_once_with(handler)


if __name__ == "__main__":
    unittest.main()
