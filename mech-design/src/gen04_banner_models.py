"""19:6 banner: the three supplied chassis walking at the viewer. Blender 4.5.

Run:
    blender -b -P src/gen04_banner_models.py [-- shake] [-- offset] [-- out=DIR] [-- N ...]

    shake    the camera jolts at every footfall
    offset   each chassis walks at its own point in the gait cycle, instead of
             all three in step
    out=DIR  frame directory under wip/, default `frames`
    N        render only these frame numbers

Writes numbered frames and leaves the GIF assembly to src/assemble.py, so a
failed render can be resumed without redoing the rest.

The loop is exact by construction. Every pose is a function of `phase` in
[0,1), and the ground markers are spaced exactly one loop-step apart, so
translating them by one step over the cycle reproduces frame 0 exactly.

Each chassis is painted on its mesh (src/paint.py) and walked by an armature
(src/rig.py). A planted foot slides back at exactly STEP per cycle, the speed
of the floor, so it stays locked to the floor. All three walk straight at the
camera: the floor can slide in only one direction, and a mech turned away
from it would skid sideways.
"""

import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
import paint as P
import rig as G
import logo as L
from mathutils import Euler, Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = 30
RES_X, RES_Y = 1520, 480          # 19:6
SAMPLES = 64

STEP = 5.0                        # ground travel per gait cycle, = marker spacing
FRAME_S = 0.050                   # seconds per frame, as src/assemble.py shows it

# gait-cycle offsets for `offset`, in whole frames, so every footfall lands
# exactly on a frame; footfalls then fall at frames 0, 4, 9, 15, 19 and 24
OFFSET_FRAMES = {"madcat": 0, "atlas": 11, "battlemaster": 21}

# camera jolt per footfall: a cosine that starts at full swing on the landing
# frame and dies away, so the view drops, rebounds once or twice and settles
# long before the next step
SHAKE_DEG = 0.10
SHAKE_TAU = 0.10                  # seconds for the swing to fall to 1/e
SHAKE_HZ = 7.0

# chassis, world position, heading (0 = walking straight at the camera)
PLACEMENT = [
    ("battlemaster", (-19.0, -31.0, 0.0), 0.0),
    ("madcat",       ( -3.0,  -7.0, 0.0), 0.0),
    ("atlas",        ( 15.0, -19.0, 0.0), 0.0),
]


def aim(obj, target):
    """Point a light at a world-space target."""
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def pbr(name, base, rough, metal):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def facade(base):
    """Wall cladding for the background blocks: staggered plates with recessed
    seams, a tone per plate, and vertical grime streaks. The pattern is laid out
    on world (x + y, z), so front and side walls get plates of the same size
    however each block is scaled."""
    m = pbr("facade", base, 0.85, 0.0)
    N, L = m.node_tree.nodes, m.node_tree.links
    bsdf = N["Principled BSDF"]
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(N.new("ShaderNodeNewGeometry").outputs["Position"], sep.inputs[0])
    u = N.new("ShaderNodeMath")
    u.operation = "ADD"
    L.new(sep.outputs["X"], u.inputs[0])
    L.new(sep.outputs["Y"], u.inputs[1])
    wall = N.new("ShaderNodeCombineXYZ")
    L.new(u.outputs[0], wall.inputs["X"])
    L.new(sep.outputs["Z"], wall.inputs["Y"])

    plates = N.new("ShaderNodeTexBrick")
    L.new(wall.outputs[0], plates.inputs["Vector"])
    for k, v in (("Scale", 1.0), ("Brick Width", 4.0), ("Row Height", 2.2),
                 ("Mortar Size", 0.10), ("Mortar Smooth", 0.2), ("Bias", 0.0)):
        plates.inputs[k].default_value = v
    plates.inputs["Color1"].default_value = (*(c * 0.70 for c in base), 1)
    plates.inputs["Color2"].default_value = (*(c * 1.35 for c in base), 1)
    plates.inputs["Mortar"].default_value = (*(c * 0.25 for c in base), 1)

    # streaks: noise that changes fast across the wall and slowly down it
    stretch = N.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (1.3, 0.07, 1.0)
    L.new(wall.outputs[0], stretch.inputs["Vector"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 3.0
    L.new(stretch.outputs[0], noise.inputs["Vector"])
    grime = N.new("ShaderNodeMapRange")
    grime.inputs["From Min"].default_value = 0.35
    grime.inputs["From Max"].default_value = 0.65
    grime.inputs["To Min"].default_value = 0.55
    grime.inputs["To Max"].default_value = 1.0
    L.new(noise.outputs["Fac"], grime.inputs["Value"])
    dirty = N.new("ShaderNodeVectorMath")
    dirty.operation = "SCALE"
    L.new(plates.outputs["Color"], dirty.inputs[0])
    L.new(grime.outputs["Result"], dirty.inputs["Scale"])
    L.new(dirty.outputs["Vector"], bsdf.inputs["Base Color"])

    bump = N.new("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.5
    L.new(plates.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return m


def emissive(name, colour, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs[0].default_value = (*colour, 1)
    e.inputs[1].default_value = strength
    nt.links.new(e.outputs[0], nt.nodes["Material Output"].inputs[0])
    return m


def build_scene():
    R.clear_scene()

    mechs = []
    for name, loc, yaw in PLACEMENT:
        mesh = R.load(name)
        mesh.name = name
        P.paint(mesh, name)
        # print models are faceted flat; smoothing by angle rounds the domes,
        # actuators and barrels while leaving the hard armour creases sharp
        bpy.ops.object.select_all(action="DESELECT")
        bpy.context.view_layer.objects.active = mesh
        mesh.select_set(True)
        bpy.ops.object.shade_smooth_by_angle(angle=math.radians(31))
        rig = G.build(mesh, name)
        rig.location = loc
        rig.rotation_euler = Euler((0, 0, yaw), "XYZ")
        mechs.append((name, rig))

    # ---- ground ------------------------------------------------------------
    bpy.ops.mesh.primitive_plane_add(size=1200, location=(0, 0, 0))
    ground = bpy.context.object
    ground.name = "ground"
    ground.data.materials.append(pbr("deck", (0.011, 0.013, 0.018), 0.50, 0.25))

    # distant structures, for depth behind the approach
    import random
    rng = random.Random(5)
    blocks = []
    far = facade((0.020, 0.024, 0.033))
    for _ in range(46):
        bx = rng.uniform(-240, 240)
        by = rng.uniform(-260, -95)
        bh = rng.uniform(14, 62)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(bx, by, bh / 2))
        b = bpy.context.object
        b.scale = (rng.uniform(10, 30), rng.uniform(10, 26), bh)
        b.data.materials.append(far)
        blocks.append(b)

    # the logo, on the wall the camera sees on the left of the frame: the first
    # block, whose wall spans x 44.6..73.4 at y = -126.7. It is centred on the
    # wall, left of the Atlas and level with its head
    b = blocks[0]
    L.sign(os.path.join(ROOT, "resources", "assets", "stellars_tech_ai_lab_gh_behemoth_logo.svg"),
           (b.location.x, b.location.y + b.scale.y / 2, 17.2), 22.0)

    # haze, so distance reads
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -90, 34))
    vol = bpy.context.object
    vol.name = "haze"
    vol.scale = (620, 420, 76)
    vm = bpy.data.materials.new("haze")
    vm.use_nodes = True
    nt = vm.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    sc = nt.nodes.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (0.26, 0.36, 0.55, 1)
    sc.inputs["Density"].default_value = 0.00022
    nt.links.new(sc.outputs[0], nt.nodes["Material Output"].inputs["Volume"])
    vol.data.materials.append(vm)

    # ground fog among the buildings: dense at the floor and gone by head
    # height, starting behind the rearmost mech so none drifts in front of them.
    # It does not move, so the loop stays exact. The box reaches below the
    # floor: with its bottom face on the floor, Cycles decided per frame whether
    # a floor hit was inside the fog, and the distant floor flickered
    FOG_FRONT, FOG_FULL, FOG_HEIGHT = -42.0, -75.0, 2.8
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -160, 8))
    fog = bpy.context.object
    fog.name = "ground_fog"
    fog.scale = (600, 240, 20)
    fm = bpy.data.materials.new("ground_fog")
    fm.use_nodes = True
    N, Lk = fm.node_tree.nodes, fm.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    pos = N.new("ShaderNodeNewGeometry").outputs["Position"]
    sep = N.new("ShaderNodeSeparateXYZ")
    Lk.new(pos, sep.inputs[0])

    def calc(kind, a, b):
        m = N.new("ShaderNodeMath")
        m.operation = kind
        for i, v in enumerate((a, b)):
            if isinstance(v, float):
                m.inputs[i].default_value = v
            else:
                Lk.new(v, m.inputs[i])
        return m.outputs[0]

    height = calc("EXPONENT", calc("MULTIPLY", sep.outputs["Z"], -1.0 / FOG_HEIGHT), 0.0)
    front = N.new("ShaderNodeMapRange")
    front.interpolation_type = "SMOOTHSTEP"
    front.inputs["From Min"].default_value = FOG_FRONT
    front.inputs["From Max"].default_value = FOG_FULL
    Lk.new(sep.outputs["Y"], front.inputs["Value"])
    # wisps: noise stretched along the ground
    stretch = N.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (0.035, 0.05, 0.25)
    Lk.new(pos, stretch.inputs["Vector"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 3.0
    Lk.new(stretch.outputs[0], noise.inputs["Vector"])
    wisps = N.new("ShaderNodeMapRange")
    wisps.inputs["From Min"].default_value = 0.3
    wisps.inputs["From Max"].default_value = 0.7
    wisps.inputs["To Min"].default_value = 0.1
    wisps.inputs["To Max"].default_value = 1.9
    Lk.new(noise.outputs["Fac"], wisps.inputs["Value"])
    density = calc("MULTIPLY", calc("MULTIPLY", height, front.outputs["Result"]), wisps.outputs["Result"])
    fsc = N.new("ShaderNodeVolumeScatter")
    fsc.inputs["Color"].default_value = (0.55, 0.65, 0.82, 1)
    fsc.inputs["Anisotropy"].default_value = 0.3
    Lk.new(calc("MULTIPLY", density, 0.028), fsc.inputs["Density"])
    Lk.new(fsc.outputs[0], N["Material Output"].inputs["Volume"])
    fog.data.materials.append(fm)

    mover = bpy.data.objects.new("mover", None)
    bpy.context.collection.objects.link(mover)

    strip = pbr("strip", (0.13, 0.085, 0.030), 0.75, 0.0)
    kerb = pbr("kerb", (0.055, 0.060, 0.072), 0.70, 0.0)
    # the row must outrun the visible ground in both directions, or shifting
    # it by one spacing moves a visible end and the loop shows a seam
    for i in range(-65, 22):                     # markers every STEP along Y
        y = i * STEP
        bpy.ops.mesh.primitive_cube_add(size=1, location=(0, y, 0.02))
        o = bpy.context.object
        o.scale = (26.0, 0.55, 0.02)
        o.data.materials.append(strip)
        o.parent = mover
        for lx in (-34.0, 34.0):                 # low kerb blocks, not floating bars
            bpy.ops.mesh.primitive_cube_add(size=1, location=(lx, y, 0.45))
            k = bpy.context.object
            k.scale = (2.2, 1.6, 0.9)
            k.data.materials.append(kerb)
            k.parent = mover

    # ---- camera: low, looking up the approach ------------------------------
    cd = bpy.data.cameras.new("cam")
    cd.lens = 42
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (1.0, 58.0, 8.6)
    cam.rotation_euler = Euler((math.radians(88.2), 0, math.radians(180)), "XYZ")

    # ---- light -------------------------------------------------------------
    key = bpy.data.lights.new("key", "AREA")
    key.energy, key.size, key.color = 620000, 70, (1.0, 0.78, 0.52)
    o = bpy.data.objects.new("key", key)
    o.location = (-70, -85, 70)
    o.rotation_euler = Euler((math.radians(52), 0, math.radians(-42)), "XYZ")
    bpy.context.collection.objects.link(o)

    rim = bpy.data.lights.new("rim", "AREA")
    rim.energy, rim.size, rim.color = 560000, 55, (0.34, 0.56, 1.0)
    o = bpy.data.objects.new("rim", rim)
    o.location = (78, -60, 46)
    o.rotation_euler = Euler((math.radians(64), 0, math.radians(126)), "XYZ")
    bpy.context.collection.objects.link(o)

    # the key and rim sit behind the mechs; this front key, from above the
    # camera, is what lets the paint read on the faces the camera sees
    fk = bpy.data.lights.new("front_key", "AREA")
    fk.energy, fk.size, fk.color = 200000, 40, (1.0, 0.93, 0.84)
    o = bpy.data.objects.new("front_key", fk)
    o.location = (-25.0, 75.0, 45.0)
    bpy.context.collection.objects.link(o)
    aim(o, (0.0, -18.0, 7.0))

    # a front fill aimed at the Mad Cat, which otherwise sits in its own shadow
    mc = bpy.data.lights.new("madcat_front", "SPOT")
    mc.energy, mc.color = 2600, (0.86, 0.90, 1.0)
    mc.spot_size = math.radians(24)
    mc.spot_blend = 0.55
    mc.shadow_soft_size = 1.6
    o = bpy.data.objects.new("madcat_front", mc)
    o.location = (-7.0, 20.0, 13.5)
    bpy.context.collection.objects.link(o)
    aim(o, (-3.0, -7.0, 9.0))

    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.016, 0.021, 0.034, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0

    return mechs, mover


def configure_render():
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = SAMPLES
    s.cycles.use_denoising = True
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for d in pr.devices:
        d.use = (d.type == "CUDA")
    s.render.resolution_x, s.render.resolution_y = RES_X, RES_Y
    s.render.film_transparent = False
    s.view_settings.view_transform = "AgX"
    for look in ("AgX - Medium High Contrast", "Medium High Contrast", "None"):
        try:
            s.view_settings.look = look
            break
        except TypeError:
            continue


def shake(i, offsets):
    """Camera (pitch, yaw, roll) in radians at frame `i`, summed over footfalls.

    The left foot of a chassis lands at its gait phase 0 and the right at 0.5,
    so in frames at -offset and FRAMES/2 - offset. Time since each landing is
    counted in whole frames, modulo the loop, which makes the shake exactly
    periodic. Left and right footfalls tip the view to opposite sides.
    """
    out = [0.0, 0.0, 0.0]
    for o in offsets:
        for land, side in ((-o, 1.0), (FRAMES // 2 - o, -1.0)):
            t = ((i - land) % FRAMES) * FRAME_S
            a = (math.radians(SHAKE_DEG) * math.exp(-t / SHAKE_TAU)
                 * math.cos(2 * math.pi * SHAKE_HZ * t))
            out[0] -= a
            out[1] += 0.4 * side * a
            out[2] += 0.3 * side * a
    return out


def main():
    mechs, mover = build_scene()
    configure_render()
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    use_shake, use_offset = "shake" in argv, "offset" in argv
    sub = next((a[4:] for a in argv if a.startswith("out=")), "frames")
    outdir = os.path.join(ROOT, "wip", sub)
    os.makedirs(outdir, exist_ok=True)
    offset = {name: (OFFSET_FRAMES[name] if use_offset else 0) for name, _ in mechs}
    cam = bpy.context.scene.camera
    cam_rot = cam.rotation_euler.copy()

    for i in ([int(a) for a in argv if a.isdigit()] or range(FRAMES + 1)):
        phase = i / FRAMES          # frame FRAMES is phase 1.0, rendered to check the seam
        for name, rig in mechs:
            G.walk(rig, name, (i + offset[name]) / FRAMES, STEP)
        # The mechs face +Y and walk +Y on the spot, so the world has to slide
        # -Y past them, like a treadmill belt. Running it +Y made them moonwalk.
        mover.location = (0, -phase * STEP, 0)    # exactly one spacing per loop
        if use_shake:
            d = shake(i, offset.values())
            cam.rotation_euler = Euler((cam_rot.x + d[0], cam_rot.y + d[2], cam_rot.z + d[1]), "XYZ")
        bpy.context.view_layer.update()
        fname = f"f{i:03d}.png" if i < FRAMES else "seam-check.png"
        bpy.context.scene.render.filepath = os.path.join(outdir, fname)
        bpy.ops.render.render(write_still=True)
        print(f"FRAME {i + 1}/{FRAMES}", flush=True)
    print("RENDER_DONE", outdir)


main()
