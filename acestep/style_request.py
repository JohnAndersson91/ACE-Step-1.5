"""Translate a small, explicit style library into musical instructions, not artist cloning."""
import re

import gradio as gr


PROFILE_SOURCE = "https://www.nuclearblast.com/blogs/news/children-of-bodom-enter-the-studio-2877191"
BODOM = re.compile(r"(?:a\s+)?children\s+of\s+bodo+m(?:['’]s)?(?:[-\s]+style)?(?:\s+intro)?",re.I)
DIRECTION = "\n\nPerformance direction:\n"


def expand_style_request(text):
    """Resolve supported references while preserving intro scope and explicit exclusions."""
    text = str(text or "")
    matched = []

    def replace(match):
        prefix = text[max(0,match.start()-35):match.start()]
        if re.search(r"(?:not\s+like|avoid|unlike|without|don['’]t want)\s*$",prefix,re.I):
            return match.group()
        intro = "intro" in match.group().lower() or bool(re.search(r"intro.{0,25}$",prefix,re.I))
        scope = "Intro direction" if intro else "Musical direction"
        matched.append("Children of Bodom → melodic / neoclassical metal guitar traits")
        return (scope+": Finnish melodic death-metal and neoclassical-metal influences, "
            "a dominant electric-guitar lead, harmonic-minor melodic phrases, alternate-picked runs, "
            "sweep-picked arpeggios, harmonized lead lines and tight palm-muted supporting riffs. "
            "Write a new melody rather than quoting a particular recording")

    return BODOM.sub(replace,text),matched


def shape_style(text,tempo,power,rasp,natural,language,voice="Female"):
    """Combine an editable request with explicit performance and metadata choices."""
    text = str(text or "").split(DIRECTION,1)[0].strip()
    if not text or len(text)>2200:
        raise gr.Error("Describe the sound briefly before applying these controls.")
    if tempo is not None and not 30<=tempo<=240:
        raise gr.Error("Choose 30–240 BPM, or leave tempo empty.")
    powers = {"Natural":"expressive lead vocal with clear diction",
        "Powerful":"full-bodied lead vocal, strong chest voice, confident projection and dynamic attack",
        "Epic":"commanding full-bodied lead vocal, strong chest voice, soaring anthemic choruses and emotional intensity"}
    rasps = {"Clean throughout":"clean melodic singing throughout",
        "A few transitions":"mostly clean melodic singing; on only two climactic lines, gradually add grit and rasp "
            "within the same sung phrase, crest briefly into a human metal scream, then return to clean singing; "
            "keep other lines clean; no guttural or creature-like delivery",
        "Mostly harsh":"predominantly harsh human metal singing with clear rhythmic phrasing"}
    if power not in powers or rasp not in rasps:
        raise gr.Error("Choose a vocal-power and rasp option.")
    if voice not in {"Female","Male","Unspecified"}:
        raise gr.Error("Choose a lead voice.")
    from acestep.constants import VALID_LANGUAGES
    if language not in VALID_LANGUAGES or language=="unknown":
        raise gr.Error("Choose a supported vocal language.")
    expanded,matches = expand_style_request(text)
    parts = [powers[power],rasps[rasp]]
    if voice!="Unspecified":
        parts.insert(0,f"{voice.lower()} lead singer")
    if natural:
        parts.append("natural pitch movement and human phrasing, restrained vocal layering, audible breath and "
            "preserved vocal texture; avoid robotic pitch snapping and synthetic vocal doubling")
    if tempo is not None:
        parts.append(f"tempo {tempo:g} BPM")
    caption = expanded+DIRECTION+". ".join(parts)+"."
    summary = ("Mapped: "+"; ".join(matches)+". " if matches else "No curated artist match; your description is kept. ")
    return (caption,gr.update(value=tempo,interactive=True) if tempo is not None else gr.skip(),
        False if tempo is not None else gr.skip(),language,False,
        summary+"Applied as model instructions. Lyrics are unchanged. This cannot guarantee artist similarity, "
        "a rasp transition, or removal of pitch artifacts.")


def check_song_length(task_type,duration):
    """Require a chosen length for new songs instead of silently using a fallback."""
    if task_type=="text2music" and (duration is None or not 10<=duration<=600):
        raise gr.Error("Choose your song length in seconds before generating (for example 60, 150 or 240).")
