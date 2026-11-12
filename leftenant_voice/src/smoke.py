"""Speak one English sentence in the built-in voice of Ming-3.0-tts-0.5B and log device, timing and VRAM.

One warm-up call is discarded, then three calls are timed. Writes wip/smoke.wav. Run through `make smoke`; the optional argument sets the attention (default `flash_attention_2`).
"""
import sys
import time

from ming_loader import CODE, ROOT, load_model  # sets GPU and offline mode before torch loads

import torch  # noqa: E402

TEXT = "Soldiers of the line, hold your ground, for tonight we stand together."
PROMPT = CODE / "data" / "voice_presets" / "voice_audio" / "lingguang.wav"
PROMPT_TEXT = "诶，你今天有空吗？我们能不能聊聊这件事啊？"
OUTPUT = ROOT / "wip" / "smoke.wav"

print("torch:", torch.__version__)
start = time.time()
model = load_model(sys.argv[1] if len(sys.argv) > 1 else "flash_attention_2")
print(f"load_seconds: {time.time() - start:.2f}")

import soundfile as sf  # noqa: E402


def speak() -> tuple[float, float]:
    """Speak the smoke sentence once and return (synthesis seconds, audio seconds)."""
    start = time.time()
    model.synthesize(
        task="TTS", language_id="English", text=TEXT,
        prompt_wav_path=str(PROMPT), prompt_text=PROMPT_TEXT,
        use_spk_emb=True, output_path=str(OUTPUT),
    )
    seconds = time.time() - start
    audio, rate = sf.read(OUTPUT)
    return seconds, len(audio) / rate


speak()  # warm-up, discarded
for call in range(1, 4):
    synth_seconds, seconds = speak()
    print(f"call {call}: synth_seconds {synth_seconds:.2f} audio_seconds {seconds:.2f} rtf {synth_seconds / seconds:.3f}")
print(f"max_memory_allocated_gb: {torch.cuda.max_memory_allocated() / 1e9:.2f}")
