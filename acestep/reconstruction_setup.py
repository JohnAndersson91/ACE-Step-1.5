"""Download the upstream synthesizer example bank for the optional prototype."""
from pathlib import Path
from urllib.request import urlretrieve


def main() -> None:
    """Install the instrument bank without modifying global system settings."""
    path = Path(__file__).resolve().parents[1] / "checkpoints/reconstruction/florestan-subset.sf2"
    path.parent.mkdir(parents=True,exist_ok=True)
    if not path.exists():
        urlretrieve("https://raw.githubusercontent.com/schellingb/TinySoundFont/master/examples/florestan-subset.sf2",path)
    print("Reconstruction prototype ready. Basic Pitch is installed without its outdated "
          "TensorFlow/numpy pins; this setup uses its ONNX model with the existing runtime.")


if __name__ == "__main__":
    main()
