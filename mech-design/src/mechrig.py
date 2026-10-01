"""Cut a print-model BattleMech into limb parts and walk it. Blender 4.5.

The supplied STLs are single fused shells meant for a printer: no skeleton, no
way to pose them as they stand. This slices each shell with horizontal planes
at the hip, knee and ankle, splits the legs left from right, caps the openings,
and hangs each part off an empty at the joint it turns about.

Pivots are not guessed. Each one is the centroid of the shell's cross-section
at that height, taken per leg, so the thigh turns about the actual hip mass and
not about the model origin.

Rig hierarchy, per mech:

    root            placement in the scene - location and heading
      body          vertical bob, twice per gait cycle
        torso       everything above the hip plane
        {L,R}_hip   -> thigh mesh
          _knee     -> shin mesh
            _ankle  -> foot mesh

The mech is built facing +Y and walks along +Y, so every joint turns about X.
"""

import bpy, bmesh, math, os
from mathutils import Vector, Euler

MODELS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "in", "models")

# ---------------------------------------------------------------- chassis ---
# hip/knee/ankle are fractions of the model's own height, measured from the feet
# Joint heights, leg corridors and canopy positions are all read off the
# measured sheets in wip/preview/ - grid-*.png is the side view, frontgrid-*.png the
# front. Nothing here is guessed.
#
#   hip / ankle   fractions of the model's own height, measured from the feet
#   x_in, x_out   the leg's corridor, as fractions of height. Everything inside
#                 x_in is central mass and everything beyond x_out is an arm or
#                 a gun; both stay with the torso instead of swinging with a leg
#   canopy        cockpit glass centre (x, y, z) and radius, in model units
CHASSIS = {
    "madcat": dict(
        file="madcat-timberwolf.stl", height=12.0, yaw=0.0,       # already faces +Y
        hip=0.542, ankle=0.090,
        x_in=0.075, x_out=0.275,
        swing=0.30, pitch=0.030, clear=0.10,
        foot_follow=0.85, toe=0.22,
        canopy_z=(0.66, 0.86), canopy_r=0.62, canopy_power=1.6, canopy_angle=36.0,
    ),
    "atlas": dict(
        file="atlas-as7-rs.stl", height=13.4, yaw=math.pi,        # modelled facing -Y
        hip=0.478, ankle=0.080,
        x_in=0.030, x_out=0.280,
        swing=0.24, pitch=0.022, clear=0.08,
        foot_follow=0.85, toe=0.18,
        canopy_power=3.4,
        # the Atlas's glass is the two eye slots, not the cranium the fill finds,
        # so this one is selected by an explicit box: (x0,x1, y0,y1, z0,z1)
        # y is bounded on BOTH sides: the skull's front surface sits at y ~= 1.15,
        # so 0.45..1.02 is the recess behind it - the eye sockets themselves
        canopy_box=(-0.85, 0.85, 0.45, 1.02, 11.88, 12.45),
    ),
    "battlemaster": dict(
        file="battlemaster.stl", height=12.8, yaw=math.radians(90),  # faces +X
        hip=0.414, ankle=0.080,
        x_in=0.020, x_out=0.245,
        swing=0.26, pitch=0.026, clear=0.09,
        foot_follow=0.85, toe=0.20,
        canopy_z=(0.72, 0.94), canopy_r=0.46, canopy_power=1.8, canopy_angle=22.0,
        # the sculpt has its pelvis and legs turned 38.5 degrees against the
        # torso - measured from above, both feet at -37.9 and -37.3, both shins
        # at -39.4 and -39.3 degrees off the torso's axis. Turned back, the feet
        # land symmetric either side of the centre, at x = +2.27 and -2.01
        untwist=dict(angle=-38.5, pivot=(0.0, -1.35), z0=6.95, z1=7.45,
                     # the left arm hangs down into the lower body's height
                     # band and must stay with the torso
                     keep=lambda x, y, z: x < -3.0 and z > 4.5),
    ),
}


# ------------------------------------------------------------------ utils ---
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def parent_keep(child, parent):
    """Parent without moving the child - the inverse needs current matrices."""
    bpy.context.view_layer.update()
    child.parent = parent
    child.matrix_parent_inverse = parent.matrix_world.inverted()


def empty(name, loc):
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = 0.4
    o.location = loc
    bpy.context.collection.objects.link(o)
    return o


def import_stl(path):
    before = set(bpy.data.objects)
    bpy.ops.wm.stl_import(filepath=path)
    new = list(set(bpy.data.objects) - before)
    obj = new[0]
    if len(new) > 1:
        bpy.ops.object.select_all(action="DESELECT")
        for o in new:
            o.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.join()
    return obj


def normalise(obj, height, yaw):
    """Face +Y, stand on z = 0, centred on x, scaled to `height`."""
    bpy.context.view_layer.objects.active = obj
    obj.rotation_euler = Euler((0, 0, yaw), "XYZ")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    lo = Vector((1e18, 1e18, 1e18))
    hi = Vector((-1e18, -1e18, -1e18))
    for v in obj.data.vertices:
        for i in range(3):
            lo[i] = min(lo[i], v.co[i])
            hi[i] = max(hi[i], v.co[i])
    s = height / (hi.z - lo.z)
    obj.scale = (s, s, s)
    obj.location = (-(lo.x + hi.x) / 2 * s, -(lo.y + hi.y) / 2 * s, -lo.z * s)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return obj


def untwist(obj, spec):
    """Turn the lower body about a vertical axis to line it up with the torso.

    Below z0 a vertex turns by the full angle, above z1 not at all, and in
    between by a smooth fraction, so the waist twists instead of tearing.
    """
    px, py = spec["pivot"]
    z0, z1 = spec["z0"], spec["z1"]
    for v in obj.data.vertices:
        x, y, z = v.co
        if z >= z1 or spec["keep"](x, y, z):
            continue
        t = min(1.0, max(0.0, (z1 - z) / (z1 - z0)))
        t = t * t * (3 - 2 * t)
        a = math.radians(spec["angle"]) * t
        ca, sa = math.cos(a), math.sin(a)
        dx, dy = x - px, y - py
        v.co = (px + dx * ca - dy * sa, py + dx * sa + dy * ca, z)
    obj.data.update()
    return obj


def load(name):
    """Import a chassis, normalised to face +Y on z = 0, lower body untwisted."""
    cfg = CHASSIS[name]
    obj = normalise(import_stl(os.path.join(MODELS, cfg["file"])), cfg["height"], cfg["yaw"])
    if "untwist" in cfg:
        untwist(obj, cfg["untwist"])
    return obj


def centreline(obj, x_sign, z_lo, z_hi, steps=64, x_in=0.0, x_out=1e9):
    """Trace one leg's centre as a function of height.

    Returns a list of (z, y, x). Horizontal planes cannot separate a
    reverse-jointed leg, because its thigh runs down-and-back while its shin
    runs down-and-forward, so the two overlap in height. Following the leg's
    own centre lets each cut be taken perpendicular to the limb instead.
    """
    band = (z_hi - z_lo) / steps
    buckets = [[0.0, 0.0, 0] for _ in range(steps)]
    for v in obj.data.vertices:
        ax = v.co.x * x_sign
        if ax <= x_in or ax >= x_out:
            continue
        i = int((v.co.z - z_lo) / band)
        if 0 <= i < steps:
            buckets[i][0] += v.co.y
            buckets[i][1] += v.co.x
            buckets[i][2] += 1
    out = []
    for i, (sy, sx, n) in enumerate(buckets):
        if n < 6:
            continue
        out.append((z_lo + (i + 0.5) * band, sy / n, sx / n))
    return out


def joint_on(line, z):
    """Point on the centreline at height z, plus the unit direction toward the
    parent (up the limb), taken from the centreline's own slope there."""
    if not line:
        return Vector((0, 0, z)), Vector((0, 0, 1))
    line = sorted(line)
    near = min(range(len(line)), key=lambda i: abs(line[i][0] - z))
    zc, yc, xc = line[near]
    a = line[max(0, near - 4)]
    b = line[min(len(line) - 1, near + 4)]
    d = Vector((0.0, b[1] - a[1], b[0] - a[0]))      # (x, y, z), x ignored
    if d.length < 1e-6:
        d = Vector((0, 0, 1))
    d.normalize()
    return Vector((xc, yc, zc)), d


def cut_part(src, name, planes, x_sign=0):
    """Duplicate the shell, cut away the far side of each plane, cap the holes.

    `planes` is a list of (point, normal); geometry on the normal's side goes.
    """
    obj = src.copy()
    obj.data = src.data.copy()
    obj.name = name
    bpy.context.collection.objects.link(obj)

    planes = list(planes)
    if x_sign:
        planes.append(((0, 0, 0), (-x_sign, 0, 0)))

    for co, no in planes:
        me = bmesh.new()
        me.from_mesh(obj.data)
        geom = list(me.verts) + list(me.edges) + list(me.faces)
        res = bmesh.ops.bisect_plane(
            me, geom=geom, plane_co=Vector(co), plane_no=Vector(no),
            clear_outer=True, use_snap_center=False)
        cut = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if cut:
            bmesh.ops.holes_fill(me, edges=cut, sides=0)
        me.to_mesh(obj.data)
        me.free()
    obj.data.update()
    return obj


# ------------------------------------------------------------------ build ---
def build(name, cfg, root_loc=(0, 0, 0), root_yaw=0.0):
    """Cut at the hip and the ankle, and only inside each leg's own x-corridor.

    Cutting the whole slab below the hip and splitting it at x = 0 is wrong on
    two counts. It divides the central crotch armour down the middle, so the two
    halves swing with opposite legs and a vertical seam opens; and it captures
    any arm or gun that hangs below hip height, which then swings with the leg.
    Restricting each leg to a corridor `x_in < |x| < x_out` leaves the centre
    mass and everything outboard with the torso, where they belong.
    """
    src = normalise(import_stl(os.path.join(MODELS, cfg["file"])),
                    cfg["height"], cfg["yaw"])
    src.name = f"{name}_src"
    H = cfg["height"]
    z_hip = H * cfg["hip"]
    z_ank = H * cfg["ankle"]
    x_in, x_out = H * cfg["x_in"], H * cfg["x_out"]

    root = empty(f"{name}_root", (0, 0, 0))
    body = empty(f"{name}_body", (0, 0, 0))
    parent_keep(body, root)

    above = ((0, 0, z_hip), (0, 0, -1))          # keep what is above the hip
    below = ((0, 0, z_hip), (0, 0, 1))           # keep what is below it

    torso = cut_part(src, f"{name}_torso", [above])
    parent_keep(torso, body)

    # central mass below the hip - pelvis, crotch armour - stays with the body
    pelvis = cut_part(src, f"{name}_pelvis",
                      [below, ((x_in, 0, 0), (1, 0, 0)), ((-x_in, 0, 0), (-1, 0, 0))])
    parent_keep(pelvis, body)

    parts = {"root": root, "body": body, "torso": torso, "pelvis": pelvis,
             "cfg": cfg, "H": H, "z_hip": z_hip}

    for side, sgn in (("L", -1), ("R", 1)):
        corridor = [((x_in * sgn, 0, 0), (-sgn, 0, 0)),
                    ((x_out * sgn, 0, 0), (sgn, 0, 0))]

        # arms, guns and anything else outboard of the leg keep still
        outer = cut_part(src, f"{name}_{side}_outer",
                         [below, ((x_out * sgn, 0, 0), (-sgn, 0, 0))], sgn)
        parent_keep(outer, body)

        line = centreline(src, sgn, 0.0, z_hip * 1.02, x_in=x_in, x_out=x_out)
        hip_p, _ = joint_on(line, z_hip * 0.97)
        ank_p, _ = joint_on(line, z_ank)

        leg = cut_part(src, f"{name}_{side}_leg",
                       [below, ((0, 0, z_ank), (0, 0, -1))] + corridor, sgn)
        foot = cut_part(src, f"{name}_{side}_foot",
                        [((0, 0, z_ank), (0, 0, 1))] + corridor, sgn)

        e_hip = empty(f"{name}_{side}_hip", hip_p)
        e_ank = empty(f"{name}_{side}_ankle", ank_p)
        parent_keep(e_hip, body)
        parent_keep(leg, e_hip)
        parent_keep(e_ank, e_hip)
        parent_keep(foot, e_ank)

        parts[side] = dict(hip=e_hip, ankle=e_ank, hip_p=hip_p.copy(),
                           ank_p=ank_p.copy(), leg=leg, foot=foot, outer=outer,
                           length=hip_p.z)

    bpy.data.objects.remove(src, do_unlink=True)
    root.location = root_loc
    root.rotation_euler = Euler((0, 0, root_yaw), "XYZ")
    bpy.context.view_layer.update()
    return parts


# ------------------------------------------------------------------- gait ---
def pose(parts, phase):
    """Pendulum gait with a swivelling foot. All terms are functions of phase."""
    cfg, H = parts["cfg"], parts["H"]
    swing = cfg["swing"]

    th = {s: swing * math.sin(2 * math.pi * ((phase + o) % 1.0))
          for s, o in (("L", 0.0), ("R", 0.5))}

    stance = min(abs(th["L"]), abs(th["R"]))
    leg_len = max(parts["L"]["length"], parts["R"]["length"])
    body_pitch = cfg.get("pitch", 0.03) * math.sin(4 * math.pi * phase)
    parts["body"].location = (0, 0, -leg_len * (1.0 - math.cos(stance)))
    parts["body"].rotation_euler = Euler((body_pitch, 0, 0), "XYZ")

    for side, off in (("L", 0.0), ("R", 0.5)):
        P = parts[side]
        p = (phase + off) % 1.0
        a = th[side]
        P["hip"].rotation_euler = Euler((a, 0, 0), "XYZ")

        fwd = math.cos(2 * math.pi * p)
        lift = max(0.0, -fwd)                     # 0 planted, 1 at mid-swing
        clear = lift * cfg.get("clear", 0.16) * leg_len
        P["hip"].location = (P["hip_p"].x, P["hip_p"].y, P["hip_p"].z + clear)

        # The ankle cancels the leg's swing exactly, so the sole stays parallel
        # to the deck. The toe roll is scaled by `lift`, which is zero while the
        # foot is planted, so it only ever happens in the air.
        # -a cancels the leg swing and -body_pitch cancels the torso's nod, so
        # the sole is parallel to the deck rather than merely close to it.
        toe = cfg.get("toe", 0.2) * lift * math.sin(2 * math.pi * p)
        P["ankle"].rotation_euler = Euler((-a - body_pitch + toe, 0, 0), "XYZ")

    bpy.context.view_layer.update()


# ----------------------------------------------------------------- canopy ---
def redden_canopy(parts, name, strength=None):
    """Isolate the cockpit glass as a surface, and make it burn.

    The torso arrives as one welded shell with one material, so the canopy has
    to be found geometrically. A radius grab is not good enough - it takes a
    ball of whatever happens to be nearby. Instead:

      1. seed   - inside the chassis's measured head band, the forward-facing
                  face that sits furthest forward on the centreline
      2. spread - flood-fill outward across shared edges, but only where two
                  faces meet at a shallow angle. A canopy is a smooth panel or
                  dome set into a sharp rim, so the rim itself stops the fill
      3. cap    - a generous distance limit, purely as a backstop in case the
                  glass runs smoothly into the surrounding armour

    That yields the canopy surface and nothing else.
    """
    cfg = parts["cfg"]
    H = parts["H"]
    power = strength if strength is not None else cfg.get("canopy_power", 1.0)
    torso = parts["torso"]

    box = cfg.get("canopy_box")
    if box:
        x0, x1, y0, y1, z0, z1 = box
        keep = {f.index for f in torso.data.polygons
                if x0 <= f.center.x <= x1 and y0 <= f.center.y <= y1
                and z0 <= f.center.z <= z1 and f.normal.y > 0.12}
        origin = (sum((torso.data.polygons[i].center for i in keep),
                      Vector((0, 0, 0))) / len(keep)) if keep else Vector(
            ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
        return _paint_canopy(parts, name, keep, origin, power)

    zlo, zhi = (h * H for h in cfg["canopy_z"])
    xlim = 0.16 * H
    cap = cfg["canopy_r"] * 2.4
    limit = math.radians(cfg.get("canopy_angle", 24.0))

    me = bmesh.new()
    me.from_mesh(torso.data)
    me.faces.ensure_lookup_table()

    seed, best = None, -1e9
    for f in me.faces:
        c = f.calc_center_median()
        if zlo <= c.z <= zhi and abs(c.x) <= xlim and f.normal.y > 0.30 and c.y > best:
            best, seed = c.y, f
    if seed is None:
        me.free()
        print(f"CANOPY {name}: no seed in band")
        return 0

    origin = seed.calc_center_median()
    keep = {seed.index}
    stack = [seed]
    while stack:
        f = stack.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g.index in keep:
                    continue
                if f.normal.angle(g.normal, math.pi) > limit:
                    continue                      # sharp crease - that is the rim
                if (g.calc_center_median() - origin).length > cap:
                    continue
                keep.add(g.index)
                stack.append(g)
    me.free()

    return _paint_canopy(parts, name, keep, origin, power)


def _paint_canopy(parts, name, keep, origin, power):
    """Apply the emissive material to the chosen faces and light them."""
    torso = parts["torso"]
    # Glass, not a flat emitter. A pure emission shader has no specular and no
    # fresnel, so it renders as a solid patch of colour and reads as something
    # painted on in 2D. A Principled surface with a near-black base, a tight
    # roughness and a clear coat picks up the scene's key and rim as real
    # highlights across the curvature, and the emission sits behind that.
    glass = bpy.data.materials.new(f"{name}_canopy")
    glass.use_nodes = True
    b = glass.node_tree.nodes["Principled BSDF"]

    def put(socket, value):
        if socket in b.inputs:
            b.inputs[socket].default_value = value

    put("Base Color", (0.030, 0.0035, 0.0025, 1))
    put("Metallic", 0.0)
    put("Roughness", 0.06)
    put("IOR", 1.52)
    put("Specular IOR Level", 0.72)
    put("Coat Weight", 0.85)
    put("Coat Roughness", 0.025)
    put("Emission Color", (0.62, 0.007, 0.004, 1))
    put("Emission Strength", 1.05 * power)

    torso.data.materials.append(glass)
    idx = len(torso.data.materials) - 1
    for i in keep:
        torso.data.polygons[i].material_index = idx

    span = max(((torso.data.polygons[i].center - origin).length for i in keep),
               default=0.0)
    print(f"CANOPY {name}: {len(keep)} faces, span {span:.2f}, "
          f"at ({origin.x:.2f}, {origin.y:.2f}, {origin.z:.2f})")

    lamp = bpy.data.lights.new(f"{name}_cockpit", "POINT")
    lamp.color = (0.85, 0.020, 0.012)
    lamp.energy = 150.0 * power
    lamp.shadow_soft_size = 0.30
    o = bpy.data.objects.new(f"{name}_cockpit", lamp)
    o.location = (origin.x, origin.y + 0.30, origin.z)
    bpy.context.collection.objects.link(o)
    parent_keep(o, parts["body"])
    return len(keep)
