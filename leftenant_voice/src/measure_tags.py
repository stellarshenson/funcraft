"""Compare each tagged sentence of a controlled render with the same sentence spoken without its tag.

Usage: measure_tags.py <voice> <out.json>   (run in .venv-tools)
Reads wip/trials/ctl-<voice>/ (controlled paragraphs) and wip/trials/plain-<voice>/ (the plain speech spoken with
the same `--paragraphs-dir`). A paragraph WAV holds its sentences separated by PAUSE_SECONDS of exact zeros; the
sentences are cut there. Per tagged sentence of a TTS paragraph, with and without the tag: duration, the time before
speech starts (the first 50 ms frame at or above ONSET_DBFS) and the loudest 50 ms frame before that onset. Every tag
of the speech opens a sentence, so the tag's sound lies before the onset. A tag is audible when the sound before the
onset lasts at least AUDIBLE_SECONDS above AUDIBLE_DBFS and the sentence without the tag has none.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from speak_text import BRACKETS, split_sentences

PAUSE_SECONDS = 0.4
FRAME_SECONDS = 0.05
ONSET_DBFS = -35.0
AUDIBLE_DBFS = -60.0
AUDIBLE_SECONDS = 0.15
TAG_AT_START = re.compile(r"^(\[[^\]]+\])\s*")


def cut_sentences(audio: np.ndarray, rate: int) -> list[np.ndarray]:
    """Split a paragraph WAV at its runs of exact zeros of at least PAUSE_SECONDS (the pauses `speak.py` inserts)."""
    zero = audio == 0
    edges = np.flatnonzero(np.diff(np.concatenate(([0], zero.view(np.int8), [0]))))
    cuts, start = [], 0
    for begin, end in zip(edges[::2], edges[1::2]):
        if end - begin >= int(PAUSE_SECONDS * rate) * 0.99:
            cuts.append(audio[start:begin])
            start = end
    cuts.append(audio[start:])
    return cuts


def frame_levels(audio: np.ndarray, rate: int) -> np.ndarray:
    """RMS level in dBFS of consecutive FRAME_SECONDS frames."""
    step = int(FRAME_SECONDS * rate)
    frames = audio[: len(audio) // step * step].reshape(-1, step)
    return 20 * np.log10(np.sqrt((frames**2).mean(1)) + 1e-9)


def lead_in(audio: np.ndarray, rate: int) -> dict[str, float]:
    """Seconds before speech starts, seconds of sound above AUDIBLE_DBFS in that time, and its loudest level."""
    levels = frame_levels(audio, rate)
    before = levels[: int(np.argmax(levels >= ONSET_DBFS))]
    return {
        "onset_seconds": round(len(before) * FRAME_SECONDS, 2),
        "sound_seconds": round(float((before >= AUDIBLE_DBFS).sum()) * FRAME_SECONDS, 2),
        "sound_peak_dbfs": round(float(before.max()), 1) if len(before) else -180.0,
    }


def sentences_of(folder: Path) -> dict[str, np.ndarray]:
    """Map each sentence text (tags removed) of a folder's paragraphs to its audio, in order of appearance."""
    found = {}
    for task in json.loads((folder / "tasks.json").read_text()):
        audio, rate = sf.read(folder / f"p-{task['number']:02d}.wav")
        texts = split_sentences(task["text"])
        pieces = cut_sentences(audio, rate)
        if len(texts) != len(pieces):
            raise SystemExit(f"{folder} paragraph {task['number']}: {len(texts)} sentences, {len(pieces)} pieces")
        for text, piece in zip(texts, pieces):
            found[text] = (piece, rate)
    return found


if __name__ == "__main__":
    voice = sys.argv[1]
    controlled = sentences_of(Path("wip/trials") / f"ctl-{voice}")
    plain = sentences_of(Path("wip/trials") / f"plain-{voice}")
    records = []
    for text, (audio, rate) in controlled.items():
        match = TAG_AT_START.match(text)
        if not match:
            continue
        bare = BRACKETS.sub("", text).strip()
        plain_audio = plain[bare][0]
        tagged, bare_lead = lead_in(audio, rate), lead_in(plain_audio, rate)
        records.append({
            "tag": match.group(1), "sentence": bare, "seconds_tagged": round(len(audio) / rate, 2),
            "seconds_plain": round(len(plain_audio) / rate, 2), "lead_tagged": tagged, "lead_plain": bare_lead,
            "audible": tagged["sound_seconds"] >= AUDIBLE_SECONDS and bare_lead["sound_seconds"] < AUDIBLE_SECONDS,
        })
    Path(sys.argv[2]).write_text(json.dumps(records, indent=1))
    for r in records:
        print(r)
