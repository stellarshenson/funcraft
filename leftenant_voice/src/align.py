"""Turn the Nemotron windows of a voice into sentence pieces with timestamps and quality measures.

Usage: align.py <voice>
Reads  wip/voices/<voice>/asr/window-NNN.pt/.json (from transcribe.py)
Writes wip/voices/<voice>/segments.json: one record per sentence piece with
  start, end (seconds in the recording), text, tag (the window's speaker tag),
  tokens (alignment tokens of the text),
  nll (CTC loss per token of the text against the audio: low means the transcript fits the sound).
Runs on the CPU.
"""
import json
import sys
from pathlib import Path

import torch
from transformers import AutoProcessor, PreTrainedTokenizerFast

from asr_model import MODEL_ID, REVISION, SAMPLE_RATE as RATE

MAX_SECONDS = 20.0
LONG_PAUSE = 0.5
CTC_PAD = 0.1


def load_processor() -> AutoProcessor:
    """Load the processor with the alignment tokenizer from its subfolder (the automatic load picks the wrong one)."""
    processor = AutoProcessor.from_pretrained(MODEL_ID, revision=REVISION)
    cache = Path.home() / ".cache/huggingface/hub" / f"models--{MODEL_ID.replace('/', '--')}"
    folder = cache / "snapshots" / REVISION / "alignment_tokenizer"
    processor.alignment_tokenizer = PreTrainedTokenizerFast.from_pretrained(folder)
    return processor


def split_words(words: list[dict]) -> list[list[dict]]:
    """Group words into sentences, also cut at speaker-tag changes, pauses of LONG_PAUSE and 20 s."""
    pieces, current = [], [words[0]]
    for prev, word in zip(words, words[1:]):
        gap = word["start"] - prev["end"]
        if (
            word["tag"] != prev["tag"]
            or gap >= LONG_PAUSE
            or prev["text"][-1] in ".?!"
            or word["end"] - current[0]["start"] > MAX_SECONDS
        ):
            pieces.append(current)
            current = []
        current.append(word)
    return pieces + [current]


def ctc_nll(log_probs: torch.Tensor, frame_seconds: float, words: list[dict], tokenizer, blank: int) -> float:
    """CTC loss per token of the words against the head's frames around them."""
    lo = max(int((words[0]["start"] - CTC_PAD) / frame_seconds), 0)
    hi = min(int((words[-1]["end"] + CTC_PAD) / frame_seconds) + 1, len(log_probs))
    targets = [i for w in words for i in tokenizer.encode(" " + w["text"], add_special_tokens=False)]
    loss = torch.nn.functional.ctc_loss(
        log_probs[lo:hi].unsqueeze(1), torch.tensor([targets]), torch.tensor([hi - lo]), torch.tensor([len(targets)]),
        blank=blank, reduction="sum",
    )
    return float(loss) / len(targets)


def window_segments(processor, folder: Path, number: int) -> list[dict]:
    """Sentence pieces of one window, with times in the recording."""
    data = torch.load(folder / "asr" / f"window-{number:03d}.pt")
    meta = json.loads((folder / "asr" / f"window-{number:03d}.json").read_text())
    logits = data["word_timestamp_logits"]
    result = processor.align_word_timestamps([data["text"]], logits, data["input_features_mask"], data["speaker_logits"])[0]
    words = [
        {"text": c["text"], "start": c["timestamp"][0], "end": c["timestamp"][1], "tag": c["speaker"]}
        for c in result["chunks"]
    ]
    if not words:
        return []
    # one item per batch, no padding: the head's frames span the whole spectrogram
    frame_seconds = int(data["input_features_mask"].sum()) * processor.feature_extractor.hop_length / RATE / logits.shape[1]
    log_probs = logits[0].float().log_softmax(-1)
    blank = logits.shape[-1] - 1
    out = []
    for piece in split_words(words):
        start, end = piece[0]["start"] + meta["offset"], piece[-1]["end"] + meta["offset"]
        out.append({
            "window": number, "start": round(start, 3), "end": round(end, 3), "tag": piece[0]["tag"],
            "text": " ".join(w["text"] for w in piece), "tokens": sum(len(processor.alignment_tokenizer.encode(" " + w["text"], add_special_tokens=False)) for w in piece),
            "nll": ctc_nll(log_probs, frame_seconds, piece, processor.alignment_tokenizer, blank),
        })
    return out


if __name__ == "__main__":
    folder = Path("wip/voices") / sys.argv[1]
    processor = load_processor()
    segments = []
    for path in sorted((folder / "asr").glob("window-*.pt")):
        segments += window_segments(processor, folder, int(path.stem.split("-")[1]))
    (folder / "segments.json").write_text(json.dumps(segments, indent=1))
    print(sys.argv[1], len(segments), "segments")
