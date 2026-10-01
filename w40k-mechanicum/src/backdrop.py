"""A 3D backdrop from a reference image: the MoGe-2 point map
(src/img2geometry.py) as a mesh, textured with the image itself, seen by a
camera that matches the image. From its own viewpoint it reproduces the
image; a camera moved a little shows real parallax.

Test run (renders previews into wip/preview/):
    blender -b -P src/backdrop.py -- wip/scene3d/altar-rite
"""
import bpy, bmesh, math, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def layer(name, V, uv, quads, image):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.ravel())
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4))
    me.polygons.foreach_set("loop_total", np.full(len(quads), 4))
    me.uv_layers.new(name="uv").data.foreach_set("uv", uv[quads.ravel()].ravel())
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    tex = N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(image)
    tex.interpolation = "Cubic"
    em = N.new("ShaderNodeEmission")
    L.new(tex.outputs["Color"], em.inputs["Color"])
    L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    me.materials.append(m)
    return ob


def backdrop(stem, step=2, cut=1.25):
    """Mesh of `stem`.npz textured with `stem`.png. One vertex per `step`
    pixels; a quad whose far corner is over `cut` times the depth of its near
    corner spans a depth break and is left out. Pixels MoGe-2 leaves out (the
    sky) become a far dome at twice the farthest depth. Camera coordinates are
    OpenCV's (x right, y down, z forward); the world here is x right, y
    forward, z up, the camera at the origin looking along +Y. Returns the
    object and the horizontal field of view in radians."""
    d = np.load(stem + ".npz")
    P, mask = d["points"][::step, ::step].copy(), d["mask"][::step, ::step].copy()
    h, w = mask.shape
    bg = d["bg_depth"][::step, ::step].copy()
    if not mask.all():
        K = d["intrinsics"]
        far = 2 * float(P[..., 2][mask].max())
        u = (np.arange(w) * step + 0.5) / (w * step)
        v = (np.arange(h) * step + 0.5) / (h * step)
        ray = np.stack(np.broadcast_arrays((u[None, :] - K[0, 2]) / K[0, 0], (v[:, None] - K[1, 2]) / K[1, 1],
                                           np.ones((h, w))), -1)
        P[~mask] = ray[~mask] * far
        bg[~mask | ~np.isfinite(bg)] = far
        mask[:] = True
    V = np.stack([P[..., 0], P[..., 2], -P[..., 1]], -1).reshape(-1, 3)
    V[~np.isfinite(V)] = 0
    idx = np.arange(h * w).reshape(h, w)
    a, b, c, e = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    z = P[..., 2]
    zq = np.stack([z[:-1, :-1], z[:-1, 1:], z[1:, 1:], z[1:, :-1]], -1)
    mq = np.stack([mask[:-1, :-1], mask[:-1, 1:], mask[1:, 1:], mask[1:, :-1]], -1).all(-1)
    keep = mq & (zq.max(-1) < cut * zq.min(-1))
    quads = np.stack([a, e, c, b], -1)[keep]                     # counter-clockwise seen from the camera
    uv = np.stack([(np.arange(w) * step + 0.5) / (w * step) * np.ones((h, 1)),
                   1 - (np.arange(h)[:, None] * step + 0.5) / (h * step) * np.ones((1, w))], -1).reshape(-1, 2)
    ob = layer("backdrop", V, uv, quads, stem + ".png")
    # the fill: the same grid pushed back to the far side of every depth
    # break, whole, painted with the inpainted image, a little behind the
    # front layer so it only shows where the front layer is cut
    far = bg * 1.01
    Pb = P * (far / np.where(z > 0, z, 1))[..., None]
    Vb = np.stack([Pb[..., 0], Pb[..., 2], -Pb[..., 1]], -1).reshape(-1, 3)
    Vb[~np.isfinite(Vb)] = 0
    layer("backdrop_fill", Vb, uv, np.stack([a, e, c, b], -1).reshape(-1, 4), stem + "_bg.png")
    fx = float(d["intrinsics"][0, 0])                          # normalised by the image width
    return ob, 2 * math.atan(0.5 / fx)


def camera(fov, res, band=0.5, at=(0, 0, 0), look=None):
    """A camera with the image's horizontal field of view; `band` is the
    image row (0 top, 1 bottom) at the centre of a frame narrower than the
    image."""
    s = bpy.context.scene
    cd = bpy.data.cameras.new("cam")
    cd.sensor_fit = "HORIZONTAL"
    cd.lens = cd.sensor_width / (2 * math.tan(fov / 2))
    cam = bpy.data.objects.new("cam", cd)
    s.collection.objects.link(cam)
    s.camera = cam
    cam.location = at
    cam.rotation_euler = (math.pi / 2, 0, 0)
    s.render.resolution_x, s.render.resolution_y = res
    return cam


if __name__ == "__main__":
    stem = os.path.join(ROOT, sys.argv[sys.argv.index("--") + 1])
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ob, fov = backdrop(stem)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = 16
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for dv in pr.devices:
        dv.use = dv.type == "CUDA"
    s.view_settings.view_transform = "Standard"
    cam = camera(fov, (1122, 1402))
    print("FOV", math.degrees(fov), "faces", len(ob.data.polygons))
    name = os.path.basename(stem)
    for tag, loc in (("orig", (0, 0, 0)), ("left", (-0.25, 0.3, 0)), ("up", (0.1, 0.4, 0.2)), ("near", (-0.05, 0.08, 0.02))):
        cam.location = loc
        s.render.filepath = os.path.join(ROOT, "wip", "preview", f"backdrop-{name}-{tag}.png")
        bpy.ops.render.render(write_still=True)
