"""Render externally transcribed MIDI with explicit, auditable instrument choices."""
import copy
import json
from pathlib import Path
from uuid import uuid4

import gradio as gr
import numpy as np
import pretty_midi
import soundfile as sf

from acestep.arrangement_register import fit_register
from acestep.reconstruction_render import render_notes


def render_external_midi(path: str, layout: str, start: float, duration: float,
                         exclude_voices: bool):
    """Use supplied MIDI notes rather than estimating notes again from audio."""
    if not path or not Path(path).is_file():
        raise gr.Error("Upload a MIDI transcription first.")
    if Path(path).stat().st_size>8_000_000 or not 0<=start or not 5<=duration<=60:
        raise gr.Error("Use a MIDI file under 8 MB and a 5–60 second excerpt.")
    if layout not in {"Keep MIDI instrument assignments","Piano","Acoustic guitar"}:
        raise gr.Error("Choose an instrument layout.")
    try:
        original = pretty_midi.PrettyMIDI(path)
    except (ValueError,OSError,EOFError,KeyError) as error:
        raise gr.Error("Could not read this MIDI file.") from error
    tracks = []
    report = []
    for instrument in original.instruments:
        voice = (52<=instrument.program<=54 or any(word in instrument.name.lower()
                  for word in ("vocal","singing","voice","choir"))) and not instrument.is_drum
        if (exclude_voices and voice) or (layout!="Keep MIDI instrument assignments" and instrument.is_drum):
            continue
        track = copy.deepcopy(instrument)
        track.notes = []
        for note in instrument.notes:
            if note.end>start and note.start<start+duration:
                item = copy.deepcopy(note)
                item.start = max(0,note.start-start)
                item.end = min(duration,note.end-start)
                track.notes.append(item)
        if not track.notes:
            continue
        # Carry the last pre-excerpt controller state into the excerpt at time zero.
        controls = {}
        for event in track.control_changes:
            if event.time<=start:
                controls[event.number] = event
        track.control_changes = [pretty_midi.ControlChange(n,e.value,0) for n,e in controls.items()]+[
            pretty_midi.ControlChange(e.number,e.value,e.time-start)
            for e in instrument.control_changes if start<e.time<start+duration]
        bends = [e for e in instrument.pitch_bends if e.time<=start]
        track.pitch_bends = ([pretty_midi.PitchBend(bends[-1].pitch,0)] if bends else [])+[
            pretty_midi.PitchBend(e.pitch,e.time-start) for e in instrument.pitch_bends if start<e.time<start+duration]
        midi = pretty_midi.PrettyMIDI()
        midi.instruments.append(track)
        shifted = 0
        if layout != "Keep MIDI instrument assignments":
            track.program = 0 if layout=="Piano" else 25
            track.pitch_bends = []
            midi,shifted = fit_register(midi,*( (21,108) if layout=="Piano" else (40,88) ))
            track = midi.instruments[0]
        report.append([instrument.name or "Unnamed",pretty_midi.program_to_instrument_name(instrument.program),
                       "Drum kit" if track.is_drum else pretty_midi.program_to_instrument_name(track.program),
                       len(track.notes),shifted])
        tracks.append(midi)
    if not tracks or len(tracks)>32 or sum(len(i.notes) for m in tracks for i in m.instruments)>20000:
        raise gr.Error("No usable notes, or too many tracks/notes in this excerpt.")
    root = Path(__file__).resolve().parents[1]
    bank = root/"checkpoints/reconstruction/GeneralUser-GS.sf2"
    if not bank.exists():
        raise gr.Error("Run Setup Reconstruction.bat to install the instrument bank.")
    mix = np.zeros((int(duration*44100),2),np.float32)
    combined = pretty_midi.PrettyMIDI()
    for midi in tracks:
        track = midi.instruments[0]
        mix += render_notes(midi,str(bank),duration,track.program,128 if track.is_drum else 0,track.is_drum)
        combined.instruments.append(track)
    peak = float(abs(mix).max())
    if not np.isfinite(mix).all() or peak<1e-8:
        raise gr.Error("The supplied MIDI did not produce valid audio.")
    mix *= min(1.0,0.126/peak)
    folder = root/"acestep_output/imported-midi"/uuid4().hex
    folder.mkdir(parents=True)
    wav,midi = folder/"arrangement.wav",folder/"arrangement.mid"
    sf.write(wav,mix,44100,subtype="PCM_16")
    combined.write(str(midi))
    (folder/"instrument-audit.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    return str(wav),str(midi),report,"Rendered supplied MIDI. This does not verify its notes or instrument identification."
