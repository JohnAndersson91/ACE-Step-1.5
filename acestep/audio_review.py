"""Prepare conservative comparisons and measurable audio diagnostics."""
from pathlib import Path
from uuid import uuid4

import gradio as gr
import numpy as np
import soundfile as sf


ROOT = Path(__file__).resolve().parents[1]/"acestep_output/audio-review"


def read_clip(path, start=0, duration=None):
    """Read a bounded clip; reject missing, invalid or unusually large inputs."""
    if not path or not Path(path).is_file():
        raise gr.Error("Choose an audio file first.")
    info = sf.info(path)
    if info.duration>600 or info.channels>2 or info.samplerate>192000:
        raise gr.Error("Use mono/stereo audio of ten minutes or less at a standard sample rate.")
    if not 0<=start<info.duration or (duration is not None and not 1<=duration<=60):
        raise gr.Error("Choose a start inside the recording and a 1–60 second comparison.")
    first = round(start*info.samplerate)
    stop = min(info.frames,first+round(duration*info.samplerate)) if duration else info.frames
    audio,rate = sf.read(path,start=first,stop=stop,always_2d=True,dtype="float32")
    if not len(audio) or not np.isfinite(audio).all():
        raise gr.Error("The file contains empty or invalid audio.")
    return audio,rate


def audio_metrics(audio,rate):
    """Report sample levels without equating those levels to musical quality."""
    peak = float(abs(audio).max())
    rms = float(np.sqrt(np.mean(audio.astype(np.float64)**2)))
    windows = [float(np.sqrt(np.mean(audio[i:i+rate].astype(np.float64)**2)))
               for i in range(0,len(audio),rate)]
    drops = [i for i in range(1,len(windows)) if windows[i-1]>0.001 and
             windows[i]<windows[i-1]*0.25]
    return {"peak_dbfs":round(20*np.log10(max(peak,1e-12)),2),
            "rms_dbfs":round(20*np.log10(max(rms,1e-12)),2),
            "samples_at_or_above_full_scale":int(np.sum(abs(audio)>=0.9999)),
            "possible_level_drop_seconds":drops}


def compare_versions(first,second,start,duration):
    """Create RMS-matched previews by attenuation only, leaving source files intact."""
    from acestep.comparison_player import comparison_markup
    clips = [read_clip(path,start,duration) for path in (first,second)]
    levels = [float(np.sqrt(np.mean(audio.astype(np.float64)**2))) for audio,_ in clips]
    if min(levels)<1e-8:
        raise gr.Error("One version is silent; choose another excerpt.")
    target = min(*levels,0.025)
    folder = ROOT/uuid4().hex
    folder.mkdir(parents=True)
    paths,report = [],{}
    for label,(audio,rate),level in zip(("A","B"),clips,levels):
        report[label] = audio_metrics(audio,rate)
        scaled = audio*(target/level)
        peak = float(abs(scaled).max())
        if peak>0.8:
            # Apply the same further attenuation to both previews below.
            target *= 0.8/peak
    for label,(audio,rate),level in zip(("A","B"),clips,levels):
        path = folder/f"{label}.wav"
        sf.write(path,audio*(target/level),rate,subtype="PCM_24")
        paths.append(str(path))
    report["note"] = ("RMS matching is approximate perceived-loudness matching. Drops may be intentional. "
                      "These checks do not measure tuning, natural vocals, instrument accuracy or song similarity.")
    return comparison_markup(*paths,labels=("Version A — level matched","Version B — level matched")),report


def splice_section(original,replacement,start,end,replacement_mode,fade_ms):
    """Patch only the selected interval into a new floating-point WAV copy."""
    source,rate = read_clip(original)
    repair,repair_rate = read_clip(replacement)
    if repair_rate!=rate or repair.shape[1]!=source.shape[1]:
        raise gr.Error("Both files must have the same sample rate and channel count.")
    if not 0<=start<end<=len(source)/rate or not 0<=fade_ms<=500:
        raise gr.Error("Select a valid section and a transition of 0–500 milliseconds.")
    a,b = round(start*rate),round(end*rate)
    if replacement_mode=="Full song at the same timing":
        repair = repair[a:b]
    elif replacement_mode!="A clip starting at the repair":
        raise gr.Error("Choose whether the replacement is a full song or a short clip.")
    if len(repair)<b-a or b<=a:
        raise gr.Error("The replacement is too short for the selected section.")
    repair = repair[:b-a].copy()
    if abs(repair).max()>1:
        raise gr.Error("The replacement exceeds full scale. Reduce its level first.")
    count = min(round(fade_ms/1000*rate),(b-a)//2)
    if count:
        ramp = np.linspace(0,1,count,dtype=np.float32)[:,None]
        repair[:count] = source[a:a+count]*(1-ramp)+repair[:count]*ramp
        repair[-count:] = repair[-count:]*(1-ramp)+source[b-count:b]*ramp
    result = source.copy()
    result[a:b] = repair
    folder = ROOT/uuid4().hex
    folder.mkdir(parents=True)
    destination = folder/"song-with-section-repair.wav"
    sf.write(destination,result,rate,subtype="FLOAT")
    return str(destination),(f"New copy saved: repaired {start:.2f}–{end:.2f}s. "
        "Decoded samples outside that interval are unchanged. No time stretching, tuning, or automatic "
        "level matching was applied. Audition the transition before keeping this version.")
