"""Speak a text with Fish Audio Drama 3, cloning a voice from wip/fish/refs/<voice>.wav and .txt.

Each paragraph (blank-line separated; lines starting with '#' are comments) is one request in one pass, so a
style prefix such as [angry] covers its whole paragraph. Paragraphs are joined with a pause of PAUSE_SECONDS,
as src/speak.py does for Ming. Each paragraph is also written as wip/fish/paragraphs/<voice>/p-NN.wav. A JSON file next to the render (an MP3 when the path is under out/, see audio_out.py) records synthesis time, audio length and peak GPU memory.

Usage (GPU chosen by the caller, see fish.mk):
    python src/fish/speak_fish.py --voice dijkstra --file texts/fish/inspiring-speech-fish.txt --out out/fish/x.mp3
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import torch
from huggingface_hub import snapshot_download

from fish_speech.models.text2semantic.inference import (
    decode_to_audio,
    encode_audio,
    generate_long,
    init_model,
    load_codec_model,
    resolve_codec_path,
)

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from audio_out import write_render  # noqa: E402
MODEL = "fishaudio/drama-3"
REVISION = "78e5ab79e49aa9a25abe8799eff2c4d73a1c3216"
PAUSE_SECONDS = 0.4
PEAK_LIMIT = 0.98
SEED = 42


def parse_paragraphs(path: Path) -> list[str]:
    """Return the paragraphs of a text file without comment lines, each opened by the speaker tag."""
    lines = [line for line in path.read_text().splitlines() if not line.startswith("#")]
    blocks = re.split(r"\n\s*\n", "\n".join(lines))
    return ["<|speaker:0|> " + " ".join(block.split()) for block in blocks if block.strip()]


def main() -> None:
    """Render the text and write the render and its timing file."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    refs = ROOT / "wip/fish/refs"
    parts = ROOT / "wip/fish/paragraphs" / args.voice
    parts.mkdir(parents=True, exist_ok=True)
    ref_text = (refs / f"{args.voice}.txt").read_text().strip()
    paragraphs = parse_paragraphs(ROOT / args.file)

    checkpoint = Path(snapshot_download(MODEL, revision=REVISION, local_files_only=True))
    start = time.time()
    model, decode_one_token = init_model(checkpoint, "cuda:0", torch.bfloat16)
    codec = load_codec_model(resolve_codec_path(checkpoint), str(model.device), model.dtype)
    prompt_tokens = encode_audio(refs / f"{args.voice}.wav", codec, str(model.device)).cpu()
    load_seconds = time.time() - start

    def speak(text: str) -> torch.Tensor:
        """Generate the codes of one paragraph in one pass."""
        responses = generate_long(
            model=model, device="cuda:0", decode_one_token=decode_one_token, text=text, num_samples=1,
            max_new_tokens=0, top_p=0.7, top_k=30, temperature=0.7, compile=False, iterative_prompt=True,
            chunk_length=200, single_chunk=True, prompt_text=[ref_text], prompt_tokens=[prompt_tokens],
        )
        return torch.cat([r.codes for r in responses if r.action == "sample"], dim=1)

    speak("<|speaker:0|> Ready.")  # warm-up: captures the CUDA graphs, which would otherwise count as synthesis time
    torch.manual_seed(SEED)
    torch.cuda.manual_seed(SEED)
    torch.cuda.reset_peak_memory_stats()
    pieces, synth_seconds = [], 0.0
    pause = np.zeros(int(PAUSE_SECONDS * codec.sample_rate), dtype=np.float32)
    for number, text in enumerate(paragraphs, 1):
        start = time.time()
        codes = speak(text)
        synth_seconds += time.time() - start
        audio = decode_to_audio(codes.to(model.device), codec).cpu().float().numpy()
        sf.write(parts / f"p-{number:02d}.wav", audio, codec.sample_rate)
        pieces += [audio, pause]
        print(f"paragraph {number}: {len(audio) / codec.sample_rate:.1f}s", flush=True)

    joined = np.concatenate(pieces[:-1])
    joined *= min(1.0, PEAK_LIMIT / np.abs(joined).max())
    out = write_render(args.out, joined, codec.sample_rate)
    stats = {
        "voice": args.voice, "audio_seconds": len(joined) / codec.sample_rate, "synth_seconds": synth_seconds,
        "load_seconds": load_seconds, "peak_gpu_gib": torch.cuda.max_memory_allocated() / 2**30,
    }
    stats["rtf"] = stats["synth_seconds"] / stats["audio_seconds"]
    out.with_suffix(".json").write_text(json.dumps(stats, indent=1))
    print(stats, flush=True)


if __name__ == "__main__":
    main()
