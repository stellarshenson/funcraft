# Mech banner design

The mech banner is a looping 19:6 GIF: 1140 × 360 pixels and 30 frames at 50 ms,
so one loop lasts 1.5 s. Three BattleMech chassis walk towards the viewer through
an industrial yard. Blender renders every frame with Cycles at 1520 × 480 from the
supplied high-poly meshes, which are painted and rigged in Blender. This document
records what the banner must show and the decisions behind it. `README.md`
covers how to build it.

## Requirements

These rules came out of reviews of earlier versions, and every change must keep
them.

- The mechs are the supplied meshes, kept whole. There are no self-modelled or
  low-poly stand-ins, and no mesh is cut into separately moving parts
- Each mech faces the viewer and walks straight towards the camera. The torso
  and legs face the same way, and the feet step straight ahead, not diagonally
- A planted foot lies flat on the ground and does not slide against it
- The Mad Cat's knees bend backwards (reverse-jointed legs). The Atlas's and the
  BattleMaster's knees bend forwards
- The Atlas's arms and arm weapons keep their modelled position. They do not
  extend or retract
- All colour is painted on the mesh in Blender, including the canopy glass.
  Nothing is recoloured in 2D after rendering
- The canopy glass is dark red with a dim red glow. The Atlas's glass is the
  brightest
- The loop is exact: the frame after the last is identical to the first
- Small tears in the skin at the joints are acceptable where they are invisible
  at banner size

## Chassis

| Chassis | Mesh | Height | Paint | Glass glow |
|---|---|---|---|---|
| Mad Cat (Timber Wolf) | `in/models/madcat-timberwolf.stl` | 12.0 | steel blue-grey armour, near-black limbs and feet, oxblood on the front faces of the missile racks | 0.45 |
| Atlas AS7 | `in/models/atlas-as7-rs.stl` | 13.4 | charcoal hull, oxblood arms and shoulders, bone-white skull face | 0.9 |
| BattleMaster | `in/models/battlemaster.stl` | 12.8 | sand armour, dark helmet and feet | 0.40 |

Heights are in scene units, with the feet on z = 0. The colours, as linear RGB,
and the body regions that receive them are in `SCHEMES` in `src/paint.py`.

Every face is painted as one of three classes:

- **Armour** - the chassis colours, assigned by body region
- **Machinery** - small flat patches such as actuators, pistons, vents and bolts,
  in one gunmetal colour shared by all three chassis
- **Glass** - the cockpit faces, selected on the mesh and set back behind a
  frame. The Mad Cat's and BattleMaster's canopies are selected by filling
  outwards from seed points. The Atlas's glass is its two eye sockets, each
  selected whole by a bounding box

All armour darkens in creases and wears to bare metal on convex edges. It also
varies slightly in tone from plate to plate and carries light grime. The glass
is near-black with a glossy clear coat, so it reflects the lights. Its red glow
is darker at the rim and brighter where the glass faces the viewer, so it never
renders as a flat colour.

## Rig and walk

Each chassis has an armature with a body bone and, for each leg, a thigh, shin
and foot bone:

- The thigh and shin form a two-bone inverse-kinematics (IK) chain that ends at
  a foot controller
- A pole bone sets the direction the knee bends
- The foot copies the controller's rotation, so the sole keeps the angle it is
  given

Joint positions were read off orthographic side views of each leg. The
BattleMaster mesh is sculpted mid-stride with its pelvis and legs turned 38.5°
against the torso. Its lower body is turned back into line when the mesh loads,
and each of its legs has its own joint positions.

The walk runs one gait cycle per loop:

- **Stride** - 5 units per cycle. This equals the floor's travel per loop and
  the spacing of the floor markers
- **Duty** - each foot is planted for 60 % of the cycle, so both feet are down
  twice per cycle
- **Planted foot** - moves backwards in a straight line at the floor's speed,
  so it stays fixed to the floor
- **Swinging foot** - lifts on an arch, points its toe down as it leaves and up
  before it lands, and never dips below the floor
- **Body** - drops as far as the more stretched leg requires, bobs twice per
  cycle, shifts sideways over the planted foot and tilts forward and back
  slightly

The mechs walk on the spot while the ground slides away from the camera under
them. With a fixed camera, this keeps the loop exact.

## Scene

The camera stands at (1, 58, 8.6) with a 42 mm lens. It looks along -Y and is
tilted 1.8° down. World +X appears on the left of the image.

| Chassis | Position (x, y) | Place in the frame |
|---|---|---|
| Atlas | (15, -19) | left, middle distance |
| Mad Cat | (-3, -7) | centre, nearest |
| BattleMaster | (-19, -31) | right, furthest |

- **Ground** - a dark deck. Orange floor strips cross the approach every 5 units
  and low kerb blocks run along it at x = ±34. The strips and kerbs slide with
  the ground
- **Background** - 46 blocks at random positions from a fixed random seed.
  They are clad in staggered plates with seams, tone variation and grime streaks
- **Logo** - the Stellars Tech Behemoth logo as a lit sign on a dark panel. It
  is centred on the wall of the building left of the Atlas
- **Atmosphere** - a thin blue haze over the whole scene. A low, patchy ground
  fog lies among the buildings and starts behind the BattleMaster, so none of it
  is in front of a mech
- **Light** - a warm key light behind the mechs on the right and a cold rim
  light behind them on the left. A front key light above the camera lights the
  faces the camera sees. A spot light on the Mad Cat lifts it out of its own
  shadow

## Variants

| File | Difference |
|---|---|
| `out/03-banner-models.gif` | all three chassis in step |
| `out/04-banner-shake.gif` | the camera tilts 0.1° at every footfall and settles within about five frames, as a decaying cosine (7 Hz, time constant 0.1 s) |
| `out/05-banner-offset.gif` | as 04, with the Atlas 11 frames and the BattleMaster 21 frames ahead of the Mad Cat in the gait cycle, so the six footfalls per loop are spread across it |

## Loop rules

- Every animated quantity is a function of `phase` in [0, 1). Every repeating
  element moves a whole number of its periods per loop
- Shake and gait offsets are counted in whole frames, so each footfall lands
  exactly on a frame
- Each render also produces the frame at `phase = 1.0` as `seam-check.png`,
  which must match frame 0
- A volume's boundary must not coincide with a surface. When the ground fog's
  lower face lay on the floor, the distant floor changed brightness at one
  frame of the loop. The fog box now reaches below the floor
