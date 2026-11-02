"""Experimental song reconstruction via source stems, note transcription and synthesis."""
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import soundfile as sf


def reconstruct(source: str, output: str, start: float, duration: float, instrument: str) -> None:
    """Build an editable musical sketch; never claim faithful performance reconstruction."""
    from basic_pitch.inference import predict
    import torch
    from acestep.reconstruction_render import render_notes, render_drum_sketch

    folder = Path(output)
    folder.mkdir(parents=True, exist_ok=True)
    info = sf.info(source)
    audio, rate = sf.read(source, start=int(start*info.samplerate),
                          stop=int((start+duration)*info.samplerate), always_2d=True)
    duration = len(audio)/rate
    clip = folder / "source_excerpt.wav"
    sf.write(clip, audio, rate)
    subprocess.run([sys.executable,"-m","demucs","-n","htdemucs","--segment","5",
                    "--shifts","1","-d","cuda" if torch.cuda.is_available() else "cpu",
                    "-o",str(folder / "stems"),str(clip)],check=True)
    stems = folder / "stems/htdemucs/source_excerpt"
    soundfont = Path(__file__).resolve().parents[1] / "checkpoints/reconstruction/florestan-subset.sf2"
    if not soundfont.exists():
        raise FileNotFoundError("Reconstruction instrument bank is missing. Run Setup Reconstruction.bat.")
    mix = np.zeros((int(duration*44100),2), np.float32)
    metadata = {"prototype": True,"start":start,"duration":duration,"parts":{}}
    for stem, preset, low, high in [("bass",38,32,300),
                                   ("other",24 if instrument=="Guitar" else 2,100,2000)]:
        _, midi, _ = predict(stems / f"{stem}.wav", onset_threshold=0.6,
                             frame_threshold=0.4, minimum_note_length=100,
                             minimum_frequency=low, maximum_frequency=high)
        midi.write(str(folder / f"{stem}.mid"))
        rendered = render_notes(midi,str(soundfont),duration,preset)
        sf.write(folder / f"rebuilt_{stem}.wav",rendered,44100,subtype="FLOAT")
        mix += rendered * (0.6 if stem=="bass" else 0.5)
        metadata["parts"][stem] = sum(len(i.notes) for i in midi.instruments)
    drums, midi = render_drum_sketch(str(stems / "drums.wav"),duration)
    midi.write(str(folder / "drums.mid"))
    mix += drums*0.5
    peak = max(float(abs(mix).max()),1e-8)
    mix *= min(1.0,0.25/peak)
    sf.write(folder / "rebuilt_sketch.wav",mix,44100,subtype="PCM_16")
    (folder / "notes.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print("REBUILT SKETCH SAVED",folder / "rebuilt_sketch.wav",flush=True)


if __name__ == "__main__":
    reconstruct(sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),sys.argv[5])
