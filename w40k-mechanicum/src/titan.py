"""The Warhound Titan of the saint scene (src/warhound.py builds it), standing on the floor of the corridor that
src/saintcorridor.py makes in the plate's 3D scene.

The camera of the plate looks level enough that the floor of the corridor, below the eye, is seen from above. The
titan leans as the column and the frame beside the opening lean in the picture (`lean`, degrees, its top towards the
image's left), stands on a stone floor through its feet, faces the saint on the image's left, turned `turn` degrees
towards the camera. It is placed by its head: the whole head comes out of the corridor's mouth, in front of the
column and left of the frame, and the guns hang lowered from the shoulders so that they stay behind the walls; mainly
its head shows (src/warhound/fit.py measures what the plate hides, src/warhound/plan.py draws the scene from above).
It is lit by a warm
light from the chapel's side and a weak cold light from behind; plate, actors and smoke neither light it nor shade it
(as for the servo-skull, src/servoskull.py). It is never still: over the loop the torso sways, the head looks round
and the guns shift, each a whole number of cycles so the loop closes; the legs stand.
"""
import bpy, bmesh, math, os, json
from mathutils import Matrix, Vector
import warhound

FRAMES = int(os.environ.get("LOOP_FRAMES", 80))      # as src/scenes.py
# the smoke round the titan (src/titansmoke.py simulates it): where each source is on its part, kit mm (None: the
# middle of the part), and the file of their paths over the loop in metres of the scene
VENTS = {"t1": ("head", (warhound.MID - 7.6, -13.0, 47.6)), "t2": ("head", (warhound.MID + 7.6, -13.0, 47.6)),
         "t3": ("waist", None)}
SOURCES = os.path.join(warhound.ROOT, "wip", "scene3d", "saint_titan_sources.json")


def spot(name, at, target, colour, watts, cone, soft=1.0):
    lamp = bpy.data.lights.new(name, "SPOT")
    lamp.color, lamp.energy, lamp.spot_size, lamp.shadow_soft_size = colour, watts, math.radians(cone), soft
    lamp.spot_blend = 0.6
    ob = bpy.data.objects.new(name, lamp)
    ob.location = at
    ob.rotation_euler = (Vector(target) - Vector(at)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.collection.objects.link(ob)
    return ob


def stone(name, colour, rough, scale):
    """Dark flagstones: courses of slabs in object coordinates, the seams as a bump, grime in a slow noise."""
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


# the hot air over each grille of the head: index of refraction, ripples per kit mm, rise in m/s, crossfades of the
# rising ripples per loop; the box of air in the head's kit mm: distance out from the head's middle plane, up, along
SHIMMER = (1.03, 0.6, 0.5, 4)
SLAB = ((7.4, 9.0), (-16.6, 4.0), (44.5, 51.0))         # the head reaches 7.17 mm out from its middle plane


def shimmer(head, k):
    """Hot air rising from the grilles on both sides of the head: a box of air per grille, carried by the head, that
    bends the light through it by ripples rising with the air. Its index of refraction is a little above one, and the
    ripples fade out towards the box's sides and top, so the box itself never shows; only what lies behind it wavers.
    k: the titan's scale. Returns the material, its Value node `phase` to be set every frame."""
    m = bpy.data.materials.new("heat")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)

    def op(kind, a, z=0.0):
        n = N.new("ShaderNodeMath")
        n.operation = kind
        for i, x in enumerate((a, z)):
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def ramp(x, lo, hi):
        n = N.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        L.new(x, n.inputs["Value"])
        n.inputs["From Min"].default_value, n.inputs["From Max"].default_value = lo, hi
        return n.outputs["Result"]

    co = N.new("ShaderNodeTexCoord")
    box = N.new("ShaderNodeSeparateXYZ")
    L.new(co.outputs["Generated"], box.inputs[0])
    ph = N.new("ShaderNodeValue")
    ph.name = "phase"
    ior, ripples, rise, fades = SHIMMER
    lift = rise * 4.0 / fades / (warhound.SCALE * k)       # kit mm the air rises in one crossfade (the loop is 4 s)
    layers = []
    for j in (0, 1):                                       # two layers of ripples, each restarting while unseen
        t = op("FRACT", op("ADD", op("MULTIPLY", ph.outputs[0], fades), 0.5 * j))
        at = N.new("ShaderNodeVectorMath")
        at.operation = "MULTIPLY_ADD"
        L.new(op("MULTIPLY", t, -lift), at.inputs[1])
        at.inputs[0].default_value = (0.0, 1.0, 0.0)       # the head's kit +y is up
        L.new(co.outputs["Object"], at.inputs[2])
        shift = N.new("ShaderNodeVectorMath")
        shift.operation = "ADD"
        L.new(at.outputs[0], shift.inputs[0])
        shift.inputs[1].default_value = (17.3 * j, 5.1 * j, 9.7 * j)
        n = N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value, n.inputs["Detail"].default_value = ripples, 0.0
        L.new(shift.outputs[0], n.inputs["Vector"])
        layers.append((n.outputs["Fac"], op("SUBTRACT", 1.0, op("ABSOLUTE", op("SUBTRACT", op("MULTIPLY", t, 2.0), 1.0)))))
    (n0, w0), (n1, _) = layers
    wave = op("ADD", op("MULTIPLY", n0, w0), op("MULTIPLY", n1, op("SUBTRACT", 1.0, w0)))
    fade = op("MULTIPLY", op("MULTIPLY", ramp(box.outputs["Y"], 0.0, 0.15), op("SUBTRACT", 1.0, ramp(box.outputs["Y"], 0.4, 1.0))),
              op("MULTIPLY", ramp(box.outputs["Z"], 0.0, 0.25), op("SUBTRACT", 1.0, ramp(box.outputs["Z"], 0.75, 1.0))))
    bump = N.new("ShaderNodeBump")
    bump.inputs["Distance"].default_value = 0.02
    L.new(op("MULTIPLY", wave, fade), bump.inputs["Height"])
    rf = N.new("ShaderNodeBsdfRefraction")
    rf.inputs["IOR"].default_value, rf.inputs["Roughness"].default_value = ior, 0.0
    L.new(bump.outputs["Normal"], rf.inputs["Normal"])
    L.new(rf.outputs[0], N["Material Output"].inputs["Surface"])
    (x0, x1), (y0, y1), (z0, z1) = SLAB
    for side in (1, -1):
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        lo = warhound.MID + x0 if side > 0 else warhound.MID - x1   # no mirroring: the faces keep pointing out
        for v in bm.verts:
            v.co = Vector((lo + (v.co.x + 0.5) * (x1 - x0), y0 + (v.co.y + 0.5) * (y1 - y0), z0 + (v.co.z + 0.5) * (z1 - z0)))
        me = bpy.data.meshes.new("heat")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(m)
        ob = bpy.data.objects.new("heat", me)
        bpy.context.collection.objects.link(ob)
        ob.parent = head
        ob.visible_shadow = ob.visible_diffuse = ob.visible_glossy = False   # only the camera looks through it:
    bpy.context.scene.cycles.caustics_refractive = False                      # no light focused by it onto the titan
    return ph


def build(conf, K, size, movers):
    """conf: head (plate column, row, depth in metres: where the middle of its head is), scale (of the 16 m model),
    lean and turn (degrees), floor (metres before the feet and to each side; it reaches the corridor's far end), pose
    (keys of warhound.POSE), idle (amplitudes in degrees: torso turn and lean, head turn and nod, guns), key and rim
    ((right, forward, up) from the titan's middle in metres of the 16 m model, colour, watts at that size, cone)."""
    import saintcorridor
    for ob in bpy.data.objects:                      # what emits its picture neither lights nor shades the titan
        if ob.type in ("MESH", "VOLUME"):
            ob.visible_shadow = ob.visible_diffuse = ob.visible_glossy = False
    for m in bpy.data.materials:
        m.cycles.emission_sampling = "NONE"
    W, H = size
    px, row, D = conf["head"]
    target = Vector((((px + 0.5) / W - K[0, 2]) / K[0, 0] * D, D, -((row + 0.5) / H - K[1, 2]) / K[1, 1] * D))
    k = conf["scale"]
    a = math.radians(conf["lean"])
    up = Vector((-math.sin(a), 0, math.cos(a)))
    t = math.radians(conf["turn"])
    front = Vector((-math.cos(t), -math.sin(t), 0))
    front = (front - up * front.dot(up)).normalized()
    side = front.cross(up)                           # the model's +x: its left
    R = Matrix((side, -front, up)).transposed()      # columns: where the model's x, y and z go; the model faces -y
    pose = {**warhound.POSE, **conf["pose"]}
    root, obs, place = warhound.model(pose)
    root.matrix_world = R.to_4x4() @ Matrix.Scale(k, 4)
    bpy.context.view_layer.update()
    head = next(o for o in obs if o.name == "head")
    pts = [head.matrix_world @ Vector(c) for c in head.bound_box]
    centre = sum(pts, Vector()) / 8
    root.matrix_world = Matrix.Translation(target - centre) @ root.matrix_world
    bpy.context.view_layer.update()
    feet = root.matrix_world.translation
    # the floor: a slab through the feet, square to the titan's vertical, from before the feet to the corridor's end
    near, wide = conf["floor"]
    far = saintcorridor.BACK - feet.y
    across = up.cross(Vector((0, 1, 0))).normalized()
    along = across.cross(up)
    bm = bmesh.new()
    corners = [feet + across * sx * wide + along * sy for sx, sy in ((-1, -near), (1, -near), (1, far), (-1, far))]
    bm.faces.new([bm.verts.new(c) for c in corners])
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=8, use_grid_fill=True)
    me = bpy.data.meshes.new("corridor_floor")
    bm.to_mesh(me)
    bm.free()
    fl = bpy.data.objects.new("corridor_floor", me)
    bpy.context.collection.objects.link(fl)
    me.materials.append(stone("corridor_floor", (0.05, 0.045, 0.04), 0.55, 0.12 / k))
    middle = feet + up * 8.0 * k
    for name in ("key", "rim"):
        (r, f, h), colour, watts, cone = conf[name]
        at = middle + (Vector((1, 0, 0)) * r + up.cross(Vector((1, 0, 0))).normalized() * f + up * h) * k
        spot("titan_" + name, at, middle, colour, watts * k * k, cone)
    ty, tp, hy, hp, g = conf["idle"]

    def idle(ph):
        c = 2 * math.pi * ph
        place({**pose, "torso": (pose["torso"][0] + ty * math.sin(c), pose["torso"][1] + tp * math.sin(2 * c + 0.7)),
               "head": (pose["head"][0] + hy * math.sin(c + 1.9), pose["head"][1] + hp * math.sin(c + 0.3)),
               "guns": {"right": pose["guns"]["right"] + g * math.sin(c + 0.4), "left": pose["guns"]["left"] - g * math.sin(c + 1.3)}})

    movers.append(idle)
    clocks = [shimmer(head, k)] + [m.node_tree.nodes["phase"] for m in bpy.data.materials if m.name.startswith("wh_grille")]
    movers.append(lambda ph: [setattr(c.outputs[0], "default_value", ph) for c in clocks])
    paths = {sid: [] for sid in VENTS}                 # the smoke sources, carried by their parts through the loop
    for i in range(FRAMES):
        idle(i / FRAMES)
        bpy.context.view_layer.update()
        for sid, (part, at) in VENTS.items():
            o = next(o for o in obs if o.name == part)
            local = Vector(at) if at else sum((Vector(c) for c in o.bound_box), Vector()) / 8
            paths[sid].append(list(o.matrix_world @ local))
    idle(0.0)
    json.dump([dict(id=sid, path=p) for sid, p in paths.items()], open(SOURCES, "w"))
    print("TITAN head", [round(c, 2) for c in target], "feet", [round(c, 2) for c in feet], "scale", k, "up", [round(c, 3) for c in up], "front", [round(c, 3) for c in front], flush=True)
    return root
