"""Paint a print-model BattleMech on its mesh: armour colours, exposed
machinery, and cockpit glass set into the hull. Blender 4.5, Cycles.

Works on the whole normalised mesh (facing +Y, feet on z = 0) before any
rigging. Every colour is a material slot on the mesh's own faces, so it travels
with the geometry through the armature and into every render.

Faces are sorted in three passes, first match wins:

  1. glass    flood-filled from measured seed points inside a measured window,
              then inset into the hull so the glass sits behind a frame
  2. machine  faces in small flat patches - actuators, pistons, vents, bolts
  3. armour   everything else, coloured by body region from the scheme

Seed points and windows were read off front close-ups of each head with a
0.1-unit grid; region boxes off the front and side measurement sheets.
"""

import bpy, bmesh, math, random

# a patch smaller than this, in square model units, is machinery, not a plate
MACHINE_AREA = 0.03
PATCH_ANGLE = math.radians(10)

GUNMETAL = (0.20, 0.205, 0.215)

# colours are linear RGB
SCHEMES = {
    # Clan Wolf-style: steel blue-grey armour, black limbs, red on the missile racks
    "madcat": dict(
        colours=dict(primary=(0.085, 0.10, 0.12), secondary=(0.028, 0.030, 0.034),
                     accent=(0.30, 0.020, 0.012)),
        regions=[
            (lambda c, n: c.z > 10.35 and 1.45 < abs(c.x) < 3.75 and n.y > 0.8, "accent"),
            (lambda c, n: c.z > 10.35 and 1.45 < abs(c.x) < 3.75, "secondary"),
            (lambda c, n: abs(c.x) > 3.35, "secondary"),
            (lambda c, n: c.z < 0.62, "secondary"),
        ],
        glass=dict(
            seeds=[(0.0, 9.55), (0.7, 9.45), (-0.7, 9.45)], angle=20.0,
            bound=lambda c: c.z > 9.13 and c.x * c.x + (c.z - 9.25) ** 2 < 1.02 ** 2,
            inset=0.030, depth=-0.015, glow=0.45),
    ),
    # charcoal hull, oxblood arms and shoulders, a bone-white skull
    "atlas": dict(
        colours=dict(primary=(0.045, 0.047, 0.052), secondary=(0.16, 0.012, 0.010),
                     bone=(0.50, 0.44, 0.33)),
        regions=[
            (lambda c, n: abs(c.x) < 1.05 and c.z > 11.35 and c.y > -0.2, "bone"),
            (lambda c, n: abs(c.x) > 3.35, "secondary"),
            (lambda c, n: c.z > 10.6 and abs(c.x) > 1.8, "secondary"),
        ],
        # the eye sockets hold a separate lens piece that no flood-fill from the
        # socket reaches, so the whole socket interior is taken by its window
        glass=dict(
            box=True,
            bound=lambda c: 0.26 < abs(c.x) < 0.66 and 12.06 < c.z < 12.25,
            inset=0.012, depth=-0.02, glow=0.9),
    ),
    # desert sand, dark helmet and feet
    "battlemaster": dict(
        colours=dict(primary=(0.32, 0.25, 0.14), secondary=(0.07, 0.06, 0.04)),
        regions=[
            (lambda c, n: abs(c.x) < 0.8 and c.z > 9.45 and -1.8 < c.y < 0.7, "secondary"),
            (lambda c, n: c.z < 1.1 and abs(c.x) < 3.6, "secondary"),
        ],
        glass=dict(
            seeds=[(0.0, 10.15)], angle=22.0,
            bound=lambda c: abs(c.x) < 0.62 and 9.45 < c.z < 11.2,
            inset=0.035, depth=-0.02, glow=0.40),
    ),
}


# ------------------------------------------------------------- materials ---
def _sock(node, ident):
    """Socket by identifier - ShaderNodeMix repeats names across data types."""
    return next(s for s in node.inputs if s.identifier == ident)


def _surface(name, colour, rough, metal, wear):
    """Painted or bare metal, with cavity dirt, edge wear and panel variation.

    AO darkens the creases and panel lines the mesh already carries. The
    difference between a bevelled normal and the true normal marks every hard
    edge; multiplied by AO it keeps only the convex ones, where paint chips to
    bare metal. The Bevel normal also rounds those edges for the light.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]

    rgb = N.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = (*colour, 1)

    ao = N.new("ShaderNodeAmbientOcclusion")
    ao.only_local = True
    ao.inputs["Distance"].default_value = 0.35
    cavity = N.new("ShaderNodeMapRange")
    cavity.inputs["To Min"].default_value = 0.30
    L.new(ao.outputs["AO"], cavity.inputs["Value"])

    panel = N.new("ShaderNodeAttribute")
    panel.attribute_type = "GEOMETRY"
    panel.attribute_name = "panel"

    tc = N.new("ShaderNodeTexCoord")
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 1.4
    noise.inputs["Detail"].default_value = 8.0
    L.new(tc.outputs["Object"], noise.inputs["Vector"])
    grime = N.new("ShaderNodeMapRange")
    grime.inputs["From Min"].default_value = 0.30
    grime.inputs["From Max"].default_value = 0.70
    grime.inputs["To Min"].default_value = 0.78
    grime.inputs["To Max"].default_value = 1.10
    L.new(noise.outputs["Fac"], grime.inputs["Value"])

    k1 = N.new("ShaderNodeMath"); k1.operation = "MULTIPLY"
    L.new(cavity.outputs["Result"], k1.inputs[0]); L.new(grime.outputs["Result"], k1.inputs[1])
    k2 = N.new("ShaderNodeMath"); k2.operation = "MULTIPLY"
    L.new(k1.outputs[0], k2.inputs[0]); L.new(panel.outputs["Fac"], k2.inputs[1])
    base = N.new("ShaderNodeVectorMath"); base.operation = "SCALE"
    L.new(rgb.outputs[0], base.inputs[0]); L.new(k2.outputs[0], base.inputs["Scale"])

    bev = N.new("ShaderNodeBevel")
    bev.samples = 6
    bev.inputs["Radius"].default_value = 0.016
    geo = N.new("ShaderNodeNewGeometry")
    dot = N.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    L.new(bev.outputs["Normal"], dot.inputs[0]); L.new(geo.outputs["Normal"], dot.inputs[1])
    edge = N.new("ShaderNodeMapRange")
    edge.inputs["From Min"].default_value = 0.96
    edge.inputs["From Max"].default_value = 0.998
    edge.inputs["To Min"].default_value = 1.0
    edge.inputs["To Max"].default_value = 0.0
    L.new(dot.outputs["Value"], edge.inputs["Value"])
    chip = N.new("ShaderNodeMath"); chip.operation = "MULTIPLY"
    L.new(edge.outputs["Result"], chip.inputs[0]); L.new(ao.outputs["AO"], chip.inputs[1])
    worn = N.new("ShaderNodeMath"); worn.operation = "MULTIPLY"
    worn.inputs[1].default_value = wear
    L.new(chip.outputs[0], worn.inputs[0])

    mix = N.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L.new(worn.outputs[0], _sock(mix, "Factor_Float"))
    L.new(base.outputs[0], _sock(mix, "A_Color"))
    _sock(mix, "B_Color").default_value = (0.42, 0.42, 0.44, 1)
    L.new(next(s for s in mix.outputs if s.identifier == "Result_Color"), b.inputs["Base Color"])

    met = N.new("ShaderNodeMath"); met.operation = "MAXIMUM"
    met.inputs[0].default_value = metal
    L.new(worn.outputs[0], met.inputs[1])
    L.new(met.outputs[0], b.inputs["Metallic"])

    ro = N.new("ShaderNodeMath"); ro.operation = "MULTIPLY_ADD"
    ro.inputs[1].default_value = -0.25
    ro.inputs[2].default_value = rough
    L.new(worn.outputs[0], ro.inputs[0])
    L.new(ro.outputs[0], b.inputs["Roughness"])

    L.new(bev.outputs["Normal"], b.inputs["Normal"])
    return m


def _glass(name, glow):
    """Dark red glass with a lit cockpit behind it.

    The surface is a near-black clear-coated dielectric, so the scene's lights
    and sky show as sharp reflections across it - that is what reads as glass.
    The emission is deliberately weak, well below the point where the image
    saturates, and hotter where the glass faces the viewer, so it has a core
    and falls off towards the rim instead of rendering as one flat colour.
    """
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.012, 0.0015, 0.0012, 1)
    b.inputs["Metallic"].default_value = 0.0
    b.inputs["Roughness"].default_value = 0.05
    b.inputs["IOR"].default_value = 1.50
    b.inputs["Coat Weight"].default_value = 1.0
    b.inputs["Coat Roughness"].default_value = 0.02

    lw = N.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.45
    face = N.new("ShaderNodeMath"); face.operation = "SUBTRACT"
    face.inputs[0].default_value = 1.0
    L.new(lw.outputs["Facing"], face.inputs[1])            # 1 facing the viewer, 0 at the rim

    col = N.new("ShaderNodeMix"); col.data_type = "RGBA"
    L.new(face.outputs[0], _sock(col, "Factor_Float"))
    _sock(col, "A_Color").default_value = (0.35, 0.003, 0.002, 1)   # rim: deep red
    _sock(col, "B_Color").default_value = (0.85, 0.012, 0.006, 1)   # core: red, no orange
    L.new(next(s for s in col.outputs if s.identifier == "Result_Color"), b.inputs["Emission Color"])

    st = N.new("ShaderNodeMapRange")
    st.inputs["To Min"].default_value = 0.20 * glow
    st.inputs["To Max"].default_value = glow
    L.new(face.outputs[0], st.inputs["Value"])
    L.new(st.outputs["Result"], b.inputs["Emission Strength"])
    return m


# ------------------------------------------------------------- selection ---
def _patches(bm):
    """Flat patches: neighbours join when their normals differ by < PATCH_ANGLE.

    Returns per-face patch id and per-patch area. Neighbour-to-neighbour
    comparison lets a smoothly curved plate grow into one patch, while a
    faceted cylinder or a cluster of bolts stays in small pieces.
    """
    pid = [-1] * len(bm.faces)
    area = []
    for f in bm.faces:
        if pid[f.index] >= 0:
            continue
        k = len(area)
        pid[f.index] = k
        stack, a = [f], 0.0
        while stack:
            g = stack.pop()
            a += g.calc_area()
            for e in g.edges:
                for h in e.link_faces:
                    if pid[h.index] < 0 and g.normal.angle(h.normal, math.pi) < PATCH_ANGLE:
                        pid[h.index] = k
                        stack.append(h)
        area.append(a)
    return pid, area


def _glass_faces(bm, spec):
    """Flood-fill the cockpit glass from each seed, inside the window.

    With `box`, every forward-facing face inside the window is glass.
    """
    bound = spec["bound"]
    if spec.get("box"):
        return {f.index for f in bm.faces
                if f.normal.y > 0.05 and bound(f.calc_center_median())}
    limit = math.radians(spec["angle"])
    keep = set()
    for sx, sz in spec["seeds"]:
        seed, front = None, -1e9
        for f in bm.faces:
            c = f.calc_center_median()
            if ((c.x - sx) ** 2 + (c.z - sz) ** 2 < 0.08 ** 2 and f.normal.y > 0.2
                    and c.y > front and bound(c)):
                seed, front = f, c.y
        if seed is None:
            print(f"GLASS no seed at ({sx}, {sz})")
            continue
        keep.add(seed.index)
        stack = [seed]
        while stack:
            f = stack.pop()
            for e in f.edges:
                for g in e.link_faces:
                    if (g.index not in keep and f.normal.angle(g.normal, math.pi) < limit
                            and bound(g.calc_center_median())):
                        keep.add(g.index)
                        stack.append(g)
    return keep


# ------------------------------------------------------------------ paint ---
def paint(obj, name):
    """Assign every face of `obj` a material slot from the chassis's scheme."""
    sc = SCHEMES[name]
    rng = random.Random(name)
    mats = {k: _surface(f"{name}_{k}", c, 0.52, 0.0, 0.55) for k, c in sc["colours"].items()}
    mats["machine"] = _surface(f"{name}_machine", GUNMETAL, 0.36, 0.9, 0.0)
    mats["glass"] = _glass(f"{name}_glass", sc["glass"]["glow"])
    order = list(mats)
    obj.data.materials.clear()
    for k in order:
        obj.data.materials.append(mats[k])
    slot = {k: i for i, k in enumerate(order)}

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()

    glass_idx = _glass_faces(bm, sc["glass"])
    pid, area = _patches(bm)

    counts = dict.fromkeys(order, 0)
    for f in bm.faces:
        if f.index in glass_idx:
            continue
        if area[pid[f.index]] < MACHINE_AREA:
            key = "machine"
        else:
            c = f.calc_center_median()
            key = next((k for test, k in sc["regions"] if test(c, f.normal)), "primary")
        f.material_index = slot[key]
        counts[key] += 1

    # set the glass back into the hull: the rim faces the inset creates become
    # a machined frame, and the glass itself drops behind it
    glass = [bm.faces[i] for i in glass_idx]
    for f in glass:
        f.material_index = slot["glass"]
    counts["glass"] = len(glass)
    g = sc["glass"]
    rim = bmesh.ops.inset_region(bm, faces=glass, thickness=g["inset"], depth=g["depth"],
                                 use_even_offset=True)["faces"]
    for f in rim:
        f.material_index = slot["machine"]

    # a small per-patch brightness offset, as on a hand-painted model, where
    # no two plates come out exactly the same tone
    bm.faces.ensure_lookup_table()
    pid, _ = _patches(bm)
    tone = {}
    layer = bm.faces.layers.float.new("panel")
    for f in bm.faces:
        p = pid[f.index]
        if p not in tone:
            tone[p] = rng.uniform(0.90, 1.08)
        f[layer] = tone[p]

    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    print(f"PAINT {name}: " + ", ".join(f"{k} {v}" for k, v in counts.items()))
    return counts
