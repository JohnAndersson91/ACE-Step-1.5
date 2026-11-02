"""Local stem separation, practice trimming, and editable song transcription."""

from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import gradio as gr
import numpy as np
import soundfile as sf


def trim_audio(path: str, start: float, end: float) -> str:
    """Save an audio excerpt with a short fade at its end."""
    if not path:
        raise gr.Error("Upload or choose an audio file first.")
    info = sf.info(path)
    end = min(float(end), info.duration)
    if not 0 <= float(start) < end:
        raise gr.Error("End time must be after start time and inside the song.")
    audio, rate = sf.read(path, start=int(start * info.samplerate),
                          stop=int(end * info.samplerate), always_2d=True)
    fade = min(len(audio), int(rate * 0.25))
    audio[-fade:] *= np.linspace(1, 0, fade)[:, None]
    folder = Path(__file__).resolve().parents[1] / "acestep_output" / "practice"
    folder.mkdir(parents=True, exist_ok=True)
    result = folder / f"practice-{uuid4().hex}.wav"
    sf.write(result, audio, rate, subtype="PCM_16")
    return str(result)


def split_audio(path: str, quality: str = "Quick") -> tuple[str, str]:
    """Separate a local recording into instrumental and vocal WAV files."""
    if not path:
        raise gr.Error("Upload or import a recording first.")
    if quality not in {"Quick", "Higher quality (slower)"}:
        raise gr.Error("Choose a separation quality.")
    model = "htdemucs_ft" if quality != "Quick" else "htdemucs"
    import torch
    device = "cuda" if torch.cuda.is_available() else "cpu"
    folder = Path(__file__).resolve().parents[1] / "acestep_output" / "stems" / uuid4().hex
    try:
        subprocess.run(
            [sys.executable, "-m", "demucs", "--two-stems", "vocals", "-n", model,
             "--segment", "5", "--shifts", "2" if quality != "Quick" else "1",
             "-d", device, "-o", str(folder), path],
            check=True, capture_output=True, timeout=1800,
        )
    except subprocess.SubprocessError as error:
        raise gr.Error("Separation failed. Try a shorter WAV recording.") from error
    output = folder / model / Path(path).stem
    return str(output / "no_vocals.wav"), str(output / "vocals.wav")


def transcribe_lyrics(path: str) -> str:
    """Produce editable draft lyrics from uploaded audio, using local Whisper."""
    if not path:
        raise gr.Error("Choose a vocal recording first.")
    from faster_whisper import WhisperModel

    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(path, beam_size=5, vad_filter=False)
    return "\n".join(segment.text.strip() for segment in segments)


def build_practice_controls(source: gr.Audio, lyrics: gr.Textbox) -> None:
    """Build a practice workspace that also displays the generation lyrics."""
    with gr.Accordion("Vocal practice, stems and lyrics", open=False):
        gr.Markdown("Import/upload a song above, then separate it. CPU separation can take a few minutes.")
        split = gr.Button("Separate source into instrumental and vocals")
        quality = gr.Radio(["Quick", "Higher quality (slower)"], value="Higher quality (slower)",
                           label="Separation quality")
        gr.Markdown("Separation preserves the recording's timing but can leave artifacts. "
                    "An exact clean instrumental is not guaranteed. Remix generation changes the music.")
        instrumental = gr.Audio(label="Instrumental backing", type="filepath")
        vocals = gr.Audio(label="Isolated vocals / vocal recording", type="filepath")
        from acestep.vocal_recording import build_recorder
        build_recorder(vocals)
        split.click(split_audio, [source, quality], [instrumental, vocals])
        with gr.Row():
            start = gr.Number(value=0, label="Practice start (seconds)")
            end = gr.Number(value=90, label="Practice end (seconds)")
        trim = gr.Button("Make short practice backing")
        excerpt = gr.Audio(label="Short practice backing", type="filepath")
        trim.click(trim_audio, [instrumental, start, end], excerpt)
        draft = gr.Button("Transcribe vocals into draft lyrics")
        viewer = gr.Textbox(label="Practice lyrics (editable)", lines=18, interactive=True)
        gr.Markdown("Automatic lyrics may be inaccurate. Correct them before singing.")
        draft.click(transcribe_lyrics, vocals, viewer)
        show = gr.Button("Show my generation lyrics here")
        show.click(lambda text: text, lyrics, viewer)
