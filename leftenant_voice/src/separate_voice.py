"""Replace a recording's mixed audio by its voice stem (Demucs `htdemucs`, GPU 0), for recordings with music or effects.

Usage: separate_voice.py <voice>   (run in .venv-tools, after decode_audio.py)
Moves wip/voices/<voice>/full-44k.wav and full-16k.wav to mixed-44k.wav and mixed-16k.wav, then writes the
vocals stem as the new full-44k.wav and full-16k.wav. A rerun does nothing when the mixed files exist.
"""
import os
import sys

# The device must be fixed before torch is imported.
os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

from pathlib import Path  # noqa: E402

import librosa  # noqa: E402
import soundfile as sf  # noqa: E402
import torch  # noqa: E402
from demucs.apply import apply_model  # noqa: E402
from demucs.pretrained import get_model  # noqa: E402

RATE_44K, RATE_16K = 44100, 16000

if __name__ == "__main__":
    folder = Path("wip/voices") / sys.argv[1]
    if (folder / "mixed-44k.wav").exists():
        sys.exit(f"{sys.argv[1]}: already separated")
    print("device:", torch.cuda.get_device_name(0), flush=True)
    mixed, rate = sf.read(folder / "full-44k.wav", dtype="float32")
    assert rate == RATE_44K
    model = get_model("htdemucs").cuda().eval()
    assert model.samplerate == RATE_44K
    wave = torch.from_numpy(mixed)[None].repeat(2, 1)  # the model takes stereo; the recording is mono
    scale = wave.mean(0).std()
    with torch.no_grad():
        stems = apply_model(model, ((wave - wave.mean()) / scale)[None].cuda(), device="cuda", split=True)[0]
    vocals = (stems[model.sources.index("vocals")] * scale + wave.mean()).mean(0).cpu().numpy()
    for name in ("44k", "16k"):
        (folder / f"full-{name}.wav").rename(folder / f"mixed-{name}.wav")
    sf.write(folder / "full-44k.wav", vocals, RATE_44K, subtype="PCM_16")
    sf.write(folder / "full-16k.wav", librosa.resample(vocals, orig_sr=RATE_44K, target_sr=RATE_16K), RATE_16K, subtype="PCM_16")
    print(sys.argv[1], "vocals written", len(vocals) / RATE_44K, "s")
