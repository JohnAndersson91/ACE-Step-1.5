"""Estimate a shared, editable score before selecting playback instruments."""
from pathlib import Path

import librosa
import numpy as np
import pretty_midi
from scipy.ndimage import median_filter


def monophonic_notes(path: str, low: float, high: float) -> pretty_midi.PrettyMIDI:
    """Track a single pitched line, smoothing vibrato before MIDI quantization."""
    audio, rate = librosa.load(path,sr=22050)
    frequency, voiced, _ = librosa.pyin(audio,sr=rate,hop_length=256,frame_length=2048,
                                      fmin=low,fmax=high)
    pitch = np.where(voiced & np.isfinite(frequency),
                     np.rint(librosa.hz_to_midi(np.nan_to_num(frequency,nan=low))),-1)
    pitch = median_filter(pitch,size=5)
    result = pretty_midi.PrettyMIDI()
    track = pretty_midi.Instrument(0)
    start = 0
    for index in range(1,len(pitch)+1):
        if index < len(pitch) and pitch[index] == pitch[start]:
            continue
        beginning, end = start*256/rate,min(index*256/rate,len(audio)/rate)
        if pitch[start] >= 0 and end-beginning >= 0.09:
            track.notes.append(pretty_midi.Note(80,int(pitch[start]),beginning,end))
        start = index
    result.instruments.append(track)
    return result


def build_score(stems: Path, output: Path) -> dict:
    """Estimate melody, bass, accompaniment and drums with explicit provenance."""
    from basic_pitch.inference import predict
    from acestep.reconstruction_render import render_drum_sketch

    score = {
        "melody": monophonic_notes(str(stems / "vocals.wav"),80,1000),
        "bass": monophonic_notes(str(stems / "bass.wav"),32,300),
    }
    _, score["accompaniment"], _ = predict(stems / "other.wav",onset_threshold=0.65,
        frame_threshold=0.45,minimum_note_length=180,minimum_frequency=120,maximum_frequency=1400)
    duration = librosa.get_duration(path=str(stems / "drums.wav"))
    _, score["drums"] = render_drum_sketch(str(stems / "drums.wav"),duration)
    for name,midi in score.items():
        midi.write(str(output / f"score-{name}.mid"))
    return score
