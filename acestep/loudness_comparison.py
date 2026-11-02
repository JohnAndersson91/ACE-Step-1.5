"""Measure local playback copies with the existing FFmpeg EBU R128 analyzer."""
import json
import math
from pathlib import Path
import subprocess
import tempfile

import soundfile as sf

from acestep.ffmpeg_path import ffmpeg_executable


def measure_loudness(audio, rate):
    """Return integrated LUFS and true peak, or None when measurement is unavailable."""
    try:
        with tempfile.TemporaryDirectory(prefix="music-loudness-") as folder:
            path = Path(folder) / "excerpt.wav"
            sf.write(path, audio, rate, subtype="FLOAT")
            result = subprocess.run(
                [ffmpeg_executable(), "-hide_banner", "-nostdin", "-i", str(path),
                 "-af", "loudnorm=I=-32:TP=-6:LRA=11:print_format=json",
                 "-f", "null", "-"],
                capture_output=True, text=True, timeout=45, check=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        start = result.stderr.rfind("{")
        end = result.stderr.rfind("}")
        values = json.loads(result.stderr[start:end + 1])
        loudness, peak = float(values["input_i"]), float(values["input_tp"])
        if math.isfinite(loudness) and math.isfinite(peak):
            return {"integrated_lufs": loudness, "true_peak_dbtp": peak}
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, RuntimeError):
        return None
    return None


def comparison_gains(measurements):
    """Match to the quieter excerpt with at least 6 dB of measured true-peak headroom."""
    target = min(-32.0, *(item["integrated_lufs"] for item in measurements))
    gains_db = [target - item["integrated_lufs"] for item in measurements]
    extra = min(0.0, *(-6.0 - item["true_peak_dbtp"] - gain
                       for item, gain in zip(measurements, gains_db)))
    return [10 ** ((gain + extra) / 20) for gain in gains_db]
