"""Keep explicit vocal delivery choices consistent without altering lyric words."""
import re

import gradio as gr

CLEAN_DELIVERIES = {"Clean throughout", "Clean and intimate", "Powerful clean belting",
                    "Clean and powerful throughout"}
HARSH = re.compile(r"\b(?:rasp(?:y)?|scream(?:s|ed|ing)?|growl(?:s|ed|ing)?|harsh vocals?)\b", re.I)


def validate_delivery(caption, delivery):
    """Reject positive harsh-vocal requests under an explicitly clean selection."""
    if delivery not in CLEAN_DELIVERIES:
        return
    text = str(caption or "")
    for match in HARSH.finditer(text):
        if re.match(r"\s+(?:electric\s+)?guitar\b", text[match.end():], re.I):
            continue
        prefix = re.split(r"[.!?;\n]|\bbut\b", text[:match.start()], flags=re.I)[-1]
        negative = re.search(r"\b(?:no|not|without|avoid|never|exclude|don't want|do not want)\b",
                             prefix, re.I)
        if not negative and not text[match.end():].lower().startswith("-free"):
            raise gr.Error("Clean vocals are selected, but the description still requests rasp, "
                           "screaming or growling. Remove that conflicting direction first.")


def replace_managed_direction(caption, explicit_delivery):
    """Drop the old generated performance block when applying a new delivery choice."""
    text = str(caption or "")
    if explicit_delivery != "Keep my request":
        text = text.split("\n\nPerformance direction:\n", 1)[0]
    return text
