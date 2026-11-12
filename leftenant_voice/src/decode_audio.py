"""Decode a recording to mono WAV at 16 kHz (speech recognition) and 44.1 kHz (Ming prompt rate).

Usage: decode_audio.py <recording.mp3> <out_dir>
Writes <out_dir>/full-16k.wav and <out_dir>/full-44k.wav.
"""
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
RATES = {"16k": 16000, "44k": 44100}


def decode(source: Path, target: Path, rate: int) -> None:
    """Convert `source` to a mono 16-bit WAV at `rate` Hz."""
    subprocess.run(
        [FFMPEG, "-y", "-loglevel", "error", "-i", str(source), "-ac", "1", "-ar", str(rate),
         "-c:a", "pcm_s16le", str(target)],
        check=True,
    )


if __name__ == "__main__":
    source, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, rate in RATES.items():
        target = out_dir / f"full-{name}.wav"
        if not target.exists():
            decode(source, target, rate)
        print(target)
