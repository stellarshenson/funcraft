"""Animated banner loops built on generated scene plates (src/genplates.py).

The clean plate (src/cleanplate.py) becomes a MoGe-2 depth mesh
(src/backdrop.py) seen by a camera that drifts a few centimetres on a
closed path. In front of it stand the actors (src/actors.py, src/rig.py):
every element of the motion map as its own mesh moved by bones. Candle
flames lean with the room's draft and change their light (src/air.py);
smoke rises from them, simulated as a gas (src/smoke.py) and placed at the
wick it comes from; molten streams flow (src/motion.py); status lights
blink; dust motes float near the lens; a scene may hold a floating
servo-skull, a painted 3D model with lights of its own (src/servoskull.py),
and a draped cloth as an object of its own with its embroidery as a texture
(src/goldwork.py).
80 frames (4 s at 50 ms), an exact loop. LOOP_FRAMES and LOOP_WIDTH in the environment give another frame count for
the same 4 s and another width (LOOP_FRAMES=120 LOOP_WIDTH=2432: 30 frames per second at the plate's own size); the
same LOOP_FRAMES must be set for the smoke sources and for src/smoke.py, which make one record per frame.

    blender -b -P src/scenes.py -- choir sources     # wip/scene3d/choir_sources.json for src/smoke.py
    blender -b -P src/scenes.py -- choir preview     # one still, wip/preview/scene-choir.png
    blender -b -P src/scenes.py -- choir             # wip/frames-choir/f000..f079 + seam-check
    blender -b -P src/scenes.py -- choir 0 20 40     # those frames only
"""
import bpy, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import backdrop as B
import rig

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES, SAMPLES = int(os.environ.get("LOOP_FRAMES", 80)), 64
TICK = FRAMES // 5                         # a status light holds its state that many frames: 0.8 s
RES = (int(os.environ.get("LOOP_WIDTH", 1520)), int(os.environ.get("LOOP_WIDTH", 1520)) * 6 // 19)
CLOCKS, MOVERS, PLATES = [], [], []

# halo: (u, v, radius) of a gold halo a glint sweeps round once per loop
# skull: a floating servo-skull. px, depth: where it is (plate pixel, metres); height in metres; yaw: its face
#        turned so many degrees to the camera's right; key, rim: its warm light and the cold light behind it,
#        each (plate pixel, depth, colour, watts); ambient: the weak light from all round
# titan: the Warhound in a hall behind an opening in the wall (src/titanhall.py)
SCENES = {"saint": dict(halo=(0.30, 0.25, 0.10),
                        titan=dict(opening=(1660, 1946), behind=10.4, depth=56.0, feet=-9.0, yaw=0.0, haze=0.008,
                                   piers=((-14, 25), (12, 30)), windows=0.6,
                                   key=((-14, -14, 20), (1.0, 0.62, 0.32), 8.0e4, 40),
                                   rim=((10, 24, 22), (0.5, 0.65, 1.0), 5.0e4, 35))),
          "forge": dict(skull=dict(px=(790, 235), depth=3.3, height=0.36, yaw=22,
                                   key=((965, 345), 3.05, (1.0, 0.6, 0.28), 7.0),      # the lantern
                                   rim=((700, 110), 4.3, (0.4, 0.58, 1.0), 25.0),      # the night window
                                   ambient=(0.012, 0.017, 0.026)))}


def pixels(img):
    """The image as a (rows, cols, 4) array, top row first."""
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)[::-1]


def to_image(name, a):
    """A float image from a (rows, cols) or (rows, cols, 3) array, top row first."""
    h, w = a.shape[:2]
    img = bpy.data.images.new(name, w, h, float_buffer=True, is_data=True)
    rgba = np.concatenate([a[::-1].reshape(h, w, -1)] * (3 if a.ndim == 2 else 1) + [np.ones((h, w, 1))], 2).astype(np.float32)
    rgba[..., 3] = 1
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    return img


def blur(a, r):
    """Box blur of radius r, twice (close to a Gaussian)."""
    for _ in range(2):
        for ax in (0, 1):
            c = np.cumsum(np.pad(a, [(r + 1, r) if k == ax else (0, 0) for k in range(a.ndim)], mode="edge"), ax)
            a = (np.take(c, range(2 * r + 1, c.shape[ax]), ax) - np.take(c, range(0, c.shape[ax] - 2 * r - 1), ax)) / (2 * r + 1)
    return a


class Nodes:
    """Terse node building in one node tree."""
    def __init__(self, nt):
        self.N, self.L = nt.nodes, nt.links

    def new(self, kind, **kw):
        n = self.N.new(kind)
        for k, v in kw.items():
            setattr(n, k, v)
        return n

    def op(self, operation, a, b=None, c=None):
        n = self.new("ShaderNodeMath", operation=operation)
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                self.L.new(x, n.inputs[i])
        return n.outputs[0]

    def clock(self, kind):
        n = self.new("ShaderNodeValue")
        CLOCKS.append((kind, n))
        return n.outputs[0]

    def loop_noise(self, vec, scale, radius=2.0, detail=2.0):
        """Noise that changes smoothly through the loop and returns to its
        start: the fourth dimension and the vector's z go round a circle."""
        ph = self.op("MULTIPLY", self.clock("phase"), 2 * math.pi)
        cz = self.new("ShaderNodeCombineXYZ")
        self.L.new(self.op("MULTIPLY", self.op("COSINE", ph), radius), cz.inputs[2])
        add = self.new("ShaderNodeVectorMath", operation="ADD")
        self.L.new(vec, add.inputs[0])
        self.L.new(cz.outputs[0], add.inputs[1])
        n = self.new("ShaderNodeTexNoise", noise_dimensions="4D")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        self.L.new(add.outputs[0], n.inputs["Vector"])
        self.L.new(self.op("MULTIPLY", self.op("SINE", ph), radius), n.inputs["W"])
        return n.outputs["Fac"]


def plate_masks(img, conf):
    """Status lights (small bright green spots), the halo (bright gold
    pixels near the halo centre) and the plate's light spread wide."""
    p = pixels(img)[..., :3]
    r, g, b = p[..., 0], p[..., 1], p[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    led = ((g > 0.45) & (g > r + 0.2) & (g > b + 0.1)).astype(np.float32)
    big = (blur(led, 6) >= 0.25).astype(np.float32)   # more than 42 green pixels in a 13 px square: no status light
    led = led * (blur(big, 8) < 1e-3)            # small lights only: a screen, a beam, a pair of glowing eyes stays whole
    led = np.clip(blur(led, 1) * 2, 0, 1)
    glow = blur(p ** 2.2, 40)                    # what lights the smoke from behind
    halo = None
    if "halo" in conf:
        cu, cv, rad = conf["halo"]
        h, w = lum.shape
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.hypot(xx / w - cu, (yy / h - cv) * h / w)
        halo = ((lum > 0.5) & (r > b + 0.15) & (d < rad)).astype(np.float32)
        halo = np.clip(blur(halo, 2) * 1.5, 0, 1)
    return led, halo, glow


def plate_material(m, conf, group):
    """A plate material's emission, multiplied by a gain: the candle light
    (`group`, src/rig.py); status lights and screen cells switch off at
    random once per tick; a glint sweeps round the halo once per loop."""
    X = Nodes(m.node_tree)
    tex = next(n for n in X.N if n.type == "TEX_IMAGE")
    em = next(n for n in X.N if n.type == "EMISSION")
    img = tex.image
    led, halo, glow = plate_masks(img, conf)
    uv = X.new("ShaderNodeTexCoord").outputs["UV"]

    def sample(name, a):
        t = X.new("ShaderNodeTexImage", image=to_image(name, a), interpolation="Linear")
        X.L.new(uv, t.inputs["Vector"])
        return t.outputs["Color"]

    aspect = img.size[0] / img.size[1]
    gain = X.new("ShaderNodeGroup", node_tree=group).outputs["Gain"]
    if led.max() > 0:                             # status lights: a 6-pixel grid of cells, each on or off per tick
        cells = X.new("ShaderNodeVectorMath", operation="MULTIPLY")
        X.L.new(uv, cells.inputs[0])
        cells.inputs[1].default_value = (img.size[0] / 6, img.size[1] / 6, 0.0)
        fl = X.new("ShaderNodeVectorMath", operation="FLOOR")
        X.L.new(cells.outputs[0], fl.inputs[0])
        wn = X.new("ShaderNodeTexWhiteNoise", noise_dimensions="4D")
        X.L.new(fl.outputs[0], wn.inputs["Vector"])
        X.L.new(X.clock("tick"), wn.inputs["W"])
        off = X.op("GREATER_THAN", wn.outputs["Value"], 0.6)
        gain = X.op("SUBTRACT", gain, X.op("MULTIPLY", sample("led", led), X.op("MULTIPLY", off, 0.75)))
    if halo is not None and halo.max() > 0:
        cu, cv, _ = conf["halo"]
        sep = X.new("ShaderNodeSeparateXYZ")
        X.L.new(uv, sep.inputs[0])
        ang = X.op("ARCTAN2", X.op("SUBTRACT", sep.outputs["Y"], 1 - cv),
                   X.op("MULTIPLY", X.op("SUBTRACT", sep.outputs["X"], cu), aspect))
        sweep = X.op("POWER", X.op("MAXIMUM", X.op("COSINE", X.op("SUBTRACT", ang,
                     X.op("MULTIPLY", X.clock("phase"), 2 * math.pi))), 0.0), 10.0)
        gain = X.op("ADD", gain, X.op("MULTIPLY", sample("halo", halo), X.op("MULTIPLY", sweep, 1.2)))
    mix = X.new("ShaderNodeVectorMath", operation="SCALE")
    X.L.new(tex.outputs["Color"], mix.inputs[0])
    X.L.new(gain, mix.inputs["Scale"])
    X.L.new(mix.outputs[0], em.inputs["Color"])
    return glow


def plumes(name, group, glow):
    """The simulated smoke of every source (wip/sim/<name>/<source>.npz) as
    a volume at the place it was simulated for. Each loop frame becomes an
    OpenVDB file once. The smoke shows the light it stands in: the plate's
    light behind it, and the candle flames near it."""
    import openvdb as vdb
    sim = os.path.join(ROOT, "wip", "sim", name)
    for f in sorted(os.listdir(sim)) if os.path.isdir(sim) else []:
        if not f.endswith(".npz"):
            continue
        sid = f[:-4]
        d = np.load(os.path.join(sim, f))
        seq = os.path.join(sim, sid)
        first = os.path.join(seq, "s_0001.vdb")
        if not os.path.exists(first) or os.path.getmtime(first) < os.path.getmtime(os.path.join(sim, f)):
            os.makedirs(seq, exist_ok=True)
            dens = d["density"].astype(np.float32)
            for k in range(FRAMES):
                g = vdb.FloatGrid()
                g.copyFromArray(dens[k], tolerance=2e-3)
                g.name = "density"
                g.transform = vdb.createLinearTransform(voxelSize=float(d["cell"]))
                vdb.write(os.path.join(seq, f"s_{k + 1:04d}.vdb"), grids=[g])
        vol = bpy.data.volumes.new("smoke_" + sid)
        vol.filepath = first
        vol.is_sequence, vol.frame_duration, vol.frame_start, vol.sequence_mode = True, FRAMES, 1, "REPEAT"
        ob = bpy.data.objects.new("smoke_" + sid, vol)
        ob.location = d["origin"].tolist()
        bpy.context.collection.objects.link(ob)
        m = bpy.data.materials.new("smoke_" + sid)
        m.use_nodes = True
        X = Nodes(m.node_tree)
        for n in list(X.N):
            if n.type != "OUTPUT_MATERIAL":
                X.N.remove(n)
        dens = X.new("ShaderNodeVolumeInfo").outputs["Density"]
        t = X.new("ShaderNodeTexImage", image=glow, interpolation="Linear", extension="EXTEND")
        X.L.new(X.new("ShaderNodeTexCoord").outputs["Window"], t.inputs["Vector"])
        back = X.new("ShaderNodeVectorMath", operation="MULTIPLY_ADD")      # the plate's light behind, and a floor
        X.L.new(t.outputs["Color"], back.inputs[0])
        back.inputs[1].default_value = (1.6, 1.65, 1.8)
        back.inputs[2].default_value = (0.10, 0.105, 0.115)
        near = X.new("ShaderNodeVectorMath", operation="SCALE")            # the flames near it
        near.inputs[0].default_value = (0.5, 0.36, 0.22)             # half the backlight's weight: no white clumps over a flame
        X.L.new(X.new("ShaderNodeGroup", node_tree=group).outputs["Glow"], near.inputs["Scale"])
        lit = X.new("ShaderNodeVectorMath", operation="ADD")
        X.L.new(back.outputs[0], lit.inputs[0])
        X.L.new(near.outputs[0], lit.inputs[1])
        em = X.new("ShaderNodeEmission")
        X.L.new(lit.outputs[0], em.inputs["Color"])
        X.L.new(X.op("MULTIPLY", dens, 250.0), em.inputs["Strength"])
        ab = X.new("ShaderNodeVolumeAbsorption")
        X.L.new(X.op("MULTIPLY", dens, 30.0), ab.inputs["Density"])
        add = X.new("ShaderNodeAddShader")
        X.L.new(em.outputs[0], add.inputs[0])
        X.L.new(ab.outputs[0], add.inputs[1])
        X.L.new(add.outputs[0], X.N["Material Output"].inputs["Volume"])
        vol.materials.append(m)
        print("SMOKE", sid, d["density"].shape, flush=True)


def motes(near, count=36, seed=3):
    """Dust near the lens, each on its own slow closed path."""
    rng = np.random.default_rng(seed)
    m = bpy.data.materials.new("mote")
    m.use_nodes = True
    X = Nodes(m.node_tree)
    b = X.N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.9, 0.75, 0.5, 1)
    b.inputs["Emission Color"].default_value = (1.0, 0.8, 0.55, 1)
    b.inputs["Emission Strength"].default_value = 0.6
    for k in range(count):
        y = near * rng.uniform(0.25, 0.8)
        x, z = rng.uniform(-1.3, 1.3) * y * 0.6, rng.uniform(-0.5, 0.5) * y * 0.4
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0015 * y, segments=8, ring_count=4, location=(x, y, z))
        ob = bpy.context.object
        ob.data.materials.append(m)
        ob.visible_shadow = False
        a, o = rng.uniform(0.02, 0.05) * y, rng.random()
        MOVERS.append(lambda ph, ob=ob, x=x, y=y, z=z, a=a, o=o: setattr(ob, "location", (
            x + a * math.sin(2 * math.pi * (ph + o)), y, z + a * 0.6 * math.sin(4 * math.pi * (ph + o)))))


def drape(stem, back, group):
    """The cloths with gold of the plate, where src/goldwork.py has written them (<stem>_drape.npz). A cloth that is
    an object of its own is the mesh of its measured surface, cut out of the backdrop; a cloth that is an element of
    the motion map keeps its mesh and its bones. Each has the plate as its first UV map, whose picture of the velvet
    it emits, and the cloth laid flat as its second, through which lies the texture of its gold (red: where it lies,
    green: the shading of its strokes, blue: its shadow on the velvet). The gold emits a tone chosen by the velvet's
    light at its pixel of the plate and the shading of the stroke, under the same candle light: it bends, shortens
    and moves with the cloth because the cloth carries it, and darkens where the velvet does."""
    if not os.path.exists(stem + "_drape.npz"):
        return
    import bmesh
    d = np.load(stem + "_drape.npz")
    light = to_image("velvet_light", d["light"].astype(np.float32))
    lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    for i in range(int(d["n"])):
        if f"{i}/V" in d.files:
            bm = bmesh.new()
            bm.from_mesh(back.data)
            under = d[f"{i}/cut"][::2, ::2].ravel()     # the backdrop has a vertex for every second pixel
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if all(under[v.index] for v in f.verts)], context="FACES_ONLY")
            bm.to_mesh(back.data)
            bm.free()
            m = rig.material(f"drape_{i}", stem + "_clean.png")
            ob = rig.mesh(f"drape_{i}", d[f"{i}/V"], d[f"{i}/uv"], d[f"{i}/quads"], m)
        else:
            ob = bpy.data.objects["cloth_" + str(d[f"{i}/actor"])]
            m = ob.data.materials[0].copy()
            ob.data.materials[0] = m
        me = ob.data
        vi = np.empty(len(me.loops), np.int32)
        me.loops.foreach_get("vertex_index", vi)
        me.uv_layers.new(name="chart").data.foreach_set("uv", d[f"{i}/chart"][vi].ravel())
        X = Nodes(m.node_tree)
        velvet = next(n for n in X.N if n.type == "EMISSION")
        work = X.new("ShaderNodeTexImage", image=to_image(f"gold_{i}", d[f"{i}/work"].astype(np.float32)), interpolation="Cubic", extension="CLIP")
        X.L.new(X.new("ShaderNodeUVMap", uv_map="chart").outputs["UV"], work.inputs["Vector"])
        part = X.new("ShaderNodeSeparateColor")
        X.L.new(work.outputs["Color"], part.inputs["Color"])
        X.L.new(X.op("SUBTRACT", 1.0, part.outputs["Blue"]), velvet.inputs["Strength"])
        lit = X.new("ShaderNodeTexImage", image=light, interpolation="Linear", extension="EXTEND")
        X.L.new(X.new("ShaderNodeUVMap", uv_map="uv").outputs["UV"], lit.inputs["Vector"])
        # the gold: the velvet's light, times the shading of the stroke, through the plate's three tones of gold
        level = X.op("MULTIPLY", lit.outputs["Color"], X.op("ADD", 1.0, part.outputs["Green"]))
        ramp = X.new("ShaderNodeValToRGB")
        X.L.new(X.op("MULTIPLY", level, 0.5 / 1.2), ramp.inputs["Fac"])
        dark, mid, bright = (lin(c / 255) for c in d[f"{i}/tones"])
        stops = [(0.0, np.zeros(3)), (0.25 / 1.2, dark), (0.5 / 1.2, mid), (0.9 / 1.2, bright), (1.0, np.minimum(1.0, 1.2 * bright))]
        el = ramp.color_ramp.elements
        while len(el) < len(stops):
            el.new(0.5)
        for e, (at, c) in zip(el, stops):
            e.position, e.color = at, (*c.tolist(), 1.0)
        gold = X.new("ShaderNodeEmission")
        glow = X.new("ShaderNodeVectorMath", operation="SCALE")
        X.L.new(ramp.outputs["Color"], glow.inputs[0])
        X.L.new(X.new("ShaderNodeGroup", node_tree=group).outputs["Gain"], glow.inputs["Scale"])
        X.L.new(glow.outputs[0], gold.inputs["Color"])
        mix = X.new("ShaderNodeMixShader")
        for k, sock in enumerate((part.outputs["Red"], velvet.outputs[0], gold.outputs[0])):
            X.L.new(sock, mix.inputs[k])
        X.L.new(mix.outputs[0], X.N["Material Output"].inputs["Surface"])
        print("DRAPE", ob.name, len(me.vertices), "vertices, texture", d[f"{i}/work"].shape[1::-1], flush=True)


def build(name):
    conf = SCENES.get(name, {})
    bpy.ops.wm.read_factory_settings(use_empty=True)
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    d = np.load(stem + ".npz")
    ob, fov = B.backdrop(stem + "_clean")
    group = rig.build(name, MOVERS, stem + ".png")
    drape(stem, ob, group)
    plate = ob.material_slots[0].material
    glow = to_image("glow", plate_material(plate, conf, group))
    for m in bpy.data.materials:                     # the actors and the fill behind the plate's edges
        if m is not plate and m.node_tree and any(n.type == "TEX_IMAGE" for n in m.node_tree.nodes):
            plate_material(m, conf, group)
    if os.path.isdir(stem + "_flow"):                # streams: one clean plate per loop frame
        PLATES.append((next(n.image for n in plate.node_tree.nodes if n.type == "TEX_IMAGE" and n.image.filepath), stem + "_flow"))
    plumes(name, group, glow)
    z = d["depth"][d["mask"]]
    near = float(np.percentile(z, 1))
    motes(near)
    cam = B.camera(fov, RES)
    K = d["intrinsics"]
    cam.data.shift_x, cam.data.shift_y = 0.5 - float(K[0, 2]), (float(K[1, 2]) - 0.5) * RES[1] / RES[0]
    amp = 0.008 * near                               # a few centimetres: parallax without tearing
    MOVERS.append(lambda ph: setattr(cam, "location", (amp * math.sin(2 * math.pi * ph),
                                                       amp * 0.6 * (1 - math.cos(2 * math.pi * ph)),
                                                       amp * 0.3 * math.sin(4 * math.pi * ph))))
    s = bpy.context.scene
    s.world = bpy.data.worlds.new("world")
    s.world.color = (0, 0, 0)
    if "skull" in conf:
        import servoskull
        W, H = d["depth"].shape[1], d["depth"].shape[0]
        at = lambda px, z: (((px[0] + 0.5) / W - K[0, 2]) / K[0, 0] * z, z, -((px[1] + 0.5) / H - K[1, 2]) / K[1, 1] * z)
        sk = conf["skull"]
        servoskull.build(at(sk["px"], sk["depth"]), sk["height"], sk["yaw"], MOVERS,
                         *[(at(px, z), colour, watts) for px, z, colour, watts in (sk["key"], sk["rim"])])
        s.world.color = sk["ambient"]
    if "titan" in conf:
        import titanhall
        titanhall.build(conf["titan"], d["depth"], K, ob, bpy.data.objects["backdrop_fill"])
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = SAMPLES
    s.cycles.use_denoising = False
    s.cycles.volume_step_rate = 1.0
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for dv in pr.devices:
        dv.use = dv.type == "CUDA"
    s.view_settings.view_transform = "Standard"    # the plate is already graded
    s.render.image_settings.file_format = "PNG"


def pose(i):
    phase = i / FRAMES
    tick = float((i % FRAMES) // TICK)
    bpy.context.scene.frame_set(i % FRAMES + 1)      # the smoke's frame
    for kind, node in CLOCKS:
        node.outputs[0].default_value = phase if kind == "phase" else tick
    for mv in MOVERS:
        mv(phase)
    for img, seq in PLATES:
        img.filepath = os.path.join(seq, f"p{i % FRAMES + 1:04d}.png")
        img.reload()
    bpy.context.view_layer.update()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:]
    name = argv[0]
    build(name)
    if "sources" in argv:                            # rig.build has written the smoke sources
        return
    s = bpy.context.scene
    if "preview" in argv:
        s.cycles.samples = 24
        pose(0)
        s.render.filepath = os.path.join(ROOT, "wip", "preview", f"scene-{name}.png")
        bpy.ops.render.render(write_still=True)
        return
    outdir = os.path.join(ROOT, "wip", f"frames-{name}")
    os.makedirs(outdir, exist_ok=True)
    for i in ([int(a) for a in argv[1:] if a.isdigit()] or range(FRAMES + 1)):
        pose(i)
        s.render.filepath = os.path.join(outdir, f"f{i:03d}.png" if i < FRAMES else "seam-check.png")
        bpy.ops.render.render(write_still=True)
        print(f"FRAME {i + 1}/{FRAMES}", flush=True)
    print("RENDER_DONE", outdir)


main()
