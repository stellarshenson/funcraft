---
name: design-blender
description: Builds, paints, rigs and renders 3D scenes in headless Blender 4.5 with Cycles on the GPU for the funcraft banner projects (mech-design, w40k-mechanicum). Use when asked to render, model, light, texture, paint or animate anything in Blender - supplied STL/OBJ/FBX meshes, colouring a model on its mesh, canopy glass, armatures ("skelegons", skeletons), walk cycles, feet and knees, procedural materials, fog or volumetrics, light shafts, a logo on a wall, lookdev stills - or when a Blender render looks wrong (torn joints, cut or twisted parts, sliding feet, walking backwards, flat colours, flicker).
---

# Design in Blender

Headless scripts build the whole scene from code and render it frame by frame. Paths are relative to `~/workspace/funcraft/`. Working examples to copy from: `mech-design/src/` (supplied meshes, paint, rig, walk) and `w40k-mechanicum/src/mechanicum.py` (procedural architecture, animated shaders). Loop timing, seam checks and GIF assembly: `design-gif` skill.

## Run
- `~/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/<script>.py -- <args>`; the script reads args after `--`
- `CUDA_VISIBLE_DEVICES=1` (RTX PRO 6000; 0 is the RTX PRO 4000); inside the script enable every CUDA device - copy `render_setup()` from `mechanicum.py`
- AgX view transform, look "AgX - Medium High Contrast"; 1520 × 480 (19:6), 64-96 samples, denoiser on → 8-20 s per frame
- Generators take `out=DIR` and frame numbers: test with `-- out=test 0 26 27 40`, only the frames under suspicion
- Long renders: `nohup setsid make … > wip/logs/<name>.log 2>&1 &`, keep `$!`, wait with `while kill -0 $PID` - `pgrep -f <pattern>` also matches the waiting shell's own command line and never finishes

## Models
- Use supplied or downloaded high-poly meshes, whole. Self-modelled low-poly stand-ins were rejected; where real models exist, find them
- `in/models/originals/` holds files exactly as received; renamed working copies in `in/models/`; source and licence in `SOURCE.txt` or the README provenance section
- Licences: CC0 and CC BY first. Fan models labelled CC BY often remix CC BY-NC parts - check the remix sources. Skip files named like game-engine assets (likely rips). Sketchfab downloads need a login - list those for the Star Colonel to fetch
- Normalise at load: face +Y, feet on z = 0, height per chassis (`CHASSIS` in `mech-design/src/mechrig.py`)
- Look from above before rigging - sculpts come posed. The BattleMaster's lower body was turned 38.5° against its torso; `untwist()` turns it back at load (full turn below the waist, blended through a z band, a predicate keeps parts such as a hanging arm with the torso)

## Paint on the mesh
- Colour = material slots on faces, assigned before rigging so it moves with the geometry (`mech-design/src/paint.py`). Never recolour the rendered image
- Armour: region predicates on face centre and normal. Machinery: planar patches (10° neighbour angle) with area < 0.03 → one gunmetal. Glass: flood fill from seed points measured on close-ups, bounded by angle and a region test; a bounding box where fill cannot reach (Atlas eye sockets)
- Inset the glass (`bmesh.ops.inset_region`) and push it back, so a frame surrounds it
- Glass shader: near-black base, coat 1.0, roughness 0.05, red emission mixed rim → core by Layer Weight facing, strength 0.4-0.9. Give the world a sky gradient so the glass has something to reflect
- Armour shader: AO darkens creases, Bevel-vs-Geometry normal gives edge wear, a per-face `panel` attribute varies plate tone, noise adds grime
- Get colours approved on stills first: `make lookdev` (4 views + head close-up, neutral studio), then animate

## Rig and walk
- Armature per chassis (`mech-design/src/rig.py`): `body`; per leg `thigh`, `shin`, `foot`; IK on the shin to controller `ik.L/R`; a pole bone sets knee direction; the foot copies the controller's rotation
- Joint positions from orthographic side renders on a half-unit grid (`make measure`); pole angle fitted by search so the rest pose holds
- Walk on a treadmill: the mech steps on the spot, the floor slides one stride per gait cycle, every pose a function of phase (loop rules: `design-gif`)

## Caveats
Each line is a failure that reached the Star Colonel, with the rule that prevents it.

**Cutting geometry**
- Never cut a mesh into separately animated parts - the cut shows as a gap or a vertical seam where halves move differently ("cut in half from the waist down"). Keep the mesh whole and skin it to bones
- `mechrig.py` still holds that earlier cut rig (`build`, `cut_part`, `pose`, `redden_canopy`, used only by `cuttest.py`, `striptest.py`, `canopycheck.py`). Load with `mechrig.load()` and rig with `rig.build()`
- Do not move parts the design keeps fixed: the Atlas's arms and arm guns stay with the body, no extend or retract

**Joints and joined pieces**
- An STL is many separate pieces; give each piece wholly to the bone it clearly belongs to (armour plate → thigh, toe spike → foot) instead of per-vertex nearest bone, which tears pieces across joints
- In a fused shell: a split height marks the torso underside; below it choose the leg side per connected piece; inside a leg the nearest bone wins with a narrow blend at the joint
- Keep per-leg corridors tight or a hanging arm is captured by a leg (BattleMaster); penalise the foot above the ankle and the thigh below the knee
- Measure with `make rigcheck` (edges stretched > 3× and > 0.3 units) and `make weights` (flat colour per bone). Tears invisible at banner size are accepted - stop polishing there

**Feet**
- A planted foot is flat: the foot copies the controller rotation; pitch only during swing (toe down leaving, toe up landing)
- A planted foot moves at exactly the floor's speed in a straight line - a sine-shaped hip swing makes it slip even when step lengths match
- The swing foot clears the floor on an arch and never dips below z = 0
- Knee direction per chassis: the Mad Cat is reverse-jointed (knee behind), the Atlas and BattleMaster bend forward. Set it with the pole, check it in a side render

**Direction of movement**
- Mechs walking towards the camera: the planted foot slides away from the camera with the floor, the swing foot comes forward. Flip either and it reads as walking backwards
- When one of the two is wrong, fix that one - reversing the correct floor to match wrong legs made both wrong
- Walk straight at the camera (heading 0). A turned mech on a straight floor slides sideways; torso and legs must face the same way or the legs step diagonally

**Glass and colour**
- Strong emission clips to one flat colour and AgX turns over-bright red coral pink - glass looks painted on the 2D image. Keep emission weak and dark; measure pixel values in the glass
- Select glass along panel lines, not triangle blobs; check the selection on the final render, not on a debug render

**Volumes and light**
- A volume box must never share a face with a surface - reach below the floor. With the fog's bottom on the floor, the distant floor brightened 9 % for four frames of the loop
- Haze: one Volume Scatter box containing camera and scene, density ~0.01, anisotropy ~0.45. Ground fog: density × exp(-z/h) × smoothstep fade-in along depth × stretched noise, starting behind the subjects
- Light shafts: spots ~1.5 MW, 12° cone, high above, through the haze
- Subjects lit from behind need a front key above the camera, or the paint does not read

## Procedural scenery
For architecture and props no downloaded model covers; subjects stay real models.

- Build with bmesh and bake sizes into vertices (object scale 1) so bevels and world-space textures stay even. Helpers in `mechanicum.py`: `box`, `cyl` (smooth sides, flat caps), `sphere`, `torus`, `ribbon`, `arch` (pointed), `gear`, `curve` (cables)
- Texture on world `(x + y, z)` so walls along X and Y share one pattern scale; Brick Texture for plates, masonry and slabs, its Fac into a Bump for the seams
- Parent each assembly to an empty and pose the empty
- Animated shaders read Value nodes registered in `CLOCKS` ("phase" or "tick") and set every frame; moving objects sit in `MOVERS` as `(object, fn(phase))`
- Blinking cells: White Noise 4D on (cell x, cell y, face) with W = tick. Data pulses: a pulse of `fract(coord / period - laps · phase)`

## API traps
- `ShaderNodeMix` RGBA sockets by identifier - `Factor_Float`, `A_Color`, `B_Color`, `Result_Color`; `inputs["A"]` is the float socket
- Principled emission inputs: `Emission Color`, `Emission Strength`
- A local named like an imported module (`math`) shadows it → `UnboundLocalError`
- `io_curve_svg` keeps only `style=` fills; `fill=` attributes import black - parse them from the SVG and assign per path id (`mech-design/src/logo.py`); offset overlapping layers by document order against z-fighting
- Camera at +Y looking -Y (rotation z 180°): world +X is on the image left
- 19:6 leaves little vertical view: a 24 mm lens sees ~27° vertically; visible height at distance D is `2·D·tan(vfov/2)`

## Before sending
- Downscale to 1140 × 360 and look; crop at 2× where detail matters; stack old above new for a change
- Measure what the request names - pixel values, margins in pixels, brightness per frame. An unmeasured "looks right" drew "have you even checked?"
- Sheets and seam checks: `design-gif` scripts

<!-- improved 2026-09-30 | body 0→1453w / 0→88L | benchmark n/a (declined) | via improve-skill -->
