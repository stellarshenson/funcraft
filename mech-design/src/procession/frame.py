"""The contract of the procession scene (banner 07). Blender 4.5.

The scene is banner 03 with another backdrop and decorated
mechs: three BattleMechs walk at the camera, the ground moves under them,
a backdrop stands far behind. Meshes and armature are those of banner 03
(src/mechrig.py, src/rig.py); the walk is that of src/procession/gait.py,
with longer and higher steps. On top of them: arms swing (ARM_SWING,
src/procession/arms.py),
hips rock (HIP_ROCK, src/procession/hips.py; banner 08 and later). Banner 09
adds the six mechs of REAR behind the three. In banner 10 the Marauder, a
fourth chassis from src/marauder.py, walks in the place of one of the six
(MARAUDER), and it and the Mad Cat of the three wear a cloth banner (CLOTH,
src/procession/cloth.py).

Frame of reference, as in banner 03. Units are metres: a mech is 12 to 13.4
tall. The camera stands still at CAMERA and looks along -Y, so world +X is on
the left of the picture. The mechs face +Y and walk on the spot. The ground
slides away from the camera, along -Y, at the speed of the planted feet.

Loop. FRAMES frames at 30 per second hold CYCLES gait cycles of GAIT_FRAMES
frames. Banner 03 has 30 frames of 50 ms per gait cycle, 1.5 s; here a gait
cycle is 44 frames, 1.47 s: an even number, so both feet of a mech land on a
frame. In one loop the ground travels TRAVEL = STEP * CYCLES. Frame FRAMES must show exactly what frame 0 shows:

    still     the backdrop's structures, the lights
    sliding   everything that lies on the ground: child of `scene.ground`,
              repeated along Y with a period that divides TRAVEL, and laid
              beyond both ends of what the camera sees
    cyclic    every other motion: a whole number of cycles in FRAMES frames.
              As in banner 05, each chassis walks GAIT_OFFSET frames ahead
              and the camera jolts at every footfall of the three

A mover is a function f(i) of the frame number 0..FRAMES, with f(FRAMES)
leaving the state of f(0); Scene.pose(i) calls them all.

    blender -b -P src/procession/frame.py -- layout     # wip/preview/procession/layout.png, wip/procession/layout.json
"""
import bpy, os, sys, math, json
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))                  # mech-design
WIP = os.path.join(ROOT, "wip", "procession")                  # generated data, not tracked
PREVIEW = os.path.join(ROOT, "wip", "preview", "procession")   # pictures to look at
sys.path.insert(0, os.path.join(ROOT, "src"))

GAIT_FRAMES = 44                   # one gait cycle, left and right step
CYCLES = 2                         # gait cycles per loop: 88 frames, 2.93 s, the ground travels 15 m
FRAMES = GAIT_FRAMES * CYCLES      # one loop
FRAME_S = 1 / 30                   # seconds per frame in the animation (src/assemble.py writes the same)
STEP = 7.5                         # ground travel per gait cycle: the length of the ground's piece (src/procession/groundtex.py)
TRAVEL = STEP * CYCLES             # ground travel per loop: sliding things repeat with a period that divides this
# as banner 05: each chassis at its own point in the gait cycle, in whole frames, so that every footfall lands on
# a frame (frames 0, 6, 13, 22, 28 and 35 of a cycle)
GAIT_OFFSET = {"madcat": 0, "atlas": 16, "battlemaster": 31}
SHAKE_DEG = 0.10                   # the camera's jolt at a footfall: a cosine at full swing on the landing frame ...
SHAKE_TAU = 0.10                   # ... that falls to 1/e in this many seconds
SHAKE_HZ = 7.0
ARM_SWING = {"atlas": 3.5, "battlemaster": 2.5, "marauder": 2.5}  # degrees that the arms swing to each side in the walk (src/procession/arms.py); the Mad Cat's pods are fixed mounts
HIP_ROCK = 0.0                     # degrees that the hips roll in the walk (src/procession/hips.py): 4.5 in banners 08 to 10; 0 leaves the rig of banner 03 as it is
RES = (1520, 480)                  # render, 19:6
GIF = (1140, 360)                  # what the viewer sees: judge every picture at this size
SAMPLES = 64

CAMERA = dict(location=(1.0, 58.0, 8.6), lens=42.0, pitch=1.8)   # pitch: degrees below level
# chassis and world position of its root; all face +Y
PLACEMENT = [("battlemaster", (-19.0, -31.0, 0.0)),              # right of the picture, furthest
             ("madcat", (-3.0, -7.0, 0.0)),                      # centre, nearest
             ("atlas", (15.0, -19.0, 0.0))]                      # left, middle distance
# banner 09: more mechs behind the three, each a second or third mech of one of the three chassis: chassis, world
# position of its root, frames it walks ahead. They stand in two ranks, 133 to 198 m from the camera (the three: 65
# to 89 m), and the camera sees them in the gaps between the three and beside them. No two feet of the nine land on
# the same frame. Their footfalls do not jolt the camera
REAR = [("battlemaster", (9.5, -90.0, 0.0), 19),                 # between the Atlas and the Mad Cat
        ("atlas", (-46.0, -75.0, 0.0), 35),                      # right of the BattleMaster
        ("madcat", (53.0, -82.0, 0.0), 25),                      # at the left edge
        ("atlas", (-29.0, -140.0, 0.0), 6),                      # second rank: between the Mad Cat and the BattleMaster
        ("battlemaster", (56.0, -130.0, 0.0), 12),               # second rank: left of the Atlas
        ("madcat", (-50.0, -114.0, 0.0), 10)]                    # between the BattleMaster and the Atlas right of it
REAR_COUNT = 0                     # how many of REAR stand in the scene: 0 is banner 07 and 08, 6 is banner 09 and 10
CLOTH = False                      # banner 10: the mechs that src/procession/cloth.py lists wear a cloth banner; a twin does not
MARAUDER = None                    # banner 10: the index in REAR of the mech in whose place the Marauder walks; 0 is the BattleMaster between the Atlas and the Mad Cat


import mechrig, paint as mechpaint, rig as mechwalk, logo as mechlogo
import marauder
if os.path.exists(os.path.join(marauder.MODELS, "marauder.json")):     # the fourth chassis, once src/marauder.py has built it
    marauder.register()
LOGO = os.path.join(ROOT, "resources", "assets", "stellars_tech_ai_lab_gh_behemoth_logo.svg")


class Scene:
    """What the modules share: mechs[name] = (mesh, rig), the sliding
    `ground` empty, and the list of movers."""

    def __init__(self):
        self.mechs, self.movers = {}, []
        self.ground = bpy.data.objects.new("ground", None)
        bpy.context.collection.objects.link(self.ground)
        self.movers.append(self._slide)
        self.cam = camera()
        self.rest = self.cam.rotation_euler.copy()
        self.movers.append(self._rumble)

    def _slide(self, i):
        self.ground.location = (0.0, -TRAVEL * i / FRAMES, 0.0)

    def _rumble(self, i):
        """The camera's jolt, summed over the footfalls, as `shake` of
        src/gen04_banner_models.py: a chassis's left foot lands at its gait
        phase 0 and its right foot at 0.5, and the two tip the view to
        opposite sides. Time since a landing is counted in whole frames
        modulo the gait cycle, so the jolt repeats exactly."""
        pitch = yaw = roll = 0.0
        for o in GAIT_OFFSET.values():
            for land, side in ((-o, 1.0), (GAIT_FRAMES // 2 - o, -1.0)):
                t = ((i - land) % GAIT_FRAMES) * FRAME_S
                a = math.radians(SHAKE_DEG) * math.exp(-t / SHAKE_TAU) * math.cos(math.tau * SHAKE_HZ * t)
                pitch, yaw, roll = pitch - a, yaw + 0.4 * side * a, roll + 0.3 * side * a
        self.cam.rotation_euler = Euler((self.rest.x + pitch, self.rest.y + roll, self.rest.z + yaw), "XYZ")

    def pose(self, i):
        """Set every mover for frame i (0..FRAMES)."""
        for f in self.movers:
            f(i)
        bpy.context.view_layer.update()


def load_mechs(scene, livery=None, dress=None):
    """Load, paint, smooth, rig and place the three chassis, and add their
    walk to the movers. livery(mesh, name) paints the whole mesh before it is
    rigged (default: the paint of banner 03). dress(mesh, name), if given, runs
    after the paint and before the rig, on the mesh at rest, facing +Y, feet
    on z = 0, in its own coordinates. The first REAR_COUNT mechs of REAR
    follow, with the Marauder in the place of mech MARAUDER: a chassis that
    stands in the scene already gets a twin, another one is loaded.
    scene.mechs holds the three only."""
    def fresh(name, offset):
        mesh, rig = load_mech(name, livery, dress)
        if CLOTH:
            import cloth
            if name in cloth.CLOTHS:
                cloth.hang(scene, rig, name, offset)
        return mesh, rig

    for name, loc in PLACEMENT:
        mesh, rig = fresh(name, GAIT_OFFSET[name])
        rig.location = loc
        scene.mechs[name] = (mesh, rig)
    walkers = [(name, rig, GAIT_OFFSET[name]) for name, (_, rig) in scene.mechs.items()]
    loaded = dict(scene.mechs)
    rear = REAR[:REAR_COUNT]
    if MARAUDER is not None:
        rear[MARAUDER] = ("marauder",) + rear[MARAUDER][1:]
    for name, loc, offset in rear:
        if name in loaded:
            rig = twin(*loaded[name])
        else:
            loaded[name] = fresh(name, offset)
            rig = loaded[name][1]
        rig.location = loc
        walkers.append((name, rig, offset))

    def walk(i):
        for name, rig, offset in walkers:
            phase = ((i + offset) % GAIT_FRAMES) / GAIT_FRAMES
            pose(rig, name, phase)

    scene.movers.append(walk)


def load(name):
    """The mesh of a chassis as src/mechrig.py loads it. A model of separate
    rigid parts (the Marauder) marks them here, before any paint changes the
    mesh."""
    mesh = mechrig.load(name)
    mesh.name = name
    if "label" in mechrig.CHASSIS[name]:
        mechrig.CHASSIS[name]["label"](mesh)
    return mesh


def painted(name, livery=None, dress=None):
    """The mesh of a chassis: loaded, painted, dressed and smoothed, not
    rigged. livery and dress as in `load_mechs`; a chassis may bring a dress
    of its own (the Marauder's open muzzles and its missiles)."""
    mesh = load(name)
    (livery or mechpaint.paint)(mesh, name)
    if "dress" in mechrig.CHASSIS[name]:
        mechrig.CHASSIS[name]["dress"](mesh)
    if dress:
        dress(mesh, name)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = mesh
    mesh.select_set(True)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(31))
    return mesh


def load_mech(name, livery=None, dress=None):
    """One chassis at the origin: loaded, painted, smoothed and rigged.
    Returns its mesh and its rig. livery and dress as in `load_mechs`."""
    mesh = painted(name, livery, dress)
    chassis = mechrig.CHASSIS[name]
    rig = mechwalk.build(mesh, name)
    if "skin" in chassis:
        chassis["skin"](mesh, rig)
    if name in ARM_SWING:                              # before the hips: an arm that hangs beside the pelvis stays an arm
        import arms
        arms.split(mesh, rig, name)
    if HIP_ROCK:
        import hips
        hips.split(mesh, rig, name)
    return mesh, rig


def pose(rig, name, phase):
    """The walk of chassis `name` at gait phase `phase` (0..1)."""
    import gait
    gait.walk(rig, name, phase, STEP)
    if name in ARM_SWING:
        import arms
        arms.swing(rig, name, phase, ARM_SWING[name])
    if HIP_ROCK:
        import hips
        hips.rock(rig, name, phase, HIP_ROCK, gait.GAIT[name]["turn"])


def twin(mesh, rig):
    """A second mech of a chassis that is loaded already: copies of its mesh
    object and its rig object. The two mechs share the mesh, its paint and the
    armature; the pose belongs to each rig object. Returns the new rig."""
    mesh2, rig2 = mesh.copy(), rig.copy()
    for o in (mesh2, rig2):
        bpy.context.collection.objects.link(o)
    mesh2.parent = rig2
    mesh2.modifiers["rig"].object = rig2
    for pb in rig2.pose.bones:                     # the copied leg constraints still aim at the first rig
        for c in pb.constraints:
            c.target = rig2
            if c.type == "IK":
                c.pole_target = rig2
    return rig2


def bone_child(ob, rig, bone):
    """Make `ob` follow one bone of a mech's rig without moving it now. Bones:
    body (everything above the hips, arms and head included), thigh.L/R,
    shin.L/R, foot.L/R. L is the -x side of the mech."""
    bpy.context.view_layer.update()
    world = ob.matrix_world.copy()
    ob.parent, ob.parent_type, ob.parent_bone = rig, "BONE", bone
    bpy.context.view_layer.update()
    ob.matrix_world = world


def camera():
    cd = bpy.data.cameras.new("cam")
    cd.lens = CAMERA["lens"]
    cd.clip_end = 50000.0                          # the backdrop stands kilometres away
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = CAMERA["location"]
    cam.rotation_euler = Euler((math.radians(90 - CAMERA["pitch"]), 0, math.radians(180)), "XYZ")
    return cam


def render_setup(samples=SAMPLES, denoise=True, scale=1.0):
    """Cycles on the GPU that CUDA_VISIBLE_DEVICES names. Standard view
    transform: a surface that emits a picture then shows that picture as it
    is, which is how the backdrop is drawn."""
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = samples
    s.cycles.use_denoising = denoise
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for d in pr.devices:
        d.use = d.type == "CUDA"
    s.render.resolution_x, s.render.resolution_y = int(RES[0] * scale), int(RES[1] * scale)
    s.render.resolution_percentage = 100
    s.render.film_transparent = False
    s.view_settings.view_transform = "Standard"
    s.view_settings.look = "None"


def render(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def pixel(point):
    """Where a world point falls in the render: (x, y) in pixels of RES, y
    from the top, and its distance along the view axis."""
    from bpy_extras.object_utils import world_to_camera_view
    u, v, d = world_to_camera_view(bpy.context.scene, bpy.context.scene.camera, Vector(point))
    return u * RES[0], (1 - v) * RES[1], d


def layout():
    """The three mechs in the paint of banner 03 on a grey floor with a line
    every 10 m: where they stand in the frame, and what they hide."""
    mechrig.clear_scene()
    sc = Scene()
    load_mechs(sc)
    bpy.ops.mesh.primitive_plane_add(size=1200, location=(0, 0, 0))
    floor = bpy.data.materials.new("floor")
    floor.diffuse_color = (0.2, 0.2, 0.2, 1)
    bpy.context.object.data.materials.append(floor)
    line = bpy.data.materials.new("line")
    line.use_nodes = True
    line.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.9, 0.5, 0.1, 1)
    for k in range(-40, 6):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 10.0 * k, 0.02))
        o = bpy.context.object
        o.scale = (80.0, 0.3, 0.02)
        o.data.materials.append(line)
        o.parent = sc.ground
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.0
    sun.rotation_euler = Euler((math.radians(55), 0, math.radians(200)), "XYZ")
    bpy.context.collection.objects.link(sun)
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.55, 0.6, 1)
    render_setup(samples=32)
    sc.pose(0)
    render(os.path.join(PREVIEW, "layout.png"))

    info = dict(res=RES, camera=CAMERA, horizon_row=pixel((1.0, -1e6, CAMERA["location"][2]))[1], mechs={})
    deps = bpy.context.evaluated_depsgraph_get()
    for name, (mesh, rig) in sc.mechs.items():
        ev = mesh.evaluated_get(deps)
        pts = [pixel(ev.matrix_world @ ev.data.vertices[k].co) for k in range(0, len(ev.data.vertices), 50)]
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        info["mechs"][name] = dict(root=list(rig.location), box=[round(min(xs)), round(min(ys)), round(max(xs)), round(max(ys))],
                                   distance=round(sum(p[2] for p in pts) / len(pts), 1))
    for y in (0, -50, -100, -200, -400):
        info[f"ground_row_y{y}"] = round(pixel((1.0, y, 0.0))[1], 1)
    os.makedirs(WIP, exist_ok=True)
    json.dump(info, open(os.path.join(WIP, "layout.json"), "w"), indent=1)
    print("LAYOUT", json.dumps(info))


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "layout" in argv:
        layout()
