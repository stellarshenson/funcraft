"""Blender side of the actors (src/actors.py): builds every priest's mesh
and armature from wip/scene3d/<name>_actors.npz, binds the mesh and the things
the priest carries to the bones, and returns each priest's loop as a
function of the loop phase.
"""
import bpy, json, math, os
import numpy as np
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 2 * math.pi


def material(plate):
    m = bpy.data.materials.new("actors")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    tex = N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(plate)
    tex.interpolation = "Cubic"
    em = N.new("ShaderNodeEmission")
    L.new(tex.outputs["Color"], em.inputs["Color"])
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
    """The priest's armature. Every bone's local z points at the camera, so
    a rotation about x nods, about y turns, about z leans or lifts."""
    ad = bpy.data.armatures.new("rig_" + a["id"])
    rig = bpy.data.objects.new("rig_" + a["id"], ad)
    bpy.context.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for name, head, tail, parent in a["bones"]:
        b = ad.edit_bones.new(name)
        b.head, b.tail = Vector(head), Vector(tail)
        b.align_roll(Vector((0, -1, 0)))
        if parent:
            b.parent = ad.edit_bones[parent]
            b.inherit_scale = "NONE"
    bpy.ops.object.mode_set(mode="OBJECT")
    for pb in rig.pose.bones:
        pb.rotation_mode = "XYZ"
    return rig


def animate(rig, a):
    """The priest's loop: a function of the loop phase 0..1."""
    pb, rad = rig.pose.bones, math.radians

    def go(ph):
        t = ph + a["phase"]
        s = lambda o=0.0: math.sin(TAU * (t + o))
        ease = lambda o=0.0: 0.5 * (1 - math.cos(TAU * (t + o)))
        pb["root"].rotation_euler = (0, 0, rad(a["sway"]) * s())
        pb["spine"].rotation_euler = (0, 0, -0.4 * rad(a["sway"]) * s())      # the chest stays more upright
        br = a["breathe"] / 100 * ease(0.1)
        pb["chest"].scale = (1 + 0.5 * br, 1 + br, 1 + 0.5 * br)
        pb["head"].rotation_euler = (rad(a["nod"]) * ease(0.25), rad(a["turn"]) * s(0.15), rad(a["tilt"]) * s(0.4))
        for arm in a["arms"]:
            pb["fore_" + arm["tag"]].rotation_euler = (0, 0, arm["sign"] * rad(arm["deg"]) * s(0.2))
    return go


def build(name, movers):
    """All actors of scene `name`; appends their loops to `movers`.
    Returns one actor object (all share one material)."""
    d = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_actors.npz"))
    meta = json.loads(str(d["meta"]))
    mat = material(os.path.join(ROOT, "wip", "scene3d", name + ".png"))
    rigs, first = {}, None
    for a in meta:
        k = a["id"]
        ob = mesh(a["kind"] + "_" + k, d[k + "/V"], d[k + "/uv"], d[k + "/q"], mat)
        if a["kind"] == "priest":
            rigs[k] = skeleton(a)
            pre = k + "/w/"
            bind(ob, rigs[k], {f[len(pre):]: d[f] for f in d.files if f.startswith(pre)})
            movers.append(animate(rigs[k], a))
            first = first or ob
        else:
            bind(ob, rigs[a["parent"]], {a["bone"]: np.ones(len(d[k + "/V"]), np.float32)})
    print("ACTORS", name, len(rigs), "rigs", flush=True)
    return first
