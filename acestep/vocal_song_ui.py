"""A compact audio-plus-text accompaniment workflow using the installed generator."""
import gradio as gr


def build_vocal_song(dit_handler,llm_handler):
    """Keep capture, backing description and original-voice mix in one place."""
    from acestep.vocal_song import generate_backing,mix_vocal
    with gr.Accordion("🎶 Build a song around my vocals",open=False):
        gr.Markdown("**1. Add your voice → 2. Describe the backing → 3. Generate.** 10–60 seconds. "
            "Experimental: timing may drift and generated vocals can remain.")
        vocal = gr.Audio(label="My voice or melody · upload MP3/WAV/M4A or record",type="filepath",
            sources=["upload","microphone"])
        prompt = gr.Textbox(label="What should play around your voice?",lines=3,
            placeholder="Acoustic guitar and piano, gentle verse, powerful chorus, space for my singing")
        with gr.Accordion("Adjust generation",open=False):
            influence = gr.Slider(0,1,value=0.7,step=0.05,label="Melody influence (experimental)")
            seed = gr.Number(value=42901,precision=0,label="Variation seed · change for another version")
        action = gr.Button("Generate backing from my recording",variant="primary")
        backing = gr.Audio(label="Generated backing · listen first",type="filepath")
        saved = gr.Audio(label="My saved original vocal",type="filepath")
        status = gr.Textbox(label="Status",interactive=False)

        def generate(path,description,strength,variation):
            """Bind the existing model handlers without installing or loading another model."""
            return generate_backing(path,description,strength,variation,dit_handler,llm_handler)

        action.click(generate,[vocal,prompt,influence,seed],[backing,saved,status],concurrency_id="music_gpu",concurrency_limit=1)
        with gr.Accordion("🎚 Mix my real voice with the backing",open=False):
            voice_level = gr.Slider(0,2,value=1,step=0.05,label="My voice level")
            backing_level = gr.Slider(0,2,value=0.5,step=0.05,label="Backing level")
            offset = gr.Slider(-5,5,value=0,step=0.01,label="Move my voice · negative earlier / positive later (seconds)")
            mix = gr.Button("Make a mix with my voice")
            output = gr.Audio(label="My voice + backing · new WAV copy",type="filepath")
            mix_status = gr.Textbox(label="Mix status",interactive=False)
            mix.click(mix_vocal,[saved,backing,voice_level,backing_level,offset],[output,mix_status])
