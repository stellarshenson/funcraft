"""Join clean clips of a voice into one 10-20 s Fish reference (wav plus transcript).

The clip named in resources/voices/<voice>/chosen.txt comes first; clips with a word error rate of 0 in
wip/voices/<voice>/verify.csv follow, in file order, until the reference lasts at least TARGET_SECONDS.

Usage: python src/fish/build_refs.py dijkstra vesemir
"""

import csv
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
TARGET_SECONDS = 15.0
MAX_SECONDS = 20.0
GAP_SECONDS = 0.3


def clean_clips(voice: str) -> list[tuple[str, str, float]]:
    """Return (file, transcript, seconds) of every clip with WER 0, in file order."""
    folder = ROOT / "wip/voices" / voice
    wer = {row["file"]: float(row["wer"]) for row in csv.DictReader(open(folder / "verify.csv"), delimiter="|")}
    rows = csv.DictReader(open(folder / "metadata.csv"), delimiter="|")
    return [(r["file"], r["text"], float(r["seconds"])) for r in rows if wer.get(r["file"]) == 0.0]


def build(voice: str) -> None:
    """Write wip/fish/refs/<voice>.wav and .txt."""
    chosen = int((ROOT / f"resources/voices/{voice}/chosen.txt").read_text().split()[0])
    first = ROOT / f"resources/voices/{voice}/ref-{chosen}"
    first_text = first.with_suffix(".txt").read_text().strip()
    audio, rate = sf.read(first.with_suffix(".wav"))
    parts, texts, total = [audio], [first_text], len(audio) / rate
    for name, text, seconds in clean_clips(voice):
        if total >= TARGET_SECONDS:
            break
        if text.strip() == first_text or total + seconds + GAP_SECONDS > MAX_SECONDS:
            continue
        clip, clip_rate = sf.read(ROOT / "wip/voices" / voice / "segments" / name)
        if clip_rate != rate:
            raise ValueError(f"{name}: {clip_rate} Hz, expected {rate} Hz")
        parts += [np.zeros(int(GAP_SECONDS * rate)), clip]
        texts.append(text.strip())
        total += seconds + GAP_SECONDS
    out = ROOT / "wip/fish/refs"
    out.mkdir(parents=True, exist_ok=True)
    sf.write(out / f"{voice}.wav", np.concatenate(parts), rate)
    (out / f"{voice}.txt").write_text(" ".join(texts) + "\n")
    print(f"{voice}: {len(texts)} clips, {total:.1f} s")


if __name__ == "__main__":
    for voice_name in sys.argv[1:]:
        build(voice_name)
