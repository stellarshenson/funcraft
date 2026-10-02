"""A servo-skull that floats in a plate scene: the downloaded model
(src/models.py, "servo_skull": 117 loose pieces), painted by piece, lit by
lights of its own, and moved a little.

Paint. The model has no colours. Each loose piece gets a material by what
it is, found from its shape:

    bone      the piece with the most vertices: the skull itself; and
              the small pieces low at the front: its teeth
    rubber    a tube: its volume over its surface is under 3 % of its
              length (the cables, the ribbed hose)
    brass     the fittings on the face, and every small fitting
    iron      the rest: the housing at the back, the antennas

Every material is old: grime in a slow noise, darker and rougher there.
The eye: the piece that reaches furthest forward is the ocular, a tube. A
disc that only emits is set inside its mouth: saturated red, brightest in
a core of a quarter of its radius, falling to dark red at the rim. It
reflects nothing: a lit, glossy disc came out pale orange.

Light. A plate scene has no lights: plate and actors emit their picture.
The skull is a real surface, so it gets a warm light where the scene has
one (a lantern), a cold rim light from behind, and a weak light from all
round. Lights do not change emitting surfaces, so the plate stays as it is.
The emitting plate would light the skull too, but as a large patterned
light of a million triangles it takes nearly every light sample, and the
skull comes out speckled at 64 samples. Plate, actors and smoke are
therefore hidden from the skull's diffuse and glossy rays, cast no shadow,
and their materials are left out of the light sampling.

Motion. It rises and sinks once per loop, drifts sideways and turns its
head a few degrees: whole cycles, so the loop closes.
"""
import bpy, bmesh, math
import numpy as np
import models

BONE, RUBBER, BRASS, IRON = range(4)


def classify(pieces):
    """The class of each piece (a list of objects, model 1 unit tall, facing
    +Y), and the centre and radius of the ocular's mouth."""
    stats = []
    for ob in pieces:
        co = models._co(ob)
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        vol, area = abs(bm.calc_volume()), sum(f.calc_area() for f in bm.faces)
        bm.free()
        stats.append((len(co), co.min(0), co.max(0), vol / max(area, 1e-9)))
    skull = int(np.argmax([s[0] for s in stats]))
    cls = []
    for k, (n, lo, hi, thick) in enumerate(stats):
        size, mid = hi - lo, (lo + hi) / 2
        if k == skull or (mid[2] < 0.14 and mid[1] > 0.1):
            cls.append(BONE)
        elif thick < 0.03 * float(np.linalg.norm(size)):
            cls.append(RUBBER)
        elif mid[1] > 0.0 or n < 600:
            cls.append(BRASS)
        else:
            cls.append(IRON)
    front = max((k for k in range(len(pieces)) if k != skull), key=lambda k: stats[k][2][1])
    co = models._co(pieces[front])
    rim = co[co[:, 1] > co[:, 1].max() - 0.03]
    return cls, rim.mean(0), 0.5 * float(np.ptp(rim[:, 0]))


def aged(name, colour, metallic, rough, grime=0.5, emit=0.0):
    """A material with grime in a slow noise: darker and rougher there."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    b = N["Principled BSDF"]
    noise = N.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.5
    noise.inputs["Detail"].default_value = 3.0
    L.new(N.new("ShaderNodeTexCoord").outputs["Object"], noise.inputs["Vector"])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position, ramp.color_ramp.elements[1].position = 0.3, 0.75
    L.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    mix = N.new("ShaderNodeMixRGB")
    mix.inputs["Color1"].default_value = tuple(c * (1 - grime) for c in colour) + (1,)
    mix.inputs["Color2"].default_value = tuple(colour) + (1,)
    L.new(ramp.outputs["Color"], mix.inputs["Fac"])
    L.new(mix.outputs["Color"], b.inputs["Base Color"])
    r = N.new("ShaderNodeMapRange")
    r.inputs["To Min"].default_value, r.inputs["To Max"].default_value = min(rough + 0.3, 1.0), rough
    L.new(ramp.outputs["Color"], r.inputs["Value"])
    L.new(r.outputs["Result"], b.inputs["Roughness"])
    b.inputs["Metallic"].default_value = metallic
    if emit:
        b.inputs["Emission Color"].default_value = tuple(colour) + (1,)
        b.inputs["Emission Strength"].default_value = emit
    return m


def ember(radius):
    """The eye's material for a disc of `radius` in its own coordinates:
    red light only, 3 times full red out to a quarter of the radius,
    falling to an eighth of full red at 0.9 of the radius."""
    m = bpy.data.materials.new("skull_eye")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    flat = N.new("ShaderNodeVectorMath")             # distance from the disc's axis
    flat.operation = "MULTIPLY"
    flat.inputs[1].default_value = (1, 0, 1)
    L.new(N.new("ShaderNodeTexCoord").outputs["Object"], flat.inputs[0])
    dist = N.new("ShaderNodeVectorMath")
    dist.operation = "LENGTH"
    L.new(flat.outputs["Vector"], dist.inputs[0])
    power = N.new("ShaderNodeMapRange")
    power.inputs["From Min"].default_value, power.inputs["From Max"].default_value = 0.25 * radius, 0.9 * radius
    power.inputs["To Min"].default_value, power.inputs["To Max"].default_value = 3.0, 0.12
    L.new(dist.outputs["Value"], power.inputs["Value"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.015, 0.008, 1)
    L.new(power.outputs["Result"], em.inputs["Strength"])
    L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def build(at, height, yaw, movers, key, rim):
    """The skull at world point `at`, `height` metres tall, its face turned
    `yaw` degrees from the camera (positive: to the camera's right). key and
    rim: (position, colour, watts) of the warm light and of the cold light
    behind it."""
    for ob in bpy.data.objects:                      # what emits its picture neither lights nor shades the skull
        if ob.type in ("MESH", "VOLUME"):
            ob.visible_shadow = ob.visible_diffuse = ob.visible_glossy = False
    for m in bpy.data.materials:
        m.cycles.emission_sampling = "NONE"
    ob = models.load("servo_skull", 1.0)
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.separate(type="LOOSE")
    bpy.ops.object.mode_set(mode="OBJECT")
    pieces = list(bpy.context.selected_objects)
    mats = [aged("skull_bone", (0.62, 0.52, 0.36), 0.0, 0.55, 0.4), aged("skull_rubber", (0.03, 0.027, 0.025), 0.0, 0.55, 0.3),
            aged("skull_brass", (0.78, 0.55, 0.22), 1.0, 0.3, 0.45),
            aged("skull_iron", (0.22, 0.22, 0.24), 1.0, 0.4, 0.4)]
    cls, mouth, radius = classify(pieces)
    for p, c in zip(pieces, cls):
        p.data.materials.clear()
        p.data.materials.append(mats[c])
    bpy.ops.object.select_all(action="DESELECT")
    for p in pieces:
        p.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    skull = bpy.context.view_layer.objects.active
    skull.name = "servo_skull"
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(35))
    piv = bpy.data.objects.new("servo_skull_pivot", None)
    bpy.context.collection.objects.link(piv)
    skull.parent = piv
    skull.scale = (height,) * 3
    skull.location = (0, 0, -height / 2)             # the pivot at the skull's middle
    x, y, z = at
    turn = math.pi + math.radians(yaw)               # the model faces +Y; the camera looks along +Y
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.8 * radius, segments=24, ring_count=12,
                                         location=(float(mouth[0]), float(mouth[1]) - 0.04, float(mouth[2])))
    eye = bpy.context.object                         # the glow in the ocular, in the model's coordinates
    eye.scale = (1, 0.25, 1)
    eye.parent = skull
    eye.data.materials.append(ember(0.8 * radius))

    def hover(ph):
        a = 2 * math.pi * ph
        piv.location = (x + 0.008 * math.sin(a + 1.0), y, z + 0.012 * math.sin(a))
        piv.rotation_euler = (math.radians(4) * math.sin(a + 0.6), 0, turn + math.radians(5) * math.sin(a + 2.0))

    movers.append(hover)
    for name, (pos, colour, watts), size in (("skull_key", key, 0.05), ("skull_rim", rim, 0.15)):
        lamp = bpy.data.lights.new(name, "POINT")
        lamp.color, lamp.energy, lamp.shadow_soft_size = colour, watts, size
        lo = bpy.data.objects.new(name, lamp)
        lo.location = pos
        bpy.context.collection.objects.link(lo)
    return piv
