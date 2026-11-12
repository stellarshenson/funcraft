"""Measure Fish and Ming renders of the controlled speech: duration, WER, speaker similarity, controls.

Usage: PYTHONPATH=src:src/fish measure_fish.py <out.json> <words.json> [<words.json> ...]
(run in .venv-tools from the project folder; ECAPA runs on the CPU)
Reads the transcripts of asr_words.py, the Fish renders in out/fish/ and their paragraph WAVs in
wip/fish/paragraphs/<voice>/, the copy of the Ming renders in wip/fish/ming/, the timing of each render and the voice
centroids. The Ming render of a voice is the joined paragraph WAVs' transcripts when its full WAV has none.
Writes out.json and prints markdown tables.
"""
import difflib
import json
import re
import sys
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
import torch
from speechbrain.inference.speaker import EncoderClassifier
from speaker_group import SPEAKER_MODEL
from tag_events import parse_paragraph
from wer import word_error_rate, words

VOICES = ("dijkstra", "vesemir")
FISH_TEXT, MING_TEXT = Path("texts/fish/inspiring-speech-fish.txt"), Path("wip/fish/ming/inspiring-speech-controlled.txt")
MING_SMOKE_PEAK_GIB = 3.04  # wip/logs/smoke-flash.log, max_memory_allocated_gb
FRAME = 0.025
AUDIBLE_EXTRA_GAP, AUDIBLE_EXTRA_DB, AUDIBLE_FLOOR_DB = 0.2, 6.0, -50.0


def paragraphs(path: Path) -> list[str]:
    """Paragraphs of a text file without comment lines."""
    body = "\n".join(l for l in path.read_text().splitlines() if not l.startswith("#"))
    return [" ".join(b.split()) for b in re.split(r"\n\s*\n", body) if b.strip()]


def rms_db(audio: np.ndarray) -> float:
    """RMS level in dBFS."""
    return float(20 * np.log10(np.sqrt((audio**2).mean()) + 1e-9)) if len(audio) else -180.0


def peak_frame_db(audio: np.ndarray, rate: int) -> float:
    """Highest RMS level of a FRAME-long window, in dBFS."""
    step = int(FRAME * rate)
    if len(audio) < step:
        return rms_db(audio)
    return max(rms_db(audio[i:i + step]) for i in range(0, len(audio) - step + 1, step // 2))


def map_words(spoken: list[str], heard: list[dict]) -> dict[int, int]:
    """Map the index of each spoken word to the index of the matching transcript word."""
    heard_words = [(words(h["text"]) or [""])[0] for h in heard]
    mapping = {}
    for block in difflib.SequenceMatcher(None, spoken, heard_words, autojunk=False).get_matching_blocks():
        mapping.update({block.a + k: block.b + k for k in range(block.size)})
    return mapping


def gap_around(index: int, mapping: dict[int, int], heard: list[dict], seconds: float) -> tuple[float, float] | None:
    """Start and end of the time between the matched words before and after spoken index `index`, or None."""
    before = next((mapping[i] for i in range(index - 1, -1, -1) if i in mapping), None)
    after = next((mapping[i] for i in range(index, len(mapping) + index) if i in mapping), None)
    if before is None and after is None:
        return None
    start = heard[before]["end"] if before is not None else 0.0
    end = heard[after]["start"] if after is not None else seconds
    return start, max(end, start)


def gaps(audio, rate, spoken, events, heard) -> tuple[list[dict], list[tuple[float, float]]]:
    """Measure the gap at every point tag, and the gaps (length, level) of untagged sentence ends.

    Returns the tag records without a verdict and the untagged sentence-end gaps, which `main` pools per render
    as the baseline: a paragraph can have no untagged sentence end.
    """
    mapping = map_words(spoken, heard)
    seconds = len(audio) / rate
    tags = [(e, gap_around(e.first, mapping, heard, seconds)) for e in events if e.kind == "point"]
    tagged_starts = [span[0] for _, span in tags if span]
    ends = [
        (heard[i]["end"], heard[i + 1]["start"]) for i, h in enumerate(heard[:-1])
        if h["text"].rstrip().endswith((".", "?", "!")) and all(abs(heard[i]["end"] - t) > 0.05 for t in tagged_starts)
    ]

    def measure(span: tuple[float, float]) -> tuple[float, float]:
        return span[1] - span[0], peak_frame_db(audio[int(span[0] * rate):int(span[1] * rate)], rate)

    records = [{"tag": e.label, "found": span is not None, **({"gap_s": round(measure(span)[0], 2), "gap_db": round(measure(span)[1], 1)} if span else {})} for e, span in tags]
    return records, [measure(span) for span in ends]


def judge(records: list[dict], baseline: list[tuple[float, float]]) -> None:
    """Add the baseline and the verdict to every tag record.

    A tag is audible if its gap is longer than the baseline by AUDIBLE_EXTRA_GAP, or its peak level is above the
    baseline by AUDIBLE_EXTRA_DB and above AUDIBLE_FLOOR_DB.
    """
    base_gap = float(np.median([g for g, _ in baseline]))
    base_db = float(np.median([d for _, d in baseline]))
    for r in records:
        if r["found"]:
            r |= {"base_gap_s": round(base_gap, 2), "base_db": round(base_db, 1),
                  "audible": bool(r["gap_s"] >= base_gap + AUDIBLE_EXTRA_GAP or (r["gap_db"] >= base_db + AUDIBLE_EXTRA_DB and r["gap_db"] >= AUDIBLE_FLOOR_DB))}


def scoped_events(audio, rate, spoken, events, heard) -> list[dict]:
    """Level and speaking rate of the words inside a scoped tag against the rest of the paragraph."""
    mapping = map_words(spoken, heard)
    out = []
    for e in (e for e in events if e.kind == "scoped"):
        idx = [mapping[i] for i in range(e.first, e.last) if i in mapping]
        if not idx:
            out.append({"tag": e.label, "found": False})
            continue
        a, b = heard[idx[0]]["start"], heard[idx[-1]]["end"]
        inside = audio[int(a * rate):int(b * rate)]
        outside = np.concatenate([audio[:int(a * rate)], audio[int(b * rate):]])
        rate_in = len(idx) / max(b - a, 1e-3)
        rest = [h for k, h in enumerate(heard) if k not in range(idx[0], idx[-1] + 1)]
        rate_out = len(rest) / max(rest[-1]["end"] - rest[0]["start"], 1e-3) if rest else 0.0
        out.append({
            "tag": e.label, "found": True, "db_inside": round(rms_db(inside), 1), "db_outside": round(rms_db(outside), 1),
            "words_per_s_inside": round(rate_in, 2), "words_per_s_outside": round(rate_out, 2),
        })
    return out


def paragraph_stats(audio, rate, spoken, heard) -> dict:
    """Length, level and speaking rate of one paragraph."""
    span = (heard[-1]["end"] - heard[0]["start"]) if heard else len(audio) / rate
    return {"seconds": round(len(audio) / rate, 2), "db": round(rms_db(audio), 1), "words_per_s": round(len(spoken) / max(span, 1e-3), 2)}


def speaker_similarity(model, centroids, wav: str) -> dict:
    """Cosine similarity of a WAV to each voice centroid."""
    samples, _ = librosa.load(wav, sr=16000)
    vec = model.encode_batch(torch.from_numpy(samples)[None]).squeeze().cpu().numpy()
    return {v: round(float(vec @ c / (np.linalg.norm(vec) * np.linalg.norm(c))), 3) for v, c in centroids.items()}


def ming_timing(voice: str, audio_seconds: float) -> dict:
    """Timing of the Ming render whose log reports the audio length of the measured WAV.

    The logs of other renders of the same text are returned as `other_rtf`, because the render logs show
    that real-time factors rose when several renders shared the machine.
    """
    runs = []
    for log in sorted(Path("wip/logs").glob(f"render-ctl*-{voice}.log")):
        lines = [l.split() for l in log.read_text().splitlines() if l.startswith("synth_seconds")]
        runs += [(float(l[1]), float(l[3]), float(l[5])) for l in lines]
    match = min(runs, key=lambda r: abs(r[1] - audio_seconds))
    return {"synth_seconds": match[0], "peak_gpu_gib": MING_SMOKE_PEAK_GIB, "other_rtf": sorted(r[2] for r in runs)}


def full_transcript(heard: dict, full: str, folder: str, count: int) -> str:
    """Transcript of the full WAV, or of its paragraph WAVs joined when the full WAV was not transcribed."""
    if full in heard:
        return heard[full]["text"]
    return " ".join(heard[f"{folder}/p-{n:02d}.wav"]["text"] for n in range(1, count + 1))


def main() -> None:
    """Measure both models for both voices and write the result."""
    heard = {}
    for path in sys.argv[2:]:
        heard |= json.loads(Path(path).read_text())
    model = EncoderClassifier.from_hparams(source=SPEAKER_MODEL, savedir="wip/speaker-model", run_opts={"device": "cpu"})
    centroids = {v: np.load(f"wip/voices/{v}/centroid.npy") for v in VOICES}
    result = {}
    for voice in VOICES:
        for name, text_file, full, folder in (
            ("fish", FISH_TEXT, f"out/fish/inspiring-speech-{voice}-fish.mp3", f"wip/fish/paragraphs/{voice}"),
            ("ming", MING_TEXT, f"wip/fish/ming/{voice}-controlled.wav", f"wip/fish/ming/{voice}"),
        ):
            texts = paragraphs(text_file)
            parsed = [parse_paragraph(t) for t in texts]
            timing = json.loads(Path(full).with_suffix(".json").read_text()) if name == "fish" else None
            audio, rate = sf.read(full)
            timing = timing or ming_timing(voice, len(audio) / rate)
            all_words = [w for spoken, _ in parsed for w in spoken]
            record = {
                "audio_seconds": round(len(audio) / rate, 1), "synth_seconds": round(timing["synth_seconds"], 1), "other_rtf": timing.get("other_rtf"), "rtf": round(timing["synth_seconds"] / (len(audio) / rate), 2),
                "peak_gpu_gib": round(timing["peak_gpu_gib"], 1), "wer": round(word_error_rate(" ".join(all_words), full_transcript(heard, full, folder, len(parsed))), 3),
                "similarity": speaker_similarity(model, centroids, full), "paragraphs": [],
            }
            baseline, all_points = [], []
            for number, (spoken, events) in enumerate(parsed, 1):
                wav = f"{folder}/p-{number:02d}.wav"
                clip, clip_rate = sf.read(wav)
                words_heard = heard[wav]["words"]
                point_records, untagged = gaps(clip, clip_rate, spoken, events, words_heard)
                baseline += untagged
                all_points.append(point_records)
                record["paragraphs"].append({
                    "n": number, **paragraph_stats(clip, clip_rate, spoken, words_heard),
                    "wer": round(word_error_rate(" ".join(spoken), heard[wav]["text"]), 3), "similarity": speaker_similarity(model, centroids, wav),
                    "points": point_records, "scoped": scoped_events(clip, clip_rate, spoken, events, words_heard),
                    "styles": [e.label for e in events if e.kind == "style"],
                })
            for records in all_points:
                judge(records, baseline)
            result[f"{voice}-{name}"] = record
    Path(sys.argv[1]).write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == "__main__":
    main()
