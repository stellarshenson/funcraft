"""Speak a text in a cloned voice with Ming-3.0-tts-0.5B on GPU 0.

Usage: speak.py --voice <name> (--text "<text>" | --text-file <path>) --out <path> [--ref <n>]
         [--emotion <e> | --speed <s> --pitch <p> --volume <v>] [--paragraphs-dir <dir>]
The voice is a folder under resources/voices/ with ref-N.wav and ref-N.txt. Without --ref, the clips named in
that folder's chosen.txt are used: the first number for task TTS, the optional second number for EMOTION and BASIC
(they clone from the audio alone, so another clip can match the voice better); --ref sets both. The text is split into paragraphs (see speak_text.py: directives, inline tags,
whole-text options) and each paragraph into sentences; the sentences are spoken one by one and joined with a pause
of PAUSE_SECONDS into one render at the model's sample rate (an MP3 when the path is under out/, see audio_out.py). It is scaled down if its peak exceeds PEAK_LIMIT.
--paragraphs-dir also writes each paragraph as p-NN.wav (before the scaling) and its task in tasks.json.
"""
import argparse
import json
import time
from pathlib import Path

from ming_loader import LAUNCH_DIR, ROOT, load_model  # sets GPU and offline mode before torch loads

import torch  # noqa: E402
import torchaudio  # noqa: E402
from audio_out import write_render  # noqa: E402
from speak_text import Paragraph, TextError, parse_paragraphs, split_sentences  # noqa: E402

PAUSE_SECONDS = 0.4
PEAK_LIMIT = 0.98  # the model can output samples above full scale


def parse_args() -> argparse.Namespace:
    """Read the command line."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--voice", required=True)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--text")
    source.add_argument("--text-file", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--ref", type=int)
    parser.add_argument("--emotion")
    parser.add_argument("--speed")
    parser.add_argument("--pitch")
    parser.add_argument("--volume")
    parser.add_argument("--paragraphs-dir", type=Path)
    return parser.parse_args()


def absolute(path: Path) -> Path:
    """Resolve a relative path against the folder `make` was started in."""
    return path if path.is_absolute() else LAUNCH_DIR / path


def speak_paragraph(model, paragraph: Paragraph, ref_wav: Path, ref_text: str, pause: torch.Tensor) -> torch.Tensor:
    """Speak the sentences of one paragraph with its task and join them with pauses."""
    # TTS clones from the clip and its transcript; EMOTION and BASIC take the voice from the audio alone
    clone = {"prompt_text": ref_text} if paragraph.task == "TTS" else {"controls": paragraph.controls}
    pieces = []
    for sentence in split_sentences(paragraph.text):
        waveform = model.synthesize(
            task=paragraph.task, language_id="English", text=sentence,
            prompt_wav_path=str(ref_wav), use_spk_emb=True, **clone,
        ).float().cpu()
        pieces += [waveform, pause]
    return torch.cat(pieces[:-1], dim=-1)


def main() -> None:
    """Load the model once, speak every paragraph and write the joined WAV."""
    args = parse_args()
    folder = ROOT / "resources" / "voices" / args.voice
    chosen = [args.ref] * 2 if args.ref else [int(n) for n in (folder / "chosen.txt").read_text().split()]
    ref_tts, ref_controlled = chosen[0], chosen[-1]
    text = args.text if args.text is not None else absolute(args.text_file).read_text()
    whole_text = {k: v for k in ("emotion", "speed", "pitch", "volume") if (v := getattr(args, k))}
    try:
        paragraphs = parse_paragraphs(text, whole_text)
    except TextError as error:
        raise SystemExit(str(error)) from error

    model = load_model()
    pause = torch.zeros(1, int(PAUSE_SECONDS * model.sample_rate))
    spoken = []
    start = time.time()
    for paragraph in paragraphs:
        ref = ref_tts if paragraph.task == "TTS" else ref_controlled
        ref_text = (folder / f"ref-{ref}.txt").read_text().strip()
        spoken.append(speak_paragraph(model, paragraph, folder / f"ref-{ref}.wav", ref_text, pause))
        print(f"line {paragraph.line} {paragraph.task} {spoken[-1].shape[-1] / model.sample_rate:.1f}s", flush=True)
    synth_seconds = time.time() - start
    if args.paragraphs_dir:
        save_paragraphs(absolute(args.paragraphs_dir), paragraphs, spoken, model.sample_rate)
    joined = torch.cat([p for waveform in spoken for p in (waveform, pause)][:-1], dim=-1)
    joined *= min(1.0, PEAK_LIMIT / joined.abs().max().item())
    out = write_render(absolute(args.out), joined[0].numpy(), model.sample_rate)
    audio_seconds = joined.shape[-1] / model.sample_rate
    print(f"synth_seconds {synth_seconds:.1f} audio_seconds {audio_seconds:.1f} rtf {synth_seconds / audio_seconds:.2f}")


def save_paragraphs(folder: Path, paragraphs: list[Paragraph], spoken: list[torch.Tensor], rate: int) -> None:
    """Write each paragraph as p-NN.wav and the task list as tasks.json."""
    folder.mkdir(parents=True, exist_ok=True)
    for number, waveform in enumerate(spoken, 1):
        torchaudio.save(str(folder / f"p-{number:02d}.wav"), waveform, sample_rate=rate)
    (folder / "tasks.json").write_text(json.dumps(
        [{"number": n, "line": p.line, "task": p.task, "controls": p.controls, "text": p.text}
         for n, p in enumerate(paragraphs, 1)], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
