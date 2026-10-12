# Defects - w40k-mechanicum

Faults seen in the animations, pages and scripts of w40k-mechanicum. Written through `pm-tools` only.

## Authors

- `@kj` Konrad Jelen

## Crowd `CROWD`

Figures on the walks of a plate scene: where they stand, how they move, how they look

- [x] `DEF-CROWD-1` **Crowd walks too fast** - MAJOR; muster loop of 4 s: left crowd went 5.4 m per loop, 1.35 m/s; fix: loop of 12 s, 0.45 m/s on average, each figure an uneven pace; `src/muster.py` way(), `wip/muster/host.py` stand()
  - evidence: user on the 12 s loop written 03:05 local: "it moves naturally, all is good there in this regard"
  - repro: play wip/preview/muster-draft.avif, watch the left walk
  - test-tags: MANUAL
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:25Z @kj reported on the 4 s loop: "crowd moves too fast; it must move slowly and irregularly"
  - log: 2026-10-12T01:14:25Z @kj closed: fixed: loop of 12 s, left crowd 0.45 m/s on average with uneven pace
- [ ] `DEF-CROWD-2` **Same person repeats along a lane** - MAJOR; muster: one picture stood every 3 figure heights along its file, and persons differed strongly, so every copy showed; fix: lanes of 5 to 7 chains with own length per loop, persons darkened and evened, no bearers in the walking crowd; `wip/muster/host.py`
  - repro: play the loop, follow one bright figure along its lane on the left walk
  - test-tags: MANUAL
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:25Z @kj reported: "crowd is very regular; the same person occurs every few centimeters", "the differences between the individuals must be less prominent"
  - log: 2026-10-12T01:14:25Z @kj fix built; in the 12 s loop; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect
- [ ] `DEF-CROWD-3` **Right crowd walks towards the camera** - MEDIUM; muster: crowd on the right terrace walked against the left crowd; fix: it stands, every figure a person of its own, weight shifts 9 to 12 times per loop; `wip/muster/host.py` WALKS pace
  - repro: play the loop, watch the right terrace
  - test-tags: MANUAL
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:25Z @kj reported: "crowd on the right side moves in the opposite direction - please, no, let that crowd behave on this side like last time"
  - log: 2026-10-12T01:14:25Z @kj fix built; in the 12 s loop; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect
- [ ] `DEF-CROWD-4` **Figures flicker and cover each other** - MAJOR; muster: parts of the crowd change for one frame, figures appear and disappear; fix: camera depth of a figure rises strictly with its depth by the rule, every figure solid, two picture sizes mixed, strokes from 3 rows; `src/muster.py` parapet(), deep()
  - repro: play the loop, watch the near left crowd; or python3 wip/muster/loopcheck.py
  - test-tags: MANUAL
  - root-cause: 2026-10-12T02:21:01Z @kj second cause: a figure is one flat card at one depth; two overlapping cards change order in one frame over all they share, and back when the pace changes; left walk, figures of 12 rows and more: 37 pairs per frame, 3649 of 4804 pairs more than once
  - root-cause: 2026-10-12T01:14:06Z @kj camera depth of a figure came from the measured parapet depth of its own plate column: steps of 0.04 m from column to column, and near figures behind far ones
  - lock: 2026-10-13T01:14:26Z @kj muster, next render
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:25Z @kj reported: sprites "were appearing and disappearing - very poor"; on the 12 s loop of 03:05: "still flickering in the crowd", "as if sprites depth changes stepwise or some clippings occur"
  - log: 2026-10-12T01:14:25Z @kj attempted: solid figures, strokes from 3 rows, two picture sizes mixed, entry beside the picture - flicker stayed in the loop of 03:05
  - log: 2026-10-12T01:14:25Z @kj fix built: depth by the rule; stills 48 to 50: largest one-frame change of a 12 x 12 block 16.5 -> 3.3 of 255; full loop in render
  - log: 2026-10-12T02:21:01Z @kj user on the loop with depth by the rule: "clipping still happens, because there is no hysteresis, and clipping is done to the entire object, doesn't work progressively"; confirmed by count (wip/muster/swaps.py) and on frame 88
  - log: 2026-10-12T02:21:01Z @kj attempted: figures of neighbouring lanes pushed a shoulder's width apart while passing - removed on the user's word "do not disperse the crowd, simply allow for more gradual transitions"
  - log: 2026-10-12T02:21:01Z @kj fix built: card of a walking figure in 8 strips, middle 0.30 figure heights nearer than its sides, head up to 0.10 nearer than feet; src/muster.py BODY, ROUND; frames 84 to 92, near left crowd: largest patch that changes for one frame 8.8 -> 2.1 of 255
  - log: 2026-10-12T02:21:01Z @kj third cause: lantern posts on the near railing were measured as deep as the crowd, so each figure passing changed from before the post to behind it in one frame; fix built: such plate goes behind the crowd, wip/muster/host.py export()
  - log: 2026-10-12T03:03:20Z @kj loop of 04:58, 360 frames, near left crowd: largest patch that changes for one frame 3.5 of 255, pixels in such patches over 3: 0.1 per frame; flat cards on frames 84 to 92: 8.8 and 39.9; loop closes, greatest difference 1 of 255
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect
- [ ] `DEF-CROWD-5` **No crowd behind the first railing section on the right** - MEDIUM; muster: right terrace has no figures from the corner post to 170 columns right of it; cause: crowd ended at plate row 548 to avoid a block on the railing; fix: end it at the terrace's own last rank through the corner post; `wip/muster/host.py`, `src/muster.py` place()
  - repro: any frame, right terrace, columns 1845 to 2015
  - test-tags: MANUAL
  - lock: 2026-10-13T01:14:26Z @kj muster, next render
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:25Z @kj reported with wip/preview/missing crowd.png: "what about missing crowd by the railing on the right side?"
  - log: 2026-10-12T02:21:02Z @kj fix built: right crowd ends at the rank through the corner post, 1521 figures; frame 88 shows figures from the corner post on; their left end is lit orange by brazier F5; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect

## Fire `FIRE`

Simulated fires and how they sit in the plate

- [ ] `DEF-FIRE-6` **Fires move at unequal pace** - MEDIUM; muster: fire in the gorge too slow, fires at the sides too fast; cause: pace by own width plus a cap of 8 m/s slowed only wide fires; fix: every fire moves as a fire 2.5 m wide per plate pixel of its bed; `src/muster.py` FAR, `src/fire.py` pace()
  - repro: play the loop, compare the gorge fire with the braziers on the right
  - test-tags: MANUAL
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:25Z @kj reported: "main flame at the center is too slow, while flames on the sides are too fast; now ithis is very inconsistent"
  - log: 2026-10-12T01:14:25Z @kj fix built: flame tops move 0.13 to 0.27 flame heights per second on all fires; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect
- [ ] `DEF-FIRE-7` **Dark flat shape before the base of a fire** - MEDIUM; muster: dark wedge covers the left of the base of fire F2 (columns 770 to 800, rows 437 to 447), grey wedge at the left of the base of F1; fix: plate where painted flame stood goes behind the fire's card; `src/muster.py` flames(), scene()
  - repro: any frame, base of fire F1 at column 400 and of F2 at column 790
  - test-tags: MANUAL
  - root-cause: 2026-10-12T01:14:06Z @kj plate pixels where the painted flame was are smoke-coloured now; by measured depth 23 % of them lie before the card of F2, 7 % before that of F1
  - lock: 2026-10-13T01:14:26Z @kj muster, next render
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:25Z @kj reported with wip/preview/paste-20261012-030741.png and paste-20261012-031252.png: "some artefact over the flame"
  - log: 2026-10-12T02:21:02Z @kj fix built: frame 88, close views of the bases of F1 and F2: wedge at F2 gone, at F1 a piece of about 5 x 4 pixels left at the left end; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect

## Cloth `CLOTH`

Banners as simulated cloth, and the sigils on them

- [ ] `DEF-CLOTH-8` **Banners move too quickly for their size** - MEDIUM; muster: banners wiggle at the pace of small cloth, so the scene feels small; fix: cloth simulated for a loop 1.3 times shorter and shown over the whole loop; `src/muster.py` CALM, wind()
  - repro: play the loop, watch banner B1
  - test-tags: MANUAL
  - lock: 2026-10-13T01:14:26Z @kj muster, next render
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:26Z @kj reported: "the banners wiggle in the wind too vigorously; considering their size, the gravity + wind wouldnt be able to move them such quickly", "slightly slow them down"
  - log: 2026-10-12T02:21:02Z @kj fix built: cloth simulated for 277 frames per loop and shown over 360 (CALM 1.3); in the render of 04:20; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect
- [ ] `DEF-CLOTH-9` **Sigils too clean** - MINOR; muster: gold sigils even and bright on stained, torn banners; fix: thread tarnished, soot in patches and streaks, thread lost in patches and at edges, one scorched hole off the middle; `src/heraldry.py` WEAR
  - repro: wip/preview/sigils-muster.png, or any frame
  - test-tags: MANUAL
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:26Z @kj reported: "sigils are too clean compared to the rest of the banners"
  - log: 2026-10-12T01:14:26Z @kj fix built; in the 12 s loop; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect

## Plate `PLATE`

The painted plate of a scene and the parts of it that were painted again

- [ ] `DEF-PLATE-10` **Straight edge in the smoke over the left walk** - MEDIUM; muster: smoke ends at a straight line, row 452 at column 0 to row 446 at column 1100, lighter haze below; fix: carry the tone of the smoke above across the edge; `wip/muster/host.py`
  - repro: any frame, columns 0 to 360, rows 440 to 460
  - test-tags: MANUAL
  - root-cause: 2026-10-12T01:14:07Z @kj upper edge of the part of the plate the image model painted again for the far side of the left walk: its tone differs from the plate above
  - lock: 2026-10-13T01:14:26Z @kj muster, next render
  - log: 2026-10-12T01:14:07Z @kj added
  - log: 2026-10-12T01:14:26Z @kj reported with wip/preview/paste-20261012-031021.png: "look also at somoke clipping"
  - log: 2026-10-12T02:21:02Z @kj fix built for columns 0 to 180: tone of the smoke carried under the line, 7 rows at the line evened; right of it the line is the top of a painted wall with crenellations, left as it is; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect

## Render `RENDER`

Scripts that render the frames of a loop and assemble it

- [ ] `DEF-RENDER-11` **Render ends when the crowd file is written again** - MEDIUM; muster: render of 03:06 ended at frame 146 of 360 with BadZipFile; wip/preview/muster-draft.avif then held 4.9 s that do not close; fix: scene() reads muster_crowd.npz whole at the start; src/muster.py
  - repro: start src/muster.py frames, run wip/muster/host.py export while it renders
  - test-tags: MANUAL
  - root-cause: 2026-10-12T02:21:08Z @kj pose() read arrays from the open muster_crowd.npz in every frame; wip/muster/host.py export wrote the file again at 03:20 while the render ran
  - log: 2026-10-12T02:21:08Z @kj added
  - log: 2026-10-12T02:21:08Z @kj fix built; not tested by writing the file during a render

