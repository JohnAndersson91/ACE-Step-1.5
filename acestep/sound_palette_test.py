"""Sound-specification scoping, singer consistency, and lyric-preservation checks."""
import unittest

import gradio as gr

from acestep.sound_palette import apply_palette, compile_palette, performance_lyrics
from acestep.sound_vocabulary import INSTRUMENTS


class SoundPaletteTests(unittest.TestCase):
    """Verify instructions delivered to generation, without claiming perceptual quality."""

    def test_general_instruments_are_scoped_and_idempotent(self):
        args = (["Grand piano"], ["Saxophone", "Brush drums"], "One female singer",
            "Clean and intimate", "Natural band recording")
        caption = compile_palette("A quiet song about a journey", *args)
        self.assertIn("journey", caption)
        self.assertIn("Intro instruments only: acoustic grand piano", caption)
        self.assertIn("Main song instruments: saxophone", caption)
        self.assertEqual(compile_palette(caption, *args), caption)

    def test_one_singer_transition_stays_with_same_word(self):
        caption = compile_palette("Metal", [], ["Acoustic drum kit"], "One female singer",
            "Clean → rasp → brief scream", "Natural band recording")
        self.assertIn("SAME female singer", caption)
        self.assertIn("SAME word", caption)
        self.assertIn("natural cymbal decay", caption)

    def test_role_headings_removed_without_changing_lyric_words(self):
        lyrics = "[Verse]\nI rise\n[Scream]\nStand tall!\n[Chorus]\nStay with me"
        updated = performance_lyrics(lyrics, "One female singer", "Clean → rasp → brief scream")
        self.assertEqual(updated, lyrics.replace("[Scream]\n", ""))
        self.assertEqual(performance_lyrics(lyrics, "Duet", "Clean → rasp → brief scream"), lyrics)
        self.assertEqual(performance_lyrics(lyrics, "One female singer", "Keep my request"), lyrics)

    def test_restore_vocals_cleans_remembered_tags(self):
        saved = "[Verse]\nMy words\n[Scream]\nRise!"
        result = apply_palette("Rock", [], [], "One female singer", "Clean → rasp → brief scream",
            "Keep my request", "[Instrumental]", saved)
        self.assertFalse(result[1])
        self.assertIn("My words", result[2])
        self.assertNotIn("[Scream]", result[2])
        self.assertEqual(result[2], result[3])

    def test_instrumental_keeps_saved_vocal_lyrics(self):
        result = apply_palette("Calm", [], ["Grand piano"], "Instrumental", "Keep my request",
            "Intimate acoustic", "[Instrumental]", "My old lyrics")
        self.assertTrue(result[1])
        self.assertEqual(result[3], "My old lyrics")

    def test_contradictory_singer_requests_are_not_silently_combined(self):
        args = ([], [], "One female singer", "Powerful clean belting", "Keep my request")
        with self.assertRaises(gr.Error):
            compile_palette("Male vocals in the chorus", *args)
        compile_palette("Female singing, no male vocals", *args)

    def test_unknown_or_empty_choices_fail(self):
        with self.assertRaises(gr.Error):
            compile_palette("Rock", ["Unknown sound"], [], "Keep my request", "Keep my request", "Keep my request")
        with self.assertRaises(gr.Error):
            compile_palette("Rock", [], [], "Keep my request", "Keep my request", "Keep my request")
        self.assertGreaterEqual(len(INSTRUMENTS), 25)

    def test_ui_binds_explicit_application_and_neutral_defaults(self):
        from acestep.sound_palette_ui import build_sound_palette
        with gr.Blocks() as demo:
            custom = dict(captions=gr.Textbox(), lyrics=gr.Textbox(),
                instrumental_checkbox=gr.Checkbox())
            build_sound_palette(custom, gr.State(""))
        entries = {item["props"].get("label"): item["props"].get("value")
            for item in demo.config["components"] if item["type"] == "dropdown"}
        self.assertEqual(entries["Singer lineup"], "Keep my request")
        self.assertEqual(entries["Vocal delivery"], "Keep my request")
        self.assertEqual(entries["Intro instruments"], [])


if __name__ == "__main__":
    unittest.main()
