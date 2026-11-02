"""Generate experimental accompaniment and mix it with an untouched vocal take."""
import json
from pathlib import Path
import subprocess
from uuid import uuid4

import gradio as gr
import imageio_ffmpeg
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
from math import gcd


ROOT = Path(__file__).resolve().parents[1]/"acestep_output/vocal-songs"


def prepare_vocal(path):
    """Decode at most 61 seconds locally, rejecting takes over the 60-second test limit."""
    if not path or not Path(path).is_file():
        raise gr.Error("Record a melody or upload your vocal audio first.")
    if Path(path).stat().st_size>100_000_000:
        raise gr.Error("Use a recording under 100 MB and 10–60 seconds long.")
    folder = ROOT/uuid4().hex
    folder.mkdir(parents=True)
    destination = folder/"my-original-vocal.wav"
    try:
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(),"-nostdin","-y","-i",str(path),
            "-t","61","-vn","-ar","48000","-ac","1","-c:a","pcm_s24le",str(destination)],
            check=True,capture_output=True,timeout=90)
    except (OSError,subprocess.SubprocessError) as error:
        raise gr.Error("Could not read this recording. Try WAV, MP3 or M4A.") from error
    audio,rate = sf.read(destination)
    duration = len(audio)/rate
    if not 10<=duration<=60 or not np.isfinite(audio).all() or abs(audio).max()<1e-6:
        raise gr.Error("Use a non-silent vocal or melody recording lasting 10–60 seconds.")
    return destination,duration


def generate_backing(path,description,strength,seed,dit_handler,llm_handler):
    """Use installed Remix generation as guidance, keeping the real vocal separate."""
    from acestep.inference import GenerationParams,GenerationConfig,generate_music
    description = str(description or "").strip()
    if not description or len(description)>1800 or not 0<=strength<=1:
        raise gr.Error("Describe your backing in a few sentences and choose a valid melody influence.")
    try:
        seed = int(seed)
        if not 0<=seed<=2147483647:
            raise ValueError("Invalid seed")
    except (ValueError,TypeError,OverflowError) as error:
        raise gr.Error("Use a whole-number variation seed between 0 and 2147483647.") from error
    vocal,duration = prepare_vocal(path)
    caption = "Instrumental accompaniment, space for a live singer. "+description
    params = GenerationParams(task_type="cover",src_audio=str(vocal),caption=caption,
        lyrics="",instrumental=True,duration=duration,audio_cover_strength=float(strength),
        seed=seed,thinking=False,use_cot_metas=False,use_cot_caption=False,use_cot_language=False)
    result = generate_music(dit_handler,llm_handler,params,
        GenerationConfig(batch_size=1,audio_format="wav",use_random_seed=False),save_dir=str(vocal.parent))
    if not result.success or not result.audios:
        raise gr.Error("Backing generation did not finish. Your saved vocal is kept; try again.")
    backing = result.audios[0]["path"]
    (vocal.parent/"recipe.json").write_text(json.dumps(dict(description=description,strength=strength,
        seed=seed,duration=duration,method="experimental Remix accompaniment"),indent=2),encoding="utf-8")
    return backing,str(vocal),("Backing ready. Your real vocal is saved separately. Listen first, then try the mix below. "
        "Remix may change timing or leave generated vocals; it does not guarantee accompaniment that follows your take.")


def mix_vocal(vocal_path,backing_path,vocal_level,backing_level,offset):
    """Mix the original performance with adjustable alignment, never replacing source files."""
    if not 0<=vocal_level<=2 or not 0<=backing_level<=2 or not -5<=offset<=5:
        raise gr.Error("Choose valid voice/backing levels and an offset between -5 and 5 seconds.")
    clips = []
    for path in (vocal_path,backing_path):
        if not path or not Path(path).is_file():
            raise gr.Error("Add your vocal and generate or upload a backing first.")
        info = sf.info(path)
        if info.duration>65 or info.channels>2 or info.samplerate>192000:
            raise gr.Error("Use mono/stereo clips of 65 seconds or less.")
        audio,rate = sf.read(path,always_2d=True,dtype="float32")
        if not len(audio) or not np.isfinite(audio).all():
            raise gr.Error("The audio is empty or contains invalid samples.")
        if rate!=48000:
            divisor = gcd(rate,48000)
            audio = resample_poly(audio,48000//divisor,rate//divisor,axis=0)
        clips.append(np.repeat(audio,2,axis=1) if audio.shape[1]==1 else audio)
    vocal,backing = clips
    shift = round(abs(offset)*48000)
    if offset>=0:
        vocal = np.pad(vocal,((shift,0),(0,0)))
    else:
        vocal = vocal[shift:]
    frames = max(len(vocal),len(backing))
    mix = np.zeros((frames,2),np.float32)
    mix[:len(vocal)] += vocal*vocal_level
    mix[:len(backing)] += backing*backing_level
    peak = float(abs(mix).max())
    if peak<1e-8:
        raise gr.Error("The mix is silent. Raise at least one level.")
    mix *= min(1,0.8/peak)
    folder = ROOT/uuid4().hex
    folder.mkdir(parents=True)
    destination = folder/"my-voice-and-backing.wav"
    sf.write(destination,mix,48000,subtype="PCM_24")
    return str(destination),"New mix saved. Your performance is retained; alignment is manual and no pitch correction was applied."
