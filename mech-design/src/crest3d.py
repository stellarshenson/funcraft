"""The crest of the welcome page as a 3D medallion: the picture and the relief
of src/crest.py on a mesh, lit and rendered from the front. Blender 4.5,
Cycles.

Every picture pixel pair becomes a mesh vertex, raised by the relief that
MoGe-2 estimated. The surface shows the picture twice: unlit, at the share
OWN, so the paint keeps its contrast, and as a lit, slightly glossy surface,
so the relief throws light and shadow of its own and the steel and the lens
glint.

    blender -b -P src/crest3d.py      # resources/assets/cog-mechanicum.png, 1024 x 1024, transparent

src/welcome.py embeds the result. `medallion` gives the mesh alone, for a model that wears the crest
(src/marauder.py).
"""
import bpy, os, math
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "wip", "crest")
RELIEF = 0.085                     # height of the highest point, as a share of the medallion's diameter
STEP = 2                           # picture pixels per mesh vertex
OWN = 0.55                         # share of the picture shown unlit


def medallion(relief=RELIEF, step=STEP):
    """The medallion as a mesh object of diameter 1 at the origin: it stands
    in the x-z plane and faces +Y. Its UV layer `uv` reads wip/crest/crest.png."""
    d = np.load(os.path.join(SRC, "crest.npz"))
    height, (cx, cy), r = d["height"], d["centre"], float(d["radius"])
    H, W = height.shape
    ys, xs = np.arange(0, H, step), np.arange(0, W, step)
    X, Y = np.meshgrid(xs, ys)
    # the medallion has diameter 1, stands in the x-z plane and faces +Y; picture x runs to -X, so the camera on +Y sees it unmirrored
    P = np.stack([-(X - cx) / (2 * r), height[np.ix_(ys, xs)] * relief, -(Y - cy) / (2 * r)], -1)
    inside = np.hypot(X - cx, Y - cy) < r - 2
    h, w = inside.shape
    idx = np.arange(h * w).reshape(h, w)
    a, b, c, e = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    keep = inside[:-1, :-1] & inside[:-1, 1:] & inside[1:, 1:] & inside[1:, :-1]
    quads = np.stack([a, b, c, e], -1)[keep]
    uv = np.stack([(X + 0.5) / W, 1 - (Y + 0.5) / H], -1).reshape(-1, 2)
    me = bpy.data.meshes.new("crest")
    me.vertices.add(h * w)
    me.vertices.foreach_set("co", P.reshape(-1, 3).astype(np.float32).ravel())
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4))
    me.polygons.foreach_set("loop_total", np.full(len(quads), 4))
    me.polygons.foreach_set("use_smooth", np.ones(len(quads), bool))
    me.uv_layers.new(name="uv").data.foreach_set("uv", uv[quads.ravel()].ravel())
    me.update()
    ob = bpy.data.objects.new("crest", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


if __name__ == "__main__":
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob = medallion()
    me = ob.data
    m = bpy.data.materials.new("crest")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    tex = N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(SRC, "crest.png"))
    tex.extension = "EXTEND"
    b = N["Principled BSDF"]
    L.new(tex.outputs["Color"], b.inputs["Base Color"])
    L.new(tex.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = OWN
    b.inputs["Roughness"].default_value = 0.38
    me.materials.append(m)

    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = 128
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for dv in pr.devices:
        dv.use = dv.type == "CUDA"
    s.render.resolution_x = s.render.resolution_y = 1024
    s.render.film_transparent = True
    s.view_settings.view_transform = "Standard"
    wd = bpy.data.worlds.new("w")
    s.world = wd
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs["Color"].default_value = (0.55, 0.6, 0.7, 1)
    wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy, sun.data.angle = 2.2, math.radians(8)
    sun.rotation_euler = (math.radians(-58), math.radians(-32), 0)          # from the upper left, as the picture is painted
    s.collection.objects.link(sun)
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type, cam.data.ortho_scale = "ORTHO", 1.01
    s.collection.objects.link(cam)
    s.camera = cam
    cam.location = (0, 5, 0)
    cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.render.filepath = os.path.join(ROOT, "resources", "assets", "cog-mechanicum.png")
    bpy.ops.render.render(write_still=True)
    print("CREST3D_DONE")
