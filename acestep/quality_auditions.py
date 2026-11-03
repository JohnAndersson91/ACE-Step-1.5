"""Audition completed local sound-setting experiments inside the music studio."""
from pathlib import Path

import gradio as gr

from acestep.audio_review import compare_versions
from acestep.comparison_player import build_comparison_player

ROOT = Path(__file__).resolve().parents[1] / "acestep_output/quality-tests"
BASELINE = "A - current settings"


def available_auditions():
    """List completed WAV tests only; an incomplete experiment is not exposed."""
    files = {path.stem: path for path in sorted(ROOT.glob("*.wav")) if path.is_file()}
    return files if BASELINE in files else {}


def compare_saved_audition(choice, start, duration):
    """Compare a known saved test with its baseline without starting generation."""
    files = available_auditions()
    if choice not in files or choice == BASELINE:
        raise gr.Error("Choose one of the completed sound-setting tests.")
    markup, report = compare_versions(
        str(files[BASELINE]), str(files[choice]), start, duration, True,
    )
    return gr.update(value=markup, visible=True), report


def build_quality_auditions():
    """Expose actual completed tests, without changing any normal generation settings."""
    files = available_auditions()
    choices = [name for name in files if name != BASELINE]
    if not choices:
        return
    with gr.Accordion("Guitar, drum & vocal sound tests", open=False):
        gr.Markdown("Same prompt, lyrics and seed; one setting changes per test. "
                    "Listen for guitar notes, drum attacks and vocal texture. "
                    "These are experiments, not guaranteed upgrades. Your normal settings stay unchanged.")
        choice = gr.Dropdown(choices, value=choices[0], label="Compare current settings against")
        with gr.Row():
            start = gr.Number(value=0, minimum=0, label="Start at (seconds)")
            duration = gr.Slider(1, 30, value=30, step=1, label="Listen for (seconds)")
        action = gr.Button("Listen to matched comparison")
        player = build_comparison_player(labels=("Current settings", "Selected test"), visible=False)
        with gr.Accordion("Technical measurements", open=False):
            report = gr.JSON(label="Levels — not a musical-quality score")
        action.click(compare_saved_audition, [choice, start, duration], [player, report])
