"""Explicit lyrics drafting and vocal-song validation for the local studio."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from uuid import uuid4

import gradio as gr


def check_vocal_lyrics(task_type,lyrics):
    """Prevent an empty vocal request from silently becoming an instrumental."""
    if task_type!="text2music":
        return
    text = str(lyrics or "").strip()
    if not text:
        raise gr.Error("Add lyrics for the singer, use Draft English lyrics, or tick Instrumental.")
    if re.fullmatch(r"\[instrumental\]",text,re.IGNORECASE):
        return
    if not re.sub(r"\[[^\]]*\]","",text).strip():
        raise gr.Error("Section headings need actual words to sing underneath them.")


def draft_lyrics(idea,style,duration,dit_handler=None):
    """Run only the installed writer in a temporary process and return a reviewable draft."""
    if not str(idea or "").strip() or len(str(idea))>2000 or len(str(style))>3000 or duration is None or not 30<=duration<=480:
        raise gr.Error("Describe the story briefly and choose a song length of 30–480 seconds.")
    root = Path(__file__).resolve().parents[1]
    if not (root/"checkpoints/acestep-5Hz-lm-1.7B/model.safetensors").exists():
        raise gr.Error("The local lyric writer is not installed. Paste your own lyrics instead.")
    from acestep.lyric_memory import release_idle_music_gpu
    release_idle_music_gpu(dit_handler)
    folder = root/"acestep_output/lyric-drafts"/uuid4().hex
    folder.mkdir(parents=True)
    request,output = folder/"request.json",folder/"draft.json"
    request.write_text(json.dumps(dict(idea=idea,style=style,duration=duration)),encoding="utf-8")
    try:
        with (folder/"writer.log").open("w",encoding="utf-8") as log:
            subprocess.run([sys.executable,"-m","acestep.songwriting_worker",str(request),str(output)],
                cwd=root,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=900,
                env=dict(os.environ,PYTHONUTF8="1"))
    except (OSError,subprocess.SubprocessError) as error:
        raise gr.Error("The local writer did not finish. Your existing lyrics are unchanged; you can paste lyrics manually.") from error
    lyrics = json.loads(output.read_text(encoding="utf-8"))["lyrics"]
    check_vocal_lyrics("text2music",lyrics)
    return lyrics,"Draft ready. Check the story, repeated chorus and bridge; the writer can miss your brief. Edit, then press Use this draft."


def use_draft(text):
    """Apply a reviewed draft, explicitly enabling vocals."""
    check_vocal_lyrics("text2music",text)
    return text,False,text


def lyric_structure(text):
    """Show the section instructions actually present, without claiming audio adherence."""
    if not str(text or "").strip():
        return "Add lyrics above, or draft them below."
    tags = [tag.strip().lower() for tag in re.findall(r"\[([^\]]+)\]",text)]
    if tags==["instrumental"]:
        return "Instrumental selected — no singing requested."
    verses = sum(bool(re.fullmatch(r"verse(?: \d+)?",tag)) for tag in tags)
    choruses = sum(bool(re.fullmatch(r"(?:final )?chorus(?: \d+)?",tag)) for tag in tags)
    bridges = sum(bool(re.fullmatch(r"bridge(?: \d+)?",tag)) for tag in tags)
    return f"Requested structure — Verses: {verses} · Choruses: {choruses} · Bridges: {bridges}"


def build_songwriting(lyrics,instrumental,caption,duration,saved_lyrics,dit_handler):
    """Expose a short story brief and explicit review step, not automatic overwriting."""
    outline = gr.Markdown(lyric_structure(""))
    lyrics.change(lyric_structure,lyrics,outline)
    with gr.Accordion("✍ Write English lyrics from my idea",open=False):
        gr.Markdown("Draft → review → Use this draft → Generate Music. Section tags guide the model; "
            "their exact timing and vocal delivery still need listening.")
        idea = gr.Textbox(label="What is the song about?",lines=3,
            placeholder="An underestimated fighter grows stronger, survives dark dungeons and commands shadows")
        action = gr.Button("Draft English lyrics · local writer")
        draft = gr.Textbox(label="Review and edit the draft",lines=12)
        status = gr.Textbox(label="Writer status",interactive=False)
        def write(brief,style,seconds):
            """Draft only while the shared music-generation queue is idle."""
            return draft_lyrics(brief,style,seconds,dit_handler)
        action.click(write,[idea,caption,duration],[draft,status],concurrency_id="music_gpu",concurrency_limit=1)
        gr.Button("Use this draft in my song").click(use_draft,draft,[lyrics,instrumental,saved_lyrics])
