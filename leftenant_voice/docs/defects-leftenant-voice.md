# Defects - leftenant_voice

Faults seen in the S2 Pro service, its renderer and its output. Every read and write goes through `pm-tools`.

## Authors

- `@kj` Konrad Jelen

## Output `OUTPUT`

MP3 files and levels: every render an MP3, no decode above full scale, the service's MP3

- log: 2026-11-09T01:29:49Z @kj category created

- [x] `DEF-OUTPUT-1-PEAK` **MP3s decode above full scale** - MAJOR; three delivered MP3s decode above full scale, peaks auk 1.0268, auk-flash 1.0103, define-scottish 1.0104, though their WAV peak was 0.98; cause: no headroom before MP3 encoding; fix: scale to -1 dBFS in src/audio_out.py and make mp3
  - evidence: the repro now prints [0.9228, 0.8977, 0.9156]; all 35 out/ MP3s decode at most 0.9962; make test 31 passed and make test-functional 11 passed; tmp/workflows/goal-trackers/peaks-after.txt
  - repro: .venv-tools/bin/python -c "import soundfile as sf; print([round(float(abs(sf.read(f)[0]).max()), 4) for f in ['out/trial/status-grimaldus-auk.mp3','out/trial/status-grimaldus-auk-flash.mp3','out/trial/status-grimaldus-define-scottish.mp3']])" prints [0.9228, 0.8977, 0.9156] after the fix; before it printed [1.0268, 1.0103, 1.0104]
  - test-tags: FUNCTIONAL
  - root-cause: 2026-11-09T01:29:49Z @kj write_render and the make mp3 rule feed libmp3lame at the WAV peak of 0.98; MP3 decoding overshoots by up to 0.05, so the decoded peak passes 1.0
  - log: 2026-11-09T01:29:49Z @kj added
  - log: 2026-11-09T01:30:43Z @kj edited repro "decode out/trial/status-grimaldus-auk.mp3, -auk-flash.mp3 and -define-scottish.mp3 and read the peak sample; recorded in tmp/workflows/tts-trial/verify.json" -> ".venv-tools/bin/python -c "import soundfile as sf; print([float(abs(sf.read(f)[0]).max()) for f in ['out/trial/status-grimaldus-auk.mp3','out/trial/status-grimaldus-auk-flash.mp3','out/trial/status-grimaldus-define-scottish.mp3']])" prints [1.0268, 1.0103, 1.0104]"
  - log: 2026-11-09T01:30:43Z @kj reproduced: soundfile peaks [1.0268, 1.0103, 1.0104]
  - log: 2026-11-09T01:31:54Z @kj edited repro ".venv-tools/bin/python -c "import soundfile as sf; print([float(abs(sf.read(f)[0]).max()) for f in ['out/trial/status-grimaldus-auk.mp3','out/trial/status-grimaldus-auk-flash.mp3','out/trial/status-grimaldus-define-scottish.mp3']])" prints [1.0268, 1.0103, 1.0104]" -> ".venv-tools/bin/python -c "import soundfile as sf; print([round(float(abs(sf.read(f)[0]).max()), 4) for f in ['out/trial/status-grimaldus-auk.mp3','out/trial/status-grimaldus-auk-flash.mp3','out/trial/status-grimaldus-define-scottish.mp3']])" prints [1.0268, 1.0103, 1.0104]"
  - log: 2026-11-09T02:41:54Z @kj closed: fixed: with_mp3_headroom in src/audio_out.py and the Makefile mp3 rule hold the encoded peak at -1 dBFS; the three delivered files were regenerated from their source WAVs
  - log: 2026-11-09T02:43:32Z @kj edited repro ".venv-tools/bin/python -c "import soundfile as sf; print([round(float(abs(sf.read(f)[0]).max()), 4) for f in ['out/trial/status-grimaldus-auk.mp3','out/trial/status-grimaldus-auk-flash.mp3','out/trial/status-grimaldus-define-scottish.mp3']])" prints [1.0268, 1.0103, 1.0104]" -> ".venv-tools/bin/python -c "import soundfile as sf; print([round(float(abs(sf.read(f)[0]).max()), 4) for f in ['out/trial/status-grimaldus-auk.mp3','out/trial/status-grimaldus-auk-flash.mp3','out/trial/status-grimaldus-define-scottish.mp3']])" prints [0.9228, 0.8977, 0.9156] after the fix; before it printed [1.0268, 1.0103, 1.0104]"; reason: the recorded output changed when the defect was fixed
  - log: 2026-11-09T02:44:12Z @kj edited evidence "the repro now prints [0.9228, 0.8977, 0.9156]; all 34 out/ MP3s decode at most 0.9962; make test 31 passed and make test-functional 11 passed; tmp/workflows/goal-trackers/peaks-after.txt" -> "the repro now prints [0.9228, 0.8977, 0.9156]; all 35 out/ MP3s decode at most 0.9962; make test 31 passed and make test-functional 11 passed; tmp/workflows/goal-trackers/peaks-after.txt"; reason: the new Fish render adds one MP3 to the we measured
- [x] `DEF-OUTPUT-3-FISH-MP3` **Fish render through the MP3 writer never run** - MEDIUM; the Fish render path through src/audio_out.py write_render has never been executed; the out/fish MP3s were made by make mp3 from WAVs; fix: run make -f fish.mk speak to an .mp3 and measure it
  - evidence: the render wrote 114.738 s, decoded peak 0.9028, ffprobe mp3, Nemotron WER 0.0094; fix3-fish-render.log, fix3-fish-probe.json, fix3-fish-measure.txt; both suites green after
  - repro: make -f fish.mk speak writes the MP3 and its JSON in the same run; the delivered pairs show MP3 2026-11-07 14:44 against JSON 2026-11-06 19:25 to 2026-11-07 14:05, so make mp3 converted them
  - test-tags: FUNCTIONAL
  - root-cause: 2026-11-09T01:29:49Z @kj the mp3-out change tested write_render on src/speak.py and a scratch file, not on src/fish/speak_fish.py; the out/fish renders predate it and make mp3 converted them
  - log: 2026-11-09T01:29:49Z @kj added
  - log: 2026-11-09T01:30:43Z @kj edited repro "compare the mtimes of out/fish/*.mp3 (14:44) with their .json sidecars (06:19-08:42): the MP3s were converted later by make mp3, not written by write_render" -> "ls -l --time-style='+%Y-%m-%d %H:%M' out/fish/*.mp3 out/fish/*.json: every MP3 is 2026-11-07 14:44, every JSON 2026-11-06 19:25 to 2026-11-07 14:05; make mp3 converted them"
  - log: 2026-11-09T01:30:43Z @kj confirmed: every out/fish MP3 is 2026-11-07 14:44, every JSON 2026-11-06 19:25 to 2026-11-07 14:05; mp3-out records make -f fish.mk speak was not run
  - log: 2026-11-09T02:41:57Z @kj closed: fixed: make -f fish.mk speak wrote out/fish/inspiring-speech-grimaldus-fish-write-render.mp3 and its JSON, so the Fish path through write_render has run
  - log: 2026-11-09T02:43:32Z @kj edited repro "ls -l --time-style='+%Y-%m-%d %H:%M' out/fish/*.mp3 out/fish/*.json: every MP3 is 2026-11-07 14:44, every JSON 2026-11-06 19:25 to 2026-11-07 14:05; make mp3 converted them" -> "make -f fish.mk speak writes the MP3 and its JSON in the same run; the delivered pairs show MP3 2026-11-07 14:44 against JSON 2026-11-06 19:25 to 2026-11-07 14:05, so make mp3 converted them"; reason: the Fish path now writes its own MP3

## Docker `DOCKER`

The image, its compose stack and the make targets around them

- log: 2026-11-09T01:29:49Z @kj category created

- [x] `DEF-DOCKER-2-MP3-STEP` **AuK render leaves a WAV in out/** - MEDIUM; an AuK render to out/ keeps its WAV because auk.mk has no make mp3 step; fix: run make mp3 at the end of the auk.mk speak target; `auk.mk`
  - evidence: make -n -f auk.mk speak MODEL=auk OUT=out/trial/x.wav now ends with make -f Makefile mp3 and its convert loop; the rule converted a 0.98 WAV to peak 0.9228 and trashed the WAV; tmp/workflows/goal-trackers/fix2-auk-dryrun.txt
  - repro: make -n -f auk.mk speak MODEL=auk OUT=out/trial/x.wav; the recipe now ends with make -f Makefile mp3; before the fix it ended at the python call
  - test-tags: MANUAL
  - root-cause: 2026-11-09T01:29:49Z @kj auk.mk speak lost its $(MAKE) -f Makefile mp3 step; define.mk still carries the same step
  - log: 2026-11-09T01:29:49Z @kj added
  - log: 2026-11-09T01:30:43Z @kj reproduced: make -n -f auk.mk speak MODEL=auk OUT=out/trial/x.wav ends at the python call; auk.mk has no make mp3
  - log: 2026-11-09T02:41:57Z @kj closed: fixed: auk.mk speak gains the $(MAKE) -f Makefile mp3 step that define.mk and fish.mk already carry
  - log: 2026-11-09T02:43:32Z @kj edited repro "make -n -f auk.mk speak MODEL=auk OUT=out/trial/x.wav; the recipe ends at the python call and has no make mp3" -> "make -n -f auk.mk speak MODEL=auk OUT=out/trial/x.wav; the recipe now ends with make -f Makefile mp3; before the fix it ended at the python call"; reason: the recipe gained the mp3 step

## Service `SERVE`

The HTTP API and the S2 Pro renderer that feeds it

- log: 2026-11-09T01:29:49Z @kj category created

- [x] `DEF-SERVE-4-HISS` **Loudness match raises background hiss** - MEDIUM; per-sentence gain to the text median raises the background hiss of a quiet sentence by up to 6.9 dB; fixed with the +3 dB cap the owner chose on 2026-11-09, plus a paragraph trim so the level spread stays within 1.5 dB; src/fish/speak_s2pro.py level_and_join
  - evidence: MAX_BOOST_DB = 3.0 caps the positive gain and MAX_PARA_SPREAD_DB = 1.2 trims a paragraph's loud pieces (src/fish/speak_s2pro.py, unit test); re-render 95.76 s, WER 0.004, ECAPA 0.778 (own highest, next 0.375), peak 0.837, paragraph ranges 0.0/1.3/0.1/0.2/0.1 dB, quietest-sentence hiss rise 3.00 dB where the gain wanted 4.63 and the earlier worst was 6.9; tmp/workflows/release/hiss-measure.json, repro-measure.json
  - repro: grep -n '6.9 dB' references/fish-audio-s2-pro.md; the gain to the median was applied to the whole sentence, noise included
  - test-tags: MANUAL
  - root-cause: 2026-11-09T01:29:49Z @kj level_and_join applies one gain per sentence to reach the text median; a quiet sentence's noise is raised by the same amount
  - log: 2026-11-09T01:29:49Z @kj added
  - log: 2026-11-09T01:30:43Z @kj proposed fix: cap the per-sentence gain at +3 dB and A/B against the winner; left open for the owner's decision; not fixed
  - log: 2026-11-09T08:37:56Z @kj closed
  - log: 2026-11-09T21:03:47Z @kj edited evidence "MAX_BOOST_DB=3.0 caps the positive gain in level_and_join (unit test); re-render 95.76 s, WER 0.004, ECAPA 0.778 (own highest, next 0.376), peak 0.837, paragraph ranges 0.0/1.8/0.1/0.2/0.1 dB; quietest-sentence hiss rise 3.00 dB where the gain wanted 4.63 and the earlier worst was 6.9; tmp/workflows/release/hiss-measure.json" -> "MAX_BOOST_DB = 3.0 caps the positive gain and MAX_PARA_SPREAD_DB = 1.2 trims a paragraph's loud pieces (src/fish/speak_s2pro.py, unit test); re-render 95.76 s, WER 0.004, ECAPA 0.778 (own highest, next 0.375), peak 0.837, paragraph ranges 0.0/1.3/0.1/0.2/0.1 dB, quietest-sentence hiss rise 3.00 dB where the gain wanted 4.63 and the earlier worst was 6.9; tmp/workflows/release/hiss-measure.json, repro-measure.json"; reason: the reproduction was re-rendered with the paragraph trim, so its recorded measures changed
  - log: 2026-11-09T21:07:05Z @kj amended text "per-sentence gain to the text median raises the background hiss of a quiet sentence by up to 6.9 dB; proposed fix: cap the gain at +3 dB and A/B against the winner; the owner chose this sound by ear, decision pending; `src/fish/speak_s2pro.py` level_and_join" -> "per-sentence gain to the text median raises the background hiss of a quiet sentence by up to 6.9 dB; fixed with the +3 dB cap the owner chose on 2026-11-09, plus a paragraph trim so the level spread stays within 1.5 dB; src/fish/speak_s2pro.py level_and_join"; reason: the owner chose the cap on 2026-11-09 and the repair added the paragraph trim, so 'decision pending' was stale

