"""Expose review flags and a piano-roll plot without asserting note accuracy."""
import gradio as gr


def review_notes(rows: list, duration: float):
    """Flag brief notes, close repetitions and wide jumps for human review."""
    from acestep.score_editor import validate_notes
    import matplotlib.pyplot as plt

    score = validate_notes(rows,duration)
    flags = []
    figure,axis = plt.subplots(figsize=(11,4))
    colors = {"melody":"#4287f5","bass":"#d88925","accompaniment":"#3a9d68"}
    for part,midi in score.items():
        notes = sorted([n for i in midi.instruments for n in i.notes],key=lambda n:n.start)
        previous = None
        for note in notes:
            axis.broken_barh([(note.start,note.end-note.start)],(note.pitch-0.35,0.7),
                             facecolors=colors[part])
            reason = []
            if note.end-note.start<0.15:
                reason.append("Very short; may be legitimate or fragmented tracking")
            if note.pitch<40 or note.pitch>88:
                reason.append("Outside selected standard acoustic-guitar register")
            if previous and part in {"melody","bass"}:
                gap = note.start-previous.end
                if 0<=gap<0.06 and note.pitch==previous.pitch:
                    reason.append("Close repeated pitch; check whether this is one sustained note")
                if abs(note.pitch-previous.pitch)>=12 and gap<0.15:
                    reason.append("Large pitch jump; check for an octave-tracking error")
            if reason:
                import pretty_midi
                flags.append([part,round(note.start,3),pretty_midi.note_number_to_name(note.pitch),
                              "; ".join(reason)])
            previous = note
    axis.set(xlabel="Seconds inside excerpt",ylabel="MIDI pitch",xlim=(0,duration),
             title="Estimated notes only — blue melody, orange bass, green accompaniment")
    axis.grid(alpha=0.2)
    figure.tight_layout()
    return flags,figure,f"{len(flags)} notes flagged for review. These flags do not prove an error."


def build_score_review(notes, duration) -> None:
    """Add transparent diagnostics to the editable score workspace."""
    with gr.Accordion("Review questionable notes and see the piano roll",open=False):
        action = gr.Button("Inspect current notes")
        flags = gr.Dataframe(headers=["part","start","note","review reason"],interactive=False)
        plot = gr.Plot(label="Estimated score piano roll")
        status = gr.Textbox(label="Review summary",interactive=False)
        action.click(review_notes,[notes,duration],[flags,plot,status])
