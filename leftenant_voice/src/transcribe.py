"""Transcribe the recordings with NVIDIA Nemotron 3.5 Transcribe: speaker tags and word timestamps.

Usage: transcribe.py <gpu_index> <voice> [<voice> ...]
Reads  wip/voices/<voice>/full-16k.wav
Writes wip/voices/<voice>/asr/window-NNN.pt (text and alignment tensors) and window-NNN.json
(offset and length in seconds), one pair per window of about WINDOW_SECONDS. align.py reads them.
Windows are cut at quiet points. The model labels speakers inside a window only, so the
speaker groups across windows are matched later with speaker embeddings.
"""
import os
import sys

# The device must be fixed before torch is imported.
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[1]
os.environ["HF_HUB_OFFLINE"] = "1"

import json  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from asr_model import MODEL_ID, REVISION, SAMPLE_RATE  # noqa: E402
from transformers import AutoModelForMultimodalLM, AutoProcessor  # noqa: E402

WINDOW_SECONDS = int(os.environ.get("WINDOW_SECONDS", "120"))
SEARCH_SECONDS = 15
PROMPT = (
    "Transcribe this audio with punctuation and capitalization. Include all spoken words and verbal "
    "fillers. Write numbers in their standard written form. Put speaker tags <spk:0> <spk:1> <spk:2> "
    "<spk:3> on the transcription."
)


def window_bounds(audio: np.ndarray) -> list[tuple[int, int]]:
    """Return sample ranges of about WINDOW_SECONDS, each cut at the quietest 0.5 s near its end."""
    step, bounds, start = SAMPLE_RATE // 2, [], 0
    while len(audio) - start > (WINDOW_SECONDS + SEARCH_SECONDS) * SAMPLE_RATE:
        lo = start + (WINDOW_SECONDS - SEARCH_SECONDS) * SAMPLE_RATE
        hi = start + (WINDOW_SECONDS + SEARCH_SECONDS) * SAMPLE_RATE
        frames = np.abs(audio[lo:hi][: (hi - lo) // step * step]).reshape(-1, step).mean(1)
        cut = lo + int(frames.argmin()) * step + step // 2
        bounds.append((start, cut))
        start = cut
    bounds.append((start, len(audio)))
    return bounds


def transcribe_window(model, processor, samples: np.ndarray, target: Path) -> str:
    """Transcribe one window; save its text and alignment tensors to `target` (.pt) and return the text."""
    inputs = processor.apply_transcription_request(samples, prompt=PROMPT).to(model.device)
    outputs = model.generate(
        **inputs, max_new_tokens=8192, do_sample=False, return_word_timestamp_logits=True
    )
    text = processor.decode(outputs.sequences[:, inputs.input_ids.shape[1]:], skip_special_tokens=False)[0]
    text = text.replace(processor.tokenizer.pad_token, "")
    torch.save(
        {
            "text": text,
            "word_timestamp_logits": outputs.word_timestamp_logits.cpu(),
            "input_features_mask": inputs.input_features_mask.cpu(),
            "speaker_logits": outputs.speaker_logits.cpu(),
        },
        target,
    )
    return text


def main() -> None:
    print("device:", torch.cuda.get_device_name(0), flush=True)
    processor = AutoProcessor.from_pretrained(MODEL_ID, revision=REVISION)
    model = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, revision=REVISION, device_map="cuda:0", dtype=torch.bfloat16)
    for voice in sys.argv[2:]:
        folder = Path("wip/voices") / voice
        (folder / "asr").mkdir(exist_ok=True)
        audio, rate = sf.read(folder / "full-16k.wav", dtype="float32")
        assert rate == SAMPLE_RATE
        for number, (start, end) in enumerate(window_bounds(audio)):
            target = folder / "asr" / f"window-{number:03d}.pt"
            if target.exists():
                continue
            began = time.time()
            transcribe_window(model, processor, audio[start:end], target)
            (folder / "asr" / f"window-{number:03d}.json").write_text(
                json.dumps({"offset": start / SAMPLE_RATE, "seconds": (end - start) / SAMPLE_RATE})
            )
            print(voice, number, f"{(end - start) / SAMPLE_RATE:.0f}s audio in {time.time() - began:.0f}s, peak {torch.cuda.max_memory_allocated() / 2**30:.1f} GiB", flush=True)


if __name__ == "__main__":
    main()
