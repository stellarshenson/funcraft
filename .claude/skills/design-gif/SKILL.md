---
name: design-gif
description: Designs, assembles and verifies seamlessly looping GIF animations and banners from rendered frames - exact-loop timing, seam checks, palette assembly, and variants such as camera shake on footfalls or offset gait phases. Use when asked to make, loop, fix or check an animated GIF or banner ("looped", "loop seam", "it jumps at the loop", "19:6 banner", "make the gif", "screen shake when they stomp", "stomp at different phase"), or when frames rendered in Blender or Pillow need turning into a GIF.
---

# Looping GIFs

A loop is exact when the frame after the last equals the first. Design every motion for that, render one frame past the end to prove it, then assemble. Building the scene itself: `design-blender` skill. Scripts below live in this skill's `scripts/`; project paths are relative to `~/workspace/funcraft/`.

## Format
- 19:6 banner: GIF 1140 × 360, rendered at 1520 × 480 and downscaled with LANCZOS - the oversample removes aliasing
- 50 ms per frame; 30 frames = 1.5 s, 40 frames = 2 s
- Frames `wip/<dir>/f000.png` …; the phase-1.0 frame is `seam-check.png` and stays out of the GIF

## Loop design
- `phase = i / FRAMES` in [0, 1); every animated quantity is a function of phase alone
- Each periodic motion completes whole cycles per loop: fans whole blade spacings, gears whole teeth, pulses whole periods, `cos(2π·k·phase)` with integer k
- Scrolling rows move exactly one spacing per loop (floor marker spacing = stride) and outrun the visible area at both ends - a visible end moves and shows the seam
- Objects that wrap (rings climbing a column) wrap where they are hidden, inside a cap
- A turning mesh must also land on its own facets: a 48-segment ring turned 20° per loop does not (5° segments do); a downloaded fan whose blade count is unknown turns one full revolution
- Discrete states (blinking lights): `tick = (i % FRAMES) // TICK` with `FRAMES % TICK == 0`
- Events (footfalls) and their effects (camera shake) count whole frames modulo FRAMES, so a tail wraps into the loop start; phase offsets between actors are whole frames too, so every footfall lands on a frame
- Keep the render seed static - still areas then repeat pixel for pixel. An animated seed, per-frame random draws, or a volume boundary lying on a surface all break the loop

## Seam check
- Render frames 0 … FRAMES; frame FRAMES (phase 1.0) is written as `seam-check.png`
- `python3 scripts/seamcheck.py wip/<dir>` - pixels whose largest channel differs by more than 8/255 between `f000.png` and `seam-check.png`; pass = 0 (denoiser noise stays below 8)
- On failure add `--trace X0 Y0 X1 Y1`: mean brightness of that region per frame with the step from the previous frame; the jump names the frame where the fault starts (fog on the floor: 415 → 451 between frames 26 and 27)
- Report with its total: "0 of 729,600 pixels"

## Assemble
- `python3 scripts/assemble.py wip/<dir> out/<name>.gif` - LANCZOS to 1140 × 360, one 224-colour median-cut palette from frame 0, Floyd-Steinberg dither, `optimize`, `disposal=1`, loops forever
- Expect 5-7 MB for 30 frames of a lit 3D scene
- Small saturated details get few palette entries (a 10-25 px canopy reduces to one or two reds) - judge colour on the GIF, not the PNG
- Each project keeps its own copy of `assemble.py` so it runs standalone; keep copies in step with this one

## Variants
- One generator; flags in argv (`shake`, `offset`, `out=DIR`); one Makefile target per variant (`banner`, `banner-shake`, `banner-offset` → `out/03-…`, `04-…`, `05-…`)
- Camera shake: a decaying cosine per footfall - 0.1° amplitude, time constant 0.1 s, 7 Hz - counted in whole frames from the landing
- Offset phases: whole-frame offsets per actor (Atlas 11, BattleMaster 21 of 30) spread six footfalls across the loop
- Render every variant in one background job and seam-check each

## Verify and deliver
- `python3 scripts/sheet.py a.gif b.gif --frame 12 -o sheet.png` stacks one frame of each at GIF size; `--crop X0 Y0 X1 Y1 --zoom 2` enlarges a detail. Read the sheet before sending
- For a change, stack the previous version above the new one
- Compare file times with the render log before calling a file new - a GIF with the old name and old content looks like a failed change
- Send the GIFs themselves; name each variant, give the seam result and say what is not yet done

<!-- improved 2026-09-30 | body 0→635w / 0→42L | benchmark n/a (declined) | via improve-skill -->
