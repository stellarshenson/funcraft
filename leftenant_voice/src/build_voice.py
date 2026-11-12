"""Build the clean segment set and the reference clips of one voice.

Usage: build_voice.py <voice>
Reads  wip/voices/<voice>/segments.json, embeddings.npy, full-16k.wav, full-44k.wav
Writes wip/voices/<voice>/segments/*.wav, metadata.csv (file|text|seconds), centroid.npy, speaker-model.txt,
       selection.json (cluster report and the numbers for the notes)
       resources/voices/<voice>/ref-1.wav .. ref-3.wav and ref-1.txt .. ref-3.txt
A segment is a run of consecutive sentence pieces of the target speaker's group, 2 to 20 s long, with a transcript
that agrees with the audio (NLL_MAX), a quiet pause around it (PAUSE_DB_MAX) and no clipping (PEAK_MAX).
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

import speaker_group
from segment_runs import MAX_SECONDS, RATE_16K, RATE_44K, cut_bounds, merge_runs, segment_record
from speaker_group import SPEAKER_MODEL

MIN_SECONDS = 2.0
NLL_MAX = 0.6
PAUSE_DB_MAX = -60.0
PEAK_MAX = 0.99
REF_COUNT = 3
# Strict rules first; a short recording that cannot give REF_COUNT clips under them gets the relaxed rules.
REF_RULES = (
    {"seconds": (4.0, 8.0), "nll": 0.1, "complete_sentence": True, "apart": 30.0},
    {"seconds": (3.0, 8.0), "nll": 0.15, "complete_sentence": False, "apart": 10.0},
    # Under one minute of voice (setrakian): any kept segment, as long as the clips do not overlap
    {"seconds": (2.5, 8.0), "nll": NLL_MAX, "complete_sentence": False, "apart": 0.0},
)


def choose_refs(segments: list[dict], centroid: np.ndarray) -> list[dict]:
    """Pick up to REF_COUNT clips: closest to the centroid, quietest pause, far apart; the strict rules if they suffice."""
    def rank(values):
        return np.argsort(np.argsort(values))
    for rules in REF_RULES:
        candidates = [
            s for s in segments
            if rules["seconds"][0] <= s["end"] - s["start"] <= rules["seconds"][1] and s["nll"] <= rules["nll"]
            and (not rules["complete_sentence"] or (s["text"][0].isupper() and s["text"][-1] in ".?!"))
        ]
        if not candidates:
            continue
        similarity = np.array([s["embedding"] @ centroid for s in candidates])
        pause = np.array([s["pause_db"] for s in candidates])
        refs: list[dict] = []
        for index in np.argsort(rank(-similarity) * 2 + rank(pause)):
            if all(abs(candidates[index]["start"] - r["start"]) >= rules["apart"] for r in refs):
                refs.append(candidates[index])
            if len(refs) == REF_COUNT:
                return refs
        if rules is REF_RULES[-1] and refs:
            return refs
    raise RuntimeError("no reference clip passes the filters")


def write_clip(audio: np.ndarray, bounds: tuple[float, float], path: Path) -> float:
    """Write the 44.1 kHz audio between bounds to path and return its length in seconds."""
    clip = audio[int(bounds[0] * RATE_44K): int(bounds[1] * RATE_44K)]
    sf.write(path, clip, RATE_44K, subtype="PCM_16")
    return len(clip) / RATE_44K


def main(voice: str) -> None:
    folder = Path("wip/voices") / voice
    pieces, embeddings = speaker_group.load_pieces(folder)
    labels = speaker_group.cluster_pieces(pieces, embeddings)
    target = speaker_group.target_cluster(pieces, labels)
    audio16, _ = sf.read(folder / "full-16k.wav", dtype="float32")
    audio44, _ = sf.read(folder / "full-44k.wav", dtype="float32")
    in_group = [i for i, l in enumerate(labels) if l == target]
    centroid = np.nanmean(embeddings[in_group], axis=0)
    centroid /= np.linalg.norm(centroid)

    runs = merge_runs(pieces, in_group)
    candidates = [(run, segment_record(pieces, embeddings, run, audio16, audio44)) for run in runs]
    kept = [
        (run, s) for run, s in candidates
        if MIN_SECONDS <= s["end"] - s["start"] <= MAX_SECONDS and s["nll"] <= NLL_MAX
        and s["pause_db"] <= PAUSE_DB_MAX and s["peak"] < PEAK_MAX
    ]
    for stale in (folder / "segments").glob("*.wav") if (folder / "segments").exists() else []:
        stale.unlink()
    (folder / "segments").mkdir(exist_ok=True)
    rows = []
    for number, (run, s) in enumerate(kept):
        name = f"{voice}-{number:04d}.wav"
        rows.append((name, s["text"], round(write_clip(audio44, cut_bounds(pieces, run), folder / "segments" / name), 2)))
    with open(folder / "metadata.csv", "w", newline="") as handle:
        writer = csv.writer(handle, delimiter="|")
        writer.writerow(["file", "text", "seconds"])
        writer.writerows(rows)
    np.save(folder / "centroid.npy", centroid)
    (folder / "speaker-model.txt").write_text(SPEAKER_MODEL + "\n")

    refs = choose_refs([s for _, s in kept], centroid)
    ref_folder = Path("resources/voices") / voice
    ref_folder.mkdir(parents=True, exist_ok=True)
    ref_info = []
    for number, ref in enumerate(refs, 1):
        run = next(r for r, s in kept if s is ref)
        seconds = write_clip(audio44, cut_bounds(pieces, run), ref_folder / f"ref-{number}.wav")
        (ref_folder / f"ref-{number}.txt").write_text(ref["text"] + "\n")
        ref_info.append({"file": f"ref-{number}.wav", "text": ref["text"], "seconds": round(seconds, 2),
                         "start": ref["start"], "nll": round(ref["nll"], 3), "pause_db": round(ref["pause_db"], 1),
                         "centroid_similarity": round(float(ref["embedding"] @ centroid), 3)})
    (folder / "selection.json").write_text(json.dumps({
        "minutes_total": round(len(audio16) / RATE_16K / 60, 2),
        "minutes_speech_pieces": round(sum(p["end"] - p["start"] for p in pieces) / 60, 2),
        "minutes_target_group": round(sum(pieces[i]["end"] - pieces[i]["start"] for i in in_group) / 60, 2),
        "minutes_kept": round(sum(r[2] for r in rows) / 60, 2), "segments": len(rows),
        "runs_before_filters": len(runs), "rejected_by_nll": sum(s["nll"] > NLL_MAX for _, s in candidates),
        "rejected_by_pause": sum(s["pause_db"] > PAUSE_DB_MAX for _, s in candidates),
        "rejected_by_clipping": sum(s["peak"] >= PEAK_MAX for _, s in candidates),
        "clusters": speaker_group.report(pieces, labels, target), "refs": ref_info,
    }, indent=1))
    print(voice, "kept", len(rows), "segments,", round(sum(r[2] for r in rows) / 60, 1), "min; refs", len(refs))


if __name__ == "__main__":
    main(sys.argv[1])
