"""Review reference-audio traits before applying them to a new song."""
import gradio as gr

from acestep.reference_analysis import analyze_reference, apply_reference, preview_reference


def build_reference_analysis(custom, options, handler):
    """Connect a short local reference analysis to caption and optional tempo/audio guidance."""
    with gr.Accordion("🎧 Use a reference section", open=False):
        gr.Markdown("Upload a song and choose the section whose sound you like. "
            "Audio guidance can influence the sound; it won't reproduce the arrangement exactly.")
        source = gr.Audio(label="Reference song · WAV, MP3 or recording", type="filepath")
        with gr.Row():
            start = gr.Number(label="Start at (seconds)", value=0, minimum=0, maximum=3600)
            seconds = gr.Number(label="Section length (seconds)", value=15, minimum=10, maximum=30)
        preview = gr.Button("Prepare selected section · no AI analysis")
        clip = gr.Audio(label="Selected reference section", type="filepath", interactive=False)
        description = gr.Textbox(label="What sound should it use? · optional", lines=3,
            placeholder="For example: harmonized electric-guitar intro, clear picked notes, heavy rhythm guitars")
        experimental = gr.Checkbox(value=False,
            label="Try experimental automatic description · can misidentify instruments")
        with gr.Group(visible=False) as analysis_group:
            gr.Markdown("The installed analyzer gave questionable descriptions in testing. "
                "Review every result. Local analysis can take several minutes.")
            analyze = gr.Button("Try local AI description")
            tempo = gr.Number(label="Estimated tempo · editable", minimum=30, maximum=240)
            use_tempo = gr.Checkbox(label="Use this tempo", value=False)
        experimental.change(lambda enabled: (gr.update(visible=enabled), False),
            experimental, [analysis_group, use_tempo])
        with gr.Row():
            use_audio = gr.Checkbox(label="Use this clip as sound guidance", value=True)
        status = gr.Textbox(label="Reference status", interactive=False, lines=3)

        def analyze_local(path, offset, duration):
            """Serialize local model use with song and lyric generation."""
            return analyze_reference(path, offset, duration, handler)

        analyze.click(analyze_local, [source, start, seconds], [clip, description, tempo, status],
            concurrency_id="music_gpu", concurrency_limit=1, api_name="analyze_reference")
        preview.click(preview_reference, [source, start, seconds], [clip, description, tempo, status],
            api_name="preview_reference")
        gr.Button("Use this reference in my song").click(apply_reference,
            [custom["captions"], description, tempo, use_tempo, clip, use_audio],
            [custom["captions"], options["bpm"], options["bpm_auto"],
             custom["reference_audio"], status], api_name="apply_reference")
