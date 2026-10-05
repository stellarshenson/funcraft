"""The contract of the procession scene (GIF 16). Blender 4.5.

The scene is banner 03 of mech-design with another backdrop and decorated
mechs: three BattleMechs walk at the camera, the ground moves under them,
a backdrop stands far behind. Meshes, armature and walk are read from the
sibling project mech-design and are not changed here.

Frame of reference, as in banner 03. Units are metres: a mech is 12 to 13.4
tall. The camera stands still at CAMERA and looks along -Y, so world +X is on
the left of the picture. The mechs face +Y and walk on the spot. The ground
slides away from the camera, along -Y, at the speed of the planted feet.

Loop. FRAMES frames at 50 ms hold CYCLES gait cycles of GAIT_FRAMES frames,
the timing of banner 03. In one loop the ground travels TRAVEL = STEP *
CYCLES. Frame FRAMES must show exactly what frame 0 shows:

    still     the backdrop's structures, the camera, the lights
    sliding   everything that lies on the ground: child of `scene.ground`,
              repeated along Y with a period that divides TRAVEL, and laid
              beyond both ends of what the camera sees
    cyclic    every other motion: a whole number of cycles in FRAMES frames

A mover is a function f(i) of the frame number 0..FRAMES, with f(FRAMES)
leaving the state of f(0); Scene.pose(i) calls them all.

    blender -b -P src/procession/frame.py -- layout     # wip/preview/procession/layout.png, wip/procession/layout.json
"""
import bpy, os, sys, math, json, importlib.util
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))                  # w40k-mechanicum
MECH = os.path.join(os.path.dirname(ROOT), "mech-design")      # the sibling project
WIP = os.path.join(ROOT, "wip", "procession")                  # generated data, not tracked
PREVIEW = os.path.join(ROOT, "wip", "preview", "procession")   # pictures to look at
sys.path.insert(0, os.path.join(ROOT, "src"))

GAIT_FRAMES = 30                   # one gait cycle, left and right step: as banner 03
CYCLES = 1                         # gait cycles per loop
FRAMES = GAIT_FRAMES * CYCLES      # one loop
FRAME_S = 0.050                    # seconds per frame in the GIF
STEP = 5.0                         # ground travel per gait cycle
TRAVEL = STEP * CYCLES             # ground travel per loop: sliding things repeat with a period that divides this
RES = (1520, 480)                  # render, 19:6
GIF = (1140, 360)                  # what the viewer sees: judge every picture at this size
SAMPLES = 64

CAMERA = dict(location=(1.0, 58.0, 8.6), lens=42.0, pitch=1.8)   # pitch: degrees below level
# chassis and world position of its root; all face +Y
PLACEMENT = [("battlemaster", (-19.0, -31.0, 0.0)),              # right of the picture, furthest
             ("madcat", (-3.0, -7.0, 0.0)),                      # centre, nearest
             ("atlas", (15.0, -19.0, 0.0))]                      # left, middle distance


def _mech(name):
    """A module of mech-design/src under the name mech_<name>: both projects
    have a rig.py and an assemble.py, so they cannot share sys.path."""
    spec = importlib.util.spec_from_file_location(f"mech_{name}", os.path.join(MECH, "src", f"{name}.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules[f"mech_{name}"] = m
    spec.loader.exec_module(m)
    return m


mechrig, mechpaint, mechwalk, mechlogo = _mech("mechrig"), _mech("paint"), _mech("rig"), _mech("logo")
LOGO = os.path.join(MECH, "resources", "assets", "stellars_tech_ai_lab_gh_behemoth_logo.svg")


class Scene:
    """What the modules share: mechs[name] = (mesh, rig), the sliding
    `ground` empty, and the list of movers."""

    def __init__(self):
        self.mechs, self.movers = {}, []
        self.ground = bpy.data.objects.new("ground", None)
        bpy.context.collection.objects.link(self.ground)
        self.movers.append(self._slide)
        self.cam = camera()

    def _slide(self, i):
        self.ground.location = (0.0, -TRAVEL * i / FRAMES, 0.0)

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
    on z = 0, in its own coordinates."""
    for name, loc in PLACEMENT:
        mesh = mechrig.load(name)
        mesh.name = name
        (livery or mechpaint.paint)(mesh, name)
        if dress:
            dress(mesh, name)
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = mesh
        mesh.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(31))
        rig = mechwalk.build(mesh, name)
        rig.location = loc
        scene.mechs[name] = (mesh, rig)

    def walk(i):
        for name, (_, rig) in scene.mechs.items():
            mechwalk.walk(rig, name, (i % GAIT_FRAMES) / GAIT_FRAMES, STEP)

    scene.movers.append(walk)


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
