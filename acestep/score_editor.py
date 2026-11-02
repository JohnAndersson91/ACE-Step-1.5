"""Convert estimated MIDI parts to validated, editable note rows."""
from pathlib import Path

import gradio as gr
import pretty_midi


PARTS = ("melody", "bass", "accompaniment")


def load_notes(folder: Path) -> list:
    """Return editable part/start/end/note/velocity rows from a saved score."""
    rows = []
    for part in PARTS:
        midi = pretty_midi.PrettyMIDI(str(folder / f"score-{part}.mid"))
        for instrument in midi.instruments:
            for note in instrument.notes:
                rows.append([part,round(note.start,3),round(note.end,3),
                             pretty_midi.note_number_to_name(note.pitch),note.velocity])
    return sorted(rows,key=lambda row:(row[0],row[1],row[3]))


def validate_notes(rows: list, duration: float) -> dict:
    """Validate all rows before saving or rendering any edits."""
    tracks = {part:pretty_midi.Instrument(0) for part in PARTS}
    for index,row in enumerate(rows):
        if not row or all(value in (None, "") for value in row):
            continue
        try:
            part,start,end,name,velocity = row
            start,end,velocity = float(start),float(end),int(velocity)
            pitch = pretty_midi.note_name_to_number(str(name).strip())
            if part not in tracks or not 0<=start<end<=duration or not 0<=pitch<=127 or not 1<=velocity<=127:
                raise ValueError("Invalid part, time, pitch or velocity")
        except (ValueError,TypeError,KeyError) as error:
            raise gr.Error(f"Note row {index+1}: use a valid part, times inside the clip, "
                           "a note such as C4, and velocity 1–127.") from error
        tracks[part].notes.append(pretty_midi.Note(velocity,pitch,start,end))
    result = {}
    for part,track in tracks.items():
        midi = pretty_midi.PrettyMIDI()
        midi.instruments.append(track)
        result[part] = midi
    return result
