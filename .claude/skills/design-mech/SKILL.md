---
name: design-mech
description: Designs and animates BattleMechs for the funcraft banners (mech-design) - the walk of a chassis by its knee (a march for forward knees, a bird walk for reverse knees), body, pelvis and arm motion, finding and cutting a joint in a fused shell (elbow, hydraulic piston), assembling a mech from a kit of parts, colouring per chassis, ornament on armour plates, bored barrels, missile racks, heavy joints, cloth banners with tassels. Use when asked to make a mech walk, march, stomp or "move naturally", when a gait looks stiff, slow or sliding, "just puts leg up and down" or "like a chicken walker", when a limb "pivots around the wrong place", when adding a chassis, a rear rank or a twin, or when asked to paint, texture, ornament, dress or accessorise a mech (barrels, missiles, joints, banner, sigil, kutasy).
---

# Design mechs

Rules for the BattleMechs of the banners, each learned from a render the Star Colonel rejected. Paths are relative to `~/workspace/funcraft/mech-design/`; `PROCESSION.md` holds the orders and the numbers. Armature, skin weights and Cycles: `design-blender`. Loop rules and seam check: `design-gif`. The Mechanicum look of livery, cloth and sigils: `design-w40k`.

## Chassis

| Chassis | Knee | Walk | Notes |
|---|---|---|---|
| Atlas | forward | march | arms and arm guns stay with the body |
| BattleMaster | forward | march | sculpted mid-stride: its two legs have their own joints; lowered left arm has an elbow |
| Mad Cat | back | bird | weapon pods are fixed mounts: no arm swing |
| Marauder | back | bird | assembled from a kit; every part is rigid |

- A chassis enters every table: `CHASSIS` (`src/mechrig.py`), `JOINTS` (`src/rig.py`), `BIRD` or `MARCH` (`src/procession/gait.py`), `ARM_SWING`, `GAIT_OFFSET`, `REAR` (`src/procession/frame.py`). The Marauder enters them from `src/marauder.py`
- Rear ranks are twins: copies of mesh object and rig object that share mesh, livery and armature; the pose belongs to each rig. Each gets its own gait offset in whole frames. The camera jolts at the footfalls of the front three only

## Walk
`src/procession/gait.py` moves the body and the two foot controllers. The knee decides the walk; one walk with other numbers for both kinds was rejected: "forward knee walkers - they don't put their toes down like chicken walkers".

**Bird walk, knee back**
- Toes land first, foot pitched 26° toe down; it rolls down flat in 0.10 of the cycle - the shock buffer
- Foot stands 0.66 of the cycle; over the last 0.16 the heel peels up while the toes stand, so the toes leave last
- Swing: toe tip rises 0.6 m, foot hangs its front down by up to 50°, "legs higher, reach further"
- Body crouched, and 0.14 m lower over a standing leg (`rise` negative): the legs give under the load

**March, knee forward**
- Heel lands first on a reaching leg, toes up 10-12°; the foot rolls flat about the heel in 0.08 of the cycle
- Foot stands 0.62 of the cycle; the heel lifts only 6-7° before the toes leave. 24° showed toes pointing down from the front
- Swing: the foot comes forward nearly level, then toes up to 14-17°. Toes never down by more than 8°
- Body rises 0.26-0.30 m over a standing leg: the leg stays long

**Building a walk**
- Describe the point of the sole that stands, not the ankle: it moves back in a straight line at the speed of the ground. Bird: path of the toe tip plus pitch. March: heights of toe tip and heel (pitch follows, and the sole cannot go under the ground while both are ≥ 0) plus a lead point that goes from heel to toe tip
- Every curve is a cubic with matched slopes that leaves and meets the ground at ground speed. A jump in speed reads as stiff
- Measure the heel's end of the sole on the mesh (foot vertices within 0.12 m of the ground)
- Body height: one fixed lowering per chassis (`crouch`), as much as the longest reach needs with the leg at most 0.97 straight; `ahead` balances reach in front and behind. Nothing in the body's height switches between the legs. Lowering the whole mech is accepted
- All chassis keep one step rate. A longer step = a faster ground for all (`frame.STEP`, and the ground piece of `groundtex.py` has that length). Rejected: one gait cycle per loop ("walks too slowly"), a foot that stands 75 % ("just puts leg up and down, no gait")
- Judge on the bare skeleton before any render:
  `blender -b -P src/procession/gait.py -- <chassis>` then `python3 src/procession/skeleton.py <chassis>` → `wip/preview/procession/skeleton-<chassis>.png`, `.avif`, and the largest change of speed between frames (ankle 0.1-0.2 m, body 0.01 m)
- From the front the viewer reads the pitch of a foot: sole visible = toes up, top visible = toes down. Render check frames on the frames where feet land

## Body, pelvis, arms
- Pelvis (`src/procession/hips.py`): a bone that takes the body's weights below a measured waist height, no cut. Roll 4-5° once per cycle, swing-side hip up; yaw 3-5° (`turn`), side of the leading leg forward. `HIP_ROCK = 0` leaves the rig untouched, so the feature can be backed out
- Body: shifts 0.14-0.20 m over the standing foot, nods 0.015 rad twice per cycle
- Arms (`src/procession/arms.py`): a shoulder bone takes the arm's weights; arms turn 2.5-3.5° against the leg of their side. Fixed mounts do not swing
- A hanging forearm gets its own elbow and the largest swing: 12°, lagging the arm by 0.12 of a cycle. 4° was "barely moves"

## Joint in a fused shell
A sculpt carries no joint data, and a guessed pivot shows: "forearm pivots around wrong place, it must be at the joint".

- Find the hinge from the model. Two limbs that are the same parts in two poses (left and right arm): mirror one, lay it on the other per rigid body (Kabsch + ICP; pair vertices by nearest-neighbour distance descriptors, RANSAC was too slow). The relative screw of the two motions is the hinge line. BattleMaster elbow: 19.11° turn, 0.1 mm slide, 1.2 m from the guessed pivot
- Give each face to the body whose motion lays it on the twin; a face neither motion places takes the body of the faces it joins. Classifying vertices instead stretched faces across the hinge
- Cut with `bmesh.ops.split_edges` only along the seam where the two rigid bodies meet. This is the one cut allowed; any other cut shows (`design-blender`, Caveats)
- Hydraulic piston: a separate loose piece. One bone turns about its upper end and aims at the rod's end carried by the forearm; a child bone slides the rod by the change of length

## Mech from a kit
`src/marauder.py`: 19 printable parts, laid flat and apart.

- Fit a sphere or a circle to each ball, cup and pin (triangles whose normals agree with it); ball and cup of one joint have one radius
- The hull stays; every other part moves rigidly so its joint lies on its parent's joint. Ball joints leave angles free: choose the stance and state it as an assumption
- A part in two versions: use the closed shell (count open edges and loose shells)
- Keep 12 % of each part's triangles; give each part wholly to one bone (`skin`); the pelvis is a part (`pelvis`)
- Remaster what the kit has for printing, in a `dress` step after paint and before rig:
  - a flat disc closes every barrel → `inset_region` 0.7 m deep, black bore. Count the guns against the real design (two per arm pod)
  - missile rack → open tubes, each with a body and a pointed nose; flat caps read as plugs
  - snap-on balls → a steel hub with two bolted flanges and ribs on the joint's axis
- Add no emblem to the model unless ordered

## Colour and ornament
- One household, three enamels - Mars red, black, bone - and each chassis is led by another one. Paint by part on the mesh before rigging (`src/paint.py`); get stills approved first: `blender -b -P src/procession/livery.py -- <chassis> full|close|joints|hang [cloth]`
- Ornament lies on the mesh per armour plate: flat charts (`plating.py`), ornament chosen by plate size (`ornament.py`), motifs as grey relief pictures (`motifs.py`), all in `src/procession/`. Trims follow the plate's real outline, mirror twins match
- A restyle changes only the named parts
- A known sign is drawn exactly from its source (glyph picture, SVG paths with `svgelements`); the image model paints surfaces only, because it changes letters and shapes

## Cloth and tassels
`src/procession/cloth.py` moves it, `clothart.py` paints the Mad Cat's.

- A grid of its own, bound to the pelvis bone. It does not stretch: the place of each row follows from the angle to the vertical - lean 7° from the wind of the walk, 3° swing per step as a wave down the cloth, 2° ripple - each a function of gait phase or place in the loop
- Mount: a rod under the lowest part of the pelvis, between the thighs. Measure the underside first; a rod under the nose hung in the air in front of the mech
- About 1 m wide on a 12 m mech; 1.5 m was "too wide". Never plain cloth
- A forked end is cut by the picture's alpha, so the border can follow it
- Tassels are part of the cloth's mesh: they hang from the lower corners at the angle the cloth would have a little further down, slightly later. Gold, and only where ordered

## Order of work
- Each numbered banner is the one before plus one change; a superseded number is not rendered again; a fix to a shared part is rendered into every current number
- Check frames first, then the full render, then the seam check (`design-gif`)
- Renders run detached from a queue script in `wip/logs/`. Never edit a running script. A script that waits with `pgrep -f <pattern>` hangs when the shell that launched it has the pattern in its own command line: wait for a line in a log instead
- Never kill a process that is on a GPU; stop a queue by killing its wrapper shell
- Stills for a check go to `wip/preview/`, a page of pictures to `out/`; animations are AVIF at 30 frames per second
- No smoke from the mechs, no halos

<!-- improved 2026-10-07 | body 0→1621w / 0→90L | trigger n/a (unrun) | via improve-skill -->
