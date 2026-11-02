"""Explain supported music tasks without presenting reconstruction as solved."""
import gradio as gr


def build_workflow_guide() -> None:
    """Display concise routes to the actual generation and separation controls."""
    with gr.Accordion("Start here — choose what you want to make", open=True):
        gr.Markdown("""**Create an original song:** choose Custom, describe the music, add lyrics,
then Generate Music. Check Instrumental if you do not want vocals.

**Make an instrumental from an existing song:** import or upload Source Audio, then open
Vocal practice, stems and lyrics and press Make instrumental from source song.
RoFormer is a new test option; separation preserves timing but can leave artifacts.

**Rebuild notes as instruments (experimental):** import Source Audio and open
Arrange a song — controlled piano, guitar and rock tests. Start with 25 seconds. It estimates
bass/accompaniment notes and drum hits, renders new samples, and exports editable MIDI.
It does not faithfully reconstruct the original performance or instrument tones.

Use the correction workspace to inspect the estimated notes and piano roll. To try a
different transcription engine, open Other transcription tools / import their MIDI.
Those external engines are optional and have not been installed or benchmarked here.

**Reimagine the accompaniment (experimental):** choose Remix, provide the song as Source
Audio, check Instrumental and describe the new arrangement. Notes and timing may change.
This does not accurately reconstruct the original instruments.

**Create backing for my voice (experimental):** choose Remix and upload your dry vocal
take as Source Audio, check Instrumental and describe the backing. Matching your take
is not guaranteed; test a short section first.
""")
