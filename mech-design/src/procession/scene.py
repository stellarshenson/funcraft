"""The procession scene (banner 07): the three mechs of banner 03 walk at the
camera, the ground moves under them, and a distant backdrop stands behind,
built from a generated plate (src/procession/plates.py). Blender 4.5.

Backdrop. The plate is the camera's whole view, 2432 x 768, with the
horizon on row 295. Every plate pixel becomes a mesh vertex on its own
camera ray, so the fixed camera sees the plate as it is. Its distance along
the ray is the corrected depth of MoGe-2, times one factor: the factor that
puts the plate's own ground on the plane z = 0, 8.6 m under the camera. The
plate's ground itself is left out: the moving ground takes its place. The
sky lies behind everything. The mesh reaches MARGIN pixels beyond the plate
on the left, the right and the top, with the plate's edge pixels repeated:
the camera's jolt at a footfall (src/procession/frame.py) shows them. The mesh emits the plate and takes no light.
The depth gives each structure its haze; sky drifts and flames flicker
(`backdrop`).

Ground. It moves as in banner 03, away from the camera, by frame.STEP per
gait cycle. Its surface is a generated pavement (src/procession/groundtex.py)
that repeats along the way with the ground's travel of one loop; it runs on
to the backdrop.

Join. A ground fog in the plate's own horizon colour, thin at the mechs
and thick far off, covers the line where the moving deck meets the
backdrop. It is absorption plus emission in equal measure, so it shows the
same colour in any light.

Mist. As in banner 03, a low, patchy ground fog lies on the deck behind the
rearmost of the three mechs, so none of it is in front of one of them. It
stands still. The rear mechs of banner 09 stand in it.

Air. Embers rise from the deck, and simulated smoke stands over the
chimneys of the backdrop (src/procession/effects.py).

    blender -b -P src/procession/scene.py -- [plate=terra_forge2] [livery=MODULE] [hips=DEGREES] [rear=COUNT] [marauder=INDEX] [cloth=1] [solo=CHASSIS] [out=DIR] [tag=NAME] [N ...]

livery names a module of src/procession with paint(mesh, name); without it
the mechs wear the paint of banner 03. rear puts that many mechs of
frame.REAR behind the three (banner 09: 6), and marauder puts the Marauder
in the place of that one of them (banner 10: 0). cloth hangs the cloth banners
of src/procession/cloth.py on their mechs (banner 10). solo shows one chassis alone,
where the Mad Cat walks: a preview of that chassis.

Renders the frames N (default: all, and frame FRAMES as seam-check.png) to
wip/DIR (default frames-procession); with tag, writes frame N as
wip/preview/procession/<tag>-fNNN.png instead.
"""
import bpy, os, sys, math, json
import numpy as np
from mathutils import Euler, Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F
import effects

PLATE = "terra_forgeto51c"           # the chosen backdrop plate in wip/scene3d: forgeto51 with its painted smoke out (plates.py desmoke)
HORIZON = 295                      # plate row of the camera's horizon
MARGIN = 16                        # plate pixels of backdrop beyond the frame: the jolt turns the camera by up to 0.12 degrees, 4 pixels
FOG_START, FOG_FULL, FOG_HEIGHT, FOG_DENSITY = -150.0, -900.0, 6.0, 0.0012
MIST_FRONT, MIST_FULL, MIST_HEIGHT = -42.0, -75.0, 2.8   # as banner 03: it starts behind the BattleMaster at y = -31
MIST_DENSITY = 0.016               # per metre at the floor, where the mist is of mean thickness; banner 03 has 0.028, which hid the far deck here
HAZE = 0.00004                     # per metre: how fast a structure pales with distance
DRIFT = (10.0, -3.0)               # plate pixels per loop that the sky drifts: to the right and up
FLICKER = 0.3                      # share by which a flame brightens and dims
GROUND = os.path.join(F.WIP, "ground")   # the pavement piece: colour.png, maps.png, meta.json
DECK_TONE = 0.85                   # the pavement's colour is multiplied by this: the plate's own ground is dark
DECK_ROUGH = (0.10, 0.42)          # roughness of the wet iron: in a puddle, outside
GLOW_COLOUR = (1.0, 0.30, 0.05)    # the light under the grates
GLOW_SEEN = 2.2                    # emission of a grate as the camera sees it
GLOW_WATTS = 450.0                 # power of the light of one glowing line, 40 m long


def ground(sc):
    """The deck: one plane that carries the generated pavement
    (src/procession/groundtex.py). The plane stands still; the pavement is
    laid out in the coordinates of `sc.ground`, so it slides with it. The
    piece is mirrored in both directions. Brass is metal and smooth, the rest
    wet iron with puddles (smooth where a slow noise is low); the piece's
    height map is the bump. The glow of the grates is seen, and lights the
    mechs through one upward area light per glowing line, which slides with
    the ground too."""
    meta = json.load(open(os.path.join(GROUND, "meta.json")))
    wide, length = meta["width"], meta["length"]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -2900, 0))
    deck = bpy.context.object
    deck.name = "deck"
    deck.scale = (3000, 6200, 1)
    m = bpy.data.materials.new("deck")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]

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

    tc = N.new("ShaderNodeTexCoord")
    tc.object = sc.ground
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["Object"], sep.inputs[0])
    uv = N.new("ShaderNodeCombineXYZ")
    L.new(calc("PINGPONG", calc("MULTIPLY_ADD", sep.outputs["X"], 1 / wide, 0.5), 1.0), uv.inputs["X"])
    L.new(calc("PINGPONG", calc("MULTIPLY", sep.outputs["Y"], 1 / length), 1.0), uv.inputs["Y"])
    col, maps = N.new("ShaderNodeTexImage"), N.new("ShaderNodeTexImage")
    col.image = bpy.data.images.load(os.path.join(GROUND, "colour.png"))
    maps.image = bpy.data.images.load(os.path.join(GROUND, "maps.png"))
    maps.image.colorspace_settings.name = "Non-Color"
    for t in (col, maps):
        t.extension = "EXTEND"
        L.new(uv.outputs[0], t.inputs["Vector"])
    ch = N.new("ShaderNodeSeparateColor")
    L.new(maps.outputs["Color"], ch.inputs[0])
    brass, glow, height = ch.outputs[0], ch.outputs[1], ch.outputs[2]
    tint = N.new("ShaderNodeVectorMath")
    tint.operation = "SCALE"
    tint.inputs["Scale"].default_value = DECK_TONE
    L.new(col.outputs["Color"], tint.inputs[0])
    L.new(tint.outputs["Vector"], bsdf.inputs["Base Color"])
    L.new(brass, bsdf.inputs["Metallic"])
    # noise that repeats with the ground's travel per loop: the way is rolled up into a cylinder of that circumference
    turn = calc("MULTIPLY", sep.outputs["Y"], 2 * math.pi / F.TRAVEL)
    rolled = N.new("ShaderNodeCombineXYZ")
    L.new(sep.outputs["X"], rolled.inputs["X"])
    L.new(calc("MULTIPLY", calc("COSINE", turn), F.TRAVEL / (2 * math.pi)), rolled.inputs["Y"])
    L.new(calc("MULTIPLY", calc("SINE", turn), F.TRAVEL / (2 * math.pi)), rolled.inputs["Z"])
    noise = N.new("ShaderNodeTexNoise")                  # puddles: metres wide, sliding with the ground
    noise.inputs["Scale"].default_value = 0.12
    noise.inputs["Detail"].default_value = 4.0
    L.new(rolled.outputs[0], noise.inputs["Vector"])
    wet = N.new("ShaderNodeMapRange")
    wet.inputs["From Min"].default_value, wet.inputs["From Max"].default_value = 0.42, 0.62
    wet.inputs["To Min"].default_value, wet.inputs["To Max"].default_value = DECK_ROUGH
    L.new(noise.outputs["Fac"], wet.inputs["Value"])
    L.new(calc("MULTIPLY_ADD", brass, calc("SUBTRACT", 0.3, wet.outputs["Result"]), wet.outputs["Result"]), bsdf.inputs["Roughness"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value, bump.inputs["Distance"].default_value = 0.6, 0.05
    L.new(height, bump.inputs["Height"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    fire = N.new("ShaderNodeTexNoise")                   # the furnaces below: stretches of a grate glow, others are dark
    fire.inputs["Scale"].default_value = 0.07
    fire.inputs["Detail"].default_value = 2.0
    L.new(rolled.outputs[0], fire.inputs["Vector"])
    lit = N.new("ShaderNodeMapRange")
    lit.interpolation_type = "SMOOTHSTEP"
    lit.inputs["From Min"].default_value, lit.inputs["From Max"].default_value = 0.42, 0.66
    lit.inputs["To Min"].default_value = 0.04
    L.new(fire.outputs["Fac"], lit.inputs["Value"])
    hot = N.new("ShaderNodeMix")                         # dull red where the fire is low, orange where it is high
    hot.data_type = "RGBA"
    L.new(lit.outputs["Result"], hot.inputs["Factor"])
    hot.inputs["A"].default_value = (0.9, 0.06, 0.01, 1)
    hot.inputs["B"].default_value = (*GLOW_COLOUR, 1)
    L.new(hot.outputs["Result"], bsdf.inputs["Emission Color"])
    L.new(calc("MULTIPLY", calc("MULTIPLY", glow, lit.outputs["Result"]), GLOW_SEEN), bsdf.inputs["Emission Strength"])
    m.cycles.emission_sampling = "NONE"                  # the area lights below do the lighting
    deck.data.materials.append(m)

    # one light per glowing line near the mechs: the lines are the rows of the piece where the glow is strong
    px = np.asarray(maps.image.pixels[:], np.float32).reshape(maps.image.size[1], maps.image.size[0], 4)
    rows = px[..., 1].mean(1)                            # row 0 is the bottom of the image: v = 0
    hot = rows > 0.5 * rows.max()
    edges = np.flatnonzero(np.diff(np.concatenate([[0], hot.astype(int), [0]])))
    lines = [(lo + hi) / 2 / len(rows) for lo, hi in zip(edges[::2], edges[1::2])]     # v of each line in the piece
    # from 18 lengths of the piece behind y = 0, or behind the rearmost mech of banner 09, to 8 in front. The row of lamps
    # slides 2 lengths per loop: its two ends must lie so far from every mech that the mech's light does not change with them
    rear = min([0.0] + [loc[1] for _, loc, _ in F.REAR[:F.REAR_COUNT]])
    ys = sorted(length * (2 * k + s) for k in range(math.floor(rear / (2 * length)) - 9, 4) for v in lines for s in (v, 2 - v))
    for k, y in enumerate(ys):
        lamp = bpy.data.lights.new("glow", "AREA")
        lamp.shape, lamp.size, lamp.size_y = "RECTANGLE", wide, 0.5
        lamp.energy, lamp.color = GLOW_WATTS, GLOW_COLOUR
        o = bpy.data.objects.new(f"glow_{k}", lamp)
        o.location, o.rotation_euler, o.parent = (0, y, 0.05), (math.pi, 0, 0), sc.ground
        o.visible_camera = False
        bpy.context.collection.objects.link(o)
    print(f"GROUND piece {wide:.1f} x {length} m, glow lines at v = {[round(v, 3) for v in lines]}, {len(ys)} lights")


def rays(xs, ys, w, h):
    """For the pixels in columns xs and rows ys of a plate of w x h pixels:
    the world direction of each pixel's camera ray, scaled so that its
    length along the view axis is 1."""
    cam = bpy.context.scene.camera
    th = cam.data.sensor_width / (2 * cam.data.lens)
    u, v = (xs + 0.5) / w, (ys + 0.5) / h
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
    D = rays(np.arange(W), np.arange(H), W, H)
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

    def spot(x, y, body):
        """The world point on the camera ray of plate pixel (x, y) at the
        depth the plate has at pixel `body`, and the metres that one plate
        pixel spans there."""
        z = float(Z[body[1], body[0]])
        cam = bpy.context.scene.camera.data
        return C + rays(np.array([x]), np.array([y]), W, H)[0, 0] * z, z * cam.sensor_width / cam.lens / W

    sc.spot = spot
    r1 = int(d["rows"][1])
    ys, xs = np.arange(-MARGIN, r1, step), np.arange(-MARGIN, W + MARGIN, step)
    at = np.ix_(np.clip(ys, 0, H - 1), np.clip(xs, 0, W - 1))          # beyond the plate: its edge pixel
    Pm, fl = C + rays(xs, ys, W, H) * Z[at][..., None], floor[at]
    Pm[..., 2] = np.where(sky[at], Pm[..., 2], np.maximum(Pm[..., 2], 0.0))    # nothing solid lies under the ground
    h, w = fl.shape
    idx = np.arange(h * w).reshape(h, w)
    a, b, c, e = idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]
    keep = ~(fl[:-1, :-1] & fl[:-1, 1:] & fl[1:, 1:] & fl[1:, :-1])
    quads = np.stack([a, e, c, b], -1)[keep]
    uv = np.stack([(xs + 0.5) / W * np.ones((h, 1)), 1 - (ys[:, None] + 0.5) / H * np.ones((1, w))], -1).reshape(-1, 2)
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


def mist(colour):
    """The ground fog of banner 03 (src/gen04_banner_models.py) in the plate's
    horizon colour: dense at the floor and gone by head height, from
    MIST_FRONT on, broken into patches by noise stretched along the ground.
    Absorption plus emission, as `fog`. The box is banner 03's, and reaches
    below the floor."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -160, 8))
    box = bpy.context.object
    box.name = "mist"
    box.scale = (600, 240, 20)
    m = bpy.data.materials.new("mist")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    pos = N.new("ShaderNodeNewGeometry").outputs["Position"]
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(pos, sep.inputs[0])

    def calc(kind, a, b):
        n = N.new("ShaderNodeMath")
        n.operation = kind
        for i, v in enumerate((a, b)):
            if isinstance(v, float):
                n.inputs[i].default_value = v
            else:
                L.new(v, n.inputs[i])
        return n.outputs[0]

    height = calc("EXPONENT", calc("MULTIPLY", calc("MAXIMUM", sep.outputs["Z"], 0.0), -1.0 / MIST_HEIGHT), 0.0)
    front = N.new("ShaderNodeMapRange")
    front.interpolation_type = "SMOOTHSTEP"
    front.inputs["From Min"].default_value, front.inputs["From Max"].default_value = MIST_FRONT, MIST_FULL
    L.new(sep.outputs["Y"], front.inputs["Value"])
    stretch = N.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (0.035, 0.05, 0.25)
    L.new(pos, stretch.inputs["Vector"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value, noise.inputs["Detail"].default_value = 1.0, 3.0
    L.new(stretch.outputs[0], noise.inputs["Vector"])
    wisps = N.new("ShaderNodeMapRange")
    for k, v in (("From Min", 0.3), ("From Max", 0.7), ("To Min", 0.1), ("To Max", 1.9)):
        wisps.inputs[k].default_value = v
    L.new(noise.outputs["Fac"], wisps.inputs["Value"])
    density = calc("MULTIPLY", calc("MULTIPLY", calc("MULTIPLY", height, front.outputs["Result"]), wisps.outputs["Result"]), MIST_DENSITY)
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
    for name, energy, colour, angle, rot in (("sun", 5.0, (1.0, 0.86, 0.66), 6, (68, 0, 50)),
                                              ("sky", 2.2, (0.70, 0.78, 0.92), 40, (52, 0, 200))):
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
    mist(haze)
    effects.embers(sc)
    effects.chimneys(sc, plate)
    lights(haze)
    F.render_setup()
    return sc


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    opt = dict(a.split("=", 1) for a in argv if "=" in a)
    livery = __import__(opt["livery"]).paint if "livery" in opt else None
    F.HIP_ROCK = float(opt.get("hips", F.HIP_ROCK))
    F.REAR_COUNT = int(opt.get("rear", F.REAR_COUNT))
    F.MARAUDER = int(opt["marauder"]) if "marauder" in opt else None
    F.CLOTH = "cloth" in opt
    if "solo" in opt:
        F.PLACEMENT, F.GAIT_OFFSET = [(opt["solo"], (-3.0, -7.0, 0.0))], {opt["solo"]: 0}
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
