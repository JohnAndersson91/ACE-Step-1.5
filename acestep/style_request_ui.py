"""Compact style-reference and vocal-direction controls connected to real generation inputs."""
import gradio as gr

from acestep.constants import VALID_LANGUAGES
from acestep.style_request import shape_style


def build_style_direction(custom,options):
    """Apply tempo/language metadata and preview the actual expanded music caption."""
    with gr.Accordion("🎸 Style, vocal power & rasp",open=False):
        gr.Markdown("Type your request in **Describe your song**, then apply these choices. "
            "Children of Bodom references are translated into guitar traits; other artist names aren't mapped yet.")
        tempo = gr.Number(value=None,label="Tempo (BPM) · optional",minimum=30,maximum=240)
        voice = gr.Radio(["Female","Male","Unspecified"],value="Female",label="Lead voice")
        power = gr.Radio(["Natural","Powerful","Epic"],value="Epic",label="Vocal power · requested")
        rasp = gr.Radio(["Clean throughout","A few transitions","Mostly harsh"],value="A few transitions",
            label="Clean → rasp → scream · requested")
        natural = gr.Checkbox(value=True,label="Ask for natural pitch and less synthetic vocal layering")
        names = {"en":"English","sv":"Swedish","fi":"Finnish","de":"German","ja":"Japanese",
            "es":"Spanish","fr":"French","it":"Italian","pt":"Portuguese","ko":"Korean","zh":"Chinese"}
        language = gr.Dropdown([(names.get(lang,lang),lang) for lang in VALID_LANGUAGES if lang!="unknown"],
            value="en",label="Vocal language")
        apply = gr.Button("Apply style & vocal direction")
        status = gr.Textbox(label="What was applied",interactive=False,lines=3)
        apply.click(shape_style,[custom["captions"],tempo,power,rasp,natural,language,voice],
            [custom["captions"],options["bpm"],options["bpm_auto"],options["vocal_language"],
             options["vocal_lang_auto"],status])
