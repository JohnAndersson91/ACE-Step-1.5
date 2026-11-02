"""Run RoFormer separation in an isolated process to release model memory afterward."""
import os
from pathlib import Path
import sys
import shutil


def main() -> None:
    """Separate the supplied audio into explicitly named instrumental/vocal WAVs."""
    import imageio_ffmpeg
    from audio_separator.separator import Separator

    source, destination = sys.argv[1:3]
    root = Path(__file__).resolve().parents[1]
    # The bundled converter is used by dependencies that look for ffmpeg on PATH.
    binary = imageio_ffmpeg.get_ffmpeg_exe()
    tools = root / "acestep_output" / "tools"
    tools.mkdir(parents=True, exist_ok=True)
    executable = tools / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
    if not executable.exists():
        shutil.copy2(binary, executable)
    os.environ["PATH"] = str(tools) + os.pathsep + os.environ.get("PATH", "")
    separator = Separator(model_file_dir=str(root / "checkpoints" / "separation"),
        output_dir=destination, output_format="WAV", use_soundfile=True,
        mdxc_params={"segment_size": 128, "override_model_segment_size": True,
                     "batch_size": 1, "overlap": 2, "pitch_shift": 0})
    separator.load_model(model_filename="model_bs_roformer_ep_317_sdr_12.9755.ckpt")
    separator.separate(source, {"Instrumental": "instrumental", "Vocals": "vocals"})


if __name__ == "__main__":
    main()
