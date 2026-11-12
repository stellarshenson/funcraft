"""Find the target speaker's group among the sentence pieces of a recording.

Pieces are clustered by ECAPA embedding (average linkage, cosine distance). The target speaker's group is the
cluster with the most speech: the recordings are named after one speaker, and the evidence is the group sizes
and the lines of each group (see `report`).
"""
import json
from pathlib import Path

import numpy as np
from sklearn.cluster import AgglomerativeClustering

SPEAKER_MODEL = "speechbrain/spkrec-ecapa-voxceleb"
CLUSTER_DISTANCE = 0.6
EXAMPLE_LINES = 6


def load_pieces(folder: Path) -> tuple[list[dict], np.ndarray]:
    """Return the sentence pieces and their unit-length embeddings (NaN rows for pieces too short to embed)."""
    pieces = json.loads((folder / "segments.json").read_text())
    embeddings = np.load(folder / "embeddings.npy")
    return pieces, embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)


def cluster_pieces(pieces: list[dict], embeddings: np.ndarray) -> np.ndarray:
    """Return a cluster label per piece, -1 for pieces without an embedding."""
    embedded = ~np.isnan(embeddings[:, 0])
    labels = np.full(len(pieces), -1)
    labels[embedded] = AgglomerativeClustering(
        n_clusters=None, distance_threshold=CLUSTER_DISTANCE, metric="cosine", linkage="average"
    ).fit_predict(embeddings[embedded])
    return labels


def target_cluster(pieces: list[dict], labels: np.ndarray) -> int:
    """Return the label of the cluster with the most seconds of speech."""
    seconds = {
        label: sum(p["end"] - p["start"] for p, l in zip(pieces, labels) if l == label)
        for label in set(labels) - {-1}
    }
    return max(seconds, key=seconds.get)


def report(pieces: list[dict], labels: np.ndarray, target: int) -> list[dict]:
    """Return per cluster: label, pieces, minutes and example lines, the target first then by size."""
    rows = []
    for label in set(labels) - {-1}:
        members = [p for p, l in zip(pieces, labels) if l == label]
        rows.append({
            "cluster": int(label), "pieces": len(members), "target": bool(label == target),
            "minutes": round(sum(p["end"] - p["start"] for p in members) / 60, 2),
            "examples": [f"{p['start']:.0f}s: {p['text']}" for p in members[:: max(len(members) // EXAMPLE_LINES, 1)][:EXAMPLE_LINES]],
        })
    return sorted(rows, key=lambda r: (not r["target"], -r["minutes"]))
