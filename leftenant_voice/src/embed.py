"""Embed every sentence piece of a voice with the ECAPA speaker model (GPU 0).

Usage: embed.py <voice>
Reads  wip/voices/<voice>/full-16k.wav and segments.json (from align.py)
Writes wip/voices/<voice>/embeddings.npy: one row per piece, in segments.json order. A piece shorter than
MIN_EMBED_SECONDS is too short for a reliable embedding and gets a row of NaN.
"""
import os
import sys

# The device must be fixed before torch is imported.
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["HF_HUB_OFFLINE"] = "1"

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from speechbrain.inference.speaker import EncoderClassifier  # noqa: E402
from speaker_group import SPEAKER_MODEL  # noqa: E402

RATE = 16000
MIN_EMBED_SECONDS = 1.0

if __name__ == "__main__":
    print("device:", torch.cuda.get_device_name(0), flush=True)
    folder = Path("wip/voices") / sys.argv[1]
    audio, _ = sf.read(folder / "full-16k.wav", dtype="float32")
    segments = json.loads((folder / "segments.json").read_text())
    model = EncoderClassifier.from_hparams(
        source=SPEAKER_MODEL, savedir="wip/speaker-model", run_opts={"device": "cuda"}
    )
    rows = np.full((len(segments), 192), np.nan, dtype=np.float32)
    for index, seg in enumerate(segments):
        if seg["end"] - seg["start"] < MIN_EMBED_SECONDS:
            continue
        wave = torch.from_numpy(audio[int(seg["start"] * RATE): int(seg["end"] * RATE)])[None].cuda()
        rows[index] = model.encode_batch(wave).squeeze().cpu().numpy()
    np.save(folder / "embeddings.npy", rows)
    print(sys.argv[1], int((~np.isnan(rows[:, 0])).sum()), "of", len(segments), "pieces embedded")
