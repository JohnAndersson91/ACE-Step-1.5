"""Compile reusable sound choices into a reviewable, bounded generation specification."""
import re

import gradio as gr

from acestep.sound_vocabulary import DELIVERIES, INSTRUMENTS, PRODUCTION, VOICES
from acestep.performance_constraints import (
    CLEAN_DELIVERIES, replace_managed_direction, validate_delivery,
)

MARKER = "\n\nSound palette:\n"


def compile_palette(caption, intro, main, voice, delivery, production):
    """Preserve the user's story and scope sound choices without changing lyric words."""
    caption = str(caption or "").split(MARKER, 1)[0].strip()
    caption = replace_managed_direction(caption, delivery).strip()
    intro, main = intro or [], main or []
    if not isinstance(intro, list) or not isinstance(main, list) or len(intro) + len(main) > 8:
        raise gr.Error("Choose up to eight instrument entries across the intro and main song.")
    if any(item not in INSTRUMENTS for item in intro + main):
        raise gr.Error("Choose instruments from the sound list.")
    if voice not in VOICES or delivery not in DELIVERIES or production not in PRODUCTION:
        raise gr.Error("Choose a listed voice, delivery and production setting.")
    if len(caption) > 3200:
        raise gr.Error("Shorten the existing description to 3200 characters before adding sound choices.")
    if voice == "Instrumental" and delivery != "Keep my request":
        raise gr.Error("For an instrumental, leave vocal delivery at Keep my request.")
    validate_delivery(caption, delivery)
    other = {"One female singer": "male", "One male singer": "female"}.get(voice)
    if other:
        for match in re.finditer(rf"\b{other}\s+(?:lead\s+)?(?:singer|vocals?|vocalist|voice)\b", caption, re.I):
            prefix = caption[max(0, match.start() - 35):match.start()]
            if not re.search(r"(?:no|without|avoid|exclude|not)\s+(?:(?:any|a)\s+)?$", prefix, re.I):
                raise gr.Error(f"Your description also requests a {other} voice. Edit that phrase or choose Duet.")
    parts = []
    for scope, choices in (("Intro instruments only", intro), ("Main song instruments", main)):
        if choices:
            parts.append(scope + ": " + "; ".join(INSTRUMENTS[item] for item in dict.fromkeys(choices)))
    parts.extend(text for text in (VOICES[voice], DELIVERIES[delivery], PRODUCTION[production]) if text)
    if not parts:
        raise gr.Error("Choose at least one instrument or vocal/production option first.")
    compiled = caption + MARKER + ". ".join(parts) + "."
    if len(compiled) > 5500:
        raise gr.Error("Choose fewer sound details so the request stays focused.")
    return compiled


def performance_lyrics(lyrics, voice, delivery):
    """Remove separate harsh-role headings for explicit clean or continuous solo delivery."""
    text = str(lyrics or "")
    if voice not in {"One female singer", "One male singer"} or (
        delivery != "Clean → rasp → brief scream" and delivery not in CLEAN_DELIVERIES
    ):
        return text
    return re.sub(r"(?im)^[ \t]*\[(?:scream|screaming|growl|growling)\][ \t]*\r?\n?", "", text)


def apply_palette(caption, intro, main, voice, delivery, production, lyrics, saved_lyrics):
    """Apply reviewed sound choices and preserve the remembered vocal lyrics on instrumentals."""
    compiled = compile_palette(caption, intro, main, voice, delivery, production)
    was_instrumental = str(lyrics).strip().lower() == "[instrumental]"
    restore_vocals = was_instrumental and voice not in {"Keep my request", "Instrumental"}
    updated = performance_lyrics(saved_lyrics if restore_vocals else lyrics, voice, delivery)
    instrumental = True if voice == "Instrumental" else (
        gr.skip() if voice == "Keep my request" else False)
    remembered = saved_lyrics if was_instrumental and not restore_vocals else updated
    status = ("Sound choices applied. Lyrics words are kept; separate scream/growl headings are removed "
        "for explicit clean solo vocals or continuous solo-vocal transitions. These are model instructions, not new sound samples "
        "or a guarantee of realistic instruments or a fixed singer identity.")
    return compiled, instrumental, updated, remembered, status
