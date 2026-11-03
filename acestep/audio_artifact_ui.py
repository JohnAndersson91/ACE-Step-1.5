"""Sound-check controls with a persistent preview pause and no automatic playback."""
import json
from pathlib import Path

import gradio as gr

from acestep.audio_artifact_gate import ROOT, listening_hold, scan_file, set_listening_hold
from acestep.audio_artifact_plot import artifact_figure


def inspect_sound(upload, saved, start, duration):
    """Return only measurements and a static plot, never an audio player."""
    path = upload or saved
    if not path:
        raise gr.Error("Choose an audio file to inspect. This will not play it.")
    report = scan_file(path)
    if "error" in report:
        return report, None
    try:
        figure = artifact_figure(path, start, duration)
    except (ValueError, OSError, RuntimeError) as error:
        raise gr.Error(str(error)) from error
    return report, figure


def build_sound_check():
    """Expose silent inspection and the user's explicit playback-pause setting."""
    with gr.Accordion("Sound check — inspect without listening", open=listening_hold()):
        gr.Markdown("Generated previews can be paused while inspecting frequency spikes. "
                    "Alerts are conservative clues, not proof of hearing safety or a diagnosis.")
        hold = gr.Checkbox(value=listening_hold(), label="Pause audio players")
        status = gr.Textbox(value="Previews paused." if listening_hold() else "Spectral screening active.",
                            label="Preview status", interactive=False)
        hold.change(set_listening_hold, [hold], [status], js="""(hold) => {
            window.acestepListeningHold = hold;
            const walk = root => {
                root.querySelectorAll('audio').forEach(audio => {
                    if (hold) {
                        if (audio.dataset.acestepHoldMuted === undefined)
                            audio.dataset.acestepHoldMuted = audio.muted ? '1' : '0';
                        audio.muted = true; audio.pause();
                    } else if (audio.dataset.acestepHoldMuted !== undefined) {
                        audio.muted = audio.dataset.acestepHoldMuted === '1';
                        delete audio.dataset.acestepHoldMuted;
                    }
                });
                root.querySelectorAll('*').forEach(node => { if (node.shadowRoot) walk(node.shadowRoot); });
            };
            walk(document);
            return hold;
        }""")
        try:
            known = json.loads((ROOT/"recent-files.json").read_text("utf-8"))
            choices = [(Path(path).name, path) for path in known if Path(path).is_file()]
        except (OSError, ValueError, TypeError):
            choices = []
        saved = gr.Dropdown(choices, value=choices[0][1] if choices else None,
                            label="Recent audio to inspect")
        upload = gr.File(label="Or choose a saved file (no playback)", type="filepath",
                          file_types=[".wav", ".mp3", ".flac"])
        with gr.Row():
            start = gr.Number(value=20, minimum=0, label="Graph starts at (seconds)")
            duration = gr.Slider(1, 30, value=10, step=1, label="Graph duration (seconds)")
        action = gr.Button("Inspect without playing")
        figure = gr.Plot(label="Frequency view — silent")
        with gr.Accordion("Flagged times and measurements", open=False):
            report = gr.JSON(label="Screening report — not a hearing-safety rating")
        action.click(inspect_sound, [upload, saved, start, duration], [report, figure],
                      api_name="inspect_sound")
