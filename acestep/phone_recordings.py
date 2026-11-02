"""Password-protected LAN upload page for phone recordings; no model is loaded."""

import secrets
import socket
import os

import gradio as gr

from acestep.practice_session import build_session


def build_phone_page() -> gr.Blocks:
    """Create a mobile upload page that writes takes into the PC recording library."""
    with gr.Blocks(title="My singing studio") as page:
        build_session()
        gr.Markdown("In the PC music program: open Record my vocals, press Refresh saved takes, "
                    "and load the new take. Bluetooth headphones are unsuitable for precise live monitoring.")
    return page


def main() -> None:
    """Start a LAN-only upload service with a fresh session password."""
    password = secrets.token_hex(3)
    secure_share = os.environ.get("MUSIC_SECURE_PHONE", "false").lower() == "true"
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(
        socket.gethostname(), None, socket.AF_INET) if not item[4][0].startswith("127.")})
    print("\nPHONE UPLOAD - connect only on trusted home Wi-Fi", flush=True)
    for address in addresses:
        print(f"Open on phone: http://{address}:7861", flush=True)
    print(f"Username: singer\nPassword: {password}\nClose this window to stop phone uploads.\n",
          flush=True)
    build_phone_page().launch(server_name="0.0.0.0", server_port=7861,
                             auth=("singer", password), share=secure_share, max_file_size="100mb")


if __name__ == "__main__":
    main()
