# Mech design - Procession banner v6

Status: DRAFT for internal review, 2026-10-07.

## Contents

- [1. Request](#1.-Request)
- [2. Picture](#2.-Picture)
- [3. Pipeline](#3.-Pipeline)
- [4. Backdrop](#4.-Backdrop)
- [5. Ground](#5.-Ground)
- [6. Livery](#6.-Livery)
  - [6.1 Plates](#6.1-Plates)
  - [6.2 Ornament](#6.2-Ornament)
  - [6.3 Household colours](#6.3-Household-colours)
  - [6.4 Cloth of the Mad Cat](#6.4-Cloth-of-the-Mad-Cat)
- [7. Air](#7.-Air)
- [8. Loop](#8.-Loop)
- [9. Frame measurements](#9.-Frame-measurements)
- [10. Marauder](#10.-Marauder)
- [11. Open points](#11.-Open-points)

## 1. Request

This section records what the user asked for. The scene becomes `out/07-banner-procession.avif`; with rocking hips `out/08-banner-procession-hips.avif`; with six more mechs `out/09-banner-procession-column.avif`; with the Marauder in the place of one rear BattleMaster `out/10-banner-procession-marauder.avif`. Each number keeps what the number before it has and changes one thing.

- **Source** - `out/03-banner-models.gif`: three BattleMechs walk at the camera, the ground moves under them, a rendered backdrop stands behind
- **Kept** - the three meshes, their armature, their walk, their places in the frame, the camera, the moving ground as a principle
- **Backdrop** - "change backdrop such that it will co-exist nicely with the moving ground and the walking robots". It is distant, it is made with the plate pipeline of `w40k-mechanicum` (generated picture, depth from MoGe-2), and "it must explicitly be very mechanicum-like or holy-terra like". Its depth is edited by hand where the model is wrong, and it is animated where that is warranted
- **Mechs** - "coloured and embroidered with symbols with intricate details - in blender. details were to be super-delicate, detailed to look as if part of the original model and carry motiffs from w40k"
- **Heraldry** - "think of imperial knights insignia, that would look very well on battlemechs"
- **Effects** - "use also effects - smoke and so on, with simulation etc"
- **Bar** - "must look legit, fidelity of animation comparable to those from w40k"
- **Place** - the scene belongs to `mech-design`, not to `w40k-mechanicum` (order of 2026-10-06)
- **Review of the first render, 2026-10-06** - "no halos please"; "let smoke not go off the mechs themselves"; "let them have different phase offset for gait; and remember about rumble"; "from now on lets not use gif, use avif"; "add some fog, like we used before"; "smoke from factories - needs to be real, dense slowly moving smoke (as it is far away)"; on the hips: "let hips rock a little; just a tiny bit when walking", "render as next - 08", "allow me to back out from this if it works incorrectly"
- **More mechs, 2026-10-06** - "can you put more mechs behind those? like 5 more - also alternate phase and position - but rumble is associated only wit the front 3 ones"; the result is a separate output, number 09; then "put somewhere in between another madcat"
- **Motion, 2026-10-06** - "when madcat puts their leg up, the front of the foot needs to point more at the ground, like birds do"; "let's make the animation 30fps"; "slightly move the mechs arms during the gait", "except for madcat (fixed mounts)"; "battlemaster - the lowered arm, can you animate the forearm joint too", and after the first render of it: "left forearm barely moves, it needs to move the most"
- **Marauder, 2026-10-06** - a fourth chassis from an assembly kit: "try assembling marauder and when ready - paint it and add mechanicum embroidery and see if you can animate it similarly; when ready - show me preview"; "some parts are in two versions, you need to find out which one works best"; "put somewhere mechanicus glyph on the corpus (the one with skull)". It walks alone in a preview and in banner 10
- **Marauder in banner 10, 2026-10-06** - a first render had it as a tenth mech at the right edge. The user: "do not add it on the right", "marauder replaces ... the second battlemaster from the left (at the back) this way marauder is nicely shown". On the model: "remove mechanicum sigil from torso's rocket launcher", "no need for sigil"; "make the barrels show like they actually have depth", "currently you plugged them with beige cap", "marauder has 2 guns in each arm"; "marauder torso has the missle array - that also nees to kind of show the heads of missiles there"; "you need to rock the hips"; "do not make it smaller, make it just do longer steps"; after a render with one step per two steps of the others: "marauder walks too slowly"; after a render with the others' step rate and a foot that stands for 75 % of the cycle: "now marauder doesn't walk - it just puts leg up and down, no gait", "it must look like it walks confidently and animation is fluid"; "from the crotch - you can show hanging cloth banner with mechanicum (as an option) - so make 2 such images - one with and one without", then "add to that marauder the cloth, and to the madcat in the front another cloth, just with two-color design, slightly moved by the wind and gait"; "marauder model ... has on the joint between torso and legs and torso and arms - the ball snap-ons (because it was designed as snap-on toy), needs to be remastered to industrial heavy duty joints"
- **Walk, 2026-10-06** - "both madcat and marauder must move their legs higher, and reach further"; "it is ok if the entire mech kind of moves lower as a result; you may try skelegon based movement to get the fluidity and natural gait - and then translate to models"; "also atlas must march more naturally, mobing leg a little further"; "you can increase the pelvis rocking to 4-5 degrees". On the foot of a bird: "when leg moves up, it starts lifting from the heel, and the last part leaving the ground is front of the foot, which leaves contact last", "the same when stomping down - fingers make first contact and then the rest", "in birds - this acrs as the shock buffer too". After a render in which all chassis had the bird's foot: "walk type must be broken between knee front and knee back (reverse) joints, can't use the same walking style, must be different", and on a banner that still had that walk: "the gait of forward knee walkers - they don't put their toes down like chicken walkers"
- **Cloth of the Mad Cat, 2026-10-06** - after a cloth in two plain colours: "the cloth under madcat is too wide and ... has nothing on it; I wanted this to be meticulously creafeted holy cloth - just using two colours, but still with inscriptions, sigils etc"; "maybe stellars-tech logo (without text) - just painted in lore colours", "in lore style"; "and embroidery"; "also add kutasy to the cloth" (kutas is the Polish word for a tassel); "make kutasy golden, and leave only bottom ones"; "the cloth on madcat is mounted too far to the front, must be mounted further back under the torso"
- **Elbow and hips, 2026-10-06** - "battlemaster forearm pivots around wrong place, it must be at the joint, it may be complicated but do it nevertheless"; "there is 'hydraulic shaft' in the forearm joint - that I would like to see that is actuated when forearm moves". On the hips of banner 08: "yes 08 keep", "do not render 7", "we have 8 that replaced it", "9,10 - rock hips", and "from now on we stage animations up"

## 2. Picture

This section describes what the viewer sees. Three BattleMechs in the livery of one knightly household of the Cult Mechanicus walk at the viewer across the deck of a forge.

- **Far** - a skyline of forge towers, cog wheels, chimneys with slowly rolling black smoke and furnace fires under a wide sky with light shafts. It stands on the horizon, pale with haze
- **Ground** - a deck of riveted black iron with brass inlays, wet in places, with grates that glow orange. It slides away from the viewer at the speed of the mechs' feet
- **Mechs** - an Atlas in red on the left, a Mad Cat in black in the centre, a BattleMaster in bone on the right. Every armour plate has a trim, and the larger plates carry engraving, emblems and heraldic fields
- **Air** - a low ground fog lies on the deck behind the mechs, and embers rise from the deck. No smoke leaves the mechs
- **Motion** - the mechs walk out of step, and the camera jolts at every footfall. The chassis have two walks. The Atlas and the BattleMaster, whose knees point forward, march: the heel lands first with the toes up, the foot rolls down flat, and the body rises over the standing leg. The Mad Cat and the Marauder, whose knees point back, walk as birds do: the toes land first and leave last, the lifted foot goes high with its front hanging down, and the body sinks a little over the standing leg. The arms of the Atlas and the BattleMaster swing a little against the legs. The forearm of the BattleMaster's lowered arm swings the most: it turns about its elbow hinge, and the hydraulic piston in front of the hinge gets longer and shorter with it. The Mad Cat's weapon pods are fixed mounts and stay. From banner 08 on the hips rock a little with every step
- **Banner 09** - six more mechs walk behind the three, in two ranks: from the left of the picture a Mad Cat, a BattleMaster, a BattleMaster, an Atlas, a Mad Cat and an Atlas, in the colours of their chassis. Each chassis walks three times. The viewer sees them in the gaps between the three and beside them, with their legs in the ground fog
- **Banner 10** - a Marauder in red walks in the place of the rear BattleMaster between the Atlas and the Mad Cat, the best seen place behind the three. It walks as the Mad Cat does. It and the Mad Cat of the three wear a cloth banner between the legs: the Marauder's is crimson with gold embroidery, the Mad Cat's is red velvet embroidered with bone thread, with a golden tassel at each lower corner. Both lean back in the wind of the walk and swing a little with every step
- **Size** - the viewer sees 1140 × 360 pixels. A mech is 170 to 230 pixels tall there, so 1 pixel is 5 to 7 cm on a mech

## 3. Pipeline

This section lists the steps in the order they run, from `mech-design`. The generators of steps 1 to 3 and the gas solver of step 7 belong to the sibling project `w40k-mechanicum`; `PY` is its Python, `../w40k-mechanicum/.venv-moge/bin/python`, and `BL` is `~/.local/opt/blender-4.5.9-linux-x64/blender -b -P`. Every GPU command starts with `CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=<index>`, and the generators with `HF_HUB_OFFLINE=1`.

| Step | Command | Output |
|---|---|---|
| 1. Backdrop plate | `PY src/procession/plates.py gen forget 5`, `widen forget 5`, `pick forgeto 51`, `desmoke forgeto51`, `edit forgeto51c` | `wip/scene3d/terra_forgeto51c.png`, `.npz`, `_fx.npz` |
| 2. Ground piece | `PY src/procession/groundtex.py gen iron 2`, `maps iron 2 65 425` | `wip/procession/ground/` |
| 3. Motifs | `PY src/procession/motifs.py gen all 1 2` | `wip/gen/motif_<name>_<seed>.png` |
| 4. Plate charts | `BL src/procession/plating.py` | `wip/procession/plating/<chassis>.npz` |
| 5. Ornament | `PY src/procession/ornament.py` | `wip/procession/livery/<chassis>_colour.png`, `_surface.png`, `_height.png` |
| 6. Close view | `BL src/procession/livery.py -- <chassis> close` | `wip/preview/procession/livery-<chassis>-close.png` |
| 7. Chimney smoke | `PY src/procession/chimneys.py` | `wip/procession/chimneys/<k>.npz` |
| 8. Test frames | `BL src/procession/scene.py -- livery=livery tag=test 0 20` | `wip/preview/procession/test-f000.png`, `test-f020.png` |
| 9. Render | `BL src/procession/scene.py -- livery=livery` | `wip/frames-procession/f000.png` to `f087.png`, `seam-check.png` |
| 10. Animation | `python3 src/assemble.py wip/frames-procession out/07-banner-procession.avif` | `out/07-banner-procession.avif` |
| 11. Banner 08 | `make procession-hips`: steps 9 and 10 with `hips=4.5 out=frames-procession-hips` | `out/08-banner-procession-hips.avif` |
| 12. Banner 09 | `make procession-column`: steps 9 and 10 with `hips=4.5 rear=6 out=frames-procession-column` | `out/09-banner-procession-column.avif` |
| 13. Marauder | `BL src/marauder.py -- build`; steps 4 to 6 with `marauder`; `BL src/procession/scene.py -- livery=livery hips=4.5 cloth=1 solo=marauder out=frames-procession-marauder` | `in/models/marauder.stl`, `marauder.json`; `wip/preview/procession/marauder-walk.avif` |
| 14. Cloth of the Mad Cat | `PY src/procession/clothart.py velvet`, `python3 src/procession/clothart.py` | `resources/assets/cloth-madcat.png`, `cloth-madcat_silk.png` |
| 15. Banner 10 | `make procession-marauder`: steps 9 and 10 with `hips=4.5 rear=6 marauder=0 cloth=1 out=frames-procession-ten` | `out/10-banner-procession-marauder.avif` |

- **Contract** - `src/procession/frame.py` holds the camera, the mechs' places, the timing and the loop rules. Every other module reads them from there
- **Sibling project** - `src/procession/gen.py` loads the Z-Image-Turbo generator of `w40k-mechanicum` and sets it to write drafts into `wip/gen/` here. Steps 4, 6, 8 to 13 and 15 need only Blender, a Python with Pillow, and the data under `wip/`; the second command of step 14 needs a Python with NumPy, SciPy and svgelements. `make procession` runs steps 9 and 10
- **Format** - an animated AVIF in full colour at 30 frames per second, written from the rendered frames (`src/assemble.py`, quality 88, colour at full resolution; a frame lasts 33 or 34 ms, because the format counts whole milliseconds). A GIF of this scene was 17.9 MB, and its palette of 255 colours changed the tones of bone and gold

## 4. Backdrop

This section covers the far skyline. `src/procession/plates.py` makes the plate and `backdrop` in `src/procession/scene.py` builds it.

- **Strip** - the scene camera stands 8.6 m above the ground and its horizon is on row 295 of a 2432 × 768 plate. The ground covers everything below, so the skyline has 295 rows
- **Wide sky** - Z-Image-Turbo fills 65 to 80 % of any picture's height with towers. `widen` reduces a draft to half size, sets its mirror images beside it and repaints the whole at strength 0.5. The result is a low skyline under a tall sky, at full width
- **Depth** - `pick` runs MoGe-2 and sets the strip into the plate with its horizon on row 295. `edit` corrects the depth: calm pixels connected to the top are sky, holes take the depth of the nearest pixel
- **Mesh** - one vertex per 2 plate pixels, each on its own camera ray, at the corrected depth. One factor scales all depths so that the plate's own ground lies on z = 0. The mesh emits the plate and takes no light
- **Haze** - a structure pales towards the horizon colour with its distance (`HAZE`), so near towers are darker than far ones
- **Motion** - the sky drifts 10 pixels to the right and 3 up per loop. Two readings half a loop apart are cross-faded, so the drift has no jump. Flames change brightness by 30 %
- **Margin** - the mesh reaches 16 plate pixels beyond the frame on the left, the right and the top, with the plate's edge pixels repeated. The camera's jolt at a footfall turns the view by up to 0.12°, 4 pixels, and would show a gap
- **Join** - a ground fog in the horizon colour, absorption plus emission, covers the line where the deck meets the plate. It starts 150 m behind the scene's origin and is full from 900 m on, so it does not veil the mechs

## 5. Ground

This section covers the moving deck. `src/procession/groundtex.py` makes its piece and `ground` in `src/procession/scene.py` lays it.

- **Piece** - a picture from straight above, generated with Z-Image-Turbo. Rows 65 to 425 of draft `ground_iron_2` stand for 7.5 m along the way and 42.7 m across. 7.5 m is the ground's travel in one gait cycle; it was 5 m until the walk got its longer step (section 8)
- **Period** - the piece is laid mirrored in both directions, so no seam shows. Along the way it repeats every 15 m, which is the ground's travel in one loop
- **Maps** - brass is metal and smooth. The rest is wet iron: a slow noise makes puddles. Dark joints are low. The grates emit orange light
- **Light** - area lights of 450 W shine upward, one per glowing line, from 135 m behind the three mechs to 60 m in front of them: 52 lights, and 92 with the rear mechs, whose row starts 285 m behind. They slide with the ground, so the light on the mechs' legs moves
- **Periodic noise** - the puddle noise reads its y coordinate rolled onto a cylinder whose circumference is the ground's travel in one loop. Without this the loop showed a jump: 105,718 pixels differed by more than 8/255

## 6. Livery

This section covers the colour and ornament of the mechs. It is drawn per armour plate and lies on the mesh; nothing is painted in 2D after rendering.

### 6.1 Plates

This subsection covers how the armour is divided. `src/procession/plating.py` gives every armour plate a flat chart in one picture per mech, the atlas.

- **Plate** - a patch of `src/paint.py`: faces whose neighbours' normals differ by less than 10°. Patches under 0.03 m² are machinery and keep their gunmetal
- **Chart** - the plate projected on its own plane, with the world's up as the chart's up (the mech's forward for a plate that lies flat). An emblem therefore stands upright, and lettering reads from left to right. A part of a plate under 0.05 m² gets no chart and keeps plain enamel
- **Atlas** - 8192 × 8192 pixels per mech, all charts at one scale

| Chassis | Charts | Charted area | Scale |
|---|---:|---:|---:|
| Atlas | 3065 | 767 m² | 198 px/m |
| Mad Cat | 1031 | 277 m² | 299 px/m |
| BattleMaster | 2467 | 466 m² | 227 px/m |

### 6.2 Ornament

This subsection covers what is drawn on a plate. `src/procession/ornament.py` decides by the plate's radius, the radius of the largest circle that fits in it.

| Radius | Ornament |
|---|---|
| under 7 cm | a dark seam line round the plate |
| from 7 cm | a band of bare steel with rivets |
| from 18 cm | a raised gold trim with rivets, and an engraved field |
| from 24 cm | 60 % carry an emblem in gold relief; 16 % have a halved field; 8 % have warning stripes |
| from 36 cm | a cog-tooth border inside the trim, an emblem, and a scroll with a motto |

- **Edge** - trim, band and seam follow the plate's real outline at a constant distance. This is what makes them read as part of the model
- **Engraving** - two patterns, a damask of quatrefoils with skulls and a filigree of vines. On red and bone they darken and lighten the enamel; on black they are inlaid in gold
- **Emblems** - cog with skull, skull in laurels, winged skull, cog-axe and staff, chalice with flames, winged hourglass, candles on a skull, fleur-de-lys, wax seal. A plate on the centre line of the mech carries the cog with skull
- **Source of the motifs** - `src/procession/motifs.py` generates each emblem and pattern as a grey relief picture, white raised on black. Its grey is the height and the shading of the gold
- **Lettering** - AVE OMNISSIAH, DEUS IN MACHINA, OMNISSIAH VULT, MACHINA VULT, PRO OMNISSIAH, MEMORIA AETERNA, SPIRITUS MACHINAE. It is drawn with a font, never generated, so the spelling is exact
- **Symmetry** - every choice is made from the plate's size and place with the side left out, so a plate and its mirror twin get the same ornament
- **Material** - `src/procession/livery.py` puts the atlas into the surface of `src/paint.py`: colour, metal, roughness and height as relief, under the same dirt and edge wear as banner 03

### 6.3 Household colours

This subsection gives the enamel of each mech. The three colours are Mars red, black and bone; each mech is led by another one.

| Chassis | Main | Second | Third |
|---|---|---|---|
| Atlas | red hull and legs | black arms and shoulders | bone skull |
| Mad Cat | black body and legs | red arms and feet | bone rack fronts |
| BattleMaster | bone | red helmet and feet | - |

### 6.4 Cloth of the Mad Cat

This subsection describes the cloth banner of the Mad Cat of the three, which `src/procession/clothart.py` paints: red velvet embroidered with bone thread, 1.0 m wide and 3.0 m long, with a forked lower end. Section 8 gives its motion.

- **Layout** - from the top: AVE OMNISSIAH; a cog wheel with the mark of Stellars Tech; STELLARS in binary, eight bytes in two rows; PER CALCULUM AD ASTRA; the cog with the skull of `resources/assets/zl789e1341kd1.jpg` between two stars; DEUS IN MACHINA; three small cogs; a star in a lozenge; a star in each tail of the fork. A border of two lines with cog teeth between them and a chain of beads follows the edge
- **Mark** - the two halves of `resources/assets/stellars_tech_ai_lab_gh_behemoth_logo.svg` without its lettering, read from the file's paths. The wheel's disc is parted as the Machina Opus is: the left half of the mark is bone on red, the right half red on bone. The stars of the cloth are the star of the mark
- **Inscriptions** - set in type and laid as thread, so every letter is right. The image model was tried on the whole layout and is not used for it: at a strength of 0.30 it wrote FER for PER and changed the binary digits, and at 0.55 it painted a skull in the place of the mark
- **Velvet** - a picture of worn silk velvet alone, with a damask of cog wheels in the pile, that Z-Image-Turbo paints (draft 4). Only its brightness is used, on the household's red, so the cloth has one red
- **Thread** - laid in ridges that follow the outline of every shape, with a darker cord along the edges and a shadow on the pile; a few stitches are worn through. `cloth-madcat_silk.png` says where the thread is: there the cloth stands higher and is less rough
- **Tassels** - a golden tassel on a cord of 0.10 m hangs from each of the two lower corners: a round head, a band round the neck and a skirt of 24 threads, 0.45 m in all. A first version also had one at each end of the rod, in bone and red; the user ordered gold and the lower two only
- **Mount** - a brass rod with two straps under the lowest part of the pelvis, between the thighs, 0.6 m behind the mech's origin and 6.0 m over the ground. A first place 3 m further forward left the rod in the air under the nose, 2 m below the hull
- **Rejected** - a cloth of 1.5 m in two plain halves, red and bone: "too wide and ... has nothing on it"

## 7. Air

This section covers the fog, the embers and the smoke of the factory chimneys. `mist` in `src/procession/scene.py` makes the ground fog, `src/procession/effects.py` the embers and the placing of the smoke, `src/procession/chimneys.py` the smoke itself.

- **Ground fog** - the fog of banner 03: dense at the floor, falling to 1/e every 2.8 m of height, broken into patches by noise stretched along the ground. It fades in between y = -42 m and y = -75 m, behind the BattleMaster at y = -31 m, so none of it is in front of a mech. It stands still, and it shows the horizon colour
- **Fog density** - 0.016 per metre at the floor. Banner 03 has 0.028, which hid the far deck in this scene
- **Embers** - 160 glowing specks leave the deck, rise 4 to 10 m and go out. The air stands still over the ground, so an ember moves away with the ground while it rises
- **Chimney smoke** - six chimneys of the backdrop carry simulated smoke. The user asked for it on 2026-10-06: "needs to be real, dense slowly moving smoke (as it is far away)". The plate's own painted smoke stood still, so `plates.py desmoke` paints it out (Z-Image-Turbo inpainting) before the depth step
- **Solver** - `src/smoke.py` of `w40k-mechanicum`: the Navier-Stokes equations with buoyancy for the air, particles for the smoke, in a box of 0.4 × 0.4 × 0.8 m. A chimney is not a wick: the air over a mouth of 2.2 cm radius is heated to 90 K over the room, and the particles wander more, so the plume is a dense rolling column and not a thread
- **Slow motion** - after 8 s of warm-up the air is recorded for 60 frames that are 1/480 s apart. The loop shows 0.125 s of the plume, 24 times slower than the candle's time
- **Smoke loop** - the record is read twice, half a loop apart. Each reading starts again while it is faded out, so frame 60 is frame 0 and the smoke is equally soft in every frame
- **Placing** - each plume stands 3 % behind its chimney and 30 % of its height below the mouth: the chimney hides the narrow jet a plume starts with, and the rolling smoke begins at the mouth. A plume is 45 to 100 m tall, 750 to 1200 m from the camera
- **Render** - one OpenVDB file per loop frame. The smoke emits and absorbs and does not scatter. Thin smoke at a plume's edge is lighter than its thick core, as sky light on rolling smoke is
- **Density trap** - Blender counts a volume's density in the object's own space. Dividing the absorption by the object's scale made the smoke a hundred times too thin, and it did not show
- **No smoke from the mechs** - a first render had exhaust smoke behind each mech. The user ordered it off on 2026-10-06
- **Rejected** - steam columns over vents of the deck. A thing that stands on the ground must repeat within the ground's travel of one loop, then 10 m, which made dense rows of columns

## 8. Loop

This section states what makes frame 88 equal frame 0. `src/procession/frame.py` holds the numbers.

- **Timing** - 88 frames at 30 per second, 2.93 s: two gait cycles of 44 frames. A gait cycle lasts 1.47 s; banner 03 has 30 frames of 50 ms, 1.5 s. 44 is even, so both feet of a mech land on a frame. The ground travels 7.5 m per gait cycle, 15 m per loop; until the walk of `src/procession/gait.py` it was 5 m and 10 m
- **Gait offsets** - as banner 05, the Atlas walks 16 frames and the BattleMaster 31 frames ahead of the Mad Cat. The six footfalls of a gait cycle land on frames 0, 6, 13, 22, 28 and 35
- **Rumble** - as banner 05, the camera jolts at every footfall: 0.1° of pitch as a cosine of 7 Hz that falls to 1/e in 0.1 s, with a little yaw and roll to the side of the foot. Time since a footfall is counted in whole frames modulo the gait cycle, so the jolt repeats exactly
- **Walk** - `src/procession/gait.py` moves the controllers of the armature of banner 03: the body and the two foot targets. It has two walks, and the knee of a chassis decides which one it gets. In both, a point of the sole that stands moves back at the speed of the ground, and every curve of a foot leaves and meets the ground with that speed and without a kink, so no speed jumps. The body sits lower than at rest by one fixed amount per chassis, as much as the longest reach of a leg needs
- **Bird walk** - Mad Cat and Marauder, knees back. The toes land first, with the foot pitched 26° toe down, and the foot rolls down flat in 0.10 of the cycle, which takes the shock. The foot stands for 0.66 of the cycle. Over the last 0.16 of that the heel rises while the toes stand, so the toes leave last. In the swing the toe tip rises 0.6 m and the foot hangs its front down by up to 50°. The body is 0.14 m lower over a standing leg than between two steps, because the legs give under the load. The Mad Cat sits 0.43 m lower than at rest, the Marauder not at all
- **March** - Atlas and BattleMaster, knees forward. The heel lands first on a leg that reaches forward, with the toes up by 12° (Atlas) or 10° (BattleMaster), and the foot rolls down flat about the heel in 0.08 of the cycle. The foot stands for 0.62 of the cycle. Over the last 0.14 of that the heel rises by 7° or 6° while the toes stand, and the toes leave last. In the swing the foot comes forward nearly level and its toes go up, by up to 17° or 14°, for the next landing. The foot never points its toes down by more than 8°; the bird's foot does so by 50°. The body is 0.30 m or 0.26 m higher over a standing leg than between two steps, because the leg stays long. The Atlas sits 0.35 m lower than at rest, the BattleMaster 0.16 m. The heel's end of the sole is measured on the mesh: 1.50 m and 1.48 m behind the ankle
- **Check on the skeleton** - `blender -b -P src/procession/gait.py -- <chassis>` records the leg bones, the soles and the body of the armature alone through a gait cycle, and `python3 src/procession/skeleton.py <chassis>` draws them from the side and from the front (`wip/preview/procession/skeleton-<chassis>.avif`). A walk is judged there before a model is rendered with it. The largest change of an ankle's speed between two frames is 0.12 m forward and 0.06 m up for the Atlas, 0.22 m and 0.11 m for the Mad Cat; of the body's height 0.012 m and 0.006 m
- **Rejected walks** - the walk of `src/rig.py` with a foot that hangs 30° at mid-swing (banners 08 to 10 until 2026-10-06: the legs did not go high and far enough); one walk with the bird's foot for all four chassis (the two kinds of knee must walk differently: "forward knee walkers - they don't put their toes down like chicken walkers"); a march whose heel rose to 24° before the toes left (from the front the toes point down)
- **Arm swing** - `src/procession/arms.py` adds a bone per arm at the shoulder to the rig of banner 03 and moves the arm's weight from the body bone to it; the mesh is not cut. The arms turn about the sideways axis once per gait cycle, against the leg of their side: Atlas 3.5°, BattleMaster 2.5°, Marauder 2.5° (`ARM_SWING`). The Mad Cat has no entry
- **Elbow** - the forearm of the BattleMaster's lowered left arm turns 12° to each side about its elbow hinge, 0.12 of a cycle after the arm. The hinge is read off the model: its two arms are the same parts in two poses. Mirrored, the left arm lies on the right one after one rigid motion where it is upper arm (1705 vertices agree within 3 mm) and after another where it is forearm (723 vertices). The two motions differ by a turn of 19.11° about one line with 0.1 mm of slide along it, and that line is the hinge: it passes through (-3.60, -2.03, 7.22) m with the direction (0.981, 0.082, -0.178), under the cap at the back of the elbow. The pivot used before lay 1.2 m higher
- **Cut at the elbow** - upper arm and forearm are two rigid bodies in one fused shell. A face belongs to the body whose motion lays its vertices on the other arm; a face that neither places, as on the hand, takes the body of the faces it is joined to. The mesh is cut along the 99 vertices where the two bodies meet, so no face stretches across the hinge
- **Piston** - the hydraulic piston in front of the hinge is a separate piece of 182 vertices. It turns about its upper end, on the upper arm, and keeps pointing at the place on the forearm where its rod ends, 0.66 m in front of the hinge; the end ring of the rod slides along it to that place, 0.14 m each way. In the model's right arm, whose elbow is 19° straighter, the same piston is 0.25 m longer
- **Hip rocking** - `src/procession/hips.py` adds a bone for the pelvis to the rig of banner 03 and rolls it about the forward axis once per gait cycle: the hip of the swinging leg rises, the hip of the standing leg sinks. With it the pelvis turns about the upright axis, so that the side of the leading leg is forward: by 5° in the bird walk, 4° for the Atlas and 3° for the BattleMaster. Banners 08, 09 and 10 have the roll at 4.5° (3° until the user allowed 4 to 5); banner 07 has neither. `HIP_ROCK` in `src/procession/frame.py` is the angle and is 0: then the module does not run and the rig is that of banner 03. `hips=4.5` on the scene's command line sets it for one render, and the make targets of banners 08 to 10 pass it. The mesh is not cut: the pelvis is the weight of the body bone below a waist height measured per chassis. The Marauder's pelvis is one of its rigid parts, the lower torso with the glyph on it
- **Rear mechs, banners 09 and 10** - `REAR` in `src/procession/frame.py` lists them: chassis, place, frames ahead in the gait. `REAR_COUNT` is 0, and `rear=6` on the scene's command line sets it for one render (banners 09 and 10); `marauder=0` puts the Marauder in the place of the first of them (banner 10). A rear mech is a twin of the front mech of its chassis: copies of the mesh object and the rig object that share the mesh, its livery and the armature; the pose belongs to each rig. The Marauder has no front mech and is loaded as the three are. The footfalls of the nine mechs land on different frames of the gait cycle. The camera's jolt is computed from the three only. The row of lamps under the glowing grates slides 15 m per loop, so with rear mechs it reaches 143 m behind the rearmost one: a mech near an end of the row is lit differently at frame 60 than at frame 0
- **Marauder's gait** - the bird walk, at the step rate of all chassis. The ground has one speed, so a longer step at the same step rate needs a faster ground: the ground's travel per gait cycle went from 5 m to 7.5 m for all. Two earlier attempts at a longer step for the Marauder alone were rejected: one gait cycle per loop (steps twice as long, "too slowly"), and a foot that stands for 75 % of the cycle (it swings forward in 11 frames, which from the front shows as a leg that goes up and down)
- **Cloth banners** - `src/procession/cloth.py` hangs a cloth between the legs of the Marauder and of the Mad Cat of the three (`cloth=1`, banner 10): a grid of its own on a brass rod, bound to the bone of the pelvis. The cloth does not stretch; its shape follows from its angle to the vertical at every point down its length. The wind of the walk lays the lower end back by 7°, every step swings it by 3° as a wave that runs down the cloth, twice per gait cycle, and the wind sends three ripples of 2° per loop down and across it. The lower end goes 4 cm to each side with the hips. A tassel is part of the cloth's mesh: it hangs from a lower corner at the angle that the cloth would have a little further down, 0.04 of a gait cycle later. A twin of a mech has no cloth
- **Still** - lights, the backdrop's structures
- **Sliding** - a thing on the ground is a child of `scene.ground` and repeats along the way with a period that divides 15 m
- **Cyclic** - every other motion makes a whole number of cycles in 88 frames
- **Transient** - a thing that is born and gone within one loop needs no repeat in space. Each ember lives one loop and is born again in its own place
- **Proof** - frame 88 is rendered as `seam-check.png` and compared with frame 0. Of 729,600 pixels, those that differ by more than 8/255: banner 08 has 1542 (mean difference 0.23 of 255), banner 09 has 1389 (mean 0.26), banner 10 has 1323 (mean 0.26), the Marauder alone has 704 (mean 0.14). The pixels lie scattered over the mechs, as render noise does: at most 22 pixels of a banner differ by more than 40/255 (the largest single difference is 169/255), and the largest mean difference over any 9 by 9 pixels is 7/255. One cause of a shaped difference was found and removed earlier: a mech near an end of the row of grate lamps (see the rear mechs above)

## 9. Frame measurements

This section gives the measured places in the render of 1520 × 480 pixels (`wip/preview/procession/layout.png`, `wip/procession/layout.json`). Rows count from the top. World +X is on the left of the picture.

| Thing | Value |
|---|---|
| Horizon | row 184 |
| Atlas, box | x 314 to 563, rows 90 to 390, 77 m from the camera |
| Mad Cat, box | x 740 to 996, rows 113 to 420, 66 m |
| BattleMaster, box | x 1058 to 1255, rows 129 to 359, 89 m |
| Ground at y = 0, 58 m from the camera | row 446 |
| Ground at y = -50, 108 m | row 325 |
| Ground at y = -100, 158 m | row 281 |
| Ground at y = -400, 458 m | row 218 |
| Field of view | 46.4° wide, 15.4° high |

| Rear mech of banners 09 and 10 | Root, world x and y | Distance from the camera | Frames ahead in the gait cycle of 44 | Place in the picture |
|---|---|---:|---:|---|
| BattleMaster; in banner 10 the Marauder | 9.5 m, -90 m | 148 m | 19 | between the Atlas and the Mad Cat |
| Atlas | -46 m, -75 m | 133 m | 35 | right of the BattleMaster |
| Mad Cat | 53 m, -82 m | 140 m | 25 | at the left edge |
| Atlas | -29 m, -140 m | 198 m | 6 | between the Mad Cat and the BattleMaster |
| BattleMaster | 56 m, -130 m | 188 m | 12 | left of the Atlas |
| Mad Cat | -50 m, -114 m | 172 m | 10 | between the BattleMaster and the rear Atlas right of it, partly hidden by both |

## 10. Marauder

This section describes the fourth chassis, which `src/marauder.py` assembles from a kit of 19 printable parts in `in/models/marauder/parts/`. It walks alone in a preview and as the tenth mech of banner 10.

- **Kit** - every part is its own STL, laid flat and apart; no part is in its place. The mech faces -Y there, and its left parts lie on +X
- **Two versions** - only the right foot comes twice. `right-foot-repaired.stl` is one closed shell with the volume of the left foot; `right-foot.stl` has 1044 open edges and 46 loose shells. The repaired one is used
- **Joints** - the parts join through ball joints and pins: waist, hips, knees, shoulders and elbows are balls in cups, the ankles are pins in clips. Each centre is a sphere or a circle fitted to the triangles whose normals agree with it; ball and cup of one joint have the same radius within 0.1 kit units
- **Assembly** - the hull stays, and every other part moves rigidly so that its joint lies on the joint of the part it hangs from. A ball joint leaves the angles free: the thigh leans back 30°, the shin forward 32° (the knee points back), the arm blocks hang down and are swung forward 35°, the gun pods hang below them with level barrels
- **Cockpit and cannon** - the cockpit's square stem goes into the square hole of the hull's front face; the cannon's square hole goes over the peg on the right of the hull top
- **Size** - the kit has 2.1 million triangles, most on balls and rounded edges; each part keeps 12 % of them, 288,000 in all. The model is 12.4 m tall
- **Rig** - the walk and the armature are those of the other chassis, with the knee pointing back as the Mad Cat's. The parts are rigid: every part goes wholly to one bone (`skin`), where the other chassis have a soft skin on one fused shell
- **Livery** - red hull and legs, bone arms and feet, black cockpit and cannon, with the ornament of section 6 on 2022 plates
- **Hips** - the lower torso is the pelvis: it rocks as one rigid part, with the missile rack on it (`pelvis` in `src/marauder.py`)
- **Muzzles** - the kit is made for printing, and a flat disc closes every barrel. `muzzles` sinks the disc 0.7 m into the barrel and paints the hole black: two guns in each arm pod, with bores of 0.38 m and 0.30 m, and the cannon on the hull
- **Missiles** - the hatch on the front of the lower torso carries a rack of 5 by 3 tubes, 0.2 m apart: a dark plate, on it an open brass tube per missile with a black floor, and in each tube a missile with a bone body and a red nose whose point reaches 3 cm out of the tube (`rack`). The rack lies on the hatch; the hull is not cut
- **Cloth banner** - a banner of crimson velvet with gold embroidery, 1.3 m wide and 3.5 m long, on a brass rod under the front of the lower torso, between the legs (`src/procession/cloth.py`, section 8). Its picture is `banner_4` of `w40k-mechanicum` (a cog with a skull, OMNISSIAH VULT), copied to `resources/assets/cloth-banner.png` and cut out of its white margin. `livery.py -- marauder full cloth` renders the still with it
- **Stride** - the bird walk (section 8)
- **Joints** - the kit is a snap-on toy: a ball on a stem joins each leg to the lower torso and each arm to the hull. `housings` hides each ball in a heavy joint on the joint's turning axis: a steel hub of 0.8 m (hip) or 0.64 m (shoulder) across, a flange with ten bolts on each of the two faces it joins, and three ribs between them. A drum on the turning axis keeps its look when the limb turns
- **Glyph** - a first version carried the Machina Opus of the welcome page as a medallion of 1.2 m on the hatch of the lower torso. The user ordered it off on 2026-10-06
- **Assumption** - the gun pods hang below the shoulders, as on the classic Marauder; the ball joints would also let them stand above the shoulders

## 11. Open points

This section lists what is undecided or left out.

- **New geometry on the mechs** - banners and tilting shields are not added. The mechs keep the shape of banner 03
- **Halos** - none, on the user's order of 2026-10-06
- **Logo sign** - the BEHEMOTH sign of banner 03 is not in this scene
- **Eagle emblem** - the generated eagle has one head, and the Imperial eagle has two. It is not used
- **File size** - at 30 frames per second banner 08 is 3.2 MB, banner 09 is 4.3 MB and banner 10 is 4.4 MB as AVIF; banner 03 is 5.7 MB as GIF. The welcome page with banner 10 is 5.9 MB
- **Self-contained folder** - `README.md` names this banner as the exception: steps 1, 2, 3, 7 and 14 use the generators and the gas solver of `w40k-mechanicum`, and step 5 its Python environment, for OpenCV
- **Banners 09 and 10** - separate outputs beside banner 08. The rear mechs wear the same wear marks as the front mech of their chassis, because they share its livery. The lamps under the glowing grates are 42.7 m wide, and lie about x = 0: the rear mech at x = 9.5 m, the BattleMaster or in banner 10 the Marauder, gets their light from below, the five rear mechs further to the sides get little of it
- **Right elbow** - the BattleMaster's raised right arm keeps a rigid elbow. Only the lowered arm was ordered
- **Banner 07** - `out/07-banner-procession.avif` is still the render at 20 frames per second, without the hanging foot, the arm swing and the elbow. The user ordered on 2026-10-06 not to render it again: banner 08 replaced it
