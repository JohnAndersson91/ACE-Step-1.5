"""User-triggered A/B controls for two Gradio audio players at a shared playhead."""
import gradio as gr


def build_comparison_player() -> None:
    """Switch at the current playhead with an independent, low default listening volume."""
    gr.HTML(value="""<div><button data-side="original">Hear original</button>
    <button data-side="piano">Hear piano at same position</button>
    <button data-stop>Stop both</button>
    <label>Listening volume <input data-volume type="range" min="0" max="1"
    step="0.01" value="0.2"></label><p data-status>Playback stopped.</p></div>""",
    js_on_load="""
    let current = null, position = 0;
    const media = side => [...document.querySelectorAll('#correction-'+side+' audio')]
      .find(audio => audio.src);
    const status = element.querySelector('[data-status]');
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
        status.textContent='Playing '+button.dataset.side+' at '+position.toFixed(1)+' seconds.';
      } catch(error) { status.textContent='Playback needs a click on the audio player: '+error.message; }
    });
    element.querySelector('[data-stop]').onclick=()=>{stop();status.textContent='Stopped.';};
    element.querySelector('[data-volume]').oninput=event=>{
      ['original','piano'].forEach(side=>{const audio=media(side);if(audio)audio.volume=Number(event.target.value);});
    };
    """)
