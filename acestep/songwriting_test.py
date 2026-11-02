"""Verify song-request defaults, vocal validation and non-destructive lyric drafting."""
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock

import gradio as gr

from acestep.songwriting import check_vocal_lyrics,draft_lyrics,use_draft,lyric_structure
from acestep.ui.gradio.interfaces.generation_tab_optional_controls import build_optional_parameter_controls
from acestep.ui.gradio.interfaces.generation_defaults import compute_init_defaults


class SongwritingTests(unittest.TestCase):
    """Check controls actually used by generation, not only a displayed duration label."""

    def test_vocal_request_requires_words(self):
        """Blank lyrics and empty section headings cannot silently produce a vocal song."""
        for lyrics in (""," ","[Verse]\n[Chorus]\n[Bridge]"):
            with self.assertRaises(gr.Error):
                check_vocal_lyrics("text2music",lyrics)
        check_vocal_lyrics("text2music","[Instrumental]")
        check_vocal_lyrics("cover","")
        check_vocal_lyrics("text2music","[Verse]\nI found my voice\n[Chorus]\nI rise")

    def test_use_draft_enables_singing(self):
        """Applying a draft explicitly clears the instrumental toggle."""
        words = "[Verse]\nI found my voice\n[Chorus]\nI rise"
        self.assertEqual(use_draft(words),(words,False,words))
        from acestep.ui.gradio.events.generation.ui_helpers import handle_instrumental_checkbox
        self.assertEqual(handle_instrumental_checkbox(False,words,words)[0],words)

    def test_structure_counts_real_section_tags(self):
        """Repeated choruses and the bridge remain explicit, not inferred from prose."""
        text = "[Verse 1]\nOne\n[Chorus]\nRise\n[Verse 2]\nTwo\n[Bridge]\nBreathe\n[Final Chorus]\nRise"
        self.assertEqual(lyric_structure(text),"Requested structure — Verses: 2 · Choruses: 2 · Bridges: 1")

    def test_guitar_metal_preset_requests_vocals(self):
        """Adding a guitar preset must not accidentally enable Instrumental."""
        from acestep.song_prompt import load_preset
        self.assertFalse(load_preset("Melodic guitar metal")[-1])

    def test_writer_uses_existing_cuda_offload_only(self):
        """Idle music models release GPU memory; CPU/non-offload settings stay unchanged."""
        from acestep.lyric_memory import release_idle_music_gpu
        handler = MagicMock(offload_to_cpu=True,device="cuda")
        release_idle_music_gpu(handler)
        self.assertEqual(handler._recursive_to_device.call_count,3)
        self.assertTrue(all(call.args[1]=="cpu" for call in handler._recursive_to_device.call_args_list))
        for device,offload in (("cpu",True),("cuda",False)):
            handler = MagicMock(device=device,offload_to_cpu=offload)
            release_idle_music_gpu(handler)
            handler._recursive_to_device.assert_not_called()

    def test_real_generation_rejects_blank_vocal_request(self):
        """The guard is wired to the actual generator before any model work."""
        import inspect
        from acestep.ui.gradio.events.results.generation_progress import generate_with_progress
        args = {name:None for name,param in inspect.signature(generate_with_progress).parameters.items()
                if param.default is inspect.Parameter.empty}
        args.update(task_type="text2music",lyrics="",captions="female English vocals")
        with self.assertRaises(gr.Error):
            next(generate_with_progress(**args))

    def test_invalid_brief_does_not_run_worker(self):
        """Invalid writing requests never launch a model process."""
        with patch("acestep.songwriting.subprocess.run") as run:
            with self.assertRaises(gr.Error):
                draft_lyrics("","metal",180)
            run.assert_not_called()

    def test_manual_duration_english_and_single_version(self):
        """New sessions request a real three-minute English song and one output."""
        self.assertEqual(compute_init_defaults(None,"en")["default_batch_size"],1)
        with gr.Blocks():
            controls = build_optional_parameter_controls(480,2,1,False)
        self.assertEqual(controls["audio_duration"].value,180)
        self.assertTrue(controls["audio_duration"].interactive)
        self.assertFalse(controls["duration_auto"].value)
        self.assertEqual(controls["vocal_language"].value,"en")
        self.assertFalse(controls["vocal_lang_auto"].value)
        self.assertEqual(controls["batch_size_input"].value,1)


if __name__ == "__main__":
    unittest.main()
