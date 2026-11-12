"""Transcribe WAV files with Nemotron 3.5 Transcribe and keep the word timestamps.

Usage: asr_words.py <gpu_index> <out.json> <wav> [<wav> ...]   (run in .venv-tools from the project folder)
Writes out.json: {wav path: {"text": transcript, "words": [{"text", "start", "end"}]}} with times in seconds.
"""
import os
import sys

# The device must be fixed before torch is imported.
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[1]
os.environ["HF_HUB_OFFLINE"] = "1"
sys.path.insert(0, "src")

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import librosa  # noqa: E402
import torch  # noqa: E402
from align import load_processor  # noqa: E402
from asr_model import MODEL_ID, REVISION, SAMPLE_RATE  # noqa: E402
from transformers import AutoModelForMultimodalLM  # noqa: E402

if __name__ == "__main__":
    processor = load_processor()
    model = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, revision=REVISION, device_map="cuda:0", dtype=torch.bfloat16)
    result = {}
    for wav in sys.argv[3:]:
        samples, _ = librosa.load(wav, sr=SAMPLE_RATE)
        inputs = processor.apply_transcription_request(samples).to(model.device)
        outputs = model.generate(**inputs, max_new_tokens=1024, do_sample=False, return_word_timestamp_logits=True)
        text = processor.decode(outputs.sequences[:, inputs.input_ids.shape[1]:], skip_special_tokens=False)[0]
        text = text.replace(processor.tokenizer.pad_token, "")
        aligned = processor.align_word_timestamps(
            [text], outputs.word_timestamp_logits.cpu(), inputs.input_features_mask.cpu(), outputs.speaker_logits.cpu()
        )[0]
        words = [{"text": c["text"], "start": c["timestamp"][0], "end": c["timestamp"][1]} for c in aligned["chunks"]]
        result[wav] = {"text": processor.decode(outputs.sequences[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0].strip(), "words": words}
        print(Path(wav).name, len(words), "words", flush=True)
    Path(sys.argv[2]).write_text(json.dumps(result, indent=1))
