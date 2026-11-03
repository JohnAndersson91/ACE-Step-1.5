"""Regression checks for clean vocal conditioning and explicit guitar-band choices."""
import unittest

import gradio as gr

from acestep.performance_constraints import HARSH, validate_delivery
from acestep.sound_palette import apply_palette, compile_palette
from acestep.style_request import shape_style


class PerformanceConstraintsTests(unittest.TestCase):
    """Verify the actual compiled request, not a claim about generated sound quality."""

    def test_clean_solo_does_not_inject_harsh_roles(self):
        """Choosing one female singer must not introduce rasp or screamed-note instructions."""
        text = compile_palette("Rock", [], [], "One female singer",
                               "Clean and powerful throughout", "Keep my request")
        self.assertIsNone(HARSH.search(text))
        self.assertIn("assertive projected verses", text)
        self.assertIn("SAME female singer", text)

    def test_clean_choice_replaces_old_managed_rasp(self):
        """Previously applied style directions cannot survive a new explicit clean selection."""
        old = shape_style("Rock", 130, "Epic", "A few transitions", True, "en")[0]
        result = apply_palette(old, [], ["High-gain metal rhythm guitar"], "One female singer",
                               "Clean and powerful throughout", "Dry guitar-led metal band",
                               "[Verse]\nStay strong\n[Scream]\nI rise", "")
        self.assertNotIn("only two climactic", result[0])
        self.assertNotIn("[Scream]", result[2])
        self.assertIn("I rise", result[2])
        self.assertIn("speaker cabinet", result[0])

    def test_free_text_conflicts_are_reported_not_silently_rewritten(self):
        """Existing user-authored harsh requests need review when clean vocals are chosen."""
        for caption in ("Raspy throughout", "A brief scream in the chorus", "Female growling"):
            with self.assertRaises(gr.Error):
                validate_delivery(caption, "Clean throughout")
        validate_delivery("No rasp, screaming or growling", "Clean throughout")
        validate_delivery("Clean rasp-free vocals", "Clean throughout")
        validate_delivery("Raspy throughout", "Raspy throughout")
        validate_delivery("Screaming electric guitar with clean vocals", "Clean throughout")

    def test_clean_style_cannot_conflict_with_old_palette(self):
        """The other control panel must also reject a stale conflicting vocal selection."""
        old = compile_palette("Rock", [], [], "One female singer", "Raspy throughout",
                              "Keep my request")
        with self.assertRaises(gr.Error):
            shape_style(old, 130, "Epic", "Clean throughout", True, "en")

    def test_non_target_lyrics_and_instruments_are_preserved(self):
        """Explicit transitions and acoustic songs retain their supported behavior."""
        text = compile_palette("Acoustic folk", [], ["Steel-string acoustic"], "One female singer",
                               "Clean and intimate", "Intimate acoustic")
        self.assertIn("wooden body resonance", text)
        self.assertNotIn("high-gain", text)

    def test_style_panel_starts_clean_without_requesting_transitions(self):
        """Opening the style panel must not preselect the previous harsh-vocal option."""
        from acestep.style_request_ui import build_style_direction
        with gr.Blocks() as demo:
            custom = {"captions": gr.Textbox()}
            options = dict(bpm=gr.Number(), bpm_auto=gr.Checkbox(),
                           vocal_language=gr.Textbox(), vocal_lang_auto=gr.Checkbox())
            build_style_direction(custom, options)
        values = {item["props"].get("label"): item["props"].get("value")
                  for item in demo.config["components"] if item["type"] == "radio"}
        self.assertEqual(values["Clean → rasp → scream · requested"], "Clean throughout")


if __name__ == "__main__":
    unittest.main()
