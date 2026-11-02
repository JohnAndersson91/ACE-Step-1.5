"""Download public YouTube audio and convert it for the local music interface."""

from pathlib import Path
import subprocess
from urllib.parse import urlsplit
from uuid import uuid4

import gradio as gr
import imageio_ffmpeg
from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError


def import_audio(url: str, audio_format: str) -> tuple[str, str, str]:
    """Return source audio, download file, and status for a public YouTube URL."""
    parsed = urlsplit(url.strip())
    if parsed.scheme != "https" or parsed.hostname not in {
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    } or parsed.username or parsed.password:
        raise gr.Error("Enter an HTTPS YouTube video link.")
    if audio_format not in {"WAV", "MP3"}:
        raise gr.Error("Choose WAV or MP3.")
    folder = Path(__file__).resolve().parents[1] / "acestep_output" / "imports" / uuid4().hex
    folder.mkdir(parents=True)
    options = {
        "format": "bestaudio/best", "noplaylist": True,
        "outtmpl": str(folder / "source.%(ext)s"),
        "socket_timeout": 30, "retries": 2, "quiet": True,
        "match_filter": lambda info, **kw: (
            "Live streams are not supported." if info.get("is_live") else None
        ),
    }
    try:
        with YoutubeDL(options) as downloader:
            info = downloader.extract_info(url.strip(), download=True)
            source = Path(downloader.prepare_filename(info))
        destination = folder / ("imported." + audio_format.lower())
        codec = ["-c:a", "pcm_s16le"] if audio_format == "WAV" else [
            "-c:a", "libmp3lame", "-b:a", "192k",
        ]
        subprocess.run(
            [imageio_ffmpeg.get_ffmpeg_exe(), "-nostdin", "-y", "-i", str(source),
             "-vn", *codec, str(destination)],
            check=True, capture_output=True, timeout=600,
        )
    except (DownloadError, OSError, subprocess.SubprocessError) as error:
        raise gr.Error(
            "Import failed. The video may be restricted or unavailable. "
            "You can upload a local audio file instead. Details: " + str(error)[-500:]
        ) from error
    path = str(destination)
    return path, path, f"Imported: {info.get('title', 'YouTube audio')}. Choose Remix to edit it."


def build_import_controls(source_audio: gr.Audio) -> None:
    """Add link import and download controls that populate existing source audio."""
    with gr.Accordion("Import audio from YouTube", open=False):
        gr.Markdown("Import public audio you own or have permission to download and use.")
        url = gr.Textbox(label="YouTube video link", placeholder="https://www.youtube.com/watch?v=...")
        audio_format = gr.Radio(["WAV", "MP3"], value="WAV", label="Import format")
        button = gr.Button("Import audio")
        download = gr.File(label="Download imported audio", interactive=False)
        status = gr.Textbox(label="Import status", interactive=False)
        button.click(import_audio, [url, audio_format], [source_audio, download, status])
