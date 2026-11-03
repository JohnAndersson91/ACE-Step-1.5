"""Visual inspection of frequency content without creating or playing any audio."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import soundfile as sf

from acestep.audio_artifact_scan import spectral_features


def artifact_figure(path, start=20, duration=10):
    """Plot a bounded excerpt's spectrum and upper-band energy; no safety verdict."""
    info = sf.info(path)
    if not 0 <= start < info.duration or not 1 <= duration <= 30:
        raise ValueError("Choose a start inside the file and a 1–30 second view.")
    audio, rate = sf.read(path, start=round(start*info.samplerate),
        stop=min(info.frames, round((start+duration)*info.samplerate)),
        dtype="float32", always_2d=True)
    data = spectral_features(audio, rate)
    frequencies, times, power = data["frequencies"], data["times"]+start, data["power"]
    relative = 10*np.log10(np.maximum(power, 1e-20)/max(float(power.max()), 1e-20))
    fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True,
                              gridspec_kw={"height_ratios": [3, 1, 1]}, layout="constrained")
    image = axes[0].pcolormesh(times, frequencies/1000, relative, cmap="magma",
                              vmin=-70, vmax=0, shading="auto")
    axes[0].set_ylim(0, min(16, rate/2000))
    axes[0].set_ylabel("Frequency (kHz)")
    axes[0].set_title("Sound inspection — brighter areas show stronger spectral energy")
    fig.colorbar(image, ax=axes[0], label="dB relative to excerpt peak (not headphone SPL)")
    axes[1].plot(times, data["high_fraction"]*100, color="#b33939", linewidth=1)
    axes[1].axhline(40, color="gray", linestyle="--", linewidth=0.8, label="Screening threshold")
    axes[1].set_ylabel("Energy ≥4 kHz (%)")
    axes[1].set_ylim(0, 100)
    axes[1].legend(loc="upper right", fontsize=8)
    axes[2].plot(times, data["frame_level_db"]-data["frame_level_db"].max(), color="#245c97")
    axes[2].set_ylabel("Frame level\n(relative dB)")
    axes[2].set_xlabel("Time in source file (seconds)")
    from acestep.audio_artifact_gate import scan_file
    for event in scan_file(path)["events"]:
        if "start_seconds" in event and event["end_seconds"] > start and event["start_seconds"] < start+duration:
            for axis in axes:
                axis.axvspan(event["start_seconds"], event["end_seconds"], color="red", alpha=0.18)
    return fig
