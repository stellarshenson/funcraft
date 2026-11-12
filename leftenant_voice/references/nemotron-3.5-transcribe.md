# Nemotron 3.5 Transcribe

`leftenant_voice` transcribes its voice recordings with NVIDIA Nemotron 3.5 Transcribe (released 2026-11-01). The facts below are what this workstation measured on 2026-11-06, transcribing 62.4 minutes of game dialogue (Dijkstra and Vesemir recordings).

## Versions

| Hugging Face id | Precision | Size | Fits |
|---|---|---:|---|
| `nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B` | bf16 | 67.5 GB | RTX PRO 5000 72 GB beside the display (used); RTX PRO 6000 96 GB |
| `nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-FP8` | FP8 | 34.7 GB | RTX PRO 5000, RTX PRO 6000 |
| `nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-NVFP4` | NVFP4 | 21.6 GB | all three cards, RTX PRO 4000 24 GB only with little working memory left |
| `nvidia/NVIDIA-Nemotron-3.5-Transcribe-30B-A4B-DFlash2` | not checked | not checked | not checked |

- The model is a mixture of experts with 30B parameters, 4B active per step, with Mamba layers
- Revision used: `c17667641642c4265ff2b7037dd101b7d4567634` (bf16)
- Hugging Face tags the licence as `other`; the terms were not read
- The authors state 40 languages, recordings of up to 1 hour, speaker labels and timestamps; other transcription models are compared in [transcription-models.md](transcription-models.md)

## Running it

- Runtime: Hugging Face Transformers `5.23.0.dev0` built from git, torch `2.7.1+cu128`, in `.venv-tools`
- Load: `AutoProcessor` and `AutoModelForMultimodalLM.from_pretrained(..., revision=..., device_map="cuda:0", dtype=torch.bfloat16)`; request: `processor.apply_transcription_request(samples, prompt=...)`, then `model.generate(..., return_word_timestamp_logits=True)`
- The cache holds the weights without `refs/main`: pass `revision` with `HF_HUB_OFFLINE=1`, or the load fails with "couldn't find them in the cached files"
- The audio front end needs `librosa`
- Without `mamba_ssm` and `causal_conv1d`, Transformers uses its slower reference PyTorch code for the Mamba layers; the results are correct
- Script: `src/transcribe.py` (GPU index as the first argument, then the voice names); input cut into windows of about 2 minutes

## Measured

| Measure | Value |
|---|---|
| GPU | RTX PRO 5000 72GB (nvidia-smi index 2), bf16 |
| Peak memory | 62.4 GiB allocated; the card showed 65.7 GB used with the display |
| Speed | 32 windows, 3,747 s of audio in 895 s: 4.19 times faster than real time |
| Consistency | a second transcription of every kept clip differed from the first by a mean word error rate of 0.020 |
| Speaker labels | every 2-minute window carried one label, `<spk:0>`, even where other characters speak; speakers were separated with ECAPA speaker embeddings instead |
| Names | misheard names: Avallac'h as "Avalorax", Ciri as "Syria", Eskel probably as "Esco's"; character names in lower case ("geralt", "triss") |
