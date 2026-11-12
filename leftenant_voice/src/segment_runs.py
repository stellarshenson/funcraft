"""Build segments from the sentence pieces of the target speaker: runs of neighbours, their measures and cut bounds."""
import numpy as np

MAX_SECONDS = 20.0
MERGE_GAP = 0.5
PAUSE_CONTEXT, PAUSE_FRAME = 0.3, 0.05
CUT_PAD = 0.05
RATE_16K, RATE_44K = 16000, 44100


def pause_db(audio: np.ndarray, start: float, end: float) -> float:
    """Quietest 50 ms frame in dBFS within PAUSE_CONTEXT seconds around the segment: the bed under the voice."""
    step = int(PAUSE_FRAME * RATE_16K)
    part = audio[int(max(start - PAUSE_CONTEXT, 0) * RATE_16K): int((end + PAUSE_CONTEXT) * RATE_16K)]
    frames = part[: len(part) // step * step].reshape(-1, step)
    return float(20 * np.log10(np.sqrt((frames**2).mean(1)) + 1e-9).min())


def merge_runs(pieces: list[dict], kept: list[int]) -> list[list[int]]:
    """Group kept piece indices into runs of neighbours with a short pause, up to MAX_SECONDS."""
    runs: list[list[int]] = []
    for index in kept:
        run = runs[-1] if runs else None
        if (
            run
            and run[-1] == index - 1
            and pieces[index]["start"] - pieces[run[-1]]["end"] < MERGE_GAP
            and pieces[index]["end"] - pieces[run[0]]["start"] <= MAX_SECONDS
        ):
            run.append(index)
        else:
            runs.append([index])
    return runs


def segment_record(
    pieces: list[dict], embeddings: np.ndarray, run: list[int], audio16: np.ndarray, audio44: np.ndarray
) -> dict:
    """Join the pieces of a run into one segment with its text, token-weighted NLL, embedding, pause level and peak."""
    parts = [pieces[i] for i in run]
    start, end = parts[0]["start"], parts[-1]["end"]
    tokens = sum(p["tokens"] for p in parts)
    weights = np.array([p["end"] - p["start"] for p in parts])
    embedding = (embeddings[run] * weights[:, None]).sum(0)
    return {
        "start": start, "end": end, "text": " ".join(p["text"] for p in parts),
        "nll": sum(p["nll"] * p["tokens"] for p in parts) / tokens,
        "embedding": embedding / np.linalg.norm(embedding),
        "pause_db": pause_db(audio16, start, end),
        "peak": float(np.abs(audio44[int(start * RATE_44K): int(end * RATE_44K)]).max()),
    }


def cut_bounds(pieces: list[dict], run: list[int]) -> tuple[float, float]:
    """Segment start and end with CUT_PAD, never reaching into the neighbouring pieces."""
    before = pieces[run[0] - 1]["end"] if run[0] > 0 else 0.0
    after = pieces[run[-1] + 1]["start"] if run[-1] + 1 < len(pieces) else float("inf")
    start, end = pieces[run[0]]["start"], pieces[run[-1]]["end"]
    return max(start - CUT_PAD, (before + start) / 2), min(end + CUT_PAD, (end + after) / 2)
