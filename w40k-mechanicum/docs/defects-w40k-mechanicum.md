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
  - log: 2026-10-12T01:14:06Z @kj added
  - log: 2026-10-12T01:14:25Z @kj reported with wip/preview/paste-20261012-030741.png and paste-20261012-031252.png: "some artefact over the flame"
  - log: 2026-10-12T02:21:02Z @kj fix built: frame 88, close views of the bases of F1 and F2: wedge at F2 gone, at F1 a piece of about 5 x 4 pixels left at the left end; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect
- [ ] `DEF-FIRE-14` **Brazier fire is not hidden by its bowl** - MAJOR; muster, brazier F5: flame picture drawn at 21.1 m, bowl at 15.6 m and near only in rows 428-439; flame base columns 2005-2049 against bowl 2005-2040; fire shows under and beside the bowl; user 2026-10-12: "the fire in this post isn't clipped by the post top bowl", screenshot out/paste-20261012-182315.png
  - repro: open out/16-muster.avif of 18:13 and enlarge the brazier of the right terrace
  - test-tags: MANUAL
  - root-cause: 2026-10-12T17:16:11Z @kj design fault: measured depth per pixel decided what covers what; bowl, flame and stand were placed by three separate rules; audit found 33 near things, 10 cut in two, 15 without one depth
  - log: 2026-10-12T17:16:11Z @kj added
  - log: 2026-10-12T17:16:26Z @kj user: "it must be fixed strategically"; fix built: scene from a list of things (src/things.py, THINGS in src/muster.py, DESIGN.md 5.13); fire tied to the bowl, cut by its rim, at its depth; test frames 0, 30, 60, 90 right; full loop rendering
  - log: 2026-10-12T19:22:18Z @kj fix rendered: out/16-muster.avif of 21:14, 360 frames, loop closes; fire rises out of the whole bowl in close views of frames 0, 30, 60, 90; first render from the list had faults of the build, corrected; sermon package 21:17, 81 and 28 checks pass; awaits the owner's word
- [ ] `DEF-FIRE-15` **Smoke column is animated as moving pixels** - MAJOR; muster: the smoke column is a pixel flow over a box of the plate, not a simulation; user: "must be animated as smoke using physiscs; you have taken a shortcut"
  - repro: play out/16-muster.avif of 2026-10-12 22:43 and watch the smoke column left of the crane
  - test-tags: MANUAL
  - root-cause: 2026-10-13T07:55:12Z @kj the flow effect of other scenes was kept for the smoke (SMOKE, fx, flowing in src/muster.py) although the rule says simulate; legend said not simulated yet
  - log: 2026-10-13T07:55:12Z @kj added
  - log: 2026-10-13T12:13:11Z @kj fix rendered, awaits the owner's word: one smoke column simulated as a gas (src/fire.py, wip/sim/muster/S1.npz), painted plumes taken out, no pixel flow in src/muster.py; render of 2026-10-13 14:01, out/16-muster.avif
- [ ] `DEF-FIRE-17` **Two smoke plumes of one shape** - MEDIUM; muster: the source picture has a dark plume in front and a larger pale one behind; both stay and move alike; user: "smoke in the front must be the only one, and slightly more dispersed"
  - repro: look at the smoke left of the crane in out/16-muster.avif of 2026-10-12 22:43
  - test-tags: MANUAL
  - root-cause: 2026-10-13T07:55:21Z @kj the painted smoke was never a thing of the list: both plumes stayed in the plate and one flow moved them
  - log: 2026-10-13T07:55:21Z @kj added
  - log: 2026-10-13T12:13:11Z @kj fix rendered, awaits the owner's word: one column, 30 m source, wind 5 m/s, leans right, passes before the crane; sky painted where the two plumes stood; render of 2026-10-13 14:01, out/16-muster.avif
- [ ] `DEF-FIRE-18` **Base of the brazier fire is tilted** - MEDIUM; muster, brazier F5: a strip of the plate's painted flame lies on the bowl, 2 rows thick on the left and 6 on the right, and stands still; 134 of the 623 pixels of bowl V5 are flame-coloured; the bowl itself is level, rows 426 to 443
  - repro: enlarge the brazier in out/16-muster.avif of 2026-10-12 22:43
  - test-tags: MANUAL
  - root-cause: 2026-10-13T07:55:21Z @kj the box of bowl V5 begins at row 426 and its mask takes every pixel that differs from the surroundings, the painted flame included
  - log: 2026-10-13T07:55:21Z @kj added
  - log: 2026-10-13T12:13:11Z @kj fix rendered, awaits the owner's word: bowl whole with level rim (mirror), fire base level; close view wip/preview/frames3d/final-brazier.png; render of 2026-10-13 14:01, out/16-muster.avif

## Cloth `CLOTH`

Banners as simulated cloth, and the sigils on them

- [ ] `DEF-CLOTH-8` **Banners move too quickly for their size** - MEDIUM; muster: banners wiggle at the pace of small cloth, so the scene feels small; fix: cloth simulated for a loop 1.3 times shorter and shown over the whole loop; `src/muster.py` CALM, wind()
  - repro: play the loop, watch banner B1
  - test-tags: MANUAL
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
- [ ] `DEF-CLOTH-21` **Cloth crosses its post** - MAJOR; in test frames a cloth lay over its post (order A) or the post over the cloth (order B); the user: "wait posts obscure the cloth in front of it???"; source picture shows post and cloth side by side
  - repro: render frames 0 30 60 90; close view of banner B1 at plate x 330-450, rows 30-400 (wip/preview/muster-cloth-and-post.png)
  - test-tags: MANUAL
  - root-cause: 2026-10-13T10:29:49Z @kj cloth held at its crossbar alone swings into the picture; camera sees left banners at up to 37 degrees, so the cloth shows up to 48 px beyond its post (B1)
  - log: 2026-10-13T10:29:49Z @kj added
  - log: 2026-10-13T12:13:11Z @kj fix rendered, awaits the owner's word: cloth edge held at its post, 45 to 202 vertices per banner; cloth B1 carried on to its post over the grey band (near=9); obstacle at the post changed nothing in the picture; render of 2026-10-13 14:01, out/16-muster.avif
  - log: 2026-10-13T14:00:06Z @kj the fix (edge fastened at the post) has a consequence the owner reported: cloths skewed, flared and nearly still, DEF-CLOTH-25; the fix is under review
  - log: 2026-10-13T16:20:03Z @kj edge no longer fastened to the post, because that fix caused DEF-CLOTH-25; in gusts the cloth passes over its post line by up to 17 px (B12 16.6, B1 15.8, B11 12.9) and is drawn before the post; the owner decides whether that is acceptable
- [ ] `DEF-CLOTH-23` **Cloth B12 hangs loose at its upper left corner** - MAJOR; owner: "why is the cloth dicsonnected in this corner?"; the left 15 px of cloth B12 are not held at the crossbar, the corner folds inward, the pale plate shows in a wedge, and a piece of 2 cells hangs alone at the crossbar
  - repro: close view of out/16-muster.avif at columns 2156-2206, rows 152-200; wip/preview/frames3d/corner-b12.png
  - test-tags: MANUAL
  - root-cause: 2026-10-13T12:55:28Z @kj the cut of the cloth (muster_cloth.png) lacks the dark hem of the corner, columns 2169-2187, rows 172-183; first held vertex of the cloth body at column 2187; the other ten cloths are held over their whole width
  - log: 2026-10-13T12:55:28Z @kj added
  - log: 2026-10-13T13:54:19Z @kj fix rendered, awaits the owner's word: cut of cloth B12 takes its dark hem (on in ELEMENTS), other ten cuts identical; every cloth held from first to last column; a pale notch of about 2 by 6 px stays beside the left tab; render ended 2026-10-13T13:44Z
- [ ] `DEF-CLOTH-25` **Cloths skewed, flared at the lower end, and nearly still** - MAJOR; owner on B11 and B12: "skewed to the left and the first one is weirdly flared out at the bottom", "the wind doesnt seem to work on it"; lower quarter of B11 is 85 px wide against 72 at rest, B12 108 against 90; they move by 1 px
  - repro: python3 wip/muster/sway.py; out/paste-20261013-155630.png
  - test-tags: MANUAL
  - root-cause: 2026-10-13T14:00:06Z @kj the edge beside the post is fastened (fix of DEF-CLOTH-21) while the wind holds the lower part 0.12 to 0.29 m deeper than at rest; the free side shifts in the picture, the fastened side stays; change in time fell from 3-9 px to 0.3-1 px
  - log: 2026-10-13T14:00:06Z @kj added
  - log: 2026-10-13T16:20:09Z @kj fix rendered, awaits the owner's word: cloth held at its crossbar only, wind STEADY -0.1, no least strength; lower quarter mean shift -1.9 to +2.4 px, width within 7 % of rest, change in time 3.2 to 9.3 px at B1, B2, B9 to B13; loop closes; tests pass
- [x] `DEF-CLOTH-28` **Forge sigils painted into the plate, flat** - MAJOR; forge (banner 04): the two sigils on the drape were drawn into the plate picture as flat discs facing the camera, then bent through a chart but still painted; owner: the cloth is a 3d cloth object, embroidery applied as a texture
  - evidence: owner 2026-10-14 10:05: "good" on look C; out/04-forge.avif of 09:46 and the sermon package banner of 09:47 show it; loop closes; tests 81 + 28 pass
  - repro: out/04-forge.avif of 2026-10-13 23:06, drape at columns 1500-1760: both sigils are upright circles on a cloth that leans 17 degrees
  - test-tags: MANUAL
  - root-cause: 2026-10-13T22:23:14Z @kj goldwork.py lay drew each glyph in picture space; the drape was part of the backdrop picture, not an object; rule of DESIGN.md 2.5 (flat texture draped on the object's shape) not applied to the sigils
  - log: 2026-10-13T22:23:14Z @kj added
  - log: 2026-10-13T22:23:19Z @kj fix rendered 2026-10-14 00:15, awaits owner's word: drape built as a mesh object (164527 vertices, chart UV), embroidery as its texture, gold thread lit by a lamp at the lantern; loop closes; lower sign: 245 px change for single frames, plate's own wheel 76; tests 81 + 28 pass
  - log: 2026-10-14T07:52:02Z @kj owner 2026-10-14: lamp-lit raised gold too flat, too metal-like, not draped; fix rendered 09:45: gold emitted in the velvet's light with satin sheen (look C, owner's choice), measured drape kept; loop closes; lower sign 13 px change for single frames; tests 81 + 28 pass; awaits owner's word
  - log: 2026-10-14T08:06:32Z @kj closed

## Plate `PLATE`

The painted plate of a scene and the parts of it that were painted again

- [ ] `DEF-PLATE-10` **Straight edge in the smoke over the left walk** - MEDIUM; muster: smoke ends at a straight line, row 452 at column 0 to row 446 at column 1100, lighter haze below; fix: carry the tone of the smoke above across the edge; `wip/muster/host.py`
  - repro: any frame, columns 0 to 360, rows 440 to 460
  - test-tags: MANUAL
  - root-cause: 2026-10-12T01:14:07Z @kj upper edge of the part of the plate the image model painted again for the far side of the left walk: its tone differs from the plate above
  - log: 2026-10-12T01:14:07Z @kj added
  - log: 2026-10-12T01:14:26Z @kj reported with wip/preview/paste-20261012-031021.png: "look also at somoke clipping"
  - log: 2026-10-12T02:21:02Z @kj fix built for columns 0 to 180: tone of the smoke carried under the line, 7 rows at the line evened; right of it the line is the top of a painted wall with crenellations, left as it is; user check pending
  - log: 2026-10-12T03:03:20Z @kj fix is in the loop of 04:58 and in out/16-muster.avif; user after that loop: "good", "build this animation final in out" - not named per defect, closure waits for the user's word on this defect
- [ ] `DEF-PLATE-12` **Things hang in the air right of the terrace brazier** - MEDIUM; muster: static dark object with rod and ball at plate x 1940-1985, y 363-428, and three remainders of painted cloth at x 2085-2183, y 390-427; user 2026-10-12: "some weird artefacts in the right, something hanging in the air"; screenshot out/paste-20261012-154221.png
  - repro: open out/16-muster.avif and enlarge the area left and right of the brazier of the right terrace
  - test-tags: MANUAL
  - root-cause: 2026-10-12T13:59:32Z @kj image model drew the object into the plate; cloth mask missed tatters of painted cloth; depth model set all four 10 to 25 m nearer than the smoke round them
  - log: 2026-10-12T13:59:32Z @kj added
  - log: 2026-10-12T13:59:45Z @kj fix built: stray() in wip/muster/host.py writes the plate behind the crowd without the four things, colour and depth carried in from round them; frame 0 rendered without them; full loop rendering
  - log: 2026-10-12T14:42:42Z @kj fix in out/16-muster.avif of 2026-10-12 16:37 and in the sermon package: 361 frames rendered again, the four things absent, 12 frames equal to the old ones within 4 of 255 outside plate x 1915-2205, y 340-450; before and after: wip/preview/muster-right-before-after.png; closure waits for the user's word
  - log: 2026-10-12T15:34:26Z @kj user 2026-10-12 16:54 on the file of 16:37: "better, but still some artefacts left", with arrows at other things (the two black posts and the brazier bowl, DEF-PLATE-13); no word yet that this defect is closed
  - log: 2026-10-12T19:22:18Z @kj rendered again from the list of things, out/16-muster.avif of 21:14: dark object and cloth remainders are taken out in THINGS (R1, R5), with four more painted things (Q1 to Q4); no remainder in close views of frames 0, 30, 60, 90; awaits the owner's word
- [ ] `DEF-PLATE-13` **Post tops and brazier bowl slide against their lower parts** - MEDIUM; muster, right terrace: the top 30 rows of two black posts (plate x 2040-2066, y 410-449) and the bowl of brazier F5 slide up to 9 pixels against the parts under them as the camera moves; the bowl has no visible support; user 2026-10-12: "still some artefacts left", screenshot out/paste-20261012-165438.png
  - repro: open out/16-muster.avif of 16:37 and enlarge the brazier of the right terrace over one camera cycle of 4 s
  - test-tags: MANUAL
  - root-cause: 2026-10-12T15:34:26Z @kj export() moves the plate behind the crowd back to 36 m from row 450 down; posts and bowl were measured at 11 to 15 m, so each was cut in two at that row; the bowl stood on a 2-pixel rod
  - log: 2026-10-12T15:34:26Z @kj added
  - log: 2026-10-12T15:34:26Z @kj user chose: remove the posts, add a stand; fix built: posts and rod removed in stray() of wip/muster/host.py, stand as a mesh at the bowl's depth in src/muster.py; six test frames without sliding; full loop rendering
  - log: 2026-10-12T16:18:08Z @kj fix in out/16-muster.avif of 2026-10-12 18:13 and in the sermon package: posts and rod absent, bowl on a stand; bowl and stand centres 2.0 to 2.4 pixels apart in frames 0, 30, 60, 90; loop closes; before and after: wip/preview/muster-brazier-before-after.png; closure waits for the user's word
  - log: 2026-10-12T19:22:18Z @kj rendered again from the list of things, out/16-muster.avif of 21:14: posts and rod taken out in THINGS (R2, R3, R4), stand S5 and bowl at the railing's measured depth 8.9 m; bowl, stand and fire move together in frames 0, 30, 60, 90; awaits the owner's word
- [ ] `DEF-PLATE-16` **Post tops move with the smoke** - MAJOR; muster: crossbar and finial of banners B5 and B6 are smeared and move; the smoke flow region holds 84 % of the top of B5 and 50 % of B6; user: "top of the posts are not smoke!"
  - repro: enlarge the third and fourth banner left of the crane in out/16-muster.avif of 2026-10-12 22:43
  - test-tags: MANUAL
  - root-cause: 2026-10-13T07:55:12Z @kj the flow acts on a box of plate pixels (muster_fx.png), so every thing inside the box moves
  - log: 2026-10-13T07:55:12Z @kj added
  - log: 2026-10-13T12:13:11Z @kj fix rendered, awaits the owner's word: no effect acts on a box of pixels; posts are built rods and do not move; render of 2026-10-13 14:01, out/16-muster.avif
- [ ] `DEF-PLATE-19` **Brazier post stands on the front of the railing** - MEDIUM; muster: the stand S5 reaches row 534 and lies at 8.82 m; the railing begins at row 527 at 8.86 m, so the foot is drawn over the railing's top edge; user: "it must be behind the railing"
  - repro: enlarge the foot of the brazier post in out/16-muster.avif of 2026-10-12 22:43
  - test-tags: MANUAL
  - root-cause: 2026-10-13T07:55:21Z @kj the list gave the stand the railing as its support (on P2) and the scene drew it 0.5 % nearer than the bowl; my choice
  - log: 2026-10-13T07:55:21Z @kj added
  - log: 2026-10-13T12:13:11Z @kj fix rendered, awaits the owner's word: stand of the brazier ends behind the railing, 3 % deeper than it; close view wip/preview/frames3d/final-brazier.png; render of 2026-10-13 14:01, out/16-muster.avif
- [ ] `DEF-PLATE-20` **Banner posts are not joined to their banners** - MAJOR; muster: true posts stand at the right end of each crossbar and lie in the ground (B9 29.4 m, B10 32.7 m); crossbar and cloth lie at 21.2 and 19.2 m, so the camera slides them apart; post of B10 is faint; user: "posts are ... erased"
  - repro: enlarge banners B9, B10, B11 in out/16-muster.avif of 2026-10-12 22:43 and watch the right end of each crossbar
  - test-tags: MANUAL
  - root-cause: 2026-10-13T08:04:51Z @kj THINGS names the masts the image model painted under the cloths, not the posts of the source picture; the repaint under cloth B10 painted over its post; black posts under it were taken out
  - log: 2026-10-13T08:04:51Z @kj added
  - log: 2026-10-13T12:13:11Z @kj fix rendered, awaits the owner's word: eleven posts measured and built as rods (src/rods.py), crossbars stand on them; tower goes on behind post B1 (beyond), which removed a pale band of 8 px seen in test frame 30; render of 2026-10-13 14:01, out/16-muster.avif
- [ ] `DEF-PLATE-22` **Crossbars flicker** - MAJOR; owner: "there is flickering here" at the crossbars of the right banners; crossbar pixels of B2, B3, B4, B9, B10, B11 change between crossbar and sky from frame to frame, up to 195 of 360 frames; new in the loop of 2026-10-13
  - repro: count per pixel the frames with |f[n] - (f[n-1]+f[n+1])/2| over 12 of 255 in wip/frames-muster; crossbar rows inside the rectangle of N<n>
  - test-tags: MANUAL
  - root-cause: 2026-10-13T12:55:28Z @kj crossbar plane M<n> and painted mast plane N<n> have one depth and overlapping rectangles: two surfaces at one place, the renderer shows one or the other; B1, B12, B13 have no N and do not flicker
  - log: 2026-10-13T12:55:28Z @kj added
  - log: 2026-10-13T13:54:19Z @kj fix rendered, awaits the owner's word: crossbar and painted mast in one picture on one surface (planes in src/things.py, 10 surfaces); flicker count over 360 frames names no crossbar; render ended 2026-10-13T13:44Z, out/16-muster.avif
- [ ] `DEF-PLATE-24` **Dark specks flicker in the sky near the banners** - MINOR; 40 to 85 dark specks of 1 px per frame in the sky rows 0-139, most right of column 2128 and at columns 304-607; the source has none; they change from frame to frame; present in every kept loop since 2026-10-12
  - repro: python3 wip/muster/loopcheck.py - wip/frames-muster: region columns 2352-2363, rows 33-44; wip/preview/frames3d/specks-b13-wide.png
  - test-tags: MANUAL
  - root-cause: 2026-10-13T13:54:19Z @kj likely cause: seam between the ground with a measured depth and the ground without; 58 % of 280 specks lie within 6 px of that edge, 12 % of random sky places; how the seam makes a dark pixel is not verified
  - log: 2026-10-13T13:54:19Z @kj added
  - log: 2026-10-13T18:20:50Z @kj in the build of 20:16 the specks are more frequent: sky pixels at the right edge that change for one frame in 8 or more frames 141 against 110 before, greatest 87 against 69 frames; the ground was built again for DEF-PLATE-26; mechanism still not found
- [ ] `DEF-PLATE-26` **Pikes of the far wall behind the flames** - MEDIUM; the owner 2026-10-13: "posts are missing" at the far wall of the left terrace (paste-20261013-183322.png): 16 pikes on the wall top are faint and covered by the flames of fire F2; post B2 ends at the wall top; lamp fixtures under B3, B4 are blurred
  - repro: out/16-muster.avif of 18:15, any frame, columns 600-915, rows 430-470, against wip/scene3d/muster.png
  - test-tags: MANUAL
  - root-cause: 2026-10-13T17:39:48Z @kj pikes were part of the far picture at the depth of the sky behind them (56-67 m); flame F2 stands at 47 m, the wall at 27-46 m; rod of B2 measured only to the wall top, where post and wall are equally dark
  - log: 2026-10-13T17:39:48Z @kj added
  - log: 2026-10-13T17:39:55Z @kj fix rendering since 19:38: pikes built as rods on the wall W1 at its depth (PIKES, thing U1), post B2 goes on to the ledge at row 466; test frames 0, 90, 170, 270 differ from the build of 18:15 at the wall top only; lamp fixtures unchanged
  - log: 2026-10-13T18:20:50Z @kj fix rendered, awaits the owner's word: out/16-muster.avif of 20:16 shows the 16 pikes before the flames and post B2 to row 466; loop closes; no pixel at the wall top changes for one frame in 3 or more frames; tests pass; lamp fixtures under B3, B4 not rebuilt
  - log: 2026-10-13T19:18:02Z @kj superseded in one part by DEF-PLATE-27: the post of B2 now goes on to the floor of the walk (row 534), not to the ledge at row 466; the pikes are unchanged in the build of 21:13
- [ ] `DEF-PLATE-27` **Posts of banners B2 to B6 not planted in the floor** - MAJOR; the owner 2026-10-13: "banner posts on the left are not put in the ground where they should. first banner - yes, it is where it should be, a couple of meters left from the railing, but the other - no"; posts of B2-B6 end at the far wall top
  - repro: out/16-muster.avif of 20:16, any frame, columns 640-975, rows 440-540
  - test-tags: MANUAL
  - root-cause: 2026-10-13T18:36:57Z @kj T2, T3, T4 were set behind the whole crowd to hide their open ends: 6.5-7.1 scene m from the railing, where their cloths measure 3.7-4.2 m and B1 2.4 m; rods of B2-B6 were measured only to the far wall top, where the picture stops showing them
  - log: 2026-10-13T18:36:57Z @kj added
  - log: 2026-10-13T18:36:57Z @kj fix rendering since 20:36: T2-T6 stand on the floor among the crowd C1 at the depth of their cloths, foot rows 534, 501, 488, 479, 475 (wip/muster/feet.py); test frames 0, 90, 170, 270 differ from the build of 20:16 at banners B2-B6 only
  - log: 2026-10-13T19:18:06Z @kj fix rendered, awaits the owner's word: out/16-muster.avif of 21:13; posts of B2-B6 stand at cloth depth in the row of B1 and go down to the floor among the crowd; loop closes; no pixel at their lower parts flickers or jumps in 3 or more frames; tests pass

## Render `RENDER`

Scripts that render the frames of a loop and assemble it

- [ ] `DEF-RENDER-11` **Render ends when the crowd file is written again** - MEDIUM; muster: render of 03:06 ended at frame 146 of 360 with BadZipFile; wip/preview/muster-draft.avif then held 4.9 s that do not close; fix: scene() reads muster_crowd.npz whole at the start; src/muster.py
  - repro: start src/muster.py frames, run wip/muster/host.py export while it renders
  - test-tags: MANUAL
  - root-cause: 2026-10-12T02:21:08Z @kj pose() read arrays from the open muster_crowd.npz in every frame; wip/muster/host.py export wrote the file again at 03:20 while the render ran
  - log: 2026-10-12T02:21:08Z @kj added
  - log: 2026-10-12T02:21:08Z @kj fix built; not tested by writing the file during a render

