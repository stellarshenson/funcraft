"""Measure audio files (WAV or MP3) against their texts: word error rate, speaker similarity, peak and longest silence.

Usage: measure_audio.py <words.json> <speaker.json> <text file> <wav> [<wav> ...]
Reads the outputs of score_words.py and score_speaker.py; every WAV is compared with the same text.
Prints one JSON object per WAV. Silence is a run of samples below SILENCE_LEVEL (absolute value).
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from wer import word_error_rate

SILENCE_LEVEL = 0.002  # about -54 dBFS


def longest_silence_seconds(audio: np.ndarray, rate: int) -> float:
    """Length in seconds of the longest run of quiet samples between the first and last loud sample."""
    loud = np.flatnonzero(np.abs(audio) >= SILENCE_LEVEL)
    return float(np.diff(loud).max() / rate) if len(loud) > 1 else float(len(audio) / rate)


if __name__ == "__main__":
    heard, speaker = json.loads(Path(sys.argv[1]).read_text()), json.loads(Path(sys.argv[2]).read_text())
    reference = Path(sys.argv[3]).read_text()
    for wav in sys.argv[4:]:
        audio, rate = sf.read(wav)
        print(json.dumps({
            "wav": wav, "seconds": round(len(audio) / rate, 2), "wer": round(word_error_rate(reference, heard[wav]), 3),
            "similarity": speaker[wav], "peak": round(float(np.abs(audio).max()), 4),
            "longest_silence_s": round(longest_silence_seconds(audio, rate), 2),
        }))
