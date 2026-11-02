"""Shared backing, lyrics, and recorder layout for desktop and secure phone use."""

from pathlib import Path

import gradio as gr

from acestep.vocal_recording import save_take


SESSION = Path(__file__).resolve().parents[1] / "acestep_output" / "session"


def build_session(output_audio: gr.Audio | None = None) -> None:
    """Keep backing playback, lyrics and a dry vocal recorder together."""
    backing = SESSION / "backing.wav"
    lyric_file = SESSION / "lyrics.txt"
    gr.Markdown("## Sing the practice section\nWear headphones. Press Record below: "
                "the backing will start from the beginning. Sing, then stop and save. "
                "Playback and recording are not sample-accurately synchronized.")
    gr.Audio(value=str(backing) if backing.exists() else None, label="Practice backing — listen here",
             type="filepath", interactive=True, elem_id="practice-session-backing")
    gr.Textbox(value=lyric_file.read_text(encoding="utf-8") if lyric_file.exists() else "",
               label="Lyrics — draft, correct any wrong words", lines=16, interactive=True)
    recording = gr.Audio(label="Record my voice", sources=["microphone", "upload"],
                         type="filepath", format="wav")
    recording.start_recording(fn=None, js="""() => {
      const audio = [...document.querySelectorAll('#practice-session-backing audio')]
        .find(item => item.src);
      if (audio) { audio.currentTime = 0; audio.play().catch(() => {}); }
    }""")
    recording.stop_recording(fn=None, js="""() => {
      const audio = [...document.querySelectorAll('#practice-session-backing audio')]
        .find(item => item.src);
      if (audio) audio.pause();
    }""")
    saved = output_audio if output_audio is not None else gr.File(label="Saved vocal take")
    status = gr.Textbox(label="Save status", interactive=False)
    gr.Button("Save my voice to PC", variant="primary").click(save_take, recording, [saved, status])
