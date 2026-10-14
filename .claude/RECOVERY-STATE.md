# Recovery state

## BRACE 2026-10-14T16:05Z - usage limit

**HORIZON: LIMIT** - `brace-horizon` printed `LIMIT 97% seven_day resets 5:00am (6414m)`. The machine stays up; the same session (`claude --continue` in `~/workspace/funcraft`) returns after the reset.

- Workflows stopped: none. Subagents alive: none
- Compute running: none (GPUs idle; no Blender or `.venv-moge` process)
- Tree difference from the brace: none (nothing was stopped)

### In flight: saint scene (banner 07), Warhound Titan in a hall behind the wall (task #108)

The owner chose "go": the whole titan, about 56 m back, in profile facing the saint, seen through an opening in the wall between the black column and the gilded frame of the sun-gear.

Done, all uncommitted, in `w40k-mechanicum/`:
- `src/titanhall.py` (new): cuts the opening (plate x 1660-1946, depth > 10.4 m) out of `backdrop` and `backdrop_fill`, builds the hall (stone floor at the titan's feet, far wall with three cold windows, two piers, haze box), places `warhound.model()` at the opening's middle (x 14.36 m, depth 56 m, feet -9.0 m, turned -90 degrees to face image left), adds a warm key spot and a cold rim spot; plate, actors and smoke neither light nor shade it
- `src/scenes.py`: `SCENES["saint"]["titan"]` settings, and a call to `titanhall.build` at the end of `build()`
- Plate files `wip/scene3d/saint.png`, `saint_clean.png`, `saint_clean_bg.png` rebuilt WITHOUT the painted 2D Warhound: originals from `wip/scene3d/before-repaint/`, then `python3 src/goldwork.py apply saint`, then `python3 src/repaint.py apply saint window-left=30 window-right=20 skull=2`
- The accepted render's frames moved to `wip/frames-saint-pre-titan/` (121 files); `out/07-saint.avif` is still the accepted render with the 2D Warhound
- Test 1 (`wip/preview/scene-saint.png`, 24 samples): titan in place and at the planned size, but the hall far too bright (mean 200 against the chapel wall's 26 of 255) and grainy
- Test 2 with lights divided by about 7.5 (key 8.0e4 W, rim 5.0e4 W, windows 0.6, haze 0.008): rendered to `wip/frames-saint/f000.png` and `f060.png` (64 samples, log `wip/logs/saint-titan-test.log`), NOT yet looked at

### FIRST ACTION

Look at `w40k-mechanicum/wip/frames-saint/f000.png`, crop x 1450-2150: measure the hall's brightness (target close to the wall's 26) and the grain. Tune lights and samples, render test frames again with
`cd ~/workspace/funcraft/w40k-mechanicum && CUDA_VISIBLE_DEVICES=1 LOOP_FRAMES=120 LOOP_WIDTH=2432 nohup setsid ~/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/scenes.py -- saint 0 60 > wip/logs/saint-titan-test.log 2>&1 &`
(wait for `Blender quit` in the log, not for the PID: `setsid` forks). Show the owner a test still before the full render (DESIGN.md 5.10).

### Then, in order

1. Grain: the hall's spots in haze are noisy at 64 samples with the denoiser off; options: more samples for this scene, or a denoised second view layer for the hall composited over the plate
2. Full render of 120 frames, AVIF 30 fps 2432 x 768 to `out/07-saint.avif`, whole-frame flicker check
3. Window fixes (task #109): designs drawn upright along the leaning window frames, taller titan in the left window, lower window parts given content
4. DESIGN.md (opening and hall), README, journal entry 103 (last entry 102)
5. Commit and push: only on the owner's word

### Awaiting the owner
- Answer on the test still of the titan in the hall
- Commit and push of the saint work (journal 101-102, DESIGN, README, goldwork, repaint, glassdesign, warhound, titanhall)
- Sermon package zip upload to the hub; the lab token decision (from 2026-10-07)
