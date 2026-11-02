"""Build controlled arrangement variants from one explicitly estimated musical score."""
import json
from pathlib import Path
import subprocess
import sys

import soundfile as sf


def arrange(source: str, output: str, start: float, duration: float,
            include_melody: bool = True) -> None:
    """Transcribe a short passage once, then render all requested instrument layouts."""
    import torch
    from acestep.arranger_score import build_score
    from acestep.arranger_render import render_arrangement, LAYOUTS

    destination = Path(output)
    destination.mkdir(parents=True,exist_ok=True)
    info = sf.info(source)
    audio,rate = sf.read(source,start=int(start*info.samplerate),
                        stop=int((start+duration)*info.samplerate),always_2d=True)
    duration = len(audio)/rate
    clip = destination / "source.wav"
    sf.write(clip,audio,rate)
    subprocess.run([sys.executable,"-m","demucs","-n","htdemucs","--segment","5",
                    "--shifts","1","-d","cuda" if torch.cuda.is_available() else "cpu",
                    "-o",str(destination / "analysis"),str(clip)],check=True)
    score = build_score(destination / "analysis/htdemucs/source",destination)
    bank = Path(__file__).resolve().parents[1] / "checkpoints/reconstruction/GeneralUser-GS.sf2"
    audit = {"start":start,"duration":duration,"score_is_estimated":True,
             "original_instruments_automatically_identified":False,"layouts":{}}
    for layout in LAYOUTS:
        audit["layouts"][layout] = render_arrangement(score,str(bank),duration,layout,
            destination / layout,include_melody)
        print("SAVED",layout,flush=True)
    (destination / "Instrument and score audit.json").write_text(json.dumps(audit,indent=2),encoding="utf-8")


if __name__ == "__main__":
    arrange(sys.argv[1],sys.argv[2],float(sys.argv[3]),float(sys.argv[4]),
            len(sys.argv)<6 or sys.argv[5]=="true")
