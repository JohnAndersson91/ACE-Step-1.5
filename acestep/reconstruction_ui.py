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
    with gr.Accordion("Arrange a song — controlled piano, guitar and rock tests",open=False):
        gr.Markdown("Transcribes one estimated score, then assigns instruments explicitly. "
                    "Piano uses only piano samples; acoustic guitar uses only steel-string "
                    "guitar samples. Rock uses electric guitar, bass and drums selected by us, "
                    "not automatically identified original instruments. No original audio is "
                    "mixed into these renders. Notes and rhythms still require listening and correction. "
                    "On a new installation, run Setup Reconstruction.bat first.")
        start = gr.Number(value=0,label="Rebuild start (seconds)")
        duration = gr.Slider(10,60,value=25,step=1,label="Rebuild length (seconds)")
        melody = gr.Checkbox(value=True,label="Play the estimated singing melody on an instrument")
        action = gr.Button("Make all three arrangement tests")
        rock = gr.Audio(label="Estimated rock ensemble",type="filepath")
        guitar = gr.Audio(label="Acoustic guitar arrangement",type="filepath")
        piano = gr.Audio(label="Piano arrangement",type="filepath")
        midi = gr.File(label="Editable MIDI parts",file_count="multiple")
        status = gr.Textbox(label="Reconstruction status",interactive=False)
        action.click(controlled_arrange,[source,start,duration,melody],[rock,guitar,piano,midi,status])


def controlled_arrange(source: str, start: float, duration: float, melody: bool):
    """Render the same score into three explicit layouts in an isolated process."""
    if not source or start < 0 or not 10 <= duration <= 60:
        raise gr.Error("Choose source audio, a valid start and 10–60 seconds.")
    try:
        length = sf.info(source).duration
    except (OSError,RuntimeError) as error:
        raise gr.Error("Please convert your source to WAV first.") from error
    if start >= length:
        raise gr.Error("Start time is outside the recording.")
    folder = Path(__file__).resolve().parents[1] / "acestep_output/arrangements" / uuid4().hex
    try:
        subprocess.run([sys.executable,"-m","acestep.arranger_worker",source,str(folder),
                        str(start),str(duration),str(bool(melody)).lower()],
                       check=True,capture_output=True,timeout=1800)
    except subprocess.SubprocessError as error:
        raise gr.Error("Arrangement test failed. Check reconstruction setup and try a shorter clip.") from error
    files = [folder / f"{name}.wav" for name in ["Rock ensemble (estimated)","Acoustic guitar","Piano"]]
    if not all(path.exists() for path in files):
        raise gr.Error("Not all arrangement files were produced.")
    return *map(str,files),[str(p) for p in sorted(folder.glob("*.mid"))],(
        "Instrument assignments are enforced. The shared score is estimated and has not been "
        "verified by listening. Rock instrumentation is a manual approximation.")
