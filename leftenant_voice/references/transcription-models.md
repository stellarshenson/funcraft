# Transcription models

This note compares speech-to-text models. The figures come from the owner's comparison of 2026-11-06; "not stated" means the release did not give the value. `leftenant_voice` uses Nemotron 3.5 Transcribe; its measured behaviour on this workstation is in [nemotron-3.5-transcribe.md](nemotron-3.5-transcribe.md).

| Model | Issue | Open weights | Languages | Real-time | Stated figure |
|---|---|---|---|---|---|
| Nemotron 3.5 Transcribe (NVIDIA) | 2026-11-01 | yes | 40 | not stated | recordings up to 1 h, speaker labels, timestamps |
| Bark 3.0 (Underdog) | 2026-10-25 | yes | English only | not stated | 163 MB |
| Phonon-2 (Fermion Research) | 2026-10-04 | yes | English only | not stated | 164 MB, 1 h of audio in about 20 s on a MacBook Air |
| Whistle (Cactus) | 2026-10-04 | not stated | 7 | not stated | 16.9 MB, runs on a device CPU |
| R2T2 | 2026-09-20 | yes | English and Mandarin shown | yes | none |
| Gemini 3.5 Transcribe (Google) | 2026-08-30 | not stated, hosted | 85+ | yes | none |
| CrisperWhisper 2.0 (Nyra Labs) | 2026-08-02 | not stated | several | not stated | word-level timing |
