"""User-triggered A/B controls for two Gradio audio players at a shared playhead."""
import gradio as gr
import base64
import html
from pathlib import Path


def comparison_markup(original: str | None = None, piano: str | None = None,
                      labels: tuple[str,str] = ("Original excerpt — level matched",
                                               "Piano from current notes — level matched")) -> str:
    """Keep both native audio elements inside the same component for reliable control."""
    from acestep.audio_artifact_gate import checked_playback_path
    original, notice_a = checked_playback_path(original)
    piano, notice_b = checked_playback_path(piano)
    notice = notice_a or notice_b
    disabled = " disabled" if notice else ""
    def source(path):
        return "data:audio/wav;base64,"+base64.b64encode(Path(path).read_bytes()).decode() if path else ""
    return f'''<div><p>{html.escape(labels[0])}</p>
    <audio data-original controls preload="metadata" src="{source(original)}"></audio>
    <p>{html.escape(labels[1])}</p>
    <audio data-piano controls preload="metadata" src="{source(piano)}"></audio>
    <p><button data-side="original"{disabled}>Play first version</button>
    <button data-side="piano"{disabled}>Switch to second at same position</button>
    <button data-stop>Stop both</button></p>
    <label>Listening volume <input data-volume type="range" min="0" max="1"
    step="0.01" value="0.2"></label><p data-status>{html.escape(notice or 'Playback stopped.')}</p></div>'''


def build_comparison_player(labels=None, visible=True):
    """Switch at the current playhead with an independent, low default listening volume."""
    markup = comparison_markup(labels=labels) if labels is not None else comparison_markup()
    return gr.HTML(value=markup, visible=visible,
    js_on_load="""
    let current = null, position = 0;
    const media = side => element.querySelector('audio[data-'+side+']');
    const status = element.querySelector('[data-status]');
    ['original','piano'].forEach(side=>{const audio=media(side);if(audio)audio.volume=0.2;});
    const stop = () => {
      if(current) position = current.currentTime;
      ['original','piano'].forEach(side => { const audio=media(side); if(audio) audio.pause(); });
    };
    element.querySelectorAll('[data-side]').forEach(button => button.onclick = async () => {
      stop(); const audio = media(button.dataset.side);
      if(!audio) { status.textContent='Player is still loading. Try its Play control first.'; return; }
      current=audio;
      audio.volume=Number(element.querySelector('[data-volume]').value);
      try { audio.currentTime=position; await audio.play();
        status.textContent='Playing '+(button.dataset.side==='original'?'first':'second')+' version at '+position.toFixed(1)+' seconds.';
      } catch(error) { status.textContent='Playback needs a click on the audio player: '+error.message; }
    });
    element.querySelector('[data-stop]').onclick=()=>{stop();status.textContent='Stopped.';};
    element.querySelector('[data-volume]').oninput=event=>{
      ['original','piano'].forEach(side=>{const audio=media(side);if(audio)audio.volume=Number(event.target.value);});
    };
    """)
