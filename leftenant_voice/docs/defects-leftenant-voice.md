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

## Transcription `ASR`

Nemotron transcription service, page and model cache

- log: 2026-11-13T18:23:45Z @kj category created

- [x] `DEF-ASR-5-SYMLINK-BYTES` **tree_bytes doubles the cache size** - MEDIUM; tree_bytes follows the snapshot symlinks Hugging Face creates, so every blob counts directly under blobs/ and again under snapshots/<rev>; GET /models bytes and DELETE freed_bytes report about twice the data
  - evidence: fixed in wf_e691bdd0-34b: tree_bytes skips symlinks (os.walk followlinks=False, lstat sizes); test_a_snapshotted_cache_counts_each_blob_once asserts tree_bytes, GET bytes and DELETE freed_bytes at 1000 for a 1000-byte blob; verifier pass; 114 unit green
  - test-tags: UNIT
  - repro: HF_HOME with blobs and snapshot symlinks: GET /models reports 2000 for 1000 bytes (wip/models-api/verify/tree_bytes_check.log)
  - log: 2026-11-13T18:23:45Z @kj added
  - log: 2026-11-13T18:23:48Z @kj edited test-tags added "UNIT"
  - log: 2026-11-13T18:28:21Z @kj closed
- [x] `DEF-ASR-6-ACCELERATE` **Merged venv lacks accelerate** - MAJOR; the merged /opt/venv lacks accelerate; AutoModelForMultimodalLM.from_pretrained(device_map='cuda:0') raises ValueError 'requires accelerate', so the transcriber fails at startup and asr.state is error
  - evidence: fixed in wf_6d3e9cb7-2fb: the Dockerfile installs accelerate 1.15.0 beside the dev Transformers; image c58d51530d8a imports accelerate, torch 2.8.0+cu128, transformers 5.23.0.dev0, librosa 1.0.0 and the nemotron module; 123 unit green; verifier pass
  - repro: docker compose up with image 71140daa481a: /health asr.state error, container log 'requires accelerate' (wip/e2e/logs/health-error.json)
  - test-tags: MANUAL
  - log: 2026-11-13T19:38:46Z @kj added
  - log: 2026-11-13T19:51:18Z @kj closed
- [x] `DEF-ASR-7-DELETE-BLOBS` **Model delete leaves the weight blobs** - MAJOR; DELETE /models removes only the model directory; the 67.5 GB weight blob stays in the shared hub blobs store reached through symlinks, so freed_bytes is 464 KB, GET /models undercounts s2pro at 4.7 GB of 11 GB, and the next use re-materialises the model without downloading
  - evidence: wf_a4d1c628-625 verify: sparse 67496013734-byte blob linked by nemotron - GET /models bytes 67496013734, DELETE freed_bytes 67496013734, blob unlinked; blob shared by two models survives the first delete (freed 0) and goes with the second (freed 2000); image 29bf480f77c5; make test 125 passed
  - repro: E2E wf_5b29b262-0db: DELETE /models/nemotron freed 464436 of 67496013734 bytes; the store measured equal before and after (wip/e2e/logs/volume-after-delete.txt)
  - test-tags: UNIT
  - log: 2026-11-13T20:35:58Z @kj added
  - log: 2026-11-13T20:56:22Z @kj closed
- [x] `DEF-ASR-8-GPU-PLACEMENT` **Worker lands on GPU 1 not GPU 2** - MEDIUM; the daemon ignores the compose device reservation (NVIDIA_VISIBLE_DEVICES=all), so ASR_GPU_INDEX=1 loads the transcriber on host GPU 1 (RTX PRO 6000) instead of the intended GPU 2; compose must set the index explicitly
  - evidence: compose sets ASR_GPU_INDEX: "2" (docker compose config renders it with device_ids 0 and 2); engine_nemotron.py:82 passes it as CUDA_VISIBLE_DEVICES at load; the prior E2E showed the worker takes that index on this daemon, where all GPUs are visible
  - repro: E2E run: the worker loads on GPU 1 while compose lists device_ids 0 and 2 (wip/e2e/logs/)
  - test-tags: MANUAL
  - log: 2026-11-13T20:35:58Z @kj added
  - log: 2026-11-13T20:56:22Z @kj closed

## Web page `WEB`

Faults of the service's browser page

- log: 2026-11-17T07:13:50Z @kj category created

- [x] `DEF-WEB-9-LOGIN-LOST` **Login not kept** - MAJOR; POST /login answers 200, then every request is 401: the browser does not send the sid cookie back; seen 2026-11-17 in the lab tab frame; cause unknown
  - evidence: live login against the deployed service, wf_26062601-8da verified: framed from galaxalabs.com /settings 200, framed cross-site from stellars-tech.eu 401, top-level 200; lab tab now frames voice-tts.behemoth.galaxalabs.com
  - root-cause: 2026-11-17T10:23:36Z @kj the lab runs at workbench.behemoth.galaxalabs.com but the lab tab framed https://voice-tts.lab.stellars-tech.eu, a cross-site frame, so the browser refused the SameSite=Strict sid cookie; same failure reproduced in the cross-site variant of wf_65bb7f94-0d7; the service also answers at voice-tts.behemoth.galaxalabs.com, same site as the lab
  - repro: log in on the page in the lab tab, press Save on the Hugging Face token, read the service log
  - test-tags: FUNCTIONAL, MANUAL
  - log: 2026-11-17T07:13:50Z @kj added
  - log: 2026-11-17T07:55:52Z @kj not reproduced, wf_65bb7f94-0d7: same-site framing with the Lumino sandbox flags keeps the cookie, only a cross-site frame drops it; page now re-checks /session after login and says when the browser dropped the cookie; cookie unchanged
  - log: 2026-11-17T10:23:36Z @kj lab-tab wrapper now frames https://voice-tts.behemoth.galaxalabs.com/; lab host read from the vault passkey record and /var/log/jupyterlab.log; awaiting a live login in the lab tab
  - log: 2026-11-17T11:25:41Z @kj closed
- [x] `DEF-WEB-10-SILENT-ERRORS` **Errors hidden on the page** - MAJOR; the page shows no refusal: Save leaves 'no token' after a 401, Create token does nothing; only Models says 'log in first'
  - evidence: every action shows running, done or the server's detail (verifier browser run of all pages and states); wf_594fe8f6-a22 verifier pass, review SHIP wf_aca86707-e16, make test 134 green, make test-functional 30 passed wf_e1e4629c-166
  - root-cause: 2026-11-17T14:13:17Z @kj the old page's handlers ignored non-OK responses and wrote no outcome; every fetch now goes through one helper that shows running, done or the server's detail beside its control
  - repro: log out, press Save or Create token, see no message
  - test-tags: UNIT, FUNCTIONAL
  - log: 2026-11-17T07:13:50Z @kj added
  - log: 2026-11-17T07:55:52Z @kj fixed in the tree, wf_65bb7f94-0d7: 134 unit green, verifier browser run 23/23; not yet in the deployed image
  - log: 2026-11-17T14:13:17Z @kj closed
- [x] `DEF-WEB-11-HF-UNCHECKED` **Hugging Face token not checked** - MEDIUM; Save stores any text as the Hugging Face token; a wrong token shows only when a model download fails
  - evidence: whoami unit tests: valid 200 with account, refused 422, timeout and 5xx 502; functional token test against Hugging Face green; wf_594fe8f6-a22 verifier pass, review SHIP wf_aca86707-e16, make test 134 green, make test-functional 30 passed wf_e1e4629c-166
  - root-cause: 2026-11-17T14:13:17Z @kj POST /settings/hf-token stored any text without asking Hugging Face; it now calls the whoami-v2 endpoint first
  - repro: save a wrong token, page reports nothing
  - test-tags: UNIT
  - log: 2026-11-17T07:13:50Z @kj added
  - log: 2026-11-17T07:55:52Z @kj fixed in the tree, wf_65bb7f94-0d7: 134 unit green, verifier browser run 23/23; not yet in the deployed image
  - log: 2026-11-17T14:13:17Z @kj closed
- [x] `DEF-WEB-12-LOGGEDOUT-FORMS` **Settings forms shown while logged out** - MEDIUM; logged out, the page shows the token, API token and model forms, which can only fail
  - evidence: tests/functional/test_browser.py: logged out shows only the login box, a 401 returns to it; wf_594fe8f6-a22 verifier pass, review SHIP wf_aca86707-e16, make test 134 green, make test-functional 30 passed wf_e1e4629c-166
  - root-cause: 2026-11-17T14:13:17Z @kj the old page drew every section before the session check; the portal shows only the login box until /session says authenticated
  - repro: open the page logged out
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T07:13:59Z @kj added
  - log: 2026-11-17T07:55:52Z @kj fixed in the tree, wf_65bb7f94-0d7: 134 unit green, verifier browser run 23/23; not yet in the deployed image
  - log: 2026-11-17T14:13:17Z @kj closed
- [x] `DEF-WEB-13-DROP-OUTSIDE` **File drop outside the drop area opens the file** - MINOR; a file dropped on another page, in the main column gutters or below the Transcription cards is not cancelled; Chrome opens it in place of the portal
  - evidence: document dragover/drop cancel file drags; headless Chrome: file drags on body, header, form and the render page cancelled, portal stays; wf_e4889bf0-ca3 verifier pass; make test 134 green; test_browser.py 10 passed; make test-functional 36 passed wf_d3353c9e-0de; review confirm rounds wf_d8b729f5-900 and wf_30e53ddc-aaa, SHIP
  - repro: drag an mp3 onto the Voice rendering page or the gutter beside the Transcription cards
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T14:20:34Z @kj added
  - log: 2026-11-17T15:04:35Z @kj closed
- [x] `DEF-WEB-14-DROP-TAP` **Drop box not a tap target** - MINOR; on a 390 px phone tapping the dashed drop box does nothing; only the 99x21 px 'choose a file' link opens the picker
  - evidence: click on the drop box opens the file chooser once, inner button once; browser test case; wf_e4889bf0-ca3 verifier pass; make test 134 green; test_browser.py 10 passed; make test-functional 36 passed wf_d3353c9e-0de; review confirm rounds wf_d8b729f5-900 and wf_30e53ddc-aaa, SHIP
  - repro: on a phone tap the dashed box on Transcription
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T14:20:35Z @kj added
  - log: 2026-11-17T15:04:35Z @kj closed
- [x] `DEF-WEB-15-TEXT-DROP` **Text drop into names and terms cancelled** - MINOR; the Transcription page drop handler cancels every drag, so text dragged into the names-and-terms field is dropped silently
  - evidence: page drag handlers act only on file drags; a real text drag inserted text into names and terms; wf_e4889bf0-ca3 verifier pass; make test 134 green; test_browser.py 10 passed; make test-functional 36 passed wf_d3353c9e-0de; review confirm rounds wf_d8b729f5-900 and wf_30e53ddc-aaa, SHIP
  - repro: drag selected text into the names-and-terms field
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T14:20:35Z @kj added
  - log: 2026-11-17T15:04:35Z @kj closed
- [x] `DEF-WEB-16-DROP-HIGHLIGHT` **No drop highlight while a recording is chosen** - MINOR; once a recording is chosen the drop box is hidden, so a file dragged over the page shows no highlight although the drop replaces the recording
  - evidence: highlight on #transcribe-form before and after a recording is chosen; browser test case; wf_e4889bf0-ca3 verifier pass; make test 134 green; test_browser.py 10 passed; make test-functional 36 passed wf_d3353c9e-0de; review confirm rounds wf_d8b729f5-900 and wf_30e53ddc-aaa, SHIP
  - repro: choose a recording, then drag another file over the Transcription page
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T14:20:35Z @kj added
  - log: 2026-11-17T15:04:35Z @kj closed
- [x] `DEF-WEB-17-STALE-DOCS` **Page descriptions inexact** - MINOR; app.py module docstring omits the public GET /static/*, and README and the app.css header cite the untracked tmp/ mockup
  - evidence: app.py docstring lists GET /static/* and the content-hash links (patch-17, patch-21); README and app.css cite no tmp file; wf_e4889bf0-ca3 verifier pass; make test 134 green; test_browser.py 10 passed; make test-functional 36 passed wf_d3353c9e-0de; review confirm rounds wf_d8b729f5-900 and wf_30e53ddc-aaa, SHIP
  - repro: read app.py lines 1-40, README page section, app.css line 1
  - test-tags: UNIT
  - log: 2026-11-17T14:20:35Z @kj added
  - log: 2026-11-17T15:04:35Z @kj closed
- [x] `DEF-WEB-18-MP3-NAME` **Every render downloads as speech.mp3** - MINOR; renders of one session cannot be told apart on disk; owner chose voice plus clock time, for example grimaldus-1259.mp3
  - evidence: result card and session list download as <voice>-<HHMM>.mp3 (grimaldus-1525.mp3 at 15:25); browser test case; wf_e4889bf0-ca3 verifier pass; make test 134 green; test_browser.py 10 passed; make test-functional 36 passed wf_d3353c9e-0de; review confirm rounds wf_d8b729f5-900 and wf_30e53ddc-aaa, SHIP
  - repro: render twice and download both
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T14:20:35Z @kj added
  - log: 2026-11-17T15:04:35Z @kj closed
- [x] `DEF-WEB-19-HF-RATELIMIT` **Functional token test fails on hub 429 or 5xx** - MINOR; tests/functional/test_webapp.py accepts only the refused and saved answers, not 'Hugging Face did not check', which the service sends for a 429 or 5xx
  - evidence: test_webapp.py token test accepts the 'Hugging Face did not check' 502 answer; wf_e4889bf0-ca3 verifier pass; make test 134 green; test_browser.py 10 passed; make test-functional 36 passed wf_d3353c9e-0de; review confirm rounds wf_d8b729f5-900 and wf_30e53ddc-aaa, SHIP
  - repro: run make test-functional while Hugging Face rate-limits
  - test-tags: FUNCTIONAL
  - log: 2026-11-17T14:20:43Z @kj added
  - log: 2026-11-17T15:04:35Z @kj closed
- [x] `DEF-WEB-20-TIMEOUT-DOCS` **Hugging Face timeout stated as 10 s total** - MINOR; README and docstrings promise a 10 s check, but the timeout applies per connection attempt and per read, so a hub that drops packets takes about 40 s; owner chose the wording fix
  - evidence: README, app.py and whoami docstrings say 10 s per connection attempt and per read; wf_e4889bf0-ca3 verifier pass; make test 134 green; test_browser.py 10 passed; make test-functional 36 passed wf_d3353c9e-0de; review confirm rounds wf_d8b729f5-900 and wf_30e53ddc-aaa, SHIP
  - repro: read the README token section and the app.py whoami docstring
  - test-tags: UNIT
  - log: 2026-11-17T14:20:43Z @kj added
  - log: 2026-11-17T15:04:36Z @kj closed

