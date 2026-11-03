"""Conservative spectral anomaly screening, never a hearing-safety certification."""
import numpy as np
from scipy.ndimage import median_filter
from scipy.signal import stft

SCAN_VERSION = 2


def _intervals(mask, times, hop_seconds, minimum_seconds):
    """Merge adjacent flagged frames into bounded inspection intervals."""
    padded = np.r_[False, mask, False].astype(np.int8)
    starts, stops = np.flatnonzero(np.diff(padded) == 1), np.flatnonzero(np.diff(padded) == -1)
    return [(int(a), int(b)) for a, b in zip(starts, stops)
            if (b-a)*hop_seconds >= minimum_seconds]


def spectral_features(audio, rate):
    """Measure each channel separately so out-of-phase tones cannot cancel."""
    wave = np.asarray(audio, dtype=np.float64)
    if wave.ndim == 1:
        wave = wave[:, None]
    if wave.ndim != 2 or not 1 <= wave.shape[1] <= 2 or rate < 8000:
        raise ValueError("Use standard mono or stereo audio at 8 kHz or above.")
    if not np.isfinite(wave).all() or len(wave) < 4096:
        raise ValueError("Audio contains invalid samples or is shorter than the scan window.")
    peak = float(np.max(abs(wave)))
    normalized = wave / max(peak, 1e-12)
    powers = []
    for channel in normalized.T:
        frequencies, times, spectrum = stft(channel, fs=rate, nperseg=4096,
            noverlap=3072, boundary=None, padded=False)
        powers.append(abs(spectrum)**2)
    power = np.maximum.reduce(powers)
    total = np.maximum(power.sum(axis=0), 1e-20)
    floor = np.maximum(median_filter(power, size=(49, 1)), power.max()*1e-10+1e-20)
    prominence = 10*np.log10(np.maximum(power, 1e-20)/floor)
    upper = (frequencies >= 3000) & (frequencies <= min(16000, rate/2))
    candidates = upper[:, None] & (prominence >= 18) & (power/total >= 0.02)
    score = np.where(candidates, power/total, 0)
    indices = score.argmax(axis=0)
    frame = np.arange(len(times))
    return dict(frequencies=frequencies, times=times, power=power,
        tonal_fraction=score[indices, frame], tone_hz=frequencies[indices],
        prominence_db=prominence[indices, frame],
        high_fraction=power[frequencies >= 4000].sum(axis=0)/total,
        frame_level_db=10*np.log10(total), peak=peak, normalized=normalized,
        hop_seconds=1024/rate)


def scan_audio(audio, rate):
    """Flag narrow upper tones, HF-heavy bursts, clicks and clipping for review."""
    features = spectral_features(audio, rate)
    times, hop = features["times"], features["hop_seconds"]
    events = []
    masks = (("narrow_upper_tone", features["tonal_fraction"] >= 0.02, 0.10),
             ("high_frequency_heavy_section", features["high_fraction"] >= 0.40, 0.08))
    for kind, mask, minimum in masks:
        for a, b in _intervals(mask, times, hop, minimum):
            event = dict(kind=kind, start_seconds=round(max(0, float(times[a])-2048/rate), 3),
                         end_seconds=round(min(len(audio)/rate, float(times[b-1])+2048/rate), 3))
            if kind == "narrow_upper_tone":
                i = a+int(np.argmax(features["tonal_fraction"][a:b]))
                event.update(frequency_hz=round(float(features["tone_hz"][i]), 1),
                    prominence_db=round(float(features["prominence_db"][i]), 1),
                    spectral_energy_fraction=round(float(features["tonal_fraction"][i]), 4))
            events.append(event)
    # Abrupt full-band level increases; musical attacks may also trigger this screen.
    levels = features["frame_level_db"]
    lookback = max(1, round(0.3/hop))
    jumps = np.zeros(len(times), dtype=bool)
    for i in range(lookback, len(times)):
        jumps[i] = levels[i]-np.median(levels[i-lookback:i]) > 15 and levels[i] > levels.max()-20
    for a, b in _intervals(jumps, times, hop, 0.02):
        events.append(dict(kind="sudden_level_increase", start_seconds=round(float(times[a]), 3),
                           end_seconds=round(float(times[b-1])+hop, 3)))
    wave = np.asarray(audio)
    if np.any(abs(wave) >= 0.9999):
        events.append(dict(kind="samples_at_full_scale", count=int(np.sum(abs(wave) >= 0.9999))))
    return dict(scan_version=SCAN_VERSION, duration_seconds=round(len(audio)/rate, 3),
        sample_rate=rate, review_required=bool(events), events=events,
        max_upper_tone_fraction=round(float(features["tonal_fraction"].max()), 4),
        max_high_frequency_fraction=round(float(features["high_fraction"].max()), 4),
        limitations="Heuristic screening only. Musical harmonics, cymbals and attacks may trigger alerts. "
        "Unflagged audio may still be unpleasant or harmful at the listener's playback level. "
        "This cannot measure headphone sound pressure or diagnose tinnitus.")
