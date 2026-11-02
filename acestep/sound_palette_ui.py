"""Small instrument and vocal palette shared by arbitrary song prompts."""
import gradio as gr

from acestep.sound_palette import apply_palette, compile_palette
from acestep.sound_vocabulary import DELIVERIES, INSTRUMENTS, PRODUCTION, VOICES


def build_sound_palette(custom, saved_lyrics):
    """Preview structured sound choices, then explicitly apply them to real generation fields."""
    with gr.Accordion("🎛️ Instruments & vocal sound", open=False):
        with gr.Row():
            intro = gr.Dropdown(list(INSTRUMENTS), multiselect=True, label="Intro instruments", value=[])
            main = gr.Dropdown(list(INSTRUMENTS), multiselect=True, label="Main song instruments", value=[])
        with gr.Row():
            voice = gr.Dropdown(list(VOICES), value="Keep my request", label="Singer lineup")
            delivery = gr.Dropdown(list(DELIVERIES), value="Keep my request", label="Vocal delivery")
        production = gr.Dropdown(list(PRODUCTION), value="Keep my request", label="Recording sound")
        preview = gr.Button("Preview sound choices")
        description = gr.Textbox(label="What the generator will receive", lines=4, interactive=False)
        status = gr.Textbox(label="Sound choices status", interactive=False, lines=2)
        inputs = [custom["captions"], intro, main, voice, delivery, production]
        preview.click(compile_palette, inputs, description)
        gr.Button("Apply these sound choices").click(apply_palette,
            [*inputs, custom["lyrics"], saved_lyrics],
            [custom["captions"], custom["instrumental_checkbox"], custom["lyrics"], saved_lyrics, status])
