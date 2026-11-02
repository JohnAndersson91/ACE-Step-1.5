"""Optional local-browser dry microphone monitoring with explicit start and stop."""

import gradio as gr


def build_monitor() -> None:
    """Render a user-initiated monitor; it never records or uploads audio."""
    gr.HTML(
        value="""<div>
        <strong>Live microphone monitor (headphones only)</strong>
        <p>Browser and Bluetooth delay can make singing difficult. Use hardware direct
        monitoring or wired headphones when available. Turn speakers off to avoid feedback.</p>
        <button class="monitor-start">Start hearing my microphone</button>
        <button class="monitor-stop">Stop monitor</button>
        <label>Monitor volume <input class="monitor-volume" type="range"
        min="0" max="1" step="0.01" value="0.25"></label>
        <p class="monitor-status">Monitor off. Your saved take stays dry.</p></div>""",
        js_on_load="""
        let context = null, stream = null, gain = null;
        const status = element.querySelector('.monitor-status');
        const stop = async () => {
          if (stream) stream.getTracks().forEach(track => track.stop());
          if (context) await context.close();
          stream = context = gain = null;
          status.textContent = 'Monitor off.';
        };
        element.querySelector('.monitor-stop').onclick = stop;
        element.querySelector('.monitor-volume').oninput = event => {
          if (gain) gain.gain.value = Number(event.target.value);
        };
        element.querySelector('.monitor-start').onclick = async () => {
          await stop();
          try {
            stream = await navigator.mediaDevices.getUserMedia({audio: {
              echoCancellation: false, noiseSuppression: false, autoGainControl: false
            }});
            context = new AudioContext({latencyHint: 'interactive'});
            gain = context.createGain();
            gain.gain.value = Number(element.querySelector('.monitor-volume').value);
            context.createMediaStreamSource(stream).connect(gain).connect(context.destination);
            await context.resume();
            status.textContent = 'Live dry monitor on. Stop it if you hear delay or feedback.';
          } catch (error) {
            await stop();
            status.textContent = 'Cannot start monitor: ' + error.message;
          }
        };
        window.addEventListener('pagehide', () => { if(stream) stream.getTracks().forEach(t => t.stop()); });
        """,
    )
