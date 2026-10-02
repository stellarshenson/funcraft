"""Blender side of the actors (src/actors.py): builds every element's mesh
and bones from wip/scene3d/<name>_actors.npz and moves the bones through
the loop.

Order. Armatures first; then one pass through the loop with only the
armatures in the scene, which records where every carried candle's wick is
at each frame; then the flames, which need that path (a flame leans away
from the candle's own motion); then the meshes. The pass also writes
wip/scene3d/<name>_sources.json: the path of every smoke source, for
src/smoke.py.

Candle light. One node group, shared by every material. A surface point
gets the scene's own light, 1, and from flame c the share
s_c = R^2 / (R^2 + d_c^2): d_c is the distance to the flame and R = REACH
the distance at which a candle's light equals the rest of the scene's. The
plate shows the point in still air; its brightness is multiplied by
(1 + sum_c I_c s_c) / (1 + sum_c s_c), where I_c is the flame's light
relative to still air (src/air.py). The factor stays between the smallest
and the largest I_c, however many flames stand together. Flames move with
their candles. No shadows.
"""
import bpy, json, math, os, sys
import numpy as np
from mathutils import Vector, Quaternion
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import air

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 2 * math.pi
FRAMES = 80
REACH = 0.5                # m
GLOW = 0.12                # m, how far a flame lights its own smoke
MAX_LIGHTS = 48


def light_group(n):
    """Node group `candlelight` with n flames. Outputs Gain (for surfaces)
    and Glow (for smoke). Returns the group and, per flame, the nodes whose
    inputs carry its position and light."""
    g = bpy.data.node_groups.new("candlelight", "ShaderNodeTree")
    g.interface.new_socket("Gain", in_out="OUTPUT", socket_type="NodeSocketFloat")
    g.interface.new_socket("Glow", in_out="OUTPUT", socket_type="NodeSocketFloat")
    N, L = g.nodes, g.links
    out = N.new("NodeGroupOutput")
    pos = N.new("ShaderNodeNewGeometry").outputs["Position"]

    def op(operation, a, b):
        m = N.new("ShaderNodeMath")
        m.operation = operation
        for i, x in enumerate((a, b)):
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                L.new(x, m.inputs[i])
        return m

    gain, total, glow, handles = 0.0, 1.0, 0.0, []
    for _ in range(n):
        at = N.new("ShaderNodeCombineXYZ")
        d = N.new("ShaderNodeVectorMath")
        d.operation = "DISTANCE"
        L.new(pos, d.inputs[0])
        L.new(at.outputs[0], d.inputs[1])
        d2 = op("MULTIPLY", d.outputs["Value"], d.outputs["Value"]).outputs[0]
        share = op("DIVIDE", REACH ** 2, op("ADD", d2, REACH ** 2).outputs[0]).outputs[0]
        dev = op("MULTIPLY", share, 0.0)                     # input 1: I - 1
        gain = op("ADD", gain, dev.outputs[0]).outputs[0]
        total = op("ADD", total, share).outputs[0]
        near = op("DIVIDE", GLOW ** 2, op("ADD", d2, GLOW ** 2).outputs[0]).outputs[0]
        lit = op("MULTIPLY", near, 1.0)                      # input 1: I
        glow = op("ADD", glow, lit.outputs[0]).outputs[0]
        handles.append((at, dev, lit))
    if handles:
        gain = op("ADD", 1.0, op("DIVIDE", gain, total).outputs[0]).outputs[0]
    else:
        gain = 1.0
    for name, v in (("Gain", gain), ("Glow", glow)):
        if isinstance(v, float):
            c = N.new("ShaderNodeValue")
            c.outputs[0].default_value = v
            v = c.outputs[0]
        L.new(v, out.inputs[name])
    return g, handles


def material(name, image):
    """An image as emission; src/scenes.py multiplies it by the light."""
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
    if tex.image.depth == 32:                                # a wheel's texture: its alpha is its shape
        tex.image.alpha_mode = "CHANNEL_PACKED"
        mix = N.new("ShaderNodeMixShader")
        L.new(tex.outputs["Alpha"], mix.inputs[0])
        L.new(N.new("ShaderNodeBsdfTransparent").outputs[0], mix.inputs[1])
        L.new(em.outputs[0], mix.inputs[2])
        L.new(mix.outputs[0], N["Material Output"].inputs["Surface"])
    else:
        L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def mesh(name, V, uv, quads, mat):
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
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def bind(ob, rig, w):
    """Vertex groups from weight arrays (32 levels) and an armature modifier."""
    for bone, v in w.items():
        g = ob.vertex_groups.new(name=bone)
        q = np.round(np.clip(v.astype(np.float32), 0, 1) * 32).astype(int)
        for level in np.unique(q[q > 0]):
            g.add(np.nonzero(q == level)[0].tolist(), level / 32, "REPLACE")
    ob.modifiers.new("rig", "ARMATURE").object = rig


def skeleton(a):
    """The element's armature. Every bone's local z points at the camera, so
    a rotation about x nods, about y turns, about z leans or lifts. A bone
    marked `upright` keeps its orientation when its parent rotates; one
    marked `track` points at the named bone."""
    ad = bpy.data.armatures.new("rig_" + a["id"])
    rig = bpy.data.objects.new("rig_" + a["id"], ad)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, tail, parent, opt in a["bones"]:
        b = ad.edit_bones.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        if b.length < 1e-4:
            b.tail = b.head + Vector((0, 0, 0.01))
        b.align_roll(Vector((0, -1, 0)))
        if parent:
            b.parent = ad.edit_bones[parent]
            b.inherit_scale = "NONE"
            b.use_inherit_rotation = not opt.get("upright", False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for name, head, tail, parent, opt in a["bones"]:
        pb = rig.pose.bones[name]
        pb.rotation_mode = "XYZ"
        if opt.get("track"):
            c = pb.constraints.new("DAMPED_TRACK")
            c.target, c.subtarget, c.track_axis = rig, opt["track"], "TRACK_Y"
    return rig


def animate(rig, a):
    """The element's loop: a function of the loop phase 0..1."""
    pb, rad, ph0 = rig.pose.bones, math.radians, a["phase"]
    s = lambda t, o=0.0: math.sin(TAU * (t + ph0 + o))
    ease = lambda t, o=0.0: 0.5 * (1 - math.cos(TAU * (t + ph0 + o)))

    def priest(t):
        pb["root"].rotation_euler = (0, 0, rad(a["sway"]) * s(t))
        pb["spine"].rotation_euler = (0, 0, -0.4 * rad(a["sway"]) * s(t))        # the chest stays more upright
        br = a["breathe"] / 100 * ease(t, 0.1)
        pb["chest"].scale = (1 + 0.5 * br, 1 + br, 1 + 0.5 * br)
        pb["head"].rotation_euler = (rad(a["nod"]) * ease(t, 0.25), rad(a["turn"]) * s(t, 0.15), rad(a["tilt"]) * s(t, 0.4))
        r = rad(a["robe"])                                                       # the robe swings after the body
        pb["robe1"].rotation_euler = (0.5 * r * s(t, -0.10), 0, r * s(t, -0.20))
        pb["robe2"].rotation_euler = (0.5 * r * s(t, -0.22), 0, r * s(t, -0.32))
        for arm in a["arms"]:
            pb["fore_" + arm["tag"]].rotation_euler = (0, 0, arm["sign"] * rad(arm["deg"]) * s(t, 0.2))

    def swing(t):
        pb["swing"].rotation_euler = (0.3 * rad(a["deg"]) * s(t, 0.25), 0, rad(a["deg"]) * s(t))

    def hover(t):
        pb["hover"].location = (0.4 * a["rise"] * math.sin(TAU * (2 * t + ph0)), a["rise"] * s(t), 0)

    def cloth(t):
        for i in range(4):
            pb[f"c{i}"].rotation_euler = (0.7 * rad(a["deg"]) * s(t, -0.07 * i + 0.18), 0, rad(a["deg"]) * s(t, -0.07 * i))

    def spin(t):
        pb["spin"].rotation_euler = (0, rad(a["rock"]) * s(t) if a["rock"] else -TAU * a["turns"] * t, 0)

    return dict(priest=priest, swing=swing, hover=hover, cloth=cloth, spin=spin).get(a["kind"])


def flame_mover(rig, bones, path, static):
    """A flame's loop and its light. path: (FRAMES, 3) wick positions.
    Returns the mover and a function frame -> (position, light)."""
    pa, pb = rig.pose.bones[bones[0]], rig.pose.bones[bones[1]]
    for p in (pa, pb):
        p.rotation_mode = "QUATERNION"
    rest = [rig.data.bones[b].matrix_local.to_quaternion() for b in bones]
    up = Vector((0, 0, 1))
    state = []
    for k in range(FRAMES):
        t = k * air.LOOP / FRAMES
        vel = (path[(k + 1) % FRAMES] - path[(k - 1) % FRAMES]) * FRAMES / (2 * air.LOOP)
        axis, length, light = air.flame(air.draft(path[k], t) + air.gust(path[k], t) - (0 if static else vel))
        state.append((up.rotation_difference(Vector(axis)), length, light))

    def go(ph):
        k = ph * FRAMES
        i, f = int(math.floor(k)) % FRAMES, k - math.floor(k)
        (q0, l0, _), (q1, l1, _) = state[i], state[(i + 1) % FRAMES]
        q, length = q0.slerp(q1, f), l0 + (l1 - l0) * f
        half = Quaternion().slerp(q, 0.5)
        pa.rotation_quaternion = rest[0].inverted() @ half @ rest[0]             # the tip leans further than the base
        pb.rotation_quaternion = rest[1].inverted() @ half @ rest[1]
        thin = 1 / math.sqrt(length)                                             # a stretched flame is thinner
        pa.scale = pb.scale = (thin, length, thin)

    return go, lambda k: (path[k % FRAMES], state[k % FRAMES][2])


def build(name, movers, plate):
    """All actors of scene `name`; appends their loops to `movers`. `plate`
    is the texture of the actors. Returns the candle-light node group."""
    d = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_actors.npz"))
    meta = json.loads(str(d["meta"]))
    seg = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_seg.npz"))
    flames = json.loads(str(seg["flames"])) if "flames" in seg.files else []
    rigs, local = {}, []
    for a in meta:
        if "parent" in a:                                    # carried things and their flames: bones of the priest
            continue
        rigs[a["id"]] = skeleton(a)
        mv = animate(rigs[a["id"]], a)
        if mv:
            local.append(mv)
    # where every carried candle's wick is through the loop
    carried = [(dict(id=a["id"], bones=a["names"]), rigs[a["parent"]]) for a in meta if a["kind"] == "flame" and "parent" in a]
    paths = {fl["id"]: np.zeros((FRAMES, 3)) for fl, _ in carried}
    tips = {}
    for k in range(FRAMES if carried else 0):
        for mv in local:
            mv(k / FRAMES)
        bpy.context.view_layer.update()
        for fl, rig in carried:
            paths[fl["id"]][k] = rig.matrix_world @ rig.pose.bones[fl["bones"][0]].head
            if k == 0:
                tips[fl["id"]] = np.array(rig.matrix_world @ rig.pose.bones[fl["bones"][1]].tail) - paths[fl["id"]][0]
    lights = []
    for fl, rig in carried:
        mv, light = flame_mover(rig, fl["bones"], paths[fl["id"]], False)
        local.append(mv)
        lights.append(light)
    for a in meta:
        if a["kind"] == "flame" and "parent" not in a:
            head = np.array(a["bones"][0][1])
            paths[a["id"]] = np.repeat(head[None], FRAMES, 0)
            tips[a["id"]] = np.array(a["bones"][1][2]) - head
            mv, light = flame_mover(rigs[a["id"]], ("fa", "fb"), paths[a["id"]], True)
            local.append(mv)
            lights.append(light)
    for fl in flames:                                        # flames too small for a mesh still give light
        if fl["id"] not in paths and "world" in fl:
            p = np.array(fl["world"])
            lights.append(lambda k, p=p: (p, air.flame(air.draft(p, k * air.LOOP / FRAMES) + air.gust(p, k * air.LOOP / FRAMES))[2]))
    lights = lights[:MAX_LIGHTS]
    group, handles = light_group(len(lights))

    def shine(ph):
        k = int(round(ph * FRAMES)) % FRAMES
        for (at, dev, lit), light in zip(handles, lights):
            p, I = light(k)
            for i in range(3):
                at.inputs[i].default_value = float(p[i])
            dev.inputs[1].default_value = I - 1
            lit.inputs[1].default_value = I

    movers += local + [shine]
    mat, lit = material("actors", plate), None
    for a in meta:
        k = a["id"]
        if a["kind"] == "flame":                             # flames: the plate with an alpha that keeps flame only
            m = lit = lit or material("flames", a["texture"])
        else:
            m = material("wheel_" + k, a["texture"]) if a["kind"] == "spin" else mat
        ob = mesh(a["kind"] + "_" + k, d[k + "/V"], d[k + "/uv"], d[k + "/q"], m)
        pre = k + "/w/"
        bind(ob, rigs[a.get("parent", k)], {f[len(pre):]: d[f] for f in d.files if f.startswith(pre)})
    # the smoke sources of the motion map, for src/smoke.py
    src = []
    for el in json.loads(str(d["sources"])):
        if el.get("of"):
            fid = next(a["id"] for a in meta if a["kind"] == "flame" and a.get("owner") == el["of"])
            src.append(dict(id=el["id"], path=(paths[fid] + tips[fid]).tolist()))
        else:
            src.append(dict(id=el["id"], path=[el["world"]] * FRAMES))
    json.dump(src, open(os.path.join(ROOT, "wip", "scene3d", name + "_sources.json"), "w"))
    print("ACTORS", name, len(rigs), "rigs,", len(lights), "flames give light,", len(src), "smoke sources", flush=True)
    return group
