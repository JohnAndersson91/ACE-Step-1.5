"""Verify that audio guidance and original-vocal mixing use the intended inputs."""
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import gradio as gr
import numpy as np
import soundfile as sf

from acestep.vocal_song import generate_backing,mix_vocal,prepare_vocal


class VocalSongTests(unittest.TestCase):
    """Exercise real audio processing while mocking expensive model generation."""

    def test_decode_and_generation_use_recording(self):
        """A vocal take becomes source audio for instrumental Remix, with no lyric cloning."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root/"voice.wav"
            audio = 0.1*np.sin(2*np.pi*220*np.arange(480000)/48000)
            sf.write(source,audio,48000)
            before = source.read_bytes()
            with patch("acestep.vocal_song.ROOT",root/"out"), \
                 patch("acestep.inference.generate_music",return_value=SimpleNamespace(
                     success=True,audios=[{"path":str(source)}])) as generate:
                backing,vocal,status = generate_backing(str(source),"piano and guitar",0.7,42,None,None)
            params = generate.call_args.args[2]
            self.assertEqual(params.task_type,"cover")
            self.assertEqual(params.src_audio,vocal)
            self.assertTrue(params.instrumental)
            self.assertEqual(params.lyrics,"")
            self.assertAlmostEqual(params.duration,10)
            self.assertEqual(source.read_bytes(),before)
            self.assertTrue(Path(vocal).exists())

    def test_mix_keeps_voice_and_moves_it(self):
        """The original voice is mixed at the chosen offset, without source mutation."""
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            vocal,backing = root/"voice.wav",root/"backing.wav"
            sf.write(vocal,np.ones(24000)*0.1,24000,subtype="FLOAT")
            sf.write(backing,np.zeros((96000,2)),48000,subtype="FLOAT")
            before = vocal.read_bytes()
            with patch("acestep.vocal_song.ROOT",root/"out"):
                path,status = mix_vocal(str(vocal),str(backing),1,0,0.5)
            output,rate = sf.read(path,always_2d=True)
            self.assertEqual(rate,48000)
            self.assertEqual(output.shape,(96000,2))
            self.assertEqual(abs(output[:24000]).max(),0)
            # Resampling introduces small pass-band ripple; it is not pitch correction.
            self.assertAlmostEqual(output[30000,0],0.1,places=3)
            self.assertEqual(vocal.read_bytes(),before)

    def test_missing_or_invalid_inputs(self):
        """Unusable inputs fail before expensive generation."""
        with self.assertRaises(gr.Error):
            prepare_vocal(None)
        with self.assertRaises(gr.Error):
            generate_backing(None,"",0.7,42,None,None)
        with self.assertRaises(gr.Error):
            mix_vocal(None,None,1,1,6)


if __name__ == "__main__":
    unittest.main()
