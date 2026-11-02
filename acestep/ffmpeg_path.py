"""Find an existing audio encoder without installing software or changing PATH."""
from pathlib import Path
import shutil


def ffmpeg_executable() -> str:
    """Prefer the system encoder, then the already-bundled imageio encoder."""
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg
        bundled = imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError,RuntimeError) as error:
        raise FileNotFoundError("No existing ffmpeg encoder was found") from error
    if not Path(bundled).is_file():
        raise FileNotFoundError("The bundled ffmpeg encoder is missing")
    return bundled
