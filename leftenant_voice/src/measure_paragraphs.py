"""Per-paragraph measures of a controlled render: task, speaker similarity, word error rate, speaking rate, level.

Usage: measure_paragraphs.py <voice> <words.json> <speaker.json> <out.json>   (run in .venv-tools)
Reads wip/trials/ctl-<voice>/ (p-NN.wav and tasks.json from `speak.py --paragraphs-dir`) and the outputs of
score_words.py and score_speaker.py for those WAV files. Writes one record per paragraph to out.json.
Rate is words per second of the whole paragraph including the pauses between sentences; level is the RMS in dBFS.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from speak_text import BRACKETS
from wer import word_error_rate, words

DIRECTIVE = re.compile(r"^\{[^}]*\}\s*")


def level_dbfs(audio: np.ndarray) -> float:
    """RMS level in dBFS."""
    return float(20 * np.log10(np.sqrt((audio**2).mean()) + 1e-9))


if __name__ == "__main__":
    voice = sys.argv[1]
    heard, speaker = json.loads(Path(sys.argv[2]).read_text()), json.loads(Path(sys.argv[3]).read_text())
    folder = Path("wip/trials") / f"ctl-{voice}"
    records = []
    for task in json.loads((folder / "tasks.json").read_text()):
        wav = f"wip/trials/ctl-{voice}/p-{task['number']:02d}.wav"
        spoken_text = BRACKETS.sub("", task["text"])
        audio, rate = sf.read(wav)
        similarity = speaker[wav]
        other = {v: round(s, 3) for v, s in similarity.items() if v != voice}
        records.append({
            "paragraph": task["number"], "task": task["task"], "controls": task["controls"],
            "seconds": round(len(audio) / rate, 2), "words_per_second": round(len(words(spoken_text)) / (len(audio) / rate), 2),
            "level_dbfs": round(level_dbfs(audio), 1), "wer": round(word_error_rate(spoken_text, heard[wav]), 3),
            "similarity_own": round(similarity[voice], 3), "similarity_other": other,
            "similarity_max_other": max(other.values()),
        })
    Path(sys.argv[4]).write_text(json.dumps(records, indent=1))
    for r in records:
        print(r)
