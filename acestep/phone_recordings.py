"""Password-protected LAN upload page for phone recordings; no model is loaded."""

import secrets
import socket

import gradio as gr

from acestep.vocal_recording import save_take


def build_phone_page() -> gr.Blocks:
    """Create a mobile upload page that writes takes into the PC recording library."""
    with gr.Blocks(title="Send vocals to my PC") as page:
        gr.Markdown("# Send vocals to my PC\n"
                    "On your Pixel, record in Recorder, export the audio to Files, "
                    "then select it here. Keep this phone and PC on the same trusted Wi-Fi. "
                    "This page uses your local network; it is not an internet sharing service.")
        audio = gr.File(label="Choose a vocal recording", file_types=["audio"], type="filepath")
        send = gr.Button("Send recording to PC", variant="primary")
        saved = gr.File(label="Saved WAV", interactive=False)
        status = gr.Textbox(label="Transfer status", interactive=False)
        send.click(save_take, audio, [saved, status])
        gr.Markdown("In the PC music program: open Record my vocals, press Refresh saved takes, "
                    "and load the new take. Bluetooth headphones are unsuitable for precise live monitoring.")
    return page


def main() -> None:
    """Start a LAN-only upload service with a fresh session password."""
    password = secrets.token_urlsafe(9)
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(
        socket.gethostname(), None, socket.AF_INET) if not item[4][0].startswith("127.")})
    print("\nPHONE UPLOAD - connect only on trusted home Wi-Fi", flush=True)
    for address in addresses:
        print(f"Open on phone: http://{address}:7861", flush=True)
    print(f"Username: singer\nPassword: {password}\nClose this window to stop phone uploads.\n",
          flush=True)
    build_phone_page().launch(server_name="0.0.0.0", server_port=7861,
                             auth=("singer", password), share=False, max_file_size="100mb")


if __name__ == "__main__":
    main()
