"""Write a final render: a `.wav` target under out/ becomes an MP3, so out/ never holds a WAV."""
import subprocess
from pathlib import Path

import numpy as np

OUT_DIR = Path(__file__).resolve().parent.parent / "out"
MP3_QUALITY = "2"  # LAME VBR quality, as `ffmpeg -q:a 2`
MP3_PEAK = 10 ** (-1 / 20)  # -1 dBFS, the headroom an MP3 decoder's overshoot needs to stay under full scale


def with_mp3_headroom(audio: np.ndarray) -> np.ndarray:
    """Return `audio` as float32, scaled down when its peak is above `MP3_PEAK`; never scaled up."""
    samples = np.asarray(audio, dtype=np.float32)
    peak = float(np.abs(samples).max()) if samples.size else 0.0
    return samples * (MP3_PEAK / peak) if peak > MP3_PEAK else samples


def write_render(path: Path, audio: np.ndarray, rate: int) -> Path:
    """Write mono float audio to `path`; under out/ a `.wav` name becomes the `.mp3` of the same name.

    An MP3 is encoded with its peak held at -1 dBFS, because a decoder overshoots the encoded peak.

    Args:
        path: target file; relative paths are taken from the current folder.
        audio: samples, shape (n,).
        rate: sample rate in Hz.

    Returns:
        The path written, also printed.

    Raises:
        subprocess.CalledProcessError: ffmpeg failed to encode.
    """
    path = Path(path).absolute()
    if path.suffix == ".wav" and OUT_DIR in path.resolve().parents:
        path = path.with_suffix(".mp3")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix == ".mp3":
        samples = with_mp3_headroom(audio)
        command = ["ffmpeg", "-nostdin", "-loglevel", "error", "-y", "-f", "f32le", "-ar", str(rate), "-ac", "1",
                   "-i", "-", "-codec:a", "libmp3lame", "-q:a", MP3_QUALITY, str(path)]
        subprocess.run(command, input=np.asarray(samples, dtype="<f4").tobytes(), check=True)
    else:
        import soundfile as sf  # the Ming venv has it too; imported here so MP3-only callers do not need it
        sf.write(path, audio, rate)
    print("wrote", path, flush=True)
    return path
