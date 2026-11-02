"""Correction workspace for the existing song excerpt and its estimated score."""
from pathlib import Path
from uuid import uuid4

import gradio as gr
import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]
SESSION = ROOT / "acestep_output/correction-session"


def matched_pair(original: Path, piano: Path, folder: Path) -> tuple[str,str]:
    """Match RMS by attenuation only; never boost either comparison file."""
    audio = [sf.read(original,always_2d=True),sf.read(piano,always_2d=True)]
    rms = [max(float(np.sqrt(np.mean(x*x))),1e-10) for x,_ in audio]
    target = min(*rms,0.025)
    paths = []
    for name,(samples,rate),level in zip(("original","piano"),audio,rms):
        destination = folder / f"compare-{name}.wav"
        sf.write(destination,samples*(target/level),rate,subtype="PCM_16")
        paths.append(str(destination))
    return tuple(paths)


def load_session():
    """Load existing estimates without claiming the song has been transcribed correctly."""
    from acestep.score_editor import load_notes,validate_notes
    from acestep.chord_editor import suggest_chords

    if not (SESSION / "source.wav").exists():
        raise gr.Error("No correction session has been prepared on this PC.")
    duration = sf.info(SESSION / "source.wav").duration
    rows = load_notes(SESSION)
    score = validate_notes(rows,duration)
    chords = suggest_chords(score,duration)
    folder = SESSION / "comparisons"
    folder.mkdir(exist_ok=True)
    original,piano = matched_pair(SESSION/"source.wav",SESSION/"Piano.wav",folder)
    return rows,chords,original,piano,duration,"Loaded estimates for original 0:25–0:50. Chords are guesses, not verified."


def render_edits(rows: list, chords: list, replace_chords: bool, duration: float):
    """Validate edits, render piano, and keep the source comparison at a matched level."""
    from acestep.score_editor import validate_notes,load_notes
    from acestep.chord_editor import apply_chords
    from acestep.arranger_render import render_arrangement

    score = validate_notes(rows,duration)
    if replace_chords:
        score = apply_chords(score,chords,duration)
    folder = SESSION / "edits" / uuid4().hex
    folder.mkdir(parents=True)
    for part,midi in score.items():
        midi.write(str(folder / f"score-{part}.mid"))
    render_arrangement(score,str(ROOT/"checkpoints/reconstruction/GeneralUser-GS.sf2"),
                       duration,"Piano",folder/"Piano")
    original,piano = matched_pair(SESSION/"source.wav",folder/"Piano.wav",folder)
    return original,piano,[str(p) for p in sorted(folder.glob("*.mid"))],load_notes(folder),(
        "Rendered the current note edits. A/B levels are matched by attenuation; "
        "musical correctness still needs listening.")


def build_correction_lab() -> None:
    """Show editable musical estimates and synchronized-position comparison controls."""
    from acestep.comparison_player import build_comparison_player

    with gr.Accordion("Correct notes and chords — original vs piano",open=False):
        gr.Markdown("Current test: original song 0:25–0:50. Times in the tables are relative "
                    "to that excerpt. Phrase boundaries and all notes/chords remain unverified. "
                    "Edit a note such as C4, its start/end in seconds, or velocity 1–127. "
                    "This workspace allows correction; it does not certify the estimates.")
        load = gr.Button("Load current song and estimated notes")
        duration = gr.State(25.0)
        notes = gr.Dataframe(headers=["part","start","end","note","velocity"],
            datatype=["str","number","number","str","number"],type="array",interactive=True)
        chords = gr.Dataframe(headers=["start","end","chord guess"],
            datatype=["number","number","str"],type="array",interactive=True)
        replace = gr.Checkbox(value=False,label="Replace accompaniment with my edited chord table")
        from acestep.score_review import build_score_review
        build_score_review(notes,duration)
        comparison = build_comparison_player()
        render = gr.Button("Render piano from edited notes")
        midi = gr.File(label="Edited MIDI files",file_count="multiple")
        status = gr.Textbox(label="Correction status",interactive=False)
        load.click(load_workspace,outputs=[notes,chords,comparison,duration,status])
        render.click(render_workspace,[notes,chords,replace,duration],[comparison,midi,notes,status])


def load_workspace():
    """Adapt saved files into a single self-contained native A/B player."""
    from acestep.comparison_player import comparison_markup
    notes,chords,original,piano,duration,status = load_session()
    return notes,chords,comparison_markup(original,piano),duration,status


def render_workspace(rows, chords, replace, duration):
    """Refresh the self-contained comparison after rendering user edits."""
    from acestep.comparison_player import comparison_markup
    original,piano,midi,notes,status = render_edits(rows,chords,replace,duration)
    return comparison_markup(original,piano),midi,notes,status
