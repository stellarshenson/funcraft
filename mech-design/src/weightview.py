"""Show which bone owns each part of the mesh, as flat colours, from four sides.

Run:
    blender -b -P src/weightview.py [-- madcat atlas battlemaster]

Writes wip/preview/rig/<chassis>-weights.png. Grey body; left leg red (thigh),
orange (shin), yellow (foot); right leg blue, cyan, green. Blends mix colours.
"""
import bpy, sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
import rig as G
from mathutils import Euler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COL = {"body": (0.5, 0.5, 0.5), "thigh.L": (0.9, 0.05, 0.05), "shin.L": (1.0, 0.45, 0.0),
       "foot.L": (1.0, 0.9, 0.0), "thigh.R": (0.05, 0.2, 1.0), "shin.R": (0.0, 0.85, 0.9),
       "foot.R": (0.1, 0.9, 0.1)}


def view(name):
    cfg = R.CHASSIS[name]
    R.clear_scene()
    mech = R.load(name)
    n = len(mech.data.vertices)
    co = np.empty(n * 3); mech.data.vertices.foreach_get("co", co); co = co.reshape(-1, 3)
    ed = np.empty(len(mech.data.edges) * 2, dtype=np.int64)
    mech.data.edges.foreach_get("vertices", ed)
    W = G.skin_weights(name, co, ed.reshape(-1, 2))
    c = sum(np.outer(W[k], COL[k]) for k in COL)
    attr = mech.data.color_attributes.new("own", "FLOAT_COLOR", "POINT")
    attr.data.foreach_set("color", np.hstack([c, np.ones((n, 1))]).ravel())
    m = bpy.data.materials.new("own"); m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    a = N.new("ShaderNodeAttribute"); a.attribute_name = "own"
    b = N["Principled BSDF"]; L.new(a.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.7
    mech.data.materials.append(m)
    w = bpy.data.worlds.new("w"); bpy.context.scene.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.6, 0.6, 0.6, 1)
    s = bpy.context.scene; s.render.engine = "CYCLES"; s.cycles.samples = 16; s.cycles.device = "GPU"
    pr = bpy.context.preferences.addons["cycles"].preferences; pr.compute_device_type = "CUDA"; pr.get_devices()
    for dv in pr.devices: dv.use = dv.type == "CUDA"
    s.view_settings.view_transform = "Standard"
    s.render.resolution_x, s.render.resolution_y = 600, 700
    cd = bpy.data.cameras.new("c"); cd.type = "ORTHO"; cd.ortho_scale = cfg["height"] * 1.12
    cam = bpy.data.objects.new("c", cd); bpy.context.collection.objects.link(cam); s.camera = cam
    H = cfg["height"]; tiles = []
    for tag, az in (("front", 0), ("right", 90), ("back", 180), ("left", 270)):
        a_ = math.radians(az)
        cam.location = (40 * math.sin(a_), 40 * math.cos(a_), H * 0.5)
        cam.rotation_euler = Euler((math.radians(90), 0, math.radians(180) - a_), "XYZ")
        s.render.filepath = f"/tmp/claude-1000/-home-lab/b27aed3a-e113-4406-a72a-7eb8ced4455c/scratchpad/w-{name}-{tag}.png"
        bpy.ops.render.render(write_still=True)
    print("WEIGHTS", name)


argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
for nm in argv or ["madcat", "atlas", "battlemaster"]:
    view(nm)
