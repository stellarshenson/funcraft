# Transcription correction

Findings from 2026-11-13; the service runs Nemotron 3.5 Transcribe greedy, with context terms only.

| Option | How it works | Cost | State |
|---|---|---|---|
| Context terms | names and terms in the prompt; fixed the measured name errors (Avallac'h, Ciri) | none | in the service |
| LLM post-correction | a small instruct LLM (8B bf16 or 14B int8 fits the free 24 GB card) rewrites the draft under a strict prompt with the context terms; draft-verify applied to text | one small model | not built; needs a measured WER win |
| ROVER voting | align two passes, vote per word; two runs of the same audio differed by mean WER 0.020 | about 2x compute | not built |
| N-best rescoring | score alternatives with a stronger language model; the Transformers runtime exposes no n-best list | a runtime change | not available |
| Beam search | `num_beams` at temperature 0 | none | untested |
| Speculative decoding | speed only; it does not correct | - | out of scope |

No standard open model is purpose-built for this; the practice is an instruct LLM or a small seq2seq model fine-tuned on ASR-error pairs.

Decision: keep greedy decoding with context terms. Accept a correction pass only with a measured WER win on the 62-minute recording (`src/wer.py`); ROVER is the fallback against LLM-invented edits.
