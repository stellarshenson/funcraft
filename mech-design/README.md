# mech-design

Looping 19:6 banner animations of BattleMechs, built four ways - from hand-drawn
2D silhouettes up to rigged high-poly meshes rendered in Blender on the GPU.

The folder is self-contained. Move it anywhere; nothing outside it is referenced
except Blender itself and a Python with Pillow, numpy and scipy. Banner 07 is
the exception: its image generators and its smoke solver belong to the sibling
project `w40k-mechanicum` (`PROCESSION.md`, section 3).

## Output

| File | How it was made | Notes |
|---|---|---|
| `out/01-banner-2d.gif` | Pure 2D, Pillow only | Silhouettes with a rim light, articulated by two-bone IK |
| `out/02-banner-3d-procedural.gif` | Own 3D engine, no libraries | Boxes, perspective camera, z-buffered software rasteriser |
| `out/03-banner-models.gif` | Blender 4.5, Cycles on GPU | The supplied meshes, painted and walked by an armature |
| `out/04-banner-shake.gif` | as 03 | The camera jolts at every footfall; all three in step |
| `out/05-banner-offset.gif` | as 03 | Each chassis at its own point in the gait cycle, camera jolting at each footfall |
| `out/behemoth-welcome.html` | `make welcome` | The BEHEMOTH welcome page of GalaxaLab: `src/welcome.template.html` with banner 10, the two badges of `src/sigil.py` (on the hazard strip the cog wheel with the Stellars Tech mark, over the closing litany the cog with the skull of `resources/assets/zl789e1341kd1.jpg`; both are enamel badges in red and bone with a steel rim; `src/crest.py` and `src/crest3d.py` made the earlier crest and are not used) and the Orbitron font of the title embedded (`src/welcome.py`: animated AVIF, PNG, WOFF2), one self-contained file without JavaScript |
| `out/07-banner-procession.avif` | `make procession` | The mechs of 03 in the livery of a knightly household of the Cult Mechanicus, with ornament on every armour plate, on a forge deck in front of a generated skyline, with the gait offsets and the camera jolt of 05; an animated AVIF; `PROCESSION.md` |
| `out/08-banner-procession-hips.avif` | `make procession-hips` | Banner 07 with the hips of the mechs rocking by 4.5° in the walk (`src/procession/hips.py`). 30 frames per second, with the two walks of `src/procession/gait.py` (the Atlas and the BattleMaster march on their heels, the Mad Cat walks on its toes as a bird), the arm swing of the Atlas and the BattleMaster, and the BattleMaster's forearm turning about its elbow hinge with its hydraulic piston (`src/procession/arms.py`) |
| `out/09-banner-procession-column.avif` | `make procession-column` | Banner 08 with six more mechs in two ranks behind the three, each at its own point in the gait cycle; the camera jolts at the footfalls of the three only |
| `out/10-banner-procession-marauder.avif` | `make procession-marauder` | Banner 09 with the Marauder in the place of the rear BattleMaster between the Atlas and the Mad Cat, and with cloth banners that move with wind and gait on the Marauder and on the Mad Cat of the three (`src/procession/cloth.py`; the Mad Cat's picture: `src/procession/clothart.py`) |

Every animated quantity is a function of `phase` in `[0,1)`, and every scrolling
element advances a whole number of its own pattern periods across the cycle.

The loop was measured, not assumed: each generator was run one frame past the
end, at `phase = 1.0`, and that frame compared against `phase = 0.0`.

| File | Result |
|---|---|
| `01-banner-2d.gif` | pixel-identical, zero difference |
| `02-banner-3d-procedural.gif` | pixel-identical, zero difference |
| `03-banner-models.gif` | no pixel of 729,600 differs by more than 8/255 |
| `04-banner-shake.gif` | no pixel of 729,600 differs by more than 8/255 |
| `05-banner-offset.gif` | no pixel of 729,600 differs by more than 8/255 |
| `07-banner-procession.avif` | 1137 pixels of 729,600 differ by more than 8/255, scattered as render noise; the mean difference is 0.18/255 |

The model banners render one extra frame at `phase = 1.0` as `seam-check.png`
in their frames folder for this comparison; the GIF leaves it out.

`DESIGN.md` records what the banner must show and why.

## Layout

```
src/                  generators and the rig
src/procession/       banners 07 to 10: backdrop, ground, livery, embers, chimney smoke, walk, hips, arms, cloth banners, scene
src/marauder.py       the fourth chassis: assembles the Marauder from its kit and enters it into the tables of the others
in/models/            the three chassis, renamed; marauder.stl and marauder.json, written by src/marauder.py
in/models/marauder/   the Marauder kit as supplied (a zip archive) and its 19 parts unpacked (parts/)
in/models/originals/  the files exactly as supplied
in/models/rigged/     painted and rigged Blender scenes, one per chassis
resources/assets/     the Stellars Tech logo, the glyph of the sigil and the two badges of the welcome page, the pictures of the cloth banners
resources/fonts/      Orbitron, the font of the title of the welcome page (SIL Open Font License 1.1)
wip/preview/          measurement sheets and cut checks - not deliverables
wip/frames/           intermediate PNG frames
wip/procession/       banners 07 to 10: ground piece, plate charts, ornament atlases, chimney smoke
wip/logs/             render logs
out/                  finished animations
```

## Running it

Blender lives at `~/.local/opt/blender-4.5.9-linux-x64/blender`. Set `BLENDER`
if yours is elsewhere.

```
make banner        # the model-based banner: render frames, then assemble
make frames        # render only
make gif           # assemble only, from whatever is in wip/frames
make banner-shake  # 04: camera shake on every footfall
make banner-offset # 05: gait cycles offset per chassis, with the shake
make procession    # 07: render with the livery, then assemble (data of PROCESSION.md steps 1 to 7 must exist)
make procession-hips  # 08: banner 07 with rocking hips
make procession-column  # 09: banner 08 with six more mechs behind the three
make procession-marauder  # 10: banner 09 with the Marauder in the place of one rear BattleMaster
make marauder      # assemble the Marauder from its kit: in/models/marauder.stl and marauder.json (PROCESSION.md, section 10)
make lookdev       # painted stills of each chassis
make rig           # pose tests and the rigged .blend scenes
make rigcheck      # count over-stretched edges in the pose tests
make weights       # colour each part by the bone that owns it
make measure       # orthographic grids, for reading joint heights
make cuts          # the earlier cut-mesh rig: part-coloured cut check
make gait          # the earlier cut-mesh rig: five-phase walk strip
```

The 2D and procedural-3D banners need no Blender:

```
python src/gen01_banner2d.py out/01-banner-2d.gif
python src/gen02_banner3d.py out/02-banner-3d-procedural.gif
```

## Paint

`src/paint.py` colours each mesh on its own faces, as material slots, before
rigging, so the colour moves with the geometry.

- **Glass** - the cockpit faces, flood-filled from seed points measured on
  front close-ups of each head (the Atlas's eye sockets are taken whole by a
  window), then inset into the hull so the glass sits behind a frame. The
  material is near-black clear-coated glass with a weak red emission that is
  stronger where the glass faces the viewer, so it reflects the lights and
  never renders as one flat colour
- **Machinery** - faces in small flat patches: actuators, pistons, vents,
  bolts. Gunmetal
- **Armour** - everything else, coloured by body region from the chassis's
  scheme in `SCHEMES`

Every surface darkens in creases (ambient occlusion), wears to bare metal on
convex edges, and varies slightly in tone from plate to plate.

`make lookdev` renders `wip/preview/lookdev/` - each chassis standing in a studio,
from four sides plus a cockpit close-up.

## Rig

`src/rig.py` gives each chassis a Blender armature. The mesh stays whole and
is skinned to the bones through vertex groups.

- **Bones** - `body`, and per side `thigh`, `shin`, `foot`. The shin carries a
  two-bone IK chain to a foot controller `ik.L`/`ik.R`; a pole bone sets the
  knee direction, behind the knee for the Mad Cat's reverse joint. The foot
  copies the controller's rotation, so the sole keeps the angle it is given
- **Joints** - read off orthographic side renders of each leg on a half-unit
  grid. The BattleMaster is modelled mid-stride, so each of its legs has its
  own joints
- **Skinning** - separate mesh pieces go whole to the body or a leg where
  they clearly belong to one; in a single fused shell a vertex is leg below
  the torso's underside, and inside a leg it goes to the nearest bone,
  blended only at a joint

`make rig` renders `wip/preview/rig/` - each chassis at rest, mid-stride and
crouched - and saves the rigged scenes to `in/models/rigged/`. `make rigcheck`
counts mesh edges stretched past three times their length in those poses.
`make weights` colours each part by the bone that owns it.

The BattleMaster is sculpted with its pelvis and legs turned 38.5 degrees
against its torso. `mechrig.load()` turns the lower body back into line as the
mesh is loaded - fully below the waist, blended through it - so the legs step
straight ahead under a torso that faces the same way.

## Walk

`walk()` in `src/rig.py` moves only the controllers. A planted foot slides
backwards at exactly the floor's speed, so it stays locked to the floor; a
swinging foot lifts on an arch and pitches toe down, then toe up, without
dipping below the floor; the body sits as low as the more stretched leg
needs, which gives it its bob. All three mechs walk straight at the camera,
because the floor slides in one direction only.

The variants reuse the same walk. `shake` rotates the camera after every
footfall by a decaying cosine - 0.1 degree per foot, gone within about five
frames - counted in whole frames from each landing so the loop stays exact.
`offset` starts each chassis's cycle a whole number of frames apart, so the
six footfalls per loop spread across it instead of landing in pairs.

## Logo

`src/logo.py` mounts `resources/assets/stellars_tech_ai_lab_gh_behemoth_logo.svg` as a lit
sign, centred on the wall of the building left of the Atlas. Blender's SVG
importer reads fill colours only from `style` attributes and drops the logo's
`fill=` colours, so the colours are read from the SVG and applied per path.

## Buildings

The background blocks share one procedural material, `facade()` in
`src/gen04_banner_models.py`: staggered plates 4 by 2.2 units with recessed
seams, a random tone per plate, and vertical grime streaks. The pattern is laid
out on world coordinates, so every wall gets plates of the same size however
its block is scaled.

A ground fog volume lies among the buildings. Its density falls off with height
(halving about every 2 units), fades in between y = -42 and y = -75, behind the
rearmost mech at y = -31, and is broken into patches by stretched noise. It is
static, so the loop stays exact.

## Provenance

The three STLs were supplied by the Star Colonel. They are fan-made models of
Catalyst Game Labs chassis; check the licence terms of wherever they came from
before publishing anything made from them. The 2D and procedural-3D banners use
original geometry and carry no such question.
