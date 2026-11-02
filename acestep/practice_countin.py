"""Add a quiet preparation count-in without changing the backing's musical timing."""
from pathlib import Path
from uuid import uuid4

import gradio as gr
import numpy as np
import soundfile as sf


def count_in(path: str, bpm: float):
    """Prepend four clicks at the chosen preparation tempo and return a new WAV."""
    if not path or not Path(path).is_file() or not 30<=bpm<=240:
        raise gr.Error("Choose a practice clip and a count-in tempo between 30 and 240 BPM.")
    info = sf.info(path)
    if info.duration>600 or info.samplerate>192000:
        raise gr.Error("Use a practice clip of ten minutes or less at a standard sample rate.")
    audio,rate = sf.read(path,always_2d=True,dtype="float32")
    if not np.isfinite(audio).all():
        raise gr.Error("The clip contains invalid audio samples.")
    lead = np.zeros((round(4*60/bpm*rate),audio.shape[1]),np.float32)
    length = min(round(0.055*rate),len(lead))
    t = np.arange(length)/rate
    for beat in range(4):
        offset = round(beat*60/bpm*rate)
        click = 0.06*np.sin(2*np.pi*(1100 if beat==0 else 850)*t)*np.exp(-t*65)
        lead[offset:offset+length] += click[:,None]
    destination = Path(__file__).resolve().parents[1]/"acestep_output/practice-countin"/f"{uuid4().hex}.wav"
    destination.parent.mkdir(parents=True,exist_ok=True)
    sf.write(destination,np.concatenate([lead,audio]),rate,subtype="PCM_24")
    return str(destination),(
        f"Four preparation beats added ({4*60/bpm:.2f} seconds). The backing itself is unchanged. "
        "This tempo is your choice, not detected from the song. Sing after any musical intro in the backing.")


def build_countin(excerpt):
    """Connect the optional count-in to the short practice clip."""
    with gr.Accordion("Give me four beats before the practice clip",open=False):
        bpm = gr.Number(value=100,label="Preparation tempo (BPM)",minimum=30,maximum=240)
        action = gr.Button("Make practice copy with count-in")
        audio = gr.Audio(label="Practice copy — four clicks then backing",type="filepath")
        status = gr.Textbox(label="Count-in status",interactive=False)
        action.click(count_in,[excerpt,bpm],[audio,status])
