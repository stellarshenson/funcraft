"""Transcribe WAV files with Nemotron 3.5 Transcribe.

Usage: score_words.py <gpu_index> <out.json> <wav> [<wav> ...]   (run in .venv-tools; Nemotron needs GPU 2)
Writes out.json: {wav path: transcript}.
"""
import os
import sys

# The device must be fixed before torch is imported.
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[1]
os.environ["HF_HUB_OFFLINE"] = "1"

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import librosa  # noqa: E402
import torch  # noqa: E402
from asr_model import MODEL_ID, REVISION, SAMPLE_RATE  # noqa: E402
from transformers import AutoModelForMultimodalLM, AutoProcessor  # noqa: E402

if __name__ == "__main__":
    print("device:", torch.cuda.get_device_name(0), flush=True)
    processor = AutoProcessor.from_pretrained(MODEL_ID, revision=REVISION)
    model = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, revision=REVISION, device_map="cuda:0", dtype=torch.bfloat16)
    heard = {}
    for wav in sys.argv[3:]:
        samples, _ = librosa.load(wav, sr=SAMPLE_RATE)
        inputs = processor.apply_transcription_request(samples).to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=1024, do_sample=False)
        heard[wav] = processor.decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0].strip()
        print(Path(wav).name, "->", heard[wav], flush=True)
    Path(sys.argv[2]).write_text(json.dumps(heard, indent=1))
