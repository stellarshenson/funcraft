"""Child process of the transcription engine: load Nemotron 3.5 Transcribe once, then transcribe each request.

Runs in the ASR interpreter (`/opt/venv/bin/python` in the image: Python 3.12, torch 2.8.0,
Transformers 5.23.0.dev0, librosa; `.venv-asr` or `ASR_PYTHON` natively), so the service's own
interpreter never imports torch or Transformers. `engine_nemotron.py` starts it. The device is fixed by
`CUDA_VISIBLE_DEVICES`, which the parent sets before this process starts; the model runs in bf16 with the
model card's request form.

Protocol, one JSON object per line:
    stdin   {"audio", "prompt"}  or  {"quit": true}
    stdout  {"ready": true} once, then {"ok": true, "text"} or {"ok": false, "error"}
`audio` is a file of mono float32 little-endian samples at 16 kHz. Library output goes to stderr; stdout
carries only protocol lines.
"""
import json
import sys

PROTOCOL = sys.stdout  # taken before the redirect below: only protocol lines use this stream
sys.stdout = sys.stderr

import numpy as np  # noqa: E402  (after the redirect, so no import or library print reaches stdout)
import torch  # noqa: E402
from asr import MODEL_ID, REVISION  # noqa: E402
from transformers import AutoModelForMultimodalLM, AutoProcessor  # noqa: E402


def main() -> None:
    """Load the model, report ready, then answer requests until quit or end of input."""
    processor = AutoProcessor.from_pretrained(MODEL_ID, revision=REVISION)
    model = AutoModelForMultimodalLM.from_pretrained(
        MODEL_ID, revision=REVISION, device_map="cuda:0", dtype=torch.bfloat16)
    print(json.dumps({"ready": True}), file=PROTOCOL, flush=True)

    for line in sys.stdin:
        request = json.loads(line)
        if request.get("quit"):
            break
        try:
            samples = np.fromfile(request["audio"], dtype="<f4")
            inputs = processor.apply_transcription_request(samples, prompt=request["prompt"]).to(model.device)
            outputs = model.generate(**inputs, max_new_tokens=8192, do_sample=False)
            text = processor.decode(outputs[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0]
            reply = {"ok": True, "text": text}
        except Exception as error:  # one failed request must not stop the worker; the parent reports it
            reply = {"ok": False, "error": f"{type(error).__name__}: {error}"}
        print(json.dumps(reply), file=PROTOCOL, flush=True)


if __name__ == "__main__":
    main()
