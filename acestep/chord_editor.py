"""Suggest triads from estimated notes; permit explicit replacement by corrected chords."""
import gradio as gr
import numpy as np
import pretty_midi


def suggest_chords(score: dict, duration: float) -> list:
    """Return rough two-second triad guesses, never certified original chords."""
    rows = []
    for start in np.arange(0,duration,2):
        end = min(start+2,duration)
        histogram = np.zeros(12)
        for part in ("bass","accompaniment"):
            for instrument in score[part].instruments:
                for note in instrument.notes:
                    overlap = max(0,min(end,note.end)-max(start,note.start))
                    histogram[note.pitch%12] += overlap
        candidates = []
        for root in range(12):
            for suffix,intervals in [("",(0,4,7)),("m",(0,3,7))]:
                score_value = sum(histogram[(root+i)%12] for i in intervals)
                candidates.append((score_value,root,suffix))
        value,root,suffix = max(candidates)
        name = pretty_midi.note_number_to_name(60+root)[:-1]+suffix if value else ""
        rows.append([float(start),float(end),name])
    return rows


def apply_chords(score: dict, rows: list, duration: float) -> dict:
    """Replace only accompaniment with explicit user-confirmed major/minor triads."""
    track = pretty_midi.Instrument(0)
    for index,row in enumerate(rows):
        try:
            start,end,name = row
            start,end = float(start),float(end)
            if not 0<=start<end<=duration:
                raise ValueError("Invalid chord times")
            name = str(name).strip()
            if not name:
                continue
            minor = name.endswith("m")
            root = pretty_midi.note_name_to_number((name[:-1] if minor else name)+"3")
            for interval in (0,3 if minor else 4,7):
                track.notes.append(pretty_midi.Note(55,root+interval,start,end))
        except (ValueError,TypeError,KeyError) as error:
            raise gr.Error(f"Chord row {index+1}: use valid times and a chord such as C, F# or Am.") from error
    midi = pretty_midi.PrettyMIDI()
    midi.instruments.append(track)
    return {**score,"accompaniment":midi}
