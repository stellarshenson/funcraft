"""Put an SVG logo on a wall as a lit sign. Blender 4.5.

Blender's SVG importer reads a fill colour only from a `style` attribute. The
Stellars Tech logo sets most of its fills with `fill=` attributes, which the
importer drops, importing those paths black. The colours are therefore read
from the SVG here and applied by path id.

The paths overlap - highlights sit on top of the shapes beneath them - so each
is lifted a hair off the one before it, in document order, or they flicker.
"""

import bpy, re, math, addon_utils
import xml.etree.ElementTree as ET
from mathutils import Vector, Euler


def _fills(svg):
    """Path id → fill colour in #rrggbb, inheriting from enclosing groups,
    in document order."""
    out = {}

    def walk(e, inherited):
        m = re.search(r"fill:(#[0-9a-fA-F]{6})", e.get("style") or "")
        fill = e.get("fill") or (m.group(1) if m else None) or inherited
        if e.tag.endswith("}path"):
            out[e.get("id")] = fill
        for c in e:
            walk(c, fill)

    walk(ET.parse(svg).getroot(), None)
    return out


def _linear(hexcol):
    c = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _emissive(name, colour, strength):
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
    return m


def sign(svg, centre, width, glow=1.3, margin=0.08, depth=0.3):
    """Mount `svg` on a dark panel, `width` units wide, centred on `centre`.

    The sign faces +Y, towards the banner camera, which looks down -Y with the
    world's +X on the left of the image - so the logo is also turned 180 degrees
    about Z to read left to right. `centre` is on the wall's surface.
    """
    addon_utils.enable("io_curve_svg", default_set=True)
    before = set(bpy.data.objects)
    bpy.ops.import_curve.svg(filepath=svg)
    parts = [o for o in bpy.data.objects if o not in before]
    fills = _fills(svg)
    order = list(fills)

    lo = [min((o.matrix_world @ Vector(c))[i] for o in parts for c in o.bound_box) for i in range(2)]
    hi = [max((o.matrix_world @ Vector(c))[i] for o in parts for c in o.bound_box) for i in range(2)]
    w0 = hi[0] - lo[0]

    mats = {}
    for o in parts:
        pid = o.name.split(".")[0]
        hexcol = fills.get(pid) or "#ffffff"
        if hexcol not in mats:
            mats[hexcol] = _emissive(f"logo_{hexcol[1:]}", _linear(hexcol), glow)
        o.data.materials.clear()
        o.data.materials.append(mats[hexcol])
        o.location.z += (order.index(pid) if pid in order else 0) * w0 * 2e-4

    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.convert(target="MESH")
    bpy.ops.object.join()
    logo = bpy.context.view_layer.objects.active
    logo.name = "logo"
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    s = width / w0
    h = (hi[1] - lo[1]) * s
    for v in logo.data.vertices:
        v.co = Vector(((v.co.x - (lo[0] + hi[0]) / 2) * s, (v.co.y - (lo[1] + hi[1]) / 2) * s, v.co.z * s))
    logo.rotation_euler = Euler((math.radians(90), 0, math.radians(180)), "XYZ")
    c = Vector(centre)
    logo.location = c + Vector((0, depth + 0.02, 0))

    bpy.ops.mesh.primitive_cube_add(size=1, location=c + Vector((0, depth / 2, 0)))
    panel = bpy.context.object
    panel.name = "logo_panel"
    panel.scale = (width * (1 + 2 * margin), depth, h + width * 2 * margin)
    pm = bpy.data.materials.new("logo_panel")
    pm.use_nodes = True
    b = pm.node_tree.nodes["Principled BSDF"]
    # matte, or it mirrors the front key light and turns pale
    b.inputs["Base Color"].default_value = (0.008, 0.009, 0.011, 1)
    b.inputs["Roughness"].default_value = 0.9
    panel.data.materials.append(pm)
    print(f"LOGO {len(parts)} paths, {width:.1f} x {h:.1f} units, colours {sorted(mats)}")
    return logo
