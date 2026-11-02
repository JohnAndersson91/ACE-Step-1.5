"""Enforce instrument layouts for a shared score, rather than prompting for sounds."""
import copy

import numpy as np
import pretty_midi
import soundfile as sf

from acestep.reconstruction_render import render_notes
from acestep.arrangement_register import fit_register


LAYOUTS = {
    "Piano": {"melody":(0,0,0.8),"accompaniment":(0,0,0.4),"bass":(0,0,0.5)},
    "Acoustic guitar": {"melody":(25,0,0.8),"accompaniment":(25,0,0.4),"bass":(25,0,0.5)},
    "Rock ensemble (estimated)": {"melody":(29,0,0.6),"accompaniment":(29,0,0.4),
                                  "bass":(33,0,0.65),"drums":(0,128,0.6)},
}


def render_arrangement(score: dict, soundfont: str, duration: float, layout: str,
                       output, include_melody: bool = True) -> dict:
    """Render only the explicitly assigned samples; return an instrument audit."""
    mix = np.zeros((int(duration*44100),2),np.float32)
    combined = pretty_midi.PrettyMIDI()
    audit = {}
    for part,(program,bank,gain) in LAYOUTS[layout].items():
        if part == "melody" and not include_melody:
            continue
        midi = copy.deepcopy(score[part])
        shifted = 0
        if layout == "Acoustic guitar":
            midi,shifted = fit_register(midi,40,88)
        for instrument in midi.instruments:
            instrument.program = program
            instrument.is_drum = part == "drums"
        combined.instruments.extend(midi.instruments)
        mix += render_notes(midi,soundfont,duration,program,bank,part=="drums")*gain
        audit[part] = {"program":program,"bank":bank,
                       "octave_shifted_notes":shifted,
                       "notes":sum(len(i.notes) for i in midi.instruments)}
    peak = float(np.max(abs(mix)))
    if not np.isfinite(mix).all() or peak <= 1e-8:
        raise RuntimeError("Arrangement produced invalid or silent audio")
    mix *= min(1.0,0.126/peak)
    fade = min(len(mix),11025)
    mix[-fade:] *= np.linspace(1,0,fade)[:,None]
    sf.write(str(output)+".wav",mix,44100,subtype="PCM_16")
    combined.write(str(output)+".mid")
    return audit
