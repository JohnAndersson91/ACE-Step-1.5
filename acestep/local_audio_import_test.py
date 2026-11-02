"""Focused validation and conversion checks for the local audio importer."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import gradio as gr

from acestep.local_audio_import import import_audio


class AudioImportTests(unittest.TestCase):
    """Exercise URL rejection and conversion without network or GPU access."""

    def test_rejects_non_youtube_links(self):
        """Local addresses and deceptive hosts must not reach the downloader."""
        for url in ["http://127.0.0.1/x", "https://youtube.com.evil.test/x"]:
            with self.subTest(url=url), patch("acestep.local_audio_import.YoutubeDL") as dl:
                with self.assertRaises(gr.Error):
                    import_audio(url, "WAV")
                dl.assert_not_called()

    def test_converts_and_returns_file(self):
        """The downloaded source is passed as a literal argument to FFmpeg."""
        with tempfile.TemporaryDirectory() as temp:
            with patch("acestep.local_audio_import.Path") as path_class, \
                 patch("acestep.local_audio_import.YoutubeDL") as dl, \
                 patch("acestep.local_audio_import.subprocess.run") as run, \
                 patch("acestep.local_audio_import.imageio_ffmpeg.get_ffmpeg_exe", return_value="ffmpeg"):
                path_class.return_value.resolve.return_value.parents = [Path(temp), Path(temp)]
                path_class.side_effect = lambda *args: Path(*args) if args != (__import__("acestep.local_audio_import", fromlist=["__file__"]).__file__,) else path_class.return_value
                downloader = MagicMock()
                downloader.extract_info.return_value = {"title": "Test"}
                downloader.prepare_filename.return_value = str(Path(temp) / "source.webm")
                dl.return_value.__enter__.return_value = downloader
                source, download, status = import_audio("https://youtu.be/example", "WAV")
                self.assertEqual(source, download)
                self.assertTrue(source.endswith(".wav"))
                self.assertIn("Test", status)
                self.assertIn("pcm_s16le", run.call_args.args[0])


if __name__ == "__main__":
    unittest.main()
