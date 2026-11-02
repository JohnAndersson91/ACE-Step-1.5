"""Validated UI entry point for explicitly experimental note-based reconstruction."""
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import gradio as gr
import soundfile as sf


def rebuild(source: str, start: float, duration: float, instrument: str):
    """Run a bounded reconstruction test and expose WAV/MIDI outputs."""
    if not source:
        raise gr.Error("Import or upload Source Audio first, preferably as WAV.")
    if instrument not in {"Guitar", "Piano"}:
        raise gr.Error("Choose Guitar or Piano.")
    if not 0 <= start or not 10 <= duration <= 60:
        raise gr.Error("Use a nonnegative start and a duration from 10 to 60 seconds.")
    try:
        length = sf.info(source).duration
    except (RuntimeError, OSError) as error:
        raise gr.Error("Convert your recording to WAV before reconstruction.") from error
    if start >= length:
        raise gr.Error("Start time must be inside the song.")
    folder = Path(__file__).resolve().parents[1] / "acestep_output/reconstruction" / uuid4().hex
    try:
        subprocess.run([sys.executable,"-m","acestep.reconstruction_worker",source,str(folder),
                        str(start),str(duration),instrument],check=True,capture_output=True,timeout=1800)
    except subprocess.SubprocessError as error:
        raise gr.Error("Reconstruction failed. Check Setup Reconstruction.bat and try a shorter WAV.") from error
    output = folder / "rebuilt_sketch.wav"
    if not output.exists():
        raise gr.Error("Reconstruction did not produce audio.")
    return str(output), [str(p) for p in sorted(folder.glob("*.mid"))], (
        "Experimental note-based sketch complete. Bass, accompaniment and drums are estimated; "
        "MIDI files are provided for correction. This is not an exact remake.")


def build_reconstruction_ui(source: gr.Audio) -> None:
    """Expose the prototype with explicit limits and editable MIDI deliverables."""
    with gr.Accordion("Rebuild instrumental — experimental musical sketch",open=False):
        gr.Markdown("Estimates notes from separated bass/accompaniment, then renders new "
                    "sampled instruments and synthetic drums. No original audio is mixed into "
                    "the rendered output. Notes, rhythms and instrument identity can be wrong. "
                    "Test a short clip; this is not a faithful one-click remake. "
                    "On a new installation, run Setup Reconstruction.bat once first.")
        start = gr.Number(value=0,label="Rebuild start (seconds)")
        duration = gr.Slider(10,60,value=25,step=1,label="Rebuild length (seconds)")
        instrument = gr.Radio(["Guitar","Piano"],value="Guitar",label="Accompaniment sound")
        action = gr.Button("Rebuild short instrumental sketch")
        audio = gr.Audio(label="Rebuilt sketch — approximate notes",type="filepath")
        midi = gr.File(label="Editable MIDI parts",file_count="multiple")
        status = gr.Textbox(label="Reconstruction status",interactive=False)
        action.click(rebuild,[source,start,duration,instrument],[audio,midi,status])
