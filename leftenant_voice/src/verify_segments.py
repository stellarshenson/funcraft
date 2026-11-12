"""Transcribe every kept segment and reference clip again on its own and compare with its stored text.

Usage: verify_segments.py <gpu_index> <voice> [<voice> ...]
Reads  wip/voices/<voice>/metadata.csv and segments/*.wav, resources/voices/<voice>/ref-N.wav and .txt
Writes wip/voices/<voice>/verify.csv (file|wer|heard): word error rate of the fresh transcript against the stored text.
A word cut at a segment edge or a wrong transcript shows as a high rate.
"""
import os
import sys

# The device must be fixed before torch is imported.
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = sys.argv[1]
os.environ["HF_HUB_OFFLINE"] = "1"

import csv  # noqa: E402
from pathlib import Path  # noqa: E402

import librosa  # noqa: E402
import torch  # noqa: E402
from asr_model import MODEL_ID, REVISION, SAMPLE_RATE  # noqa: E402
from transformers import AutoModelForMultimodalLM, AutoProcessor  # noqa: E402
from wer import word_error_rate  # noqa: E402


def main() -> None:
    print("device:", torch.cuda.get_device_name(0), flush=True)
    processor = AutoProcessor.from_pretrained(MODEL_ID, revision=REVISION)
    model = AutoModelForMultimodalLM.from_pretrained(MODEL_ID, revision=REVISION, device_map="cuda:0", dtype=torch.bfloat16)
    for voice in sys.argv[2:]:
        folder, ref_folder = Path("wip/voices") / voice, Path("resources/voices") / voice
        with open(folder / "metadata.csv") as handle:
            clips = [(folder / "segments" / r["file"], r["text"]) for r in csv.DictReader(handle, delimiter="|")]
        clips += [(w, w.with_suffix(".txt").read_text().strip()) for w in sorted(ref_folder.glob("ref-*.wav"))]
        with open(folder / "verify.csv", "w", newline="") as out:
            writer = csv.writer(out, delimiter="|")
            writer.writerow(["file", "wer", "heard"])
            for path, text in clips:
                samples, _ = librosa.load(path, sr=SAMPLE_RATE)
                inputs = processor.apply_transcription_request(samples).to(model.device)
                outputs = model.generate(**inputs, max_new_tokens=512, do_sample=False)
                heard = processor.decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
                writer.writerow([path.name if "ref-" not in path.name else f"{voice}/{path.name}", round(word_error_rate(text, heard), 3), heard.strip()])
        print(voice, len(clips), "clips verified", flush=True)


if __name__ == "__main__":
    main()
