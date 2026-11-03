"""Hold generated previews and require review for spectral alerts or scan failures."""
from functools import lru_cache
import json
from pathlib import Path

import soundfile as sf

from acestep.audio_artifact_scan import SCAN_VERSION, scan_audio

ROOT = Path(__file__).resolve().parents[1]/"acestep_output/artifact-review"


def listening_hold():
    """Read the user's playback pause; malformed preferences fail closed."""
    try:
        return bool(json.loads((ROOT/"listening-hold.json").read_text("utf-8")).get("hold", True))
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        return True


def set_listening_hold(enabled):
    """Persist the explicit preview pause without deleting or changing any audio."""
    ROOT.mkdir(parents=True, exist_ok=True)
    (ROOT/"listening-hold.json").write_text(json.dumps({"hold": bool(enabled)}), "utf-8")
    return ("Generated previews paused. Inspect files without listening." if enabled else
            "Preview pause released. Spectral alerts still hold suspect files. No file is certified safe.")


@lru_cache(maxsize=128)
def _cached_scan(path, modified, size, version):
    """Bound scan memory with overlapping 15-second chunks; never play or alter a file."""
    try:
        info = sf.info(path)
        if info.duration > 600 or info.channels > 2 or info.samplerate > 192000:
            raise ValueError("Use mono/stereo audio of ten minutes or less at a standard sample rate.")
        events, maxima = [], dict(max_upper_tone_fraction=0.0, max_high_frequency_fraction=0.0)
        rate = info.samplerate
        # Keep the STFT grid identical across chunks and whole-file analysis.
        block = (15*rate//1024)*1024
        overlap = max(1024, (rate//2//1024)*1024)
        offset = 0
        with sf.SoundFile(path) as source:
            while offset < info.frames:
                source.seek(offset)
                audio = source.read(block, dtype="float32", always_2d=True)
                if len(audio) < 4096:
                    if offset == 0:
                        raise ValueError("Audio is too short for this scan.")
                    break
                part = scan_audio(audio, rate)
                for event in part["events"]:
                    event = dict(event)
                    for key in ("start_seconds", "end_seconds"):
                        if key in event:
                            event[key] = round(event[key]+offset/rate, 3)
                    events.append(event)
                for key in maxima:
                    maxima[key] = max(maxima[key], part[key])
                if offset+len(audio) >= info.frames:
                    break
                offset += block-overlap
        report = dict(scan_version=version, file=path, review_required=bool(events), events=events,
            duration_seconds=info.duration, **maxima, limitations=part["limitations"],
            summary="Possible artifacts: review required." if events else
                    "No configured alerts detected. This is not a hearing-safety assessment.")
    except (OSError, ValueError, RuntimeError) as error:
        report = dict(scan_version=version, file=path, review_required=True, events=[],
                      error=str(error), summary="Scan unavailable; playback held.")
    return report


def scan_file(path):
    """Scan/cache by file identity and save a review sidecar when the location is writable."""
    try:
        source = Path(path).resolve()
        stat = source.stat()
        report = _cached_scan(str(source), stat.st_mtime_ns, stat.st_size, SCAN_VERSION)
    except (OSError, TypeError, ValueError) as error:
        return dict(review_required=True, events=[], error=str(error), summary="Cannot scan; playback held.")
    try:
        source.with_suffix(source.suffix+".soundcheck.json").write_text(json.dumps(report, indent=2), "utf-8")
    except OSError:
        pass
    return report


def checked_playback_path(path):
    """Return no playable source when paused, flagged or unchecked."""
    if not path:
        return None, None
    report = scan_file(path)
    if listening_hold():
        return None, "Previews paused — inspect the sound check below"
    if report["review_required"]:
        return None, "Playback held — sound check needs review"
    return path, None
