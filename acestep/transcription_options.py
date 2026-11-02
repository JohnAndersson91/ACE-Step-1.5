"""Document researched alternatives and offer an external-MIDI integration boundary."""
import gradio as gr


def render_imported(*args):
    """Load optional reconstruction dependencies only when requested."""
    from acestep.external_midi import render_external_midi
    return render_external_midi(*args)


def build_transcription_options() -> None:
    """Expose optional tool choices without claiming their engines are installed."""
    with gr.Accordion("Other transcription tools / import their MIDI",open=False):
        gr.Markdown("""**Local alternative: [NeuralNote v2](https://github.com/DamRsn/NeuralNote)**
uses MuScriptor to transcribe multiple instruments. Its code is Apache-2.0, but model
weights are CC BY-NC 4.0 (non-commercial). It is not installed or tested here.

**[MuScriptor](https://github.com/muscriptor/muscriptor)** offers official local and hosted
transcription. Code is MIT; weights are non-commercial and official setup requires
Hugging Face login/license acceptance. Nothing is uploaded or enabled automatically.

**[MT3](https://github.com/magenta/mt3)** is a research multi-instrument transcription
option using T5X. It is not installed or benchmarked on this PC.

**[Klangio](https://klang.io/)** offers instrument-specific transcription/editing and
advertises a free 20-second test. Further use can require payment. No subscription
or upload has been started.

Export a MIDI file from a tool of your choice, then import it below. Keeping MIDI
instrument assignments preserves that tool's predicted instrument labels—not proof
that they match the original recording. Piano/guitar choices enforce new sounds.
""")
        source = gr.File(label="MIDI transcription from another tool",file_types=[".mid",".midi"],type="filepath")
        layout = gr.Radio(["Keep MIDI instrument assignments","Piano","Acoustic guitar"],
                          value="Keep MIDI instrument assignments",label="Render instruments")
        start = gr.Number(value=0,label="MIDI excerpt start (seconds)")
        duration = gr.Slider(5,60,value=25,step=1,label="MIDI excerpt duration (seconds)")
        exclude = gr.Checkbox(value=True,label="Exclude tracks labeled vocals / choir")
        button = gr.Button("Render imported MIDI")
        audio = gr.Audio(label="Arrangement from imported transcription")
        midi = gr.File(label="Rendered arrangement MIDI")
        report = gr.Dataframe(headers=["track","input instrument","output instrument","notes","octave shifts"],interactive=False)
        status = gr.Textbox(label="Import status",interactive=False)
        button.click(render_imported,[source,layout,start,duration,exclude],[audio,midi,report,status])
