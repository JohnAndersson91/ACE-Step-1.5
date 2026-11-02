"""Connect generation results to comfortable comparisons and optional section repairs."""
import gradio as gr
from pathlib import Path

from acestep.audio_review import compare_versions,splice_section
from acestep.comparison_player import build_comparison_player


def build_audio_review(first,second):
    """Use existing result players as inputs without generating or spending anything."""
    with gr.Accordion("Compare versions and keep the good sections",open=False):
        gr.Markdown("Generate two versions using Batch Size 2, then compare Sample 1 and Sample 2 here. "
            "Only playback copies are level matched. Source audio is untouched. "
            "For a weak section, use Send To Repaint above, generate a repair, then patch it into a new copy below.")
        start = gr.Number(value=0,label="Comparison start (seconds)")
        duration = gr.Slider(1,60,value=25,step=1,label="Comparison duration (seconds)")
        action = gr.Button("Compare generated Sample 1 and Sample 2")
        player = build_comparison_player()
        report = gr.JSON(label="Technical checks — not a musical-quality rating")
        action.click(compare_versions,[first,second,start,duration],[player,report])
        with gr.Accordion("Compare other saved audio files",open=False):
            demos = Path(__file__).resolve().parents[1]/"acestep_output/review-auditions"
            gr.Markdown("Any preloaded files below are original-song tests, not remakes of your reference song.")
            upload_a = gr.Audio(value=str(demos/"A.wav") if (demos/"A.wav").exists() else None,
                label="Version A file",type="filepath")
            upload_b = gr.Audio(value=str(demos/"B.wav") if (demos/"B.wav").exists() else None,
                label="Version B file",type="filepath")
            compare = gr.Button("Compare these saved files")
            compare.click(compare_versions,[upload_a,upload_b,start,duration],[player,report])
        with gr.Accordion("Insert a repaired section into a new copy",open=False):
            original = gr.Audio(label="Original song to preserve",type="filepath")
            replacement = gr.Audio(label="Replacement audio from Repaint or your editor",type="filepath")
            mode = gr.Radio(["Full song at the same timing","A clip starting at the repair"],
                value="Full song at the same timing",label="Replacement file contains")
            begin = gr.Number(value=6,label="Repair starts in original (seconds)")
            end = gr.Number(value=17,label="Repair ends in original (seconds)")
            fade = gr.Slider(0,500,value=50,step=10,label="Transition inside repair boundaries (milliseconds)")
            patch = gr.Button("Save a new song copy with this repair")
            audio = gr.Audio(label="Song copy with repaired section",type="filepath")
            status = gr.Textbox(label="Repair status",interactive=False)
            patch.click(splice_section,[original,replacement,begin,end,mode,fade],[audio,status])
