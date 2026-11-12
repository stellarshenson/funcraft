"""Child process of the auk-flash engine: load AuK-Flash once, then speak each JSON request.

Runs in `.venv-auk` (Python 3.10), so AuK and its Qwen text encoder never enter the service's interpreter.
`engine_auk.py` starts it. The method is the trial's (`wip/tts-trial/auk/speak_auk.py`): runs of whole
sentences under the model's LIMIT_SECONDS, 0.4 s pauses between runs, the peak held at 0.98, seed 42.

Protocol, one JSON object per line:
    stdin   {"text", "voice", "out"}  or  {"quit": true}
    stdout  {"ready", "rate", "load_seconds"} once, then {"ok", "rate", "seconds", "audio_seconds"}
            or {"ok": false, "error"}
`out` receives the samples as mono float32 little-endian, so no audio library is needed on either side.
Library output goes to stderr; stdout carries only protocol lines.
"""
import argparse
import importlib.util
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import torch
from huggingface_hub import snapshot_download

from auk.infer.infer_auk import AukInfer, get_gen_duration

PROTOCOL = sys.stdout  # taken before the redirect below: only protocol lines use this stream
sys.stdout = sys.stderr


def load_trial(path: Path):
    """The trial script's constants and helpers, loaded by path because it is not a package.

    Args:
        path: `wip/tts-trial/auk/speak_auk.py`.

    Returns:
        The imported module.
    """
    spec = importlib.util.spec_from_file_location("speak_auk_trial", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def voice_files(voices_dir: Path, voice: str) -> tuple[Path, str]:
    """The reference recording of `voice` and its transcript.

    Raises:
        ValueError: no `<voice>.wav` + `<voice>.txt` pair in the folder.
    """
    wav = voices_dir / f"{voice}.wav"
    transcript = voices_dir / f"{voice}.txt"
    if not wav.is_file() or not transcript.is_file():
        known = sorted(p.stem for p in voices_dir.glob("*.wav") if p.with_suffix(".txt").exists())
        raise ValueError(f"unknown voice {voice!r}; available: {known}")
    return wav, transcript.read_text().strip()


def speak(engine: AukInfer, trial, wav: Path, ref_text: str, text: str) -> np.ndarray:
    """Speak the text the way the trial does: one request per run of sentences, then level and join.

    Args:
        engine: the loaded AuK model.
        trial: the trial module, for its sentence rules and constants.
        wav: reference recording of the voice.
        ref_text: transcript of the reference.
        text: paragraphs separated by blank lines.

    Returns:
        Mono float32 samples at the engine's sample rate.

    Raises:
        ValueError: the text has no words.
    """
    ref_seconds = get_gen_duration(audio=str(wav))
    ref_bytes = len(ref_text.encode())
    pause = torch.zeros(1, int(trial.PAUSE_SECONDS * engine.target_sample_rate))
    pieces: list[torch.Tensor] = []
    for paragraph in [p for p in re.split(r"\n\s*\n", text) if p.strip()]:
        for run in trial.runs_of_sentences(paragraph, ref_seconds, ref_bytes):
            seconds = get_gen_duration(str(wav), ref_text, run)
            messages = [{"role": "user", "content": [
                {"type": "text", "text": trial.TEMPLATE.format(text=run)},
                {"type": "audio", "audio": str(wav)}]}]
            audio, _ = engine.generate(messages, gen_seconds=seconds, seed=trial.SEED)
            pieces += [audio, pause]
    if not pieces:
        raise ValueError("the text has no words to speak")
    joined = torch.cat(pieces[:-1], dim=-1)
    joined *= min(1.0, trial.PEAK_LIMIT / joined.abs().max().item())
    return joined.detach().cpu().float().numpy().reshape(-1)


def main() -> None:
    """Load the model, report ready, then answer requests until quit or end of input."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--trial", type=Path, required=True)
    parser.add_argument("--voices-dir", type=Path, required=True)
    parser.add_argument("--model", default="auk-flash", choices=("auk", "auk-flash"))
    args = parser.parse_args()

    trial = load_trial(args.trial)
    repo, revision, checkpoint = trial.MODELS[args.model]
    snapshot = Path(snapshot_download(repo, revision=revision, local_files_only=True))
    qwen = snapshot_download(trial.QWEN[0], revision=trial.QWEN[1], local_files_only=True)
    start = time.time()
    engine = AukInfer(str(snapshot / "config.yaml"), str(snapshot / checkpoint), qwen_path=qwen, device="cuda")
    print(json.dumps({"ready": True, "rate": engine.target_sample_rate,
                      "load_seconds": round(time.time() - start, 1)}), file=PROTOCOL, flush=True)

    for line in sys.stdin:
        request = json.loads(line)
        if request.get("quit"):
            break
        start = time.time()
        try:
            wav, ref_text = voice_files(args.voices_dir, request["voice"])
            samples = speak(engine, trial, wav, ref_text, request["text"])
            samples.astype("<f4").tofile(request["out"])
            reply = {"ok": True, "rate": engine.target_sample_rate, "seconds": round(time.time() - start, 2),
                     "audio_seconds": round(len(samples) / engine.target_sample_rate, 2)}
        except Exception as error:  # one failed request must not stop the worker; the parent reports it
            reply = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        print(json.dumps(reply), file=PROTOCOL, flush=True)


if __name__ == "__main__":
    main()
