"""Scene-building kit shared by the Mechanicum scene: bmesh primitives, a
shader-graph helper, and animated materials driven by the loop clocks.

Everything animated reads `phase` in [0, 1) or `tick` (a whole-number state)
through Value nodes registered in CLOCKS, or is posed by a function in MOVERS;
the render loop sets both every frame.
"""
import bpy, bmesh, math
from mathutils import Vector, Matrix

MOVERS = []                     # (object, function of phase), posed every frame
CLOCKS = []                     # (kind, value node): "phase" or "tick"

Euler90X = Matrix.Rotation(math.pi / 2, 3, "X")
Euler90Y = Matrix.Rotation(math.pi / 2, 3, "Y")


# ------------------------------------------------------------------ meshes --
def link(ob, parent=None):
    bpy.context.collection.objects.link(ob)
    if parent:
        ob.parent = parent
    return ob


def from_bm(name, bm, mat, loc=(0, 0, 0), parent=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if mat:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    return link(ob, parent)


def box(name, size, loc, mat, parent=None, bevel=0.03):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    ob = from_bm(name, bm, mat, loc, parent)
    if bevel:
        m = ob.modifiers.new("bevel", "BEVEL")
        m.width, m.segments, m.limit_method = bevel, 2, "ANGLE"
    return ob


def cyl(name, r, depth, loc, mat, parent=None, r2=None, seg=32, axis="Z"):
    """Cylinder or cone, sides smooth, caps flat, centred on `loc`."""
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r,
                          radius2=r if r2 is None else r2, depth=depth)
    for f in bm.faces:
        f.smooth = len(f.verts) == 4
    if axis == "Y":
        bmesh.ops.rotate(bm, verts=bm.verts, matrix=Euler90X)
    elif axis == "X":
        bmesh.ops.rotate(bm, verts=bm.verts, matrix=Euler90Y)
    return from_bm(name, bm, mat, loc, parent)


def sphere(name, r, loc, mat, parent=None, scale=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=14, radius=r)
    for v in bm.verts:
        v.co = Vector((v.co.x * scale[0], v.co.y * scale[1], v.co.z * scale[2]))
    for f in bm.faces:
        f.smooth = True
    return from_bm(name, bm, mat, loc, parent)


def torus(name, R, r, loc, mat, parent=None, axis="Z", seg=48):
    """A ring. A ring that turns in the loop must turn a whole number of
    segments per loop, or its facets land elsewhere at phase 1.0."""
    rot = {"Z": (0, 0, 0), "Y": (math.pi / 2, 0, 0), "X": (0, math.pi / 2, 0)}[axis]
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, major_segments=seg,
                                     minor_segments=10, location=loc, rotation=rot)
    ob = bpy.context.object
    ob.name = name
    ob.data.materials.append(mat)
    ob.data.shade_smooth()
    if parent:
        ob.parent = parent
    return ob


def ribbon(name, outer, inner, depth, mat, loc=(0, 0, 0), parent=None):
    """A flat band between two outlines in the XZ plane, `depth` thick along Y.
    `outer` and `inner` are equal-length lists of (x, z)."""
    bm = bmesh.new()
    vo = [bm.verts.new((x, 0, z)) for x, z in outer]
    vi = [bm.verts.new((x, 0, z)) for x, z in inner]
    for i in range(len(outer) - 1):
        bm.faces.new((vo[i], vo[i + 1], vi[i + 1], vi[i]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    ob = from_bm(name, bm, mat, loc, parent)
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness, m.offset = depth, 0.0
    b = ob.modifiers.new("bevel", "BEVEL")
    b.width, b.segments, b.limit_method = min(0.02, depth / 4), 2, "ANGLE"
    return ob


def arch_outline(w, spring, inset=0.0, n=14):
    """Equilateral pointed arch, open at the bottom: left leg up, over the
    apex, right leg down. `inset` shrinks it inward by a band width."""
    r = w - inset
    left = [(-w / 2 + inset, 0.0), (-w / 2 + inset, spring)]
    top = math.acos(-(w / 2) / r)               # the angle at which the arc meets x = 0
    for k in range(1, n + 1):                   # left arc, centred on the right springer
        a = math.pi - (math.pi - top) * k / n
        left.append((w / 2 + r * math.cos(a), spring + r * math.sin(a)))
    return left + [(-x, z) for x, z in reversed(left[:-1])]


def arch(name, w, spring, band, depth, mat, loc, parent=None):
    return ribbon(name, arch_outline(w, spring), arch_outline(w, spring, band), depth, mat, loc, parent)


def gear(name, R, teeth, tooth, hole, depth, mat, loc, parent=None):
    """A flat toothed ring in the XZ plane."""
    n = teeth * 4
    outer, inner = [], []
    for k in range(n + 1):
        a = 2 * math.pi * k / n
        rr = R + (tooth if (k % 4) in (1, 2) else 0.0)
        outer.append((rr * math.cos(a), rr * math.sin(a)))
        inner.append((hole * math.cos(a), hole * math.sin(a)))
    return ribbon(name, outer, inner, depth, mat, loc, parent)


def curve(name, pts, r, mat, parent=None):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth, cu.bevel_resolution = r, 4
    sp = cu.splines.new("BEZIER")
    sp.bezier_points.add(len(pts) - 1)
    for p, co in zip(sp.bezier_points, pts):
        p.co = co
        p.handle_left_type = p.handle_right_type = "AUTO"
    cu.materials.append(mat)
    return link(bpy.data.objects.new(name, cu), parent)


def empty(name, loc, parent=None, rot=(0, 0, 0)):
    ob = bpy.data.objects.new(name, None)
    ob.location, ob.rotation_euler = loc, rot
    return link(ob, parent)




# --------------------------------------------------------------- materials --
class Graph:
    """Builds a shader node tree from code; sockets or plain numbers go in."""

    def __init__(self, mat):
        self.N, self.L = mat.node_tree.nodes, mat.node_tree.links

    def put(self, sock, v):
        if isinstance(v, bpy.types.NodeSocket):
            self.L.new(v, sock)
        elif isinstance(v, (tuple, list)) and len(v) == 3 and sock.type == "RGBA":
            sock.default_value = (*v, 1)
        else:
            sock.default_value = v

    def op(self, kind, a, b=0.0, clamp=False):
        n = self.N.new("ShaderNodeMath")
        n.operation, n.use_clamp = kind, clamp
        self.put(n.inputs[0], a)
        self.put(n.inputs[1], b)
        return n.outputs[0]

    def xyz(self):
        s = self.N.new("ShaderNodeSeparateXYZ")
        self.L.new(self.N.new("ShaderNodeNewGeometry").outputs["Position"], s.inputs[0])
        return s.outputs

    def clock(self, kind):
        n = self.N.new("ShaderNodeValue")
        CLOCKS.append((kind, n))
        return n.outputs[0]

    def pulse(self, v, width=0.08, power=2.0):
        """1 at the middle of every unit interval of `v`, 0 beyond +-width."""
        d = self.op("ABSOLUTE", self.op("SUBTRACT", self.op("FRACT", v), 0.5))
        return self.op("POWER", self.op("SUBTRACT", 1.0, self.op("DIVIDE", d, width), clamp=True), power)

    def mix(self, fac, a, b):
        n = self.N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        ins = {s.identifier: s for s in n.inputs}
        self.put(ins["Factor_Float"], fac)
        self.put(ins["A_Color"], a)
        self.put(ins["B_Color"], b)
        return {s.identifier: s for s in n.outputs}["Result_Color"]

    def bsdf(self):
        return self.N["Principled BSDF"]


def pbr(name, base, rough=0.5, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    return m


def lamp(name, colour, strength):
    """Pure emission."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N = m.node_tree.nodes
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    e = N.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*colour, 1)
    e.inputs["Strength"].default_value = strength
    m.node_tree.links.new(e.outputs[0], N["Material Output"].inputs["Surface"])
    return m, e


def masonry(name, base, block=(1.4, 0.7)):
    """Stone courses on world coordinates: walls running along Y use (y, z),
    faces across Y use (x, z) - (x + y, z) serves both."""
    m = pbr(name, base, 0.82)
    g = Graph(m)
    x, y, z = g.xyz()
    v = g.N.new("ShaderNodeCombineXYZ")
    g.put(v.inputs["X"], g.op("ADD", x, y))
    g.put(v.inputs["Y"], z)
    br = g.N.new("ShaderNodeTexBrick")
    g.L.new(v.outputs[0], br.inputs["Vector"])
    for k, val in (("Scale", 1.0), ("Brick Width", block[0]), ("Row Height", block[1]),
                   ("Mortar Size", 0.035), ("Bias", 0.0)):
        br.inputs[k].default_value = val
    br.inputs["Color1"].default_value = (*(c * 0.75 for c in base), 1)
    br.inputs["Color2"].default_value = (*(c * 1.25 for c in base), 1)
    br.inputs["Mortar"].default_value = (*(c * 0.35 for c in base), 1)
    g.L.new(br.outputs["Color"], g.bsdf().inputs["Base Color"])
    bump = g.N.new("ShaderNodeBump")
    bump.invert = True
    bump.inputs["Strength"].default_value = 0.35
    g.L.new(br.outputs["Fac"], bump.inputs["Height"])
    g.L.new(bump.outputs["Normal"], g.bsdf().inputs["Normal"])
    return m


def floor_mat():
    """Polished dark stone in square slabs, so the lights reflect in it."""
    m = pbr("floor", (0.022, 0.021, 0.024), 0.16)
    g = Graph(m)
    x, y, z = g.xyz()
    v = g.N.new("ShaderNodeCombineXYZ")
    g.put(v.inputs["X"], x)
    g.put(v.inputs["Y"], y)
    br = g.N.new("ShaderNodeTexBrick")
    br.offset = 0.0
    g.L.new(v.outputs[0], br.inputs["Vector"])
    for k, val in (("Scale", 1.0), ("Brick Width", 2.5), ("Row Height", 2.5),
                   ("Mortar Size", 0.03), ("Bias", 0.0)):
        br.inputs[k].default_value = val
    br.inputs["Color1"].default_value = (0.017, 0.016, 0.019, 1)
    br.inputs["Color2"].default_value = (0.030, 0.028, 0.032, 1)
    br.inputs["Mortar"].default_value = (0.006, 0.006, 0.007, 1)
    g.L.new(br.outputs["Color"], g.bsdf().inputs["Base Color"])
    # scuffs: the polish varies, so reflections break up
    nz = g.N.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.35
    nz.inputs["Detail"].default_value = 6.0
    g.L.new(v.outputs[0], nz.inputs["Vector"])
    rough = g.N.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = 0.08
    rough.inputs["To Max"].default_value = 0.45
    g.L.new(nz.outputs["Fac"], rough.inputs["Value"])
    g.L.new(rough.outputs["Result"], g.bsdf().inputs["Roughness"])
    return m


def data_flow(name, colour, axis, period, laps, strength, base=0.15, width=0.07):
    """Emission that runs along a world axis: a pulse every `period` units,
    moving `laps` periods per loop. Positive laps move towards +axis."""
    m, e = lamp(name, colour, 1.0)
    g = Graph(m)
    comps = dict(zip("xyz", g.xyz()))
    coord = g.op("ABSOLUTE", comps[axis[-1]]) if axis.startswith("|") else comps[axis]
    v = g.op("SUBTRACT", g.op("DIVIDE", coord, period), g.op("MULTIPLY", g.clock("phase"), laps))
    g.put(e.inputs["Strength"], g.op("ADD", base * strength, g.op("MULTIPLY", g.pulse(v, width), strength)))
    return m


def compute_cells(name, cell=(0.30, 0.20), laps=2, colours=((0.10, 0.75, 1.0), (1.0, 0.42, 0.08))):
    """The mainframe's face: a grid of indicator cells on a dark panel. Each
    cell is lit or dark by a hash of its position and the current tick; a few
    cells burn amber, the rest cyan; a brighter band sweeps down the rows."""
    m = pbr(name, (0.018, 0.019, 0.024), 0.35, 0.6)
    g = Graph(m)
    x, y, z = g.xyz()
    u, v = g.op("DIVIDE", x, cell[0]), g.op("DIVIDE", z, cell[1])
    cu, cv = g.op("FLOOR", u), g.op("FLOOR", v)
    fu, fv = g.op("SUBTRACT", u, cu), g.op("SUBTRACT", v, cv)
    inside = g.op("MULTIPLY",
                  g.op("MULTIPLY", g.op("GREATER_THAN", fu, 0.16), g.op("LESS_THAN", fu, 0.84)),
                  g.op("MULTIPLY", g.op("GREATER_THAN", fv, 0.22), g.op("LESS_THAN", fv, 0.78)))
    cid = g.N.new("ShaderNodeCombineXYZ")
    g.put(cid.inputs["X"], cu)
    g.put(cid.inputs["Y"], cv)
    g.put(cid.inputs["Z"], g.op("ADD", g.op("MULTIPLY", y, 0.37), 0.0))
    state = g.N.new("ShaderNodeTexWhiteNoise")
    state.noise_dimensions = "4D"
    g.L.new(cid.outputs[0], state.inputs["Vector"])
    g.put(state.inputs["W"], g.clock("tick"))
    lit = g.op("GREATER_THAN", state.outputs["Value"], 0.70)
    kind = g.N.new("ShaderNodeTexWhiteNoise")
    kind.noise_dimensions = "3D"
    g.L.new(cid.outputs[0], kind.inputs["Vector"])
    amber = g.op("GREATER_THAN", kind.outputs["Value"], 0.72)
    colour = g.mix(amber, colours[0], colours[1])
    sweep = g.pulse(g.op("ADD", g.op("DIVIDE", z, 7.0), g.op("MULTIPLY", g.clock("phase"), laps)), 0.12, 1.5)
    strength = g.op("MULTIPLY", inside,
                    g.op("MULTIPLY", g.op("ADD", 0.02, g.op("MULTIPLY", lit, 1.8)),
                         g.op("ADD", 1.0, g.op("MULTIPLY", sweep, 2.2))))
    b = g.bsdf()
    g.L.new(colour, b.inputs["Emission Color"])
    g.L.new(strength, b.inputs["Emission Strength"])
    return m


def core_mat():
    """The calculating core: cyan, pulsing twice per loop, with bright bands
    climbing it three band-spacings per loop."""
    m, e = lamp("core", (0.25, 0.85, 1.0), 1.0)
    g = Graph(m)
    x, y, z = g.xyz()
    ph = g.clock("phase")
    beat = g.op("ADD", 1.0, g.op("MULTIPLY", g.op("COSINE", g.op("MULTIPLY", ph, 4 * math.pi)), 0.35))
    bands = g.op("ADD", 0.55, g.op("MULTIPLY", g.pulse(g.op("SUBTRACT", g.op("DIVIDE", z, 1.6),
                                                                      g.op("MULTIPLY", ph, 3.0)), 0.18), 1.4))
    g.put(e.inputs["Strength"], g.op("MULTIPLY", g.op("MULTIPLY", beat, bands), 5.0))
    return m


def flame_mat():
    """Candle flames: each flickers on its own two whole-cycle frequencies."""
    m, e = lamp("flame", (1.0, 0.50, 0.14), 1.0)
    g = Graph(m)
    ph = g.clock("phase")
    rnd = g.N.new("ShaderNodeObjectInfo").outputs["Random"]
    s1 = g.op("SINE", g.op("MULTIPLY", g.op("ADD", g.op("MULTIPLY", ph, 3.0), rnd), 2 * math.pi))
    s2 = g.op("SINE", g.op("MULTIPLY", g.op("ADD", g.op("MULTIPLY", ph, 7.0), g.op("MULTIPLY", rnd, 3.1)), 2 * math.pi))
    g.put(e.inputs["Strength"], g.op("MULTIPLY", g.op("ADD", 1.0, g.op("ADD", g.op("MULTIPLY", s1, 0.18),
                                                                      g.op("MULTIPLY", s2, 0.10))), 26.0))
    return m
