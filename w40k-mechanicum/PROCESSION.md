# W40k Mechanicum - Procession scene v1

Status: DRAFT, 2026-10-02.

## Contents

- [1. Request](#1.-Request)
- [2. Picture](#2.-Picture)
- [3. Layers](#3.-Layers)
- [4. Mechs](#4.-Mechs)
- [5. Loop](#5.-Loop)
- [6. Modules](#6.-Modules)
- [7. Working rules](#7.-Working-rules)
- [8. Frame measurements](#8.-Frame-measurements)

## 1. Request

This section records what the user asked for on 2026-10-02. The scene becomes `out/16-procession.gif`.

- **Source** - `mech-design/out/03-banner-models.gif`: three BattleMechs walk at the camera through an industrial yard
- **Kept** - the three supplied meshes, their armature, their walk, their places in the frame, the camera
- **Replaced** - the yard, the box buildings, the floor strips, the blue haze, the lights, the three paint schemes
- **User, on the world** - "rich mechanicum inspired imagery with robots walking, behind them maybe something from holy terra, very gothic and very mechanicum"
- **User, on the mechs** - "colour battlemechs and equip in embroidery and symbols that would make them very much w40k mechanicum creations"
- **User, on heraldry** - "think of imperial knights insignia, that would look very well on battlemechs"
- **User, on the method** - "your concept of 3d world based on images was spot on, it looks very rich, richer than anything you could design using 3d tools"
- **User, on effects** - "use also effects - smoke and so on, with simulation etc; use drapery and so on"
- **Decision, ornament** - paint, cloth and decals, and in addition generated pictures projected on the mech meshes
- **Decision, logo** - the Stellars Tech BEHEMOTH logo stays as a lit sign, mounted on the cathedral front

## 2. Picture

This section describes what the viewer sees. Three god-machines of the Cult Mechanicus walk in procession towards the viewer, out of the gate of a cathedral-palace on Holy Terra.

- **Far** - a colossal gothic front with a gate, towers, statues, hanging crimson banners and fires, in smog with light shafts. It is paler and hazier than the mechs, so the mechs read as dark, saturated shapes in front of it
- **Middle** - a processional way: a deck with brass inlays, piers with braziers and banners, rows of robed figures 1.8 m tall beside machines 12 m tall
- **Near** - the three mechs in Mechanicum livery, with banners, a halo, censers, candles, seals and exhaust smoke
- **Grade** - low key: rust, umber and black mass, crimson and gold accents, warm fire light against cold shafts. The rules and the measured reference values are in `.claude/skills/design-w40k/SKILL.md`
- **Size** - the viewer sees 1140 × 360 pixels. A mech is about 240 pixels tall there. Ornament must be bold: large fields of colour, large emblems, wide trims, long banners. A purity seal or a line of text is a few pixels

## 3. Layers

This section explains how a still picture world and walking machines fit together. A generated picture does not move, and a walking mech needs ground that moves under its feet, so the scene has three layers.

| Layer | Moves | Content | Source |
|---|---|---|---|
| Far world | no | cathedral front, gate, towers, statues, sky, the logo sign | one generated plate, 2432 × 768, with depth from MoGe-2; its banners, flames and smoke are animated as in plate scenes 04 to 13 |
| Processional way | slides along -Y with the ground | deck, piers, braziers, banners on poles, robed figures | generated pictures as textures and as relief, existing painted models |
| Mechs | walk on the spot | three chassis with livery, cloth and regalia | meshes and rig of `mech-design`, lit as real surfaces |

- **Join** - ground smoke hides the line where the sliding deck meets the still plate
- **Emission and light** - the far world emits its picture (Standard view transform), so no light changes it. Mechs and way are lit surfaces with lights that match the plate. `src/servoskull.py` shows the method for a lit model inside an emitting plate
- **Depth of the far world** - the camera does not move, so depth serves only smoke, haze and shadows. Every plate pixel lies on its own camera ray

## 4. Mechs

This section gives the livery and equipment of each chassis. The rules of `mech-design/DESIGN.md`, section Requirements, stay in force: whole meshes, no part cut off, feet that do not slide, the Atlas's arms in their modelled position, all colour on the mesh, dark red canopy glass with a dim red glow that is brightest on the Atlas.

| Chassis | Place | Livery | Equipment |
|---|---|---|---|
| Atlas | left, 77 m from the camera | Mars red armour, blackened frame, gold trims, the skull face in bone | gold cog halo behind the head, crimson mantle on the shoulders, banner between the legs |
| Mad Cat | centre, nearest, 66 m | black and red, gold trims | missile racks as gold-framed reliquaries with candles, long banner under the cockpit, censers on chains from the arms |
| BattleMaster | right, furthest, 89 m | bone and red, gold trims | two banner poles above the shoulders, purity seals with parchment |

- **Knight heraldry** - each mech carries the insignia of an Imperial Knight of a household sworn to the Mechanicus: a tilting shield above one shoulder, the household emblem on one shoulder plate and the Cog Mechanicum on the other, halved and quartered colour fields, chevrons and chequers on plates, a heraldic banner between the legs, pennants on the weapon arms, honour scrolls, laurel wreaths, kill marks, numerals on the shin plates
- **All three** - Cog Mechanicum emblems, black-and-white cog-tooth borders, exhaust stacks whose smoke trails behind, everything old: grime, soot, worn gold
- **Cloth** - banners and the mantle are simulated cloth, driven by the walk
- **Projection** - a picture of each mech, generated from its depth render, is projected on the camera-facing surfaces and mixed with the paint

## 5. Loop

This section states what makes frame 80 equal frame 0. `src/procession/frame.py` holds the numbers and the protocol.

- **Timing** - 80 frames at 50 ms. Two gait cycles of 40 frames. The ground travels 5 m per gait cycle, 10 m per loop
- **Still** - camera, lights, far world
- **Sliding** - everything on the ground is a child of `scene.ground`, repeats along Y with a period that divides 10 m, and is laid beyond both ends of what the camera sees
- **Cyclic** - every other motion makes a whole number of cycles in 80 frames
- **Simulated** - smoke and cloth are not periodic by themselves. Record two loops after a warm-up and blend them: loop frame k is (1 - k/80) of record 80 + k plus k/80 of record k. `src/smoke.py` does this
- **Proof** - render frame 80 as `seam-check.png` and compare it with frame 0. The largest difference must be at most 8/255

## 6. Modules

This section lists the files of `src/procession/` and who writes each. A module has `build(scene)` and a preview of its own, as `frame.py` describes.

| File | Content | Workflow |
|---|---|---|
| `frame.py` | constants, camera, mech loader, walk, render setup, mover protocol | written, do not change |
| `plates.py` | far world plate drafts | 1 |
| `livery.py` | `paint(mesh, name)`: Mechanicum paint of the three chassis | 1 |
| `project.py` | `generate(name)`, `dress(mesh, name)`: generated picture projected on a mesh | 1 test, 2 all three |
| `anchors.py` | measured points on each chassis: banner bars, smoke sources, halo | 1 |
| `regalia.py` | rigid equipment on the mechs | 1 |
| `way.py` | the sliding ground and what stands on it | 1 |
| `world.py` | far world from the picked plate, its actors, its smoke, the logo sign | 2 |
| `cloth.py` | cloth simulation of banners and mantle | 2 |
| `fumes.py` | smoke and flames of exhausts, censers, candles, braziers | 2 |
| `scene.py` | assembly, lights, grade, render | 2 |

## 7. Working rules

This section holds the rules for everyone who works on the scene.

- **Read first** - this file, `src/procession/frame.py`, `.claude/skills/design-w40k/SKILL.md`, `.claude/skills/design-blender/SKILL.md`, `.claude/skills/design-gif/SKILL.md`. `DESIGN.md` describes the plate pipeline, section by section
- **Files** - write only the files your brief names. Another session works in this repository. Do not commit, push, or write the journal
- **Other projects** - read `mech-design`, never change it
- **Look at every picture you make** - open the PNG with the Read tool, at the viewer's size (1140 × 360) and as a crop at twice that. Judge what the picture shows, not what the code intends
- **Reference pictures** - `references/*.png` and `references/rogue-trader/`. Compare side by side before you report
- **Latin** - check every word letter by letter. Exact Latin is stitched with PIL (`src/gentextures.py`, `stitch`), never trusted to the image model
- **Text and decoration on a surface** - a flat texture draped on the surface's shape, never placed in image space (`DESIGN.md` section 2.5)
- **Blender** - `~/.local/opt/blender-4.5.9-linux-x64/blender -b -P <script> -- <args>`, with `CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=<index>` in front
- **Torch** - `.venv-moge/bin/python`, with the same two variables set before torch is imported. Z-Image-Turbo, MoGe-2 and SAM 2.1 are in the local Hugging Face cache; set `HF_HUB_OFFLINE=1` for them
- **GPU indices** - 0 RTX PRO 4000 (24 GB), 1 RTX PRO 6000 (96 GB), 2 RTX 5000 Ada (32 GB). Use the indices your brief gives you
- **Never kill a process that uses a GPU** - on this WSL2 workstation that blocked the GPU driver for every user for 24 minutes. Let a wrong run finish, then run again. To stop a queue, stop only the shell script that drives it
- **Long jobs** - `nohup setsid <command> > wip/logs/procession-<name>.log 2>&1 < /dev/null &`, then read the log. A job longer than 5 minutes runs this way
- **No web** - no web search and no download, unless your brief allows one
- **Scratch files** - under `wip/procession/`. Pictures to look at under `wip/preview/procession/`

## 8. Frame measurements

This section gives the measured places in the render of 1520 × 480 pixels (`wip/preview/procession/layout.png`, `wip/procession/layout.json`). Rows count from the top. World +X is on the left of the picture.

| Thing | Value |
|---|---|
| Horizon | row 184 (38.4 % from the top) |
| Atlas, box | x 314 to 563, rows 90 to 390 |
| Mad Cat, box | x 740 to 996, rows 113 to 420 |
| BattleMaster, box | x 1058 to 1255, rows 129 to 359 |
| Ground at y = 0, 58 m from the camera | row 446 |
| Ground at y = -50, 108 m | row 325 |
| Ground at y = -100, 158 m | row 281 |
| Ground at y = -200, 258 m | row 243 |
| Ground at y = -400, 458 m | row 218 |
| Field of view | 46.4° wide, 15.4° high |
| Ground first visible | 51 m from the camera, where 44 m of its width fit the frame |

- **Mech lanes** - the feet stay within 5 m of x = 15, x = -3 and x = -19. Nothing on the ground may stand in these three strips, because the ground slides through the whole length
