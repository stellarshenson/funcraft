"""The Warhound Titan of the saint scene, standing in a hall behind the chapel wall (src/warhound.py builds it).

The wall between the black column and the gilded frame of the sun-gear (plate x 1660-1946, measured 10.8-12.4 m
deep) becomes an opening: the backdrop and its fill lose every quad there that lies behind `behind` metres, so the
candlestick before the wall (6.6 m) stays. At the wall's depth the frame shows only 3.7 m of height, so a 16 m titan
stands far back in a hall beyond the opening, where the frame shows it whole: at 56 m the frame is 18.8 m tall.

The hall: a stone floor at the titan's feet, a far wall with tall windows of cold light, two piers, and haze in a
box that reaches below the floor. The titan is lit by a warm light from the chapel's side and a cold light from
behind; plate, actors and smoke neither light it nor shade it (as for the servo-skull, src/servoskull.py).
"""
import bpy, bmesh, math
import numpy as np
from mathutils import Matrix, Vector
import warhound


def cut(obs, mask, step=2):
    """Remove from each grid mesh in `obs` (one vertex per `step` plate pixels) the quads all of whose corners lie in
    `mask` (plate rows, cols)."""
    under = mask[::step, ::step].ravel()
    for ob in obs:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        gone = [f for f in bm.faces if all(under[v.index] for v in f.verts)]
        bmesh.ops.delete(bm, geom=gone, context="FACES_ONLY")
        bm.to_mesh(ob.data)
        bm.free()
        print("OPENING", ob.name, len(gone), "quads removed", flush=True)


def box(name, lo, hi, mat):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector([l + (h - l) * (c + 0.5) for l, h, c in zip(lo, hi, v.co)])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    me.materials.append(mat)
    return ob


def stone(name, colour, rough, scale):
    """Dark masonry: courses of blocks in world coordinates, the seams as a bump, grime in a slow noise."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    co = N.new("ShaderNodeTexCoord").outputs["Object"]
    brick = N.new("ShaderNodeTexBrick")
    brick.inputs["Scale"].default_value = scale
    brick.inputs["Color1"].default_value = (*colour, 1)
    brick.inputs["Color2"].default_value = (*[c * 0.7 for c in colour], 1)
    brick.inputs["Mortar"].default_value = (*[c * 0.4 for c in colour], 1)
    brick.inputs["Mortar Size"].default_value = 0.01
    L.new(co, brick.inputs["Vector"])
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.08
    L.new(co, noise.inputs["Vector"])
    mix = N.new("ShaderNodeMixRGB")
    mix.blend_type = "MULTIPLY"
    mix.inputs["Fac"].default_value = 0.6
    L.new(brick.outputs["Color"], mix.inputs["Color1"])
    L.new(noise.outputs["Color"], mix.inputs["Color2"])
    L.new(mix.outputs["Color"], b.inputs["Base Color"])
    bump = N.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.4
    L.new(brick.outputs["Fac"], bump.inputs["Height"])
    L.new(bump.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    return m


def glow(name, colour, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Color"].default_value = (*colour, 1)
    b.inputs["Emission Strength"].default_value = strength
    return m


def spot(name, at, target, colour, watts, cone, soft=1.0):
    lamp = bpy.data.lights.new(name, "SPOT")
    lamp.color, lamp.energy, lamp.spot_size, lamp.shadow_soft_size = colour, watts, math.radians(cone), soft
    lamp.spot_blend = 0.6
    ob = bpy.data.objects.new(name, lamp)
    ob.location = at
    ob.rotation_euler = (Vector(target) - Vector(at)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(ob)
    return ob


def build(conf, depth, K, back, fill):
    """The opening, the hall and the titan. conf: opening (x0, x1) plate columns, behind (metres), depth of the titan
    (metres), feet (its soles' height, metres), yaw (degrees, 0 = facing image left), key and rim (position, colour,
    watts), haze (density)."""
    H, W = depth.shape
    x0, x1 = conf["opening"]
    mask = np.zeros((H, W), bool)
    mask[:, x0:x1] = True
    cut((back, fill), mask & (depth > conf["behind"]))
    for ob in bpy.data.objects:                      # what emits its picture neither lights nor shades the titan
        if ob.type in ("MESH", "VOLUME"):
            ob.visible_shadow = ob.visible_diffuse = ob.visible_glossy = False
    for m in bpy.data.materials:
        m.cycles.emission_sampling = "NONE"
    D, F = conf["depth"], conf["feet"]
    cx = ((x0 + x1) / 2 / W - K[0, 2]) / K[0, 0] * D            # the middle of the opening at the titan's depth
    floor = stone("hall_floor", (0.05, 0.045, 0.04), 0.45, 0.06)
    wall = stone("hall_wall", (0.04, 0.036, 0.032), 0.8, 0.05)
    box("hall_floor", (cx - 40, 13.0, F - 1.0), (cx + 50, D + 70, F), floor)
    box("hall_back", (cx - 40, D + 70, F), (cx + 50, D + 72, F + 70), wall)
    for k, dx in enumerate(conf.get("piers", ())):
        box(f"hall_pier_{k}", (cx + dx[0] - 2, D + dx[1] - 2, F), (cx + dx[0] + 2, D + dx[1] + 2, F + 70), wall)
    lit = glow("hall_window", (0.55, 0.68, 1.0), conf.get("windows", 3.0))
    for k, dx in enumerate((-12, 0, 12)):
        box(f"hall_window_{k}", (cx + dx - 1.6, D + 69.8, F + 14), (cx + dx + 1.6, D + 70, F + 44), lit)
    haze = bpy.data.materials.new("hall_haze")
    haze.use_nodes = True
    N = haze.node_tree.nodes
    N.remove(N["Principled BSDF"])
    sc = N.new("ShaderNodeVolumeScatter")
    sc.inputs["Density"].default_value, sc.inputs["Anisotropy"].default_value = conf["haze"], 0.45
    haze.node_tree.links.new(sc.outputs[0], N["Material Output"].inputs["Volume"])
    box("hall_haze", (cx - 39, 13.5, F - 3.0), (cx + 49, D + 69, F + 68), haze)
    root, obs = warhound.model()
    root.location = (cx + conf.get("shift", 0.0), D, F)
    root.rotation_euler = (0, 0, math.radians(-90 + conf.get("yaw", 0.0)))
    for name, (at, colour, watts, cone) in (("hall_key", conf["key"]), ("hall_rim", conf["rim"])):
        spot(name, (cx + at[0], D + at[1], F + at[2]), (cx, D, F + 8), colour, watts, cone)
    print("TITAN at", round(cx, 2), D, F, flush=True)
    return root
