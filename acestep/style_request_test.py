"""Verify honest reference expansion, vocal instructions and explicit duration selection."""
import unittest

import gradio as gr

from acestep.style_request import expand_style_request,shape_style,check_song_length


class StyleRequestTests(unittest.TestCase):
    """Check actual generation instructions while avoiding artist-match assertions."""

    def test_intro_and_alias(self):
        """Both spellings become scoped guitar instructions without forcing tempo or vocals."""
        for artist in ("Children of Bodom","children of bodoom"):
            text,matches = expand_style_request(f"I want a {artist} style intro, then clean female singing.")
            self.assertIn("Intro direction",text)
            self.assertIn("harmonic-minor",text)
            self.assertIn("clean female singing",text)
            self.assertEqual(len(matches),1)
            self.assertNotIn("BPM",text)
            self.assertEqual(expand_style_request(text)[0],text)

    def test_negative_and_unknown_are_preserved(self):
        """A rejection or an unsupported artist must not silently activate this profile."""
        for text in ("Not like Children of Bodom", "Avoid a Children of Bodom intro", "I want a different artist intro"):
            self.assertEqual(expand_style_request(text),(text,[]))

    def test_power_transition_metadata_and_repeat_apply(self):
        """Chosen metadata and gradual, sparse screaming reach the caption without duplication."""
        result = shape_style("Children of Bodom style intro",155,"Epic","A few transitions",True,"en")
        caption,bpm,auto,lang,lang_auto,status = result
        self.assertEqual(bpm["value"],155)
        self.assertFalse(auto)
        self.assertEqual(lang,"en")
        self.assertFalse(lang_auto)
        self.assertIn("only two climactic lines",caption)
        self.assertIn("within the same sung phrase",caption)
        self.assertIn("natural pitch movement",caption)
        self.assertIn("female lead singer",caption)
        self.assertIn("cannot guarantee",status)
        self.assertEqual(shape_style(caption,155,"Epic","A few transitions",True,"en")[0],caption)

    def test_no_default_duration(self):
        """Missing duration fails for new songs but preserves audio-guided modes."""
        for duration in (None,-1,0,float("nan")):
            with self.assertRaises(gr.Error):
                check_song_length("text2music",duration)
        check_song_length("text2music",75)
        check_song_length("cover",None)


if __name__ == "__main__":
    unittest.main()
