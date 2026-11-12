"""Cosine similarity of WAV files to the centroid of each voice (ECAPA speaker model, GPU 0).

Usage: score_speaker.py <out.json> <wav> [<wav> ...]   (run in .venv-tools)
Writes out.json: {wav path: {voice: cosine similarity}} for every voice under wip/voices/.
"""
import os
import sys

# The device must be fixed before torch is imported.
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["HF_HUB_OFFLINE"] = "1"

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import librosa  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402
from speaker_group import SPEAKER_MODEL  # noqa: E402
from speechbrain.inference.speaker import EncoderClassifier  # noqa: E402

RATE = 16000

if __name__ == "__main__":
    print("device:", torch.cuda.get_device_name(0), flush=True)
    centroids = {p.parent.name: np.load(p) for p in Path("wip/voices").glob("*/centroid.npy")}
    model = EncoderClassifier.from_hparams(source=SPEAKER_MODEL, savedir="wip/speaker-model", run_opts={"device": "cuda"})
    scores = {}
    for wav in sys.argv[2:]:
        samples, _ = librosa.load(wav, sr=RATE)
        vector = model.encode_batch(torch.from_numpy(samples)[None].cuda()).squeeze().cpu().numpy()
        scores[wav] = {
            voice: float(vector @ c / (np.linalg.norm(vector) * np.linalg.norm(c))) for voice, c in centroids.items()
        }
    Path(sys.argv[1]).write_text(json.dumps(scores, indent=1))
    print(json.dumps(scores, indent=1))
