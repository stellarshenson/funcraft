"""Compare the BASIC paragraphs of a controlled render with the same sentences of the plain render.

Usage: measure_basic.py <voice> <out.json>   (run in .venv-tools)
Reads wip/trials/ctl-<voice>/ and wip/trials/plain-<voice>/ (made with `speak.py --paragraphs-dir`). Per BASIC
paragraph: words per second of speech (pauses between sentences left out) and RMS level in dBFS, for the
paragraph and for the same sentences of the plain render.
"""
import json
import sys
from pathlib import Path

import numpy as np
from measure_tags import sentences_of
from speak_text import split_sentences
from wer import words


def rate_and_level(texts: list[str], audio: dict[str, tuple[np.ndarray, int]]) -> dict[str, float]:
    """Words per second and RMS level (dBFS) over the given sentences, joined without pauses."""
    joined = np.concatenate([audio[t][0] for t in texts])
    seconds = len(joined) / audio[texts[0]][1]
    return {
        "words_per_second": round(sum(len(words(t)) for t in texts) / seconds, 2),
        "level_dbfs": round(float(20 * np.log10(np.sqrt((joined**2).mean()) + 1e-9)), 1),
    }


if __name__ == "__main__":
    voice = sys.argv[1]
    folder = Path("wip/trials") / f"ctl-{voice}"
    controlled, plain = sentences_of(folder), sentences_of(Path("wip/trials") / f"plain-{voice}")
    records = []
    for task in json.loads((folder / "tasks.json").read_text()):
        if task["task"] != "BASIC":
            continue
        texts = split_sentences(task["text"])
        records.append({
            "paragraph": task["number"], "controls": task["controls"],
            "controlled": rate_and_level(texts, controlled), "plain": rate_and_level(texts, plain),
        })
    Path(sys.argv[2]).write_text(json.dumps(records, indent=1))
    print(json.dumps(records, indent=1, ensure_ascii=False))
