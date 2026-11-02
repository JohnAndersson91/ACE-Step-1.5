"""Store dry vocal takes shared by the desktop recorder and phone uploader."""

from datetime import datetime
from pathlib import Path
import subprocess
from uuid import uuid4

import gradio as gr
import imageio_ffmpeg


TAKES = Path(__file__).resolve().parents[1] / "acestep_output" / "vocal_takes"


def save_take(path: str) -> tuple[str, str]:
    """Convert an uploaded or recorded take to a persistent WAV on this PC."""
    if not path or not Path(path).is_file():
        raise gr.Error("Record or upload a vocal take first.")
    TAKES.mkdir(parents=True, exist_ok=True)
    destination = TAKES / f"take-{datetime.now():%Y%m%d-%H%M%S}-{uuid4().hex[:6]}.wav"
    try:
        subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-y", "-i", path,
             "-vn", "-c:a", "pcm_s16le", str(destination)],
            check=True, capture_output=True, timeout=600,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise gr.Error("Could not save this recording. Try WAV, MP3 or M4A.") from error
    return str(destination), f"Saved on PC: {destination.name}"


def list_takes() -> gr.update:
    """Refresh the shared saved-take list, including files received from a phone."""
    choices = sorted(TAKES.glob("*.wav"), reverse=True) if TAKES.exists() else []
    names = [path.name for path in choices]
    return gr.update(choices=names, value=names[0] if names else None)


def load_take(name: str) -> str:
    """Resolve only a take within the dedicated recordings directory."""
    if not name or Path(name).name != name:
        raise gr.Error("Select a saved take first.")
    path = TAKES / name
    if not path.is_file():
        raise gr.Error("This recording no longer exists.")
    return str(path)


def build_recorder(vocals: gr.Audio) -> None:
    """Add recording, upload, monitoring and shared phone-take controls."""
    from acestep.vocal_monitor import build_monitor

    with gr.Accordion("Record my vocals / receive phone recordings", open=False):
        gr.Markdown("Use headphones. Play the backing separately and record your voice here. "
                    "This saves a separate vocal take; it does not automatically align it to the backing.")
        build_monitor()
        recording = gr.Audio(label="My dry vocal take", sources=["microphone", "upload"],
                             type="filepath", format="wav")
        save = gr.Button("Save my vocal take on PC")
        status = gr.Textbox(label="Recording status", interactive=False)
        save.click(save_take, recording, [vocals, status])
        takes = gr.Dropdown(label="Saved takes (including phone uploads)", choices=[])
        refresh = gr.Button("Refresh saved takes")
        refresh.click(list_takes, outputs=takes)
        load = gr.Button("Load selected take as my vocals")
        load.click(load_take, takes, vocals)
