"""The procession scene (GIF 16): the three mechs of banner 03 walk at the
camera, the ground moves under them, and a distant backdrop stands behind,
built from a generated plate (src/procession/plates.py). Blender 4.5.

Backdrop. The plate is the camera's whole view, 2432 x 768, with the
horizon on row 295. Every plate pixel becomes a mesh vertex on its own
camera ray, so the fixed camera sees the plate as it is. Its distance along
the ray is the corrected depth of MoGe-2, times one factor: the factor that
puts the plate's own ground on the plane z = 0, 8.6 m under the camera. The
plate's ground itself is left out: the moving ground takes its place. The
sky lies behind everything. The mesh emits the plate and takes no light.
The depth gives each structure its haze; sky drifts and flames flicker
(`backdrop`).

Ground. As banner 03: a deck with a floor strip every 5 m and kerb blocks,
children of `scene.ground`, which slides one spacing per gait cycle. It
runs on to the backdrop, 1 to 2 km away.

Join. A ground fog in the plate's own horizon colour, thin at the mechs
and thick far off, covers the line where the moving deck meets the
backdrop. It is absorption plus emission in equal measure, so it shows the
same colour in any light.

    blender -b -P src/procession/scene.py -- [plate=terra_forge2] [livery=MODULE] [out=DIR] [tag=NAME] [N ...]

livery names a module of src/procession with paint(mesh, name); without it
the mechs wear the paint of banner 03.

Renders the frames N (default: all, and frame FRAMES as seam-check.png) to
wip/DIR (default frames-procession); with tag, writes frame N as
wip/preview/procession/<tag>-fNNN.png instead.
"""
import bpy, os, sys, math
import numpy as np
from mathutils import Euler, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F

PLATE = "terra_forge2"             # the chosen backdrop plate in wip/scene3d
HORIZON = 295                      # plate row of the camera's horizon
FOG_START, FOG_FULL, FOG_HEIGHT, FOG_DENSITY = -60.0, -500.0, 4.0, 0.002
HAZE = 0.00011                     # per metre: how fast a structure pales with distance
DRIFT = (10.0, -3.0)               # plate pixels per loop that the sky drifts: to the right and up
FLICKER = 0.3                      # share by which a flame brightens and dims
DECK = (0.011, 0.013, 0.018)
STRIP = (0.13, 0.085, 0.030)
KERB = (0.055, 0.060, 0.072)


def pbr(name, base, rough, metal):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def ground(sc):
    """The deck and what slides on it, as banner 03."""
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2900, 0))
    deck = bpy.context.object
    deck.name = "deck"
    deck.scale = (3000, 6200, 1)
    deck.data.materials.append(pbr("deck", DECK, 0.35, 0.25))
    strip, kerb = pbr("strip", STRIP, 0.75, 0.0), pbr("kerb", KERB, 0.70, 0.0)
    bpy.ops.mesh.primitive_cube_add(size=1)
    s0 = bpy.context.object
    s0.scale = (26.0, 0.55, 0.02)
    s0.data.materials.append(strip)
    bpy.ops.mesh.primitive_cube_add(size=1)
    k0 = bpy.context.object
    k0.scale = (2.2, 1.6, 0.9)
    k0.data.materials.append(kerb)
    for i in range(-300, 22):                    # beyond the fog at the far end, behind the camera at the near end
        y = i * F.STEP
        for src, loc in ((s0, (0, y, 0.02)), (k0, (-34.0, y, 0.45)), (k0, (34.0, y, 0.45))):
            o = bpy.data.objects.new(src.name, src.data)
            o.scale, o.location, o.parent = src.scale, loc, sc.ground
            bpy.context.collection.objects.link(o)
    for o in (s0, k0):
        bpy.data.objects.remove(o)


def rays(w, h):
    """For a plate of w x h pixels: the world direction of each pixel's
    camera ray, scaled so that its length along the view axis is 1."""
    cam = bpy.context.scene.camera
    th = cam.data.sensor_width / (2 * cam.data.lens)
    u, v = (np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h
    x, y = np.meshgrid((2 * u - 1) * th, (1 - 2 * v) * th * h / w)
    R = np.array(cam.matrix_world.to_3x3())
    return np.stack([x, y, -np.ones_like(x)], -1) @ R.T


def image(name, a):
    """A numpy array (rows from the top, values 0..1) as a Blender data image."""
    h, w = a.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=False, float_buffer=True, is_data=True)
    rgba = np.ones((h, w, 4), np.float32)
    rgba[..., :3] = a[::-1, :, None] if a.ndim == 2 else a[::-1]
    img.pixels.foreach_set(rgba.ravel())
    return img


def backdrop(sc, stem, step=2):
    """The plate as a mesh, from the corrected depth and the masks of
    src/procession/plates.py `edit`. Returns the object and the mean colour
    of the plate along the horizon.

    Haze: every pixel is mixed towards the horizon colour by
    1 - exp(-HAZE * distance), so near towers stay dark and far ones pale;
    only what is darker than the mix changes, so sky glow, fires and lit
    windows keep their light. Drift: in the sky the picture is read at
    two places that move DRIFT pixels per loop, half a loop apart, each
    faded out while it jumps back, so the loop closes. Flicker: flames
    brighten and dim by whole cycles per loop, each with its own phase."""
    d = np.load(stem + "_fx.npz")
    depth, sky, normal = d["depth"], d["sky"], d["normal"]
    H, W = depth.shape
    C = np.array(bpy.context.scene.camera.location)
    D = rays(W, H)
    # the plate's ground: below the horizon, normal pointing up (-y in the camera of MoGe-2)
    rows = np.arange(H)[:, None] * np.ones((1, W))
    floor = d["mask"] & ~sky & (rows > HORIZON + 3) & (normal[..., 1] < -0.8)
    on_plane = -C[2] / np.minimum(D[..., 2], -1e-6)          # view-axis distance at which a ray meets z = 0
    ratio = on_plane[floor] / depth[floor]
    scale = float(np.median(ratio))
    Z = depth * scale
    solid = ~sky & ~floor
    solid[int(d["rows"][1]):] = False
    far = 1.05 * float(Z[solid].max())
    print(f"BACKDROP ground pixels {floor.sum()}, scale {scale:.1f} (quartiles {np.percentile(ratio, 25):.1f}, "
          f"{np.percentile(ratio, 75):.1f}); structures {np.percentile(Z[solid], 2):.0f} to {Z[solid].max():.0f} m, sky at {far:.0f} m")
    Z[sky] = far
    P = C + D * Z[..., None]
    P[..., 2] = np.where(sky, P[..., 2], np.maximum(P[..., 2], 0.0))    # nothing solid lies under the ground
    r1 = int(d["rows"][1])
    Pm, fl = P[:r1:step, ::step], floor[:r1:step, ::step]
    h, w = fl.shape
    idx = np.arange(h * w).reshape(h, w)
    a, b, c, e = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    keep = ~(fl[:-1, :-1] & fl[:-1, 1:] & fl[1:, 1:] & fl[1:, :-1])
    quads = np.stack([a, e, c, b], -1)[keep]
    uv = np.stack([(np.arange(w) * step + 0.5) / W * np.ones((h, 1)),
                   1 - (np.arange(h)[:, None] * step + 0.5) / H * np.ones((1, w))], -1).reshape(-1, 2)
    me = bpy.data.meshes.new("backdrop")
    me.vertices.add(h * w)
    me.vertices.foreach_set("co", Pm.reshape(-1, 3).astype(np.float32).ravel())
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel())
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4))
    me.polygons.foreach_set("loop_total", np.full(len(quads), 4))
    me.uv_layers.new(name="uv").data.foreach_set("uv", uv[quads.ravel()].ravel())
    me.update()
    ob = bpy.data.objects.new("backdrop", me)
    bpy.context.collection.objects.link(ob)
    ob.visible_shadow = False

    m = bpy.data.materials.new("backdrop")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    plate = bpy.data.images.load(stem + ".png")
    px = np.asarray(plate.pixels[:], np.float32).reshape(H, W, 4)[::-1]
    haze = tuple(float(v) for v in px[HORIZON - 12:HORIZON + 2, :, :3].mean((0, 1)))
    veil = 1 - np.exp(-HAZE * Z)
    for _ in range(3):                               # soft edges: the masks are a few pixels off the true outlines
        for ax in (0, 1):
            pad = np.concatenate([np.repeat(veil.take([0], ax), 4, ax), veil, np.repeat(veil.take([-1], ax), 4, ax)], ax)
            cs = np.cumsum(np.insert(pad, 0, 0, ax), ax)
            veil = (cs.take(range(9, 9 + veil.shape[ax]), ax) - cs.take(range(0, veil.shape[ax]), ax)) / 9

    def calc(kind, x, y=None, z=None):
        n = N.new("ShaderNodeMath")
        n.operation = kind
        for k, v in enumerate((x, y, z)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[k].default_value = v
            else:
                L.new(v, n.inputs[k])
        return n.outputs[0]

    def data(name, arr):
        t = N.new("ShaderNodeTexImage")
        t.image, t.extension = image(name, arr), "EXTEND"
        L.new(uvn, t.inputs["Vector"])
        return t.outputs["Color"]

    uvn = N.new("ShaderNodeTexCoord").outputs["UV"]
    phase = N.new("ShaderNodeValue")
    phase.name = "phase"
    flow = data("flow", d["flow"])
    shots = []
    for shift in (0.0, 0.5):                         # the two readings of the drifting sky
        f = calc("FRACT", calc("ADD", phase.outputs[0], shift))
        amount = calc("MULTIPLY", flow, calc("SUBTRACT", f, 0.5))
        off = N.new("ShaderNodeCombineXYZ")
        L.new(calc("MULTIPLY", amount, -DRIFT[0] / W), off.inputs["X"])      # reading to the left moves the picture right
        L.new(calc("MULTIPLY", amount, DRIFT[1] / H), off.inputs["Y"])
        at = N.new("ShaderNodeVectorMath")
        L.new(uvn, at.inputs[0])
        L.new(off.outputs[0], at.inputs[1])
        tex = N.new("ShaderNodeTexImage")
        tex.image, tex.interpolation, tex.extension = plate, "Cubic", "EXTEND"
        L.new(at.outputs[0], tex.inputs["Vector"])
        shots.append((tex.outputs["Color"], calc("SUBTRACT", 1.0, calc("ABSOLUTE", calc("MULTIPLY_ADD", f, 2.0, -1.0)))))
    both = N.new("ShaderNodeMix")
    both.data_type = "RGBA"
    L.new(shots[0][1], both.inputs["Factor"])
    L.new(shots[1][0], both.inputs["A"])
    L.new(shots[0][0], both.inputs["B"])
    mixed = N.new("ShaderNodeMix")
    mixed.data_type = "RGBA"
    L.new(data("veil", veil), mixed.inputs["Factor"])
    L.new(both.outputs["Result"], mixed.inputs["A"])
    mixed.inputs["B"].default_value = (*haze, 1)
    hazed = N.new("ShaderNodeMix")                    # haze lifts what is dark; sky glow, fires and lit windows keep their light
    hazed.data_type, hazed.blend_type = "RGBA", "LIGHTEN"
    hazed.inputs["Factor"].default_value = 1.0
    L.new(both.outputs["Result"], hazed.inputs["A"])
    L.new(mixed.outputs["Result"], hazed.inputs["B"])
    spot = N.new("ShaderNodeTexNoise")                # a phase per flame
    spot.inputs["Scale"].default_value = 60.0
    L.new(uvn, spot.inputs["Vector"])
    turn = calc("MULTIPLY", phase.outputs[0], 2 * math.pi)
    where = calc("MULTIPLY", spot.outputs["Fac"], 40.0)
    wave = calc("ADD", calc("MULTIPLY", calc("SINE", calc("MULTIPLY_ADD", turn, 3.0, where)), 0.6),
                calc("MULTIPLY", calc("SINE", calc("MULTIPLY_ADD", turn, 7.0, calc("MULTIPLY", where, 2.3))), 0.4))
    em = N.new("ShaderNodeEmission")
    L.new(hazed.outputs["Result"], em.inputs["Color"])
    L.new(calc("MULTIPLY_ADD", calc("MULTIPLY", data("fire", d["fire"]), wave), FLICKER, 1.0), em.inputs["Strength"])
    L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    m.cycles.emission_sampling = "NONE"              # seen and mirrored, but not sampled as a light of a million faces
    me.materials.append(m)
    sc.movers.append(lambda i: setattr(phase.outputs[0], "default_value", (i % F.FRAMES) / F.FRAMES))
    return ob, haze


def fog(colour):
    """Ground fog of one colour: dense at the floor, thinning with height,
    none at the mechs, full from FOG_FULL on. The box reaches below the floor
    (a volume face on a surface flickers)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -3100, 30))
    box = bpy.context.object
    box.name = "ground_fog"
    box.scale = (6000, 6100, 80)
    m = bpy.data.materials.new("ground_fog")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(N.new("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])

    def calc(kind, a, b):
        n = N.new("ShaderNodeMath")
        n.operation = kind
        for i, v in enumerate((a, b)):
            if isinstance(v, float):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    height = calc("EXPONENT", calc("MULTIPLY", calc("MAXIMUM", sep.outputs["Z"], 0.0), -1.0 / FOG_HEIGHT), 0.0)
    front = N.new("ShaderNodeMapRange")
    front.interpolation_type = "SMOOTHSTEP"
    front.inputs["From Min"].default_value, front.inputs["From Max"].default_value = FOG_START, FOG_FULL
    L.new(sep.outputs["Y"], front.inputs["Value"])
    density = calc("MULTIPLY", calc("MULTIPLY", height, front.outputs["Result"]), FOG_DENSITY)
    ab = N.new("ShaderNodeVolumeAbsorption")
    ab.inputs["Color"].default_value = (0, 0, 0, 1)
    L.new(density, ab.inputs["Density"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*colour, 1)
    L.new(density, em.inputs["Strength"])
    add = N.new("ShaderNodeAddShader")
    L.new(ab.outputs[0], add.inputs[0])
    L.new(em.outputs[0], add.inputs[1])
    L.new(add.outputs[0], N["Material Output"].inputs["Volume"])
    m.cycles.emission_sampling = "NONE"
    box.data.materials.append(m)
    box.visible_shadow = False


def lights(haze):
    """The plate's light: a low pale sun behind the skyline on the left of
    the picture, the sky's cold light from the front, and its own haze
    colour from all round."""
    for name, energy, colour, angle, rot in (("sun", 4.0, (1.0, 0.86, 0.66), 6, (68, 0, 50)),
                                              ("sky", 1.3, (0.62, 0.72, 0.9), 40, (52, 0, 200))):
        lamp = bpy.data.lights.new(name, "SUN")
        lamp.energy, lamp.color, lamp.angle = energy, colour, math.radians(angle)
        o = bpy.data.objects.new(name, lamp)
        o.rotation_euler = Euler([math.radians(a) for a in rot], "XYZ")
        bpy.context.collection.objects.link(o)
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*(0.35 * c for c in haze), 1)


def build(plate, livery=None):
    """The whole scene. livery(mesh, name) paints a mech's mesh before it is
    rigged; without it the mechs wear the paint of banner 03."""
    F.mechrig.clear_scene()
    sc = F.Scene()
    F.load_mechs(sc, livery=livery)
    ground(sc)
    ob, haze = backdrop(sc, os.path.join(F.ROOT, "wip", "scene3d", plate))
    fog(haze)
    lights(haze)
    F.render_setup()
    return sc


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opt = dict(a.split("=", 1) for a in argv if "=" in a)
    livery = __import__(opt["livery"]).paint if "livery" in opt else None
    sc = build(opt.get("plate", PLATE), livery)
    out = os.path.join(F.ROOT, "wip", opt.get("out", "frames-procession"))
    for i in ([int(a) for a in argv if a.isdigit()] or range(F.FRAMES + 1)):
        sc.pose(i)
        if "tag" in opt:
            F.render(os.path.join(F.PREVIEW, f"{opt['tag']}-f{i:03d}.png"))
        else:
            F.render(os.path.join(out, f"f{i:03d}.png" if i < F.FRAMES else "seam-check.png"))
        print(f"FRAME {i}", flush=True)
    print("RENDER_DONE")
