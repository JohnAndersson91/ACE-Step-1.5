"""Analyze a bounded reference clip locally with the already installed music models."""
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from uuid import uuid4

import gradio as gr
import imageio_ffmpeg
import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]


def preview_reference(path, start, seconds):
    """Prepare a playable reference section without loading any analysis model."""
    folder = ROOT / "acestep_output/reference-analysis" / uuid4().hex
    folder.mkdir(parents=True)
    clip = prepare_reference(path, start, seconds, folder)
    return str(clip), "", None, "Section ready. Describe what you like, or apply just the audio guidance."


def prepare_reference(path, start, seconds, folder):
    """Decode a selected 10–30 second segment without modifying the source file."""
    if not path or not Path(path).is_file():
        raise gr.Error("Upload a reference song first.")
    if (not isinstance(start, (int, float)) or not math.isfinite(start) or
            not 0 <= start <= 3600 or not isinstance(seconds, (int, float)) or
            not math.isfinite(seconds) or not 10 <= seconds <= 30):
        raise gr.Error("Choose a start from 0–3600 seconds and a clip length of 10–30 seconds.")
    clip = folder / "reference-clip.wav"
    try:
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-y", "-ss", str(start),
            "-i", str(path), "-t", str(seconds), "-vn", "-ar", "48000", "-ac", "2",
            "-c:a", "pcm_s24le", str(clip)], check=True, capture_output=True, timeout=90)
        audio, rate = sf.read(clip, dtype="float32")
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise gr.Error("Could not read that section. Try an earlier start or a WAV/MP3 file.") from error
    if len(audio) / rate < 9.9 or not np.isfinite(audio).all() or np.max(abs(audio)) < 1e-6:
        raise gr.Error("Choose a section with at least 10 seconds of audible music.")
    return clip


def analyze_reference(path, start, seconds, handler):
    """Encode real audio, offload idle models, and run a temporary offline analyzer."""
    if not (ROOT / "checkpoints/acestep-5Hz-lm-1.7B/model.safetensors").is_file():
        raise gr.Error("The local analyzer model is missing. No download was attempted.")
    if getattr(handler, "model", None) is None:
        raise gr.Error("Wait for the music program to finish starting, then try again.")
    folder = ROOT / "acestep_output/reference-analysis" / uuid4().hex
    folder.mkdir(parents=True)
    clip = prepare_reference(path, start, seconds, folder)
    codes = handler.convert_src_audio_to_codes(str(clip))
    if not codes or "<|audio_code_" not in codes:
        raise gr.Error("The music model could not read this reference. Nothing was applied.")
    from acestep.lyric_memory import release_idle_music_gpu
    release_idle_music_gpu(handler)
    request, output = folder / "request.json", folder / "analysis.json"
    request.write_text(json.dumps(dict(mode="reference", audio_codes=codes)), encoding="utf-8")
    try:
        with (folder / "analyzer.log").open("w", encoding="utf-8") as log:
            subprocess.run([sys.executable, "-m", "acestep.songwriting_worker", str(request),
                str(output)], cwd=ROOT, check=True, stdout=log, stderr=subprocess.STDOUT,
                timeout=900, env=dict(os.environ, PYTHONUTF8="1", HF_HUB_OFFLINE="1",
                    TRANSFORMERS_OFFLINE="1"))
        result = json.loads(output.read_text(encoding="utf-8"))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise gr.Error("The local analyzer did not finish. Your song settings are unchanged.") from error
    caption = str(result.get("caption", "")).strip()
    if not caption:
        raise gr.Error("No description was returned. Your song settings are unchanged.")
    bpm = valid_tempo(result.get("bpm"))
    return str(clip), caption, bpm, ("Analysis ready — edit the description before using it. "
        f"Estimated key: {result.get('key') or 'unknown'}. Tempo and instruments may be wrong. "
        "This describes the selected clip; it does not identify the song or copy its arrangement.")


def valid_tempo(value):
    """Accept only finite, plausible model tempo estimates."""
    try:
        tempo = float(value)
    except (TypeError, ValueError):
        return None
    return round(tempo) if math.isfinite(tempo) and 30 <= tempo <= 240 else None


def apply_reference(caption, description, tempo, use_tempo, clip, use_audio):
    """Apply reviewed traits without replacing lyrics, language, voice, or song duration."""
    description = str(description or "").strip()
    if (not description and not use_audio) or len(description) > 3000:
        raise gr.Error("Add a sound description of up to 3000 characters, or enable audio guidance.")
    caption = str(caption or "").strip()
    combined = caption if not description or description in caption else (
        caption + "\nReference traits: " + description).strip()
    bpm = valid_tempo(tempo) if use_tempo else None
    if use_audio and (not clip or not Path(clip).is_file()):
        raise gr.Error("Prepare a reference section before enabling audio guidance.")
    return (combined, bpm if bpm else gr.skip(), False if bpm else gr.skip(),
        clip if use_audio else gr.skip(), "Reference applied. Your lyrics and chosen song length are kept.")
