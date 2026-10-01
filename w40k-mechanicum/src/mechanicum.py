"""Machine cathedral: a behemoth altar-mainframe calculating, attended by holy
GPUs. Blender 4.5, Cycles. 19:6, exact loop.

Run (after src/emblem.py and src/textures.py):
    blender -b -P src/mechanicum.py [-- out=DIR] [frame numbers]

Renders wip/frames/f000.png .. f039.png, plus the frame at phase 1.0 as
seam-check.png, which must match f000.png.

The look follows references/: a gothic nave of detailed walls with stained
glass, red banners, candles and incense haze, and at its end a towering
altar-machine - racks of cards, a crowned skull in a sunburst, the Sacred
A5000 enshrined at its heart. Everything that moves is a function of `phase`
in [0, 1) and completes whole cycles per loop; the compute lights and the
altar screen change state every TICK frames, and FRAMES is a multiple of TICK.
"""

import bpy, bmesh, math, os, sys
from mathutils import Vector, Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit as K
import models as Mo
import paintfig as PF
from kit import box, cyl, sphere, torus, arch, gear, curve, empty, link, Graph, pbr, lamp, MOVERS, CLOCKS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = os.path.join(ROOT, "resources", "assets")
FRAMES = 40
TICK = 4                        # frames per state of the compute lights and the screen
TICKS = FRAMES // TICK
RES_X, RES_Y = 1520, 480        # 19:6
SAMPLES = 128

ALTAR_Y = -42.0                 # front of the altar table
ALTAR_SCALE = 1.25
WALL_X = 15.0                   # inner face of the side walls
STOREY = 11.0                   # height of one wall piece
MAT = {}

# the close-up camera: position, aim, lens, focus point, aperture
RELIC = (0, ALTAR_Y + ALTAR_SCALE * (0.9 - 3.5), ALTAR_SCALE * 6.4)
OFFERING = (2.4, -36.9)                        # where the shock priest holds up a card
# close-up shots: camera position, aim, lens, focus point, aperture
SHOTS = {
    # the references' composition: a priest holds a card up to the altar-machine
    "offering": dict(at=(4.9, -31.6, 1.5), look=(-0.6, -44.0, 4.2), lens=16, focus=(2.35, -37.2, 1.9), fstop=5.6),
    # low beside a servitor bowed in profile before the altar, the relic above
    "altar": dict(at=(2.75, -34.9, 1.1), look=(-0.6, -45.0, 5.6), lens=18, focus=(2.9, -36.6, 1.8), fstop=4.0),
    # low among the kneeling congregation, looking up at the whole altar-machine
    "looming": dict(at=(1.3, -29.5, 0.9), look=(-0.2, -44.0, 9.5), lens=14, focus=RELIC, fstop=8.0),
}
SERVITOR = (2.9, -36.6)                        # the servitor close to the camera in the altar shot
SHOT = None                                    # set by build(); None is the wide nave view
TABLE_TOP = 2.81 * ALTAR_SCALE                 # the altar table's top surface in the world
TABLE_Y = ALTAR_Y - 0.9 * ALTAR_SCALE


# --------------------------------------------------------------- materials --
def aim(ob, target):
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat("-Z", "Y").to_euler()


def with_ao(name, base, rough, metal, dist=0.4, power=1.6):
    """A metal or stone that darkens in its own crevices, so dense sculpted
    detail reads instead of turning into flat colour."""
    m = pbr(name, base, rough, metal)
    g = Graph(m)
    ao = g.N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = dist
    ao.samples = 8
    dark = g.op("POWER", ao.outputs["AO"], power)
    tint = g.N.new("ShaderNodeVectorMath")
    tint.operation = "SCALE"
    tint.inputs[0].default_value = base
    g.L.new(dark, tint.inputs["Scale"])
    g.L.new(tint.outputs["Vector"], g.bsdf().inputs["Base Color"])
    return m


def distressed_gold(name, base, dirt=(0.028, 0.020, 0.010), polish=0.0):
    """Old gold: black grime packed into every crevice, bright metal where
    hands and time have worn the edges, blotches of brown tarnish, and fine
    scratches that break up the reflections. `polish` (0..1) shrinks the
    tarnish and makes the open metal glossy, so it gleams in candlelight."""
    m = pbr(name, base, 0.3, 1.0)
    g = Graph(m)
    b = g.bsdf()
    ao = g.N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.25
    ao.samples = 8
    clean = g.N.new("ShaderNodeMapRange")                  # 0 in crevices, 1 in the open
    clean.inputs["From Min"].default_value = 0.35
    clean.inputs["From Max"].default_value = 0.95
    g.L.new(ao.outputs["AO"], clean.inputs["Value"])
    worn = g.N.new("ShaderNodeMapRange")                   # 1 on sharp convex edges
    worn.inputs["From Min"].default_value = 0.52
    worn.inputs["From Max"].default_value = 0.58
    g.L.new(g.N.new("ShaderNodeNewGeometry").outputs["Pointiness"], worn.inputs["Value"])
    x, y, z = g.xyz()
    pos = g.N.new("ShaderNodeCombineXYZ")
    g.put(pos.inputs["X"], x); g.put(pos.inputs["Y"], y); g.put(pos.inputs["Z"], z)
    blot = g.N.new("ShaderNodeTexNoise")
    blot.inputs["Scale"].default_value = 2.5
    blot.inputs["Detail"].default_value = 8.0
    g.L.new(pos.outputs[0], blot.inputs["Vector"])
    tarnish = g.N.new("ShaderNodeMapRange")
    tarnish.inputs["From Min"].default_value = 0.5 + 0.12 * polish
    tarnish.inputs["From Max"].default_value = 0.68 + 0.12 * polish
    g.L.new(blot.outputs["Fac"], tarnish.inputs["Value"])
    scratch = g.N.new("ShaderNodeTexNoise")
    scratch.inputs["Scale"].default_value = 60.0
    scratch.inputs["Detail"].default_value = 2.0
    stretch = g.N.new("ShaderNodeMapping")
    stretch.inputs["Scale"].default_value = (1.0, 1.0, 14.0)
    g.L.new(pos.outputs[0], stretch.inputs["Vector"])
    g.L.new(stretch.outputs[0], scratch.inputs["Vector"])
    col = g.mix(tarnish.outputs["Result"], base, (base[0] * 0.35, base[1] * 0.28, base[2] * 0.2))
    col = g.mix(worn.outputs["Result"], col, (min(1, base[0] * 1.5), min(1, base[1] * 1.45), min(1, base[2] * 1.3)))
    col = g.mix(clean.outputs["Result"], dirt, col)
    g.L.new(col, b.inputs["Base Color"])
    rough = g.op("ADD", g.op("MULTIPLY", tarnish.outputs["Result"], 0.35),
                 g.op("MULTIPLY", scratch.outputs["Fac"], 0.25))
    rough = g.op("SUBTRACT", g.op("ADD", rough, 0.18), g.op("MULTIPLY", worn.outputs["Result"], 0.12))
    rough = g.op("MULTIPLY", rough, 1.0 - 0.7 * polish)
    g.L.new(g.op("ADD", rough, g.op("MULTIPLY", g.op("SUBTRACT", 1.0, clean.outputs["Result"]), 0.5)), b.inputs["Roughness"])
    g.L.new(clean.outputs["Result"], b.inputs["Metallic"])
    return m


def weather(m, amount=1.0, dust=0.5, rough_gain=0.35):
    """Age a material in place: blotches of grime, soot streaks running down,
    dust settled on upward faces, each raising the roughness. Wraps whatever
    already feeds the Base Color and Roughness, so it works on image and
    procedural materials alike; all patterns are in world space."""
    g = Graph(m)
    b = g.bsdf()

    def source(sock):
        if sock.links:
            out = sock.links[0].from_socket
            g.L.remove(sock.links[0])
            return out
        v = sock.default_value
        return tuple(v[:3]) if sock.type == "RGBA" else v

    col, rough = source(b.inputs["Base Color"]), source(b.inputs["Roughness"])
    x, y, z = g.xyz()
    pos = g.N.new("ShaderNodeCombineXYZ")
    g.put(pos.inputs["X"], x); g.put(pos.inputs["Y"], y); g.put(pos.inputs["Z"], z)

    def noise(scale, stretch, lo, hi, detail=6.0):
        mp = g.N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        g.L.new(pos.outputs[0], mp.inputs["Vector"])
        n = g.N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = detail
        g.L.new(mp.outputs[0], n.inputs["Vector"])
        r = g.N.new("ShaderNodeMapRange")
        r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = lo, hi
        g.L.new(n.outputs["Fac"], r.inputs["Value"])
        return r.outputs["Result"]

    blot = g.op("MULTIPLY", noise(1.3, (1, 1, 1), 0.45, 0.72), 0.6 * amount)
    streak = g.op("MULTIPLY", noise(2.5, (5, 5, 0.22), 0.5, 0.78), 0.45 * amount)
    up = g.N.new("ShaderNodeSeparateXYZ")
    g.L.new(g.N.new("ShaderNodeNewGeometry").outputs["Normal"], up.inputs[0])
    top = g.N.new("ShaderNodeMapRange")
    top.inputs["From Min"].default_value, top.inputs["From Max"].default_value = 0.4, 0.9
    g.L.new(up.outputs["Z"], top.inputs["Value"])
    settle = g.op("MULTIPLY", g.op("MULTIPLY", top.outputs["Result"], noise(7.0, (1, 1, 1), 0.3, 0.7)), dust)
    col = g.mix(blot, col, (0.018, 0.014, 0.010))
    col = g.mix(streak, col, (0.010, 0.008, 0.006))
    col = g.mix(settle, col, (0.16, 0.14, 0.11))
    g.L.new(col, b.inputs["Base Color"])
    wear = g.op("ADD", g.op("ADD", blot, streak), settle)
    g.L.new(g.op("ADD", rough, g.op("MULTIPLY", wear, rough_gain), clamp=True), b.inputs["Roughness"])
    return m


def machine_mat(name, base, brass=(0.78, 0.54, 0.20), paint=(0.13, 0.018, 0.012)):
    """Servitor machinery: worn, hammered gunmetal (distressed_gold's grime
    and edge wear), oxblood paint over it in large patches, chipped back to
    bare metal on every edge, brass on the small sharp fittings - rivets,
    bolts, collars, which Cycles' pointiness picks out - and orange-brown
    rust blooming in patches, dull and no longer metal."""
    m = distressed_gold(name, base, dirt=(0.010, 0.009, 0.008), polish=0.6)
    g = Graph(m)
    b = g.bsdf()
    col = b.inputs["Base Color"].links[0].from_socket
    metal = b.inputs["Metallic"].links[0].from_socket
    rough = b.inputs["Roughness"].links[0].from_socket
    point = g.N.new("ShaderNodeNewGeometry").outputs["Pointiness"]
    fit = g.N.new("ShaderNodeMapRange")
    fit.inputs["From Min"].default_value, fit.inputs["From Max"].default_value = 0.545, 0.585
    g.L.new(point, fit.inputs["Value"])
    chip = g.N.new("ShaderNodeMapRange")                  # paint worn off where the edge is sharp
    chip.inputs["From Min"].default_value, chip.inputs["From Max"].default_value = 0.515, 0.535
    g.L.new(point, chip.inputs["Value"])
    x, y, z = g.xyz()
    pos = g.N.new("ShaderNodeCombineXYZ")
    g.put(pos.inputs["X"], x); g.put(pos.inputs["Y"], y); g.put(pos.inputs["Z"], z)
    n = g.N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 9.0
    n.inputs["Detail"].default_value = 8.0
    g.L.new(pos.outputs[0], n.inputs["Vector"])
    rust = g.N.new("ShaderNodeMapRange")
    rust.inputs["From Min"].default_value, rust.inputs["From Max"].default_value = 0.55, 0.72
    g.L.new(n.outputs["Fac"], rust.inputs["Value"])
    pn = g.N.new("ShaderNodeTexNoise")
    pn.inputs["Scale"].default_value = 1.6
    g.L.new(pos.outputs[0], pn.inputs["Vector"])
    cover = g.N.new("ShaderNodeMapRange")
    cover.inputs["From Min"].default_value, cover.inputs["From Max"].default_value = 0.47, 0.53
    g.L.new(pn.outputs["Fac"], cover.inputs["Value"])
    painted = g.op("MULTIPLY", cover.outputs["Result"], g.op("SUBTRACT", 1.0, chip.outputs["Result"]))
    col = g.mix(painted, col, paint)
    metal = g.op("MULTIPLY", metal, g.op("SUBTRACT", 1.0, painted))
    rough = g.op("ADD", g.op("MULTIPLY", rough, g.op("SUBTRACT", 1.0, painted)), g.op("MULTIPLY", painted, 0.55))
    f, r = fit.outputs["Result"], rust.outputs["Result"]
    col = g.mix(f, col, brass)
    col = g.mix(r, col, (0.20, 0.075, 0.03))
    g.L.new(col, b.inputs["Base Color"])
    g.L.new(g.op("MULTIPLY", g.op("MAXIMUM", metal, f), g.op("SUBTRACT", 1.0, r)), b.inputs["Metallic"])
    rough = g.op("ADD", g.op("MULTIPLY", rough, g.op("SUBTRACT", 1.0, f)), g.op("MULTIPLY", f, 0.28))
    g.L.new(g.op("ADD", g.op("MULTIPLY", rough, g.op("SUBTRACT", 1.0, r)), g.op("MULTIPLY", r, 0.9)), b.inputs["Roughness"])
    hammer = g.N.new("ShaderNodeTexNoise")                 # hammered, dented plate
    hammer.inputs["Scale"].default_value = 60.0
    g.L.new(pos.outputs[0], hammer.inputs["Vector"])
    bp = g.N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.25
    bp.inputs["Distance"].default_value = 0.004
    g.L.new(hammer.outputs["Fac"], bp.inputs["Height"])
    g.L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def tex_mat(stem, tile, metal, rough=(0.3, 0.7), bump=0.3, tint=(1, 1, 1), spec=0.5, fittings=False, wear=0.0):
    """A generated surface photograph (resources/assets/<stem>.png: steel, brass, skin,
    wool) projected on all sides in the object's own coordinates, one tile
    every `tile` units. Dark in the crevices (AO); brighter texture is
    smoother (`rough` from dark to bright) and raised (`bump`). `fittings`
    turns the small sharp details (rivets, bolts) brass; `wear` brightens
    every sharp edge where hands and time rubbed it bare."""
    m = pbr(stem, (0.5, 0.5, 0.5), 0.5, metal)
    g = Graph(m)
    b = g.bsdf()
    mp = g.N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile,) * 3
    g.L.new(g.N.new("ShaderNodeTexCoord").outputs["Object"], mp.inputs["Vector"])
    tex = g.N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(A, f"{stem}.png"))
    tex.projection, tex.projection_blend = "BOX", 0.3
    g.L.new(mp.outputs[0], tex.inputs["Vector"])
    ao = g.N.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.08
    ao.samples = 8
    col = g.N.new("ShaderNodeVectorMath")
    col.operation = "MULTIPLY"
    g.L.new(tex.outputs["Color"], col.inputs[0])
    col.inputs[1].default_value = tint
    dark = g.N.new("ShaderNodeVectorMath")
    dark.operation = "SCALE"
    g.L.new(col.outputs["Vector"], dark.inputs[0])
    g.L.new(g.op("POWER", ao.outputs["AO"], 2.6), dark.inputs["Scale"])
    out = dark.outputs["Vector"]
    if wear:
        edge = g.N.new("ShaderNodeMapRange")
        edge.inputs["From Min"].default_value, edge.inputs["From Max"].default_value = 0.51, 0.56
        g.L.new(g.N.new("ShaderNodeNewGeometry").outputs["Pointiness"], edge.inputs["Value"])
        lift = g.N.new("ShaderNodeVectorMath")
        lift.operation = "SCALE"
        g.L.new(out, lift.inputs[0])
        g.L.new(g.op("ADD", 1.0, g.op("MULTIPLY", edge.outputs["Result"], wear)), lift.inputs["Scale"])
        out = lift.outputs["Vector"]
    bw = g.N.new("ShaderNodeRGBToBW")
    g.L.new(tex.outputs["Color"], bw.inputs[0])
    rr = g.N.new("ShaderNodeMapRange")
    rr.inputs["To Min"].default_value, rr.inputs["To Max"].default_value = rough[1], rough[0]
    g.L.new(bw.outputs[0], rr.inputs["Value"])
    r_out, m_out = rr.outputs["Result"], metal
    if fittings:
        fit = g.N.new("ShaderNodeMapRange")
        fit.inputs["From Min"].default_value, fit.inputs["From Max"].default_value = 0.545, 0.585
        g.L.new(g.N.new("ShaderNodeNewGeometry").outputs["Pointiness"], fit.inputs["Value"])
        f = fit.outputs["Result"]
        out = g.mix(f, out, (0.78, 0.54, 0.20))
        r_out = g.op("ADD", g.op("MULTIPLY", r_out, g.op("SUBTRACT", 1.0, f)), g.op("MULTIPLY", f, 0.25))
        m_out = g.op("MAXIMUM", metal, f)
    g.L.new(out, b.inputs["Base Color"])
    g.L.new(r_out, b.inputs["Roughness"])
    g.put(b.inputs["Metallic"], m_out)
    b.inputs["Specular IOR Level"].default_value = spec
    bp = g.N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = bump
    bp.inputs["Distance"].default_value = 0.005
    g.L.new(bw.outputs[0], bp.inputs["Height"])
    g.L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def corrode(m, rust=1.0, paint=(0.13, 0.018, 0.012), cover=0.3):
    """Age a metal material in place: rust blooming in patches and bleeding
    down in streaks, dull and no longer metal; oxblood paint over about
    `cover` of it, chipped back to metal on every sharp edge. Wraps whatever
    feeds Base Color, Metallic and Roughness."""
    g = Graph(m)
    b = g.bsdf()

    def source(sock):
        if sock.links:
            out = sock.links[0].from_socket
            g.L.remove(sock.links[0])
            return out
        v = sock.default_value
        return tuple(v[:3]) if sock.type == "RGBA" else v

    col, metal, rough = (source(b.inputs[k]) for k in ("Base Color", "Metallic", "Roughness"))
    x, y, z = g.xyz()
    pos = g.N.new("ShaderNodeCombineXYZ")
    g.put(pos.inputs["X"], x); g.put(pos.inputs["Y"], y); g.put(pos.inputs["Z"], z)

    def field(scale, stretch, lo, hi):
        mp = g.N.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = stretch
        g.L.new(pos.outputs[0], mp.inputs["Vector"])
        n = g.N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = scale
        n.inputs["Detail"].default_value = 8.0
        g.L.new(mp.outputs[0], n.inputs["Vector"])
        r = g.N.new("ShaderNodeMapRange")
        r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = lo, hi
        g.L.new(n.outputs["Fac"], r.inputs["Value"])
        return r.outputs["Result"]

    point = g.N.new("ShaderNodeNewGeometry").outputs["Pointiness"]
    chip = g.N.new("ShaderNodeMapRange")
    chip.inputs["From Min"].default_value, chip.inputs["From Max"].default_value = 0.515, 0.535
    g.L.new(point, chip.inputs["Value"])
    painted = g.op("MULTIPLY", field(1.6, (1, 1, 1), 0.62 - 0.3 * cover, 0.66 - 0.3 * cover),
                   g.op("MULTIPLY", g.op("SUBTRACT", 1.0, chip.outputs["Result"]), field(14.0, (1, 1, 1), 0.3, 0.45)))
    col = g.mix(painted, col, paint)
    metal = g.op("MULTIPLY", metal, g.op("SUBTRACT", 1.0, painted))
    rough = g.op("ADD", g.op("MULTIPLY", rough, g.op("SUBTRACT", 1.0, painted)), g.op("MULTIPLY", painted, 0.6))
    patch = g.op("MULTIPLY", field(8.0, (1, 1, 1), 0.58, 0.72), rust)
    streak = g.op("MULTIPLY", field(5.0, (6, 6, 0.3), 0.6, 0.8), 0.6 * rust)
    r = g.op("MAXIMUM", patch, streak)
    col = g.mix(patch, col, (0.20, 0.075, 0.03))
    col = g.mix(streak, col, (0.11, 0.045, 0.02))
    g.L.new(col, b.inputs["Base Color"])
    g.L.new(g.op("MULTIPLY", metal, g.op("SUBTRACT", 1.0, r)), b.inputs["Metallic"])
    g.L.new(g.op("ADD", g.op("MULTIPLY", rough, g.op("SUBTRACT", 1.0, r)), g.op("MULTIPLY", r, 0.9)), b.inputs["Roughness"])
    return m


def relief_mat(stem, tile=1.6, metal=0.7):
    """Blackened metal carved in gothic relief: a generated panel
    (resources/assets/<stem>.png) projected on all six sides of a box in the object's
    own coordinates, one panel every `tile` units. Its brightness raises the
    relief and polishes it; the dark recesses stay rough."""
    m = pbr(stem, (0.1, 0.1, 0.1), 0.5, metal)
    g = Graph(m)
    b = g.bsdf()
    mp = g.N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / tile,) * 3
    g.L.new(g.N.new("ShaderNodeTexCoord").outputs["Object"], mp.inputs["Vector"])
    tex = g.N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(A, f"{stem}.png"))
    tex.projection, tex.projection_blend = "BOX", 0.2
    g.L.new(mp.outputs[0], tex.inputs["Vector"])
    g.L.new(tex.outputs["Color"], b.inputs["Base Color"])
    bw = g.N.new("ShaderNodeRGBToBW")
    g.L.new(tex.outputs["Color"], bw.inputs[0])
    g.L.new(g.op("SUBTRACT", 0.85, g.op("MULTIPLY", bw.outputs[0], 1.2), clamp=True), b.inputs["Roughness"])
    bp = g.N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.8
    bp.inputs["Distance"].default_value = 0.03
    g.L.new(bw.outputs[0], bp.inputs["Height"])
    g.L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def skin_mat(name, base=(0.56, 0.36, 0.29)):
    """A servitor's skin: pale and sickly, blotched with bruise-grey, light
    scattering a little under it, grime in every fold."""
    m = with_ao(name, base, 0.5, 0.0, 0.05, 2.2)
    g = Graph(m)
    b = g.bsdf()
    tint = b.inputs["Base Color"].links[0].from_socket
    n = g.N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 18.0
    n.inputs["Detail"].default_value = 6.0
    r = g.N.new("ShaderNodeMapRange")
    r.inputs["From Min"].default_value, r.inputs["From Max"].default_value = 0.45, 0.75
    g.L.new(n.outputs["Fac"], r.inputs["Value"])
    bruise = g.mix(r.outputs["Result"], tint, (0.30, 0.13, 0.14))
    n2 = g.N.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 7.0
    r2 = g.N.new("ShaderNodeMapRange")
    r2.inputs["From Min"].default_value, r2.inputs["From Max"].default_value = 0.5, 0.7
    g.L.new(n2.outputs["Fac"], r2.inputs["Value"])
    g.L.new(g.mix(r2.outputs["Result"], bruise, (0.52, 0.44, 0.24)), b.inputs["Base Color"])   # jaundiced patches
    b.inputs["Subsurface Weight"].default_value = 0.25
    b.inputs["Subsurface Radius"].default_value = (1.0, 0.25, 0.12)
    b.inputs["Subsurface Scale"].default_value = 0.01
    return m


def velvet_mat(name, colour):
    """Crimson velvet: deep colour, a sheen of its own hue at grazing angles,
    faded in large soft patches."""
    m = pbr(name, colour, 1.0)
    g = Graph(m)
    b = g.bsdf()
    b.inputs["Specular IOR Level"].default_value = 0.0      # velvet swallows the light: no gloss
    n = g.N.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = 0.7
    n.inputs["Detail"].default_value = 4.0
    fade = g.N.new("ShaderNodeMapRange")
    fade.inputs["From Min"].default_value, fade.inputs["From Max"].default_value = 0.4, 0.75
    g.L.new(n.outputs["Fac"], fade.inputs["Value"])
    g.L.new(g.mix(fade.outputs["Result"], colour, tuple(c * 0.55 for c in colour)), b.inputs["Base Color"])
    b.inputs["Sheen Weight"].default_value = 0.8
    b.inputs["Sheen Roughness"].default_value = 0.35
    b.inputs["Sheen Tint"].default_value = (0.9, 0.12, 0.10, 1)
    return m


def robe_mat(cloth=(0.20, 0.014, 0.010), sheen=0.4, brass=(0.55, 0.36, 0.13), rough=0.8):
    """Red cloth with brass on the sharp details: Cycles' pointiness is high on
    small convex features (buckles, cogs, mechanical parts), low on cloth."""
    m = pbr("robe", cloth, 0.8)
    g = Graph(m)
    geo = g.N.new("ShaderNodeNewGeometry")
    ramp = g.N.new("ShaderNodeMapRange")
    ramp.inputs["From Min"].default_value = 0.53
    ramp.inputs["From Max"].default_value = 0.60
    g.L.new(geo.outputs["Pointiness"], ramp.inputs["Value"])
    f = ramp.outputs["Result"]
    b = g.bsdf()
    g.L.new(g.mix(f, cloth, brass), b.inputs["Base Color"])
    g.L.new(f, b.inputs["Metallic"])
    g.L.new(g.op("SUBTRACT", rough, g.op("MULTIPLY", f, rough - 0.35)), b.inputs["Roughness"])
    b.inputs["Specular IOR Level"].default_value = 0.5 if rough < 0.9 else 0.2
    b.inputs["Sheen Weight"].default_value = sheen
    b.inputs["Sheen Tint"].default_value = (*[min(1, 4 * c) for c in cloth], 1)
    return m


def image_mat(name, path, alpha=False, metal=0.0, rough=0.6, bump=0.0, sheen=0.0):
    m = pbr(name, (0.5, 0.5, 0.5), rough, metal)
    g = Graph(m)
    b = g.bsdf()
    tex = g.N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    g.L.new(tex.outputs["Color"], b.inputs["Base Color"])
    if alpha:
        g.L.new(tex.outputs["Alpha"], b.inputs["Alpha"])
    if bump:
        bp = g.N.new("ShaderNodeBump")
        bp.inputs["Strength"].default_value = bump
        g.L.new(tex.outputs["Color"], bp.inputs["Height"])
        g.L.new(bp.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Sheen Weight"].default_value = sheen
    return m


def embroidered(stem, alpha=True, shade=1.0, matte=False):
    """Velvet: the image `stem`.png for colour (and shape), its gold mask
    `stem`_gold.png for where the thread is metal, glossier and raised.
    `shade` darkens the cloth, not the gold."""
    m = image_mat(stem, os.path.join(A, f"{stem}.png"), alpha=alpha, rough=0.85, sheen=0.5)
    g = Graph(m)
    b = g.bsdf()
    tex = b.inputs["Base Color"].links[0].from_node
    mask = g.N.new("ShaderNodeTexImage")
    mask.image = bpy.data.images.load(os.path.join(A, f"{stem}_gold.png"))
    mask.image.colorspace_settings.name = "Non-Color"
    f = mask.outputs["Color"]
    if shade != 1.0:
        dim = g.N.new("ShaderNodeVectorMath")
        dim.operation = "SCALE"
        g.L.new(tex.outputs["Color"], dim.inputs[0])
        g.L.new(g.op("ADD", shade, g.op("MULTIPLY", f, 1.0 - shade)), dim.inputs["Scale"])
        g.L.new(dim.outputs["Vector"], b.inputs["Base Color"])
    g.L.new(f, b.inputs["Metallic"])
    if matte:                                     # the cloth swallows light, only the thread shines
        g.L.new(g.op("SUBTRACT", 1.0, g.op("MULTIPLY", f, 0.8)), b.inputs["Roughness"])
        g.L.new(g.op("MULTIPLY", f, 0.5), b.inputs["Specular IOR Level"])
    else:
        g.L.new(g.op("SUBTRACT", 0.85, g.op("MULTIPLY", f, 0.5)), b.inputs["Roughness"])
    bp = g.N.new("ShaderNodeBump")
    bp.inputs["Strength"].default_value = 0.5
    bp.inputs["Distance"].default_value = 0.02
    g.L.new(f, bp.inputs["Height"])
    g.L.new(bp.outputs["Normal"], b.inputs["Normal"])
    return m


def screen_mat(strength=2.2, crt=False):
    """The altar screen: one image per tick, swapped by the render loop. `crt`
    darkens it towards the corners like the curved glass of an old tube."""
    m, e = lamp("screen", (1, 1, 1), strength)
    g = Graph(m)
    tex = g.N.new("ShaderNodeTexImage")
    imgs = [bpy.data.images.load(os.path.join(A, f"screen_{k:02d}.png")) for k in range(TICKS)]
    tex.image = imgs[0]
    g.L.new(tex.outputs["Color"], e.inputs["Color"])
    if crt:
        uv = g.N.new("ShaderNodeSeparateXYZ")
        g.L.new(g.N.new("ShaderNodeTexCoord").outputs["UV"], uv.inputs[0])
        du, dv = g.op("SUBTRACT", uv.outputs["X"], 0.5), g.op("SUBTRACT", uv.outputs["Y"], 0.5)
        d = g.op("ADD", g.op("MULTIPLY", du, du), g.op("MULTIPLY", dv, dv))
        vig = g.op("POWER", g.op("SUBTRACT", 1.0, g.op("MULTIPLY", d, 2.0), clamp=True), 1.5)
        dim = g.N.new("ShaderNodeVectorMath")
        dim.operation = "SCALE"
        g.L.new(tex.outputs["Color"], dim.inputs[0])
        g.L.new(vig, dim.inputs["Scale"])
        g.L.new(dim.outputs["Vector"], e.inputs["Color"])
    MOVERS.append((tex, lambda ph, t=tex, imgs=imgs:
                   setattr(t, "image", imgs[(round(ph * FRAMES) % FRAMES) // TICK])))
    return m


RAINBOW = [(0.02, 0.10, 0.60), (0.55, 0.02, 0.03), (0.95, 0.60, 0.10), (0.30, 0.05, 0.55),
           (0.03, 0.35, 0.12), (0.05, 0.25, 0.75), (0.85, 0.30, 0.04)]
AMBER = [(0.85, 0.42, 0.08), (0.40, 0.04, 0.02), (0.95, 0.66, 0.22), (0.60, 0.20, 0.03),
         (0.75, 0.52, 0.18), (0.30, 0.08, 0.02), (0.90, 0.55, 0.12)]      # Rogue Trader's backlit glass


def stained_glass(pal=RAINBOW, strength=2.2):
    """Lead-lined cells of coloured glass: transparent, so the window lights
    outside shine through tinted, plus a glow of its own."""
    m = bpy.data.materials.new("stained_glass")
    m.use_nodes = True
    g = Graph(m)
    N = g.N
    for n in list(N):
        if n.type != "OUTPUT_MATERIAL":
            N.remove(n)
    x, y, z = g.xyz()
    v = N.new("ShaderNodeCombineXYZ")
    g.put(v.inputs["X"], g.op("ADD", x, y))
    g.put(v.inputs["Y"], z)
    cells = N.new("ShaderNodeTexVoronoi")
    cells.inputs["Scale"].default_value = 1.6
    g.L.new(v.outputs[0], cells.inputs["Vector"])
    edge = N.new("ShaderNodeTexVoronoi")
    edge.feature = "DISTANCE_TO_EDGE"
    edge.inputs["Scale"].default_value = 1.6
    g.L.new(v.outputs[0], edge.inputs["Vector"])
    hue = N.new("ShaderNodeSeparateColor")
    g.L.new(cells.outputs["Color"], hue.inputs[0])
    ramp = N.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    els = ramp.color_ramp.elements
    els[0].position, els[0].color = 0.0, (*pal[0], 1)
    els[1].position, els[1].color = 1 / len(pal), (*pal[1], 1)
    for k in range(2, len(pal)):
        e = els.new(k / len(pal))
        e.color = (*pal[k], 1)
    g.L.new(hue.outputs[0], ramp.inputs["Fac"])
    glass = g.op("GREATER_THAN", edge.outputs["Distance"], 0.045)
    col = N.new("ShaderNodeVectorMath")
    col.operation = "SCALE"
    g.L.new(ramp.outputs["Color"], col.inputs[0])
    g.L.new(glass, col.inputs["Scale"])
    tr = N.new("ShaderNodeBsdfTransparent")
    g.L.new(col.outputs["Vector"], tr.inputs["Color"])
    em = N.new("ShaderNodeEmission")
    g.L.new(col.outputs["Vector"], em.inputs["Color"])
    em.inputs["Strength"].default_value = strength
    add = N.new("ShaderNodeAddShader")
    g.L.new(tr.outputs[0], add.inputs[0])
    g.L.new(em.outputs[0], add.inputs[1])
    g.L.new(add.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def window_mat(stem, side, strength=1.4):
    """A generated stained-glass window glowing as if backlit, once per
    storey up a glass box one bay wide: generated coordinates run 0..1 over
    the box, the window repeats twice up it, and it reads the right way
    round from inside the nave on either wall."""
    key = f"{stem}{side}"
    if key in MAT:
        return MAT[key]
    m, e = lamp(key, (1, 1, 1), strength)
    g = Graph(m)
    sep = g.N.new("ShaderNodeSeparateXYZ")
    g.L.new(g.N.new("ShaderNodeTexCoord").outputs["Generated"], sep.inputs[0])
    uv = g.N.new("ShaderNodeCombineXYZ")
    g.put(uv.inputs["X"], sep.outputs["Y"] if side < 0 else g.op("SUBTRACT", 1.0, sep.outputs["Y"]))
    g.put(uv.inputs["Y"], g.op("FRACT", g.op("MULTIPLY", sep.outputs["Z"], 2.0)))
    tex = g.N.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(A, f"{stem}.png"))
    tex.extension = "CLIP"
    g.L.new(uv.outputs[0], tex.inputs["Vector"])
    g.L.new(tex.outputs["Color"], e.inputs["Color"])
    MAT[key] = m
    return m


def smoke_mat(rise=6.0):
    """Incense smoke rising `rise` units per loop. Two copies of the same noise,
    one a loop behind the other, are cross-faded by phase, so phase 1.0 shows
    exactly what phase 0.0 shows."""
    m = bpy.data.materials.new("smoke")
    m.use_nodes = True
    g = Graph(m)
    N = g.N
    N.remove(g.bsdf())
    ph = g.clock("phase")
    x, y, z = g.xyz()
    sep = N.new("ShaderNodeSeparateXYZ")
    g.L.new(N.new("ShaderNodeObjectInfo").outputs["Location"], sep.inputs[0])
    dx, dy = g.op("SUBTRACT", x, sep.outputs["X"]), g.op("SUBTRACT", y, sep.outputs["Y"])
    rz = g.op("SUBTRACT", z, g.op("SUBTRACT", sep.outputs["Z"], 6.2))    # height above the source

    def layer(shift):
        v = N.new("ShaderNodeCombineXYZ")
        g.put(v.inputs["X"], dx)
        g.put(v.inputs["Y"], dy)
        g.put(v.inputs["Z"], g.op("SUBTRACT", rz, g.op("MULTIPLY", g.op("SUBTRACT", ph, shift), rise)))
        n = N.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = 0.9
        n.inputs["Detail"].default_value = 4.0
        n.inputs["Distortion"].default_value = 0.6
        g.L.new(v.outputs[0], n.inputs["Vector"])
        return g.op("MAXIMUM", g.op("SUBTRACT", n.outputs["Fac"], 0.42), 0.0)

    a, b = layer(0.0), layer(1.0)
    wisp = g.op("ADD", g.op("MULTIPLY", a, g.op("SUBTRACT", 1.0, ph)), g.op("MULTIPLY", b, ph))
    # a column that widens as it rises and thins out towards the top
    r = g.op("SQRT", g.op("ADD", g.op("MULTIPLY", dx, dx), g.op("MULTIPLY", dy, dy)))
    width = g.op("ADD", 0.45, g.op("MULTIPLY", rz, 0.10))
    column = g.op("SUBTRACT", 1.0, g.op("DIVIDE", r, width), clamp=True)
    fade = g.op("SUBTRACT", 1.0, g.op("DIVIDE", rz, 11.0), clamp=True)
    dens = g.op("MULTIPLY", g.op("MULTIPLY", wisp, column), g.op("MULTIPLY", fade, 30.0))
    # thin enough not to read as dark soot against the lit altar; a faint glow
    # of its own stands in for the candlelight the smoke catches
    sc = N.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (0.85, 0.82, 0.78, 1)
    sc.inputs["Anisotropy"].default_value = 0.35
    g.L.new(g.op("MULTIPLY", dens, 0.35), sc.inputs["Density"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.82, 0.62, 1)
    g.L.new(g.op("MULTIPLY", dens, 0.07), em.inputs["Strength"])
    add = N.new("ShaderNodeAddShader")
    g.L.new(sc.outputs[0], add.inputs[0])
    g.L.new(em.outputs[0], add.inputs[1])
    g.L.new(add.outputs[0], N["Material Output"].inputs["Volume"])
    return m


def materials():
    MAT["iron"] = with_ao("iron", (0.030, 0.030, 0.034), 0.45, 0.85)
    MAT["iron_dk"] = pbr("iron_dk", (0.014, 0.014, 0.016), 0.5, 0.8)
    MAT["gold"] = distressed_gold("gold", (0.62, 0.40, 0.14))
    MAT["stone"] = with_ao("stone", (0.085, 0.078, 0.070), 0.8, 0.0, 0.6, 2.0)
    MAT["pillar"] = K.masonry("pillar_stone", (0.075, 0.067, 0.060))
    MAT["floor"] = K.floor_mat()
    MAT["statue"] = distressed_gold("statue", (0.40, 0.25, 0.09))
    MAT["bone"] = with_ao("bone", (0.52, 0.45, 0.33), 0.55, 0.0, 0.15, 1.8)
    MAT["robe"] = robe_mat()
    MAT["servitor"] = with_ao("servitor", (0.20, 0.17, 0.15), 0.5, 0.6, 0.2, 1.8)
    MAT["velvet"] = embroidered("drape", alpha=False, shade=0.45)
    MAT["cable"] = pbr("cable", (0.010, 0.010, 0.010), 0.5)
    MAT["shroud"] = pbr("shroud", (0.012, 0.012, 0.013), 0.4, 0.4)
    MAT["facet"] = pbr("facet", (0.045, 0.047, 0.050), 0.3, 0.7)
    MAT["silver"] = pbr("silver", (0.62, 0.63, 0.65), 0.2, 1.0)
    MAT["green"] = lamp("green_led", (0.25, 1.0, 0.35), 6.0)[0]
    MAT["amber"] = lamp("amber", (1.0, 0.45, 0.10), 5.0)[0]
    MAT["red_eye"] = lamp("red_eye", (1.0, 0.04, 0.02), 30.0)[0]
    MAT["halo"] = lamp("halo", (1.0, 0.68, 0.28), 6.0)[0]
    MAT["flame"] = K.flame_mat()
    MAT["cells"] = K.compute_cells("cells", (0.16, 0.10), 1 if SHOT else 2, ((0.25, 1.0, 0.35), (1.0, 0.45, 0.10)))
    MAT["trace"] = K.data_flow("trace", (0.25, 1.0, 0.35), "y", 3.0, -2, 2.5)
    MAT["glass"] = stained_glass(AMBER, 0.8) if SHOT else stained_glass()
    MAT["smoke"] = smoke_mat()
    MAT["plaque"] = image_mat("plaque", os.path.join(A, "plaque.png"), metal=0.5, rough=0.4, bump=0.25)
    MAT["screen"] = screen_mat(1.0, crt=True) if SHOT else screen_mat()
    for n in range(6):
        MAT[f"banner{n}"] = embroidered(f"banner_{n}")
    for n in range(4):
        MAT[f"parchment{n}"] = image_mat(f"parchment{n}", os.path.join(A, f"parchment_{n}.png"), alpha=True, rough=0.8)
    MAT["wax"] = pbr("seal_wax", (0.30, 0.008, 0.006), 0.25)
    MAT["candle_wax"] = pbr("candle_wax", (0.72, 0.64, 0.48), 0.45)
    MAT["frieze"] = image_mat("frieze", os.path.join(A, "frieze.png"), metal=0.35, rough=0.45, bump=0.3)
    for n in range(12):
        MAT[f"plaque{n}"] = image_mat(f"plaque{n}", os.path.join(A, f"plaque_{n:02d}.png"), metal=0.8, rough=0.4, bump=0.5)
    for n in range(6):
        MAT[f"icon{n}"] = image_mat(f"icon{n}", os.path.join(A, f"icon_{n}.png"), metal=0.6, rough=0.45, bump=0.4)
    MAT["antependium"] = embroidered("antependium")
    MAT["binary"] = image_mat("binary", os.path.join(A, "binary.png"), metal=0.8, rough=0.4, bump=0.3)
    MAT["cable_red"] = pbr("cable_red", (0.09, 0.012, 0.008), 0.45)
    MAT["enamel_red"] = with_ao("enamel_red", (0.23, 0.018, 0.012), 0.35, 0.0, 0.1, 2.0)
    MAT["enamel_black"] = with_ao("enamel_black", (0.012, 0.011, 0.011), 0.3, 0.3, 0.1, 2.0)
    MAT["gunmetal"] = distressed_gold("gunmetal", (0.13, 0.13, 0.14), dirt=(0.01, 0.01, 0.01))
    MAT["eye"] = lamp("eye", (1.0, 0.07, 0.03), 4.0)[0]
    MAT["conduit"] = with_ao("conduit", (0.05, 0.045, 0.04), 0.5, 0.7)
    if SHOT:
        # the close-ups take Rogue Trader's grade (references/rogue-trader/):
        # dark old brass with the gilding worn to the edges, oxblood cloth
        # without a pale sheen, aged grimy bone, one cold accent in the coolant
        MAT["gold"] = distressed_gold("old_gold", (0.95, 0.66, 0.24), dirt=(0.012, 0.009, 0.005), polish=1.0)
        MAT["statue"] = distressed_gold("old_bronze", (0.20, 0.14, 0.06), dirt=(0.008, 0.007, 0.005))
        MAT["bone"] = with_ao("old_bone", (0.25, 0.19, 0.11), 0.7, 0.0, 0.2, 2.6)
        MAT["robe"] = robe_mat((0.075, 0.010, 0.007), 0.12, (0.30, 0.20, 0.08), rough=1.0)
        MAT["antependium"] = embroidered("antependium", matte=True)
        MAT["velvet"] = embroidered("drape", matte=True)
        for n in range(2):
            MAT[f"hanging{n}"] = embroidered(f"hanging_{n}", matte=True)
        # generated gothic relief on the altar's iron, the rack backs, the stand
        MAT["iron"] = relief_mat("relief_0", tile=1.6)
        MAT["iron_dk"] = relief_mat("relief_1", tile=1.2, metal=0.6)
        MAT["relief2"] = relief_mat("relief_2", tile=1.4)
        # the near servitor, painted by part
        MAT["skin"] = tex_mat("mat_skin", 0.16, 0.0, (0.42, 0.62), 0.35, (0.92, 0.72, 0.64))
        sk = MAT["skin"].node_tree.nodes["Principled BSDF"]
        sk.inputs["Subsurface Weight"].default_value = 0.3
        sk.inputs["Subsurface Radius"].default_value = (1.0, 0.25, 0.12)
        sk.inputs["Subsurface Scale"].default_value = 0.01
        MAT["wax"] = pbr("seal_wax", (0.15, 0.008, 0.006), 0.3)
        MAT["servitor_cloth"] = tex_mat("mat_wool", 0.3, 0.0, (0.9, 1.0), 0.4, (0.42, 0.30, 0.30), spec=0.0)
        MAT["priest_robe"] = tex_mat("mat_wool", 0.3, 0.0, (0.9, 1.0), 0.4, (0.62, 0.05, 0.04), spec=0.0)
        MAT["leather"] = with_ao("leather", (0.06, 0.035, 0.02), 0.65, 0.0, 0.1, 2.0)
        for n in range(6):
            MAT[f"banner{n}"] = embroidered(f"banner_{n}", matte=True)
        for name in ("velvet", "antependium", *(f"banner{n}" for n in range(6))):
            b = MAT[name].node_tree.nodes["Principled BSDF"]
            b.inputs["Sheen Weight"].default_value = 0.2
            b.inputs["Sheen Tint"].default_value = (0.5, 0.12, 0.08, 1)
        # rings of light rising slowly through the coolant, one spacing per loop
        MAT["coolant"] = K.data_flow("coolant", (0.20, 0.80, 1.0), "z", 0.22, 1, 2.5, base=0.12, width=0.22)
        MAT["candle_wax"] = pbr("old_wax", (0.42, 0.35, 0.23), 0.5)
        # the near servitor: photographic steel, brass, weathered skin and wool
        MAT["near_servitor"] = corrode(tex_mat("mat_steel", 0.35, 1.0, (0.14, 0.45), 0.3, (0.55, 0.53, 0.51),
                                               fittings=True, wear=1.2))
        MAT["servitor_brass"] = tex_mat("mat_brass", 0.3, 1.0, (0.15, 0.4), 0.3, wear=0.8)
        MAT["rubber"] = with_ao("rubber", (0.025, 0.024, 0.023), 0.45, 0.0, 0.05, 2.0)
        # Rogue Trader's metal: blackened pewter for the structure, gold kept for trims
        MAT["pewter"] = distressed_gold("pewter", (0.10, 0.095, 0.09), dirt=(0.008, 0.007, 0.006))
        MAT["crimson"] = velvet_mat("crimson", (0.19, 0.008, 0.010))
        MAT["tube_glass"] = pbr("tube_glass", (0.80, 0.95, 1.0), 0.06)
        MAT["tube_glass"].node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0

    MAT.setdefault("pewter", MAT["gold"])
    MAT.setdefault("relief2", MAT["gold"])
    MAT.setdefault("crimson", MAT["velvet"])
    if SHOT:                                   # everything in the close-ups is old, sooted and dusty
        for k in (*(("skin",) if "skin" in MAT else ()), "iron", "iron_dk", "stone", "pillar", "gold", "pewter", "statue", "bone", "conduit",
                  "gunmetal", "servitor", "near_servitor", "candle_wax", "robe", "shroud", "facet",
                  "enamel_red", "enamel_black", "crimson", "velvet", "antependium", "plaque", "binary", "frieze",
                  "relief2", "servitor_cloth", "priest_robe", "leather", "hanging0", "hanging1", "servitor_brass", "rubber",
                  *(f"banner{n}" for n in range(6)), *(f"plaque{n}" for n in range(12)), *(f"icon{n}" for n in range(6))):
            if k == "gold":                    # gold keeps its gleam: grime in the crevices only
                weather(MAT[k], amount=0.3, dust=0.15, rough_gain=0.08)
            else:
                weather(MAT[k], amount=0.6 if k in ("shroud", "facet") else 1.0,
                        dust=0.2 if k in ("velvet", "crimson") else 0.5)

# ---------------------------------------------------------------- geometry --
def cloth(name, w, h, mat, loc, parent=None, folds=5, depth=0.12, seg=(24, 48), taper=0.0):
    """A hanging cloth in the XZ plane facing +Y, top edge at `loc`, UV mapped
    0..1, with vertical folds that deepen towards the bottom."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    nx, nz = seg
    vs = []
    for j in range(nz + 1):
        v = j / nz
        row = []
        for i in range(nx + 1):
            u = i / nx
            x = (u - 0.5) * w * (1 - taper * v)
            y = depth * (0.35 + 0.65 * v) * math.sin(2 * math.pi * folds * u + 1.3 * v)
            row.append(bm.verts.new((x, y, -v * h)))
        vs.append(row)
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
            f.smooth = True
            for loop, (uu, vv) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                loop[uv].uv = (1 - uu / nx, 1 - vv / nz)       # seen from +Y, +X is the image's left
    return K.from_bm(name, bm, mat, loc, parent)


def curtain(name, w, h, tie, side, mat, loc, parent=None, folds=7, depth=0.14):
    """A velvet curtain hanging from `loc` (top edge centre), `w` wide and `h`
    long, gathered at `tie` (a fraction of the length) towards its outer edge
    (`side` +1 or -1 along X) by a gold rope with a tassel, flaring below.
    Its folds deepen where it is gathered."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    nx, nz = 28, 60
    vs = []
    for j in range(nz + 1):
        v = j / nz
        if v < tie:
            k = (v / tie) ** 1.5
            k = k * k * (3 - 2 * k)
            width, centre = w * (1 - 0.84 * k), side * 0.42 * w * k
        else:
            k = (v - tie) / (1 - tie)
            width, centre = w * (0.16 + 0.34 * k), side * (0.42 * w + 0.05 * w * k)
        pinch = 1 - abs(v - tie) / max(tie, 1 - tie)
        row = []
        for i in range(nx + 1):
            u = i / nx
            fx = centre + (u - 0.5) * width
            fy = depth * (0.6 + 1.4 * pinch) * math.sin(2 * math.pi * folds * u + 2.1 * v)
            row.append(bm.verts.new((fx, fy, -v * h)))
        vs.append(row)
    for j in range(nz):
        for i in range(nx):
            f = bm.faces.new((vs[j][i], vs[j + 1][i], vs[j + 1][i + 1], vs[j][i + 1]))
            f.smooth = True
            for loop, (uu, vv) in zip(f.loops, ((i, j), (i, j + 1), (i + 1, j + 1), (i + 1, j))):
                loop[uv].uv = (1 - uu / nx, 1 - vv / nz)
    ob = K.from_bm(name, bm, mat, loc, parent)
    tx, tz = loc[0] + side * 0.42 * w, loc[2] - tie * h
    rope = torus(name + "_tieback", 0.16 * w * 0.55, 0.045, (tx, loc[1], tz), MAT["gold"], parent)
    rope.scale = (1.0, 0.55, 0.6)
    cyl(name + "_tassel", 0.07, 0.35, (tx + side * 0.1, loc[1] + 0.22, tz - 0.3), MAT["gold"], parent, r2=0.03, seg=12)
    sphere(name + "_knot", 0.075, (tx + side * 0.1, loc[1] + 0.22, tz - 0.1), MAT["gold"], parent)
    return ob


def fringe(name, w, length, loc, parent=None, pitch=0.035):
    """A gold fringe: a row of thin twisted threads hanging from `loc` (the
    middle of its top edge), along X, `w` wide, all one mesh."""
    bm = bmesh.new()
    n = int(w / pitch)
    for k in range(n + 1):
        ln = length * (0.85 + 0.15 * ((k * 0.618) % 1.0))
        m = Matrix.Translation((-w / 2 + k * pitch, 0, -ln / 2))
        bmesh.ops.create_cone(bm, cap_ends=True, segments=5, radius1=pitch * 0.32, radius2=pitch * 0.22,
                              depth=ln, matrix=m)
    for f in bm.faces:
        f.smooth = True
    ob = K.from_bm(name, bm, MAT["gold"], loc, parent)
    box(name + "_band", (w, 0.03, 0.06), (loc[0], loc[1], loc[2] + 0.02), MAT["gold"], parent, 0)
    return ob


def plate(name, pts, depth, mat, loc, parent=None):
    """A flat polygon in the XZ plane, `depth` thick along Y."""
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, 0, z)) for x, z in pts])
    ob = K.from_bm(name, bm, mat, loc, parent)
    m = ob.modifiers.new("solid", "SOLIDIFY")
    m.thickness, m.offset = depth, 0.0
    return ob


def label(name, text, size, mat, loc, parent=None, font="LiberationSans-Bold.ttf"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = text
    cu.font = bpy.data.fonts.load(os.path.join("/usr/share/fonts/truetype/liberation", font))
    cu.size, cu.extrude = size, size * 0.03
    cu.align_x, cu.align_y = "CENTER", "CENTER"
    cu.materials.append(mat)
    ob = link(bpy.data.objects.new(name, cu), parent)
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, math.pi)          # upright, facing +Y
    return ob


def uv_box_front(ob):
    """Map the whole image onto the +Y face of a box made by kit.box."""
    me = ob.data
    uv = me.uv_layers.new()
    xs = [v.co.x for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    x0, x1, z0, z1 = min(xs), max(xs), min(zs), max(zs)
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = ((x1 - co.x) / (x1 - x0), (co.z - z0) / (z1 - z0))


def band(name, length, height, mat, loc, parent=None, rot=(0, 0, 0), repeat=1.0):
    """A flat strip in the XZ plane facing +Y, centred on `loc`, its image
    repeated `repeat` times along its length."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new()
    vs = [bm.verts.new((x, 0, z)) for x, z in ((length / 2, -height / 2), (-length / 2, -height / 2),
                                                (-length / 2, height / 2), (length / 2, height / 2))]
    f = bm.faces.new(vs)
    for loop, co in zip(f.loops, ((0, 0), (repeat, 0), (repeat, 1), (0, 1))):
        loop[uv].uv = co
    ob = K.from_bm(name, bm, mat, loc, parent)
    ob.rotation_euler = rot
    return ob


def seal(parent, loc, n, length=1.4, width=0.26):
    """A purity seal: a domed disc of dark red wax stamped with a cog, with a
    parchment prayer hanging from it."""
    x, y, z = loc
    cloth("parchment", width, length, MAT[f"parchment{n % 4}"], (x, y, z - 0.05), parent,
          folds=1, depth=0.015, seg=(4, 12))
    sphere("seal", 0.12, (x, y + 0.035, z), MAT["wax"], parent, (1, 0.4, 1))
    gear("seal_cog", 0.075, 10, 0.02, 0.035, 0.03, MAT["wax"], (x, y + 0.08, z), parent)


def in_collection(name):
    """Make a new collection the target for new objects; returns it."""
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[name]
    return coll


def back_to_scene(coll):
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection
    bpy.context.view_layer.layer_collection.children[coll.name].exclude = True


def a5000():
    """One blower-style RTX A5000, 1 unit long, fan towards +Y, bottom edge on
    z = 0, as a collection to instance. Seen from +Y the bracket is on the
    left and the fan on the right, as on the real card (world +X is the
    image's left). Its fan turns once per loop."""
    coll = in_collection("A5000")
    h, t = 0.415, 0.14
    box("shroud", (1.0, t, h), (0, 0, h / 2), MAT["shroud"], bevel=0.012)
    box("backplate", (1.0, 0.006, h * 0.98), (0, -t / 2 - 0.003, h / 2), MAT["facet"], bevel=0)
    plate("facet", [(0.14, 0.02), (-0.06, h - 0.02), (-0.49, h - 0.02), (-0.49, 0.02)], 0.008,
          MAT["facet"], (0, t / 2 + 0.004, 0))
    box("accent", (0.97, 0.004, 0.010), (0, t / 2 + 0.006, 0.014), MAT["green"], bevel=0)
    label("model", "RTX A5000", 0.055, MAT["silver"], (0.24, t / 2 + 0.010, h * 0.56))
    hub = empty("fan_pivot", (-0.30, t / 2 - 0.02, h / 2))
    cyl("fan_well", 0.160, 0.03, (-0.30, t / 2 - 0.04, h / 2), MAT["iron_dk"], axis="Y")
    torus("fan_ring", 0.163, 0.010, (-0.30, t / 2 + 0.006, h / 2), MAT["silver"], axis="Y")
    spin = empty("fan_spin", (0, 0, 0), hub)
    f = Mo.load("fan", 0.29)
    f.parent = spin
    f.location = (0, 0, -0.145)
    f.data.materials.clear()
    f.data.materials.append(MAT["shroud"])
    cyl("fan_cap", 0.05, 0.02, (0, 0.03, 0), MAT["silver"], spin, axis="Y")
    # one full turn per loop, exact whatever the blades; the close-ups turn it
    # one blade on, slower - the fan has nine blades and matches itself turned
    # 40 degrees to 0.3 % of its size
    turn = 2 * math.pi / 9 if SHOT else 2 * math.pi
    MOVERS.append((spin, lambda ph, s=spin: setattr(s, "rotation_euler", (0.0, -turn * ph, 0.0))))
    box("bracket", (0.012, t * 1.1, h * 1.08), (0.506, 0, h / 2), MAT["silver"], bevel=0)
    for k in range(4):
        box("port", (0.006, 0.05, 0.035), (0.515, 0, 0.07 + k * 0.08), MAT["iron_dk"], bevel=0)
    box("fingers", (0.36, 0.02, 0.03), (0.14, 0, -0.012), MAT["gold"], bevel=0)
    box("power", (0.06, 0.05, 0.03), (-0.42, 0, h + 0.012), MAT["iron_dk"], bevel=0)
    back_to_scene(coll)
    return coll


def card(coll, length, loc, parent=None, rot=(0, 0, 0)):
    e = empty("card", loc, parent, rot)
    e.instance_type = "COLLECTION"
    e.instance_collection = coll
    e.scale = (length,) * 3
    return e


def candles(parent, spots, seed=0):
    for k, (cx, cy, base) in enumerate(spots):
        h = 0.25 + 0.35 * (((k + seed) * 0.618) % 1.0)
        cyl("candle", 0.06, h, (cx, cy, base + h / 2), MAT["candle_wax"], parent, seg=12)
        sphere("flame", 0.04, (cx, cy, base + h + 0.05), MAT["flame"], parent, (1, 1, 2.0))


def candle_cluster(parent, cx, cy, base, n, seed, spread=(0.32, 0.16), drips=0, edge=None, light=30):
    """A clump of candles of mixed height burnt down into a pool of their own
    wax, lit by one warm point light. With `drips`, runs of wax hang over the
    edge at y = `edge`."""
    import random
    rnd = random.Random(seed)
    sphere("wax_pool", 1.0, (cx, cy, base), MAT["candle_wax"], parent, (spread[0] + 0.12, spread[1] + 0.1, 0.035))
    for k in range(n):
        x, y = cx + rnd.uniform(-spread[0], spread[0]), cy + rnd.uniform(-spread[1], spread[1])
        h, r = rnd.uniform(0.10, 0.62), rnd.uniform(0.032, 0.062)
        cyl("candle", r, h, (x, y, base + h / 2), MAT["candle_wax"], parent, seg=12)
        sphere("wax_rim", r * 1.15, (x, y, base + h - r * 0.2), MAT["candle_wax"], parent, (1, 1, 0.45))
        sphere("flame", r * 0.55, (x, y, base + h + r * 0.95), MAT["flame"], parent, (1, 1, 2.3))
    for k in range(drips):
        x, ln = cx + rnd.uniform(-spread[0] - 0.1, spread[0] + 0.1), rnd.uniform(0.08, 0.38)
        cyl("wax_drip", 0.024, ln, (x, edge, base - ln / 2), MAT["candle_wax"], parent, r2=0.008, seg=8)
        sphere("wax_bead", 0.03, (x, edge, base - 0.01), MAT["candle_wax"], parent, (1.2, 1.0, 0.8))
    lt = bpy.data.lights.new("cluster", "POINT")
    lt.energy, lt.color, lt.shadow_soft_size = light, (1.0, 0.52, 0.20), 0.25
    link(bpy.data.objects.new("cluster", lt), parent).location = (cx, cy, base + 0.75)


def coolant_tube(parent, loc, h=3.0):
    """A glass cylinder of glowing coolant on a brass base under a brass cap,
    caged by four rods; it lights its surroundings cyan."""
    x, y, z = loc
    cyl("tube_base", 0.44, 0.34, (x, y, z + 0.17), MAT["gold"], parent, seg=32)
    torus("tube_collar", 0.37, 0.05, (x, y, z + 0.38), MAT["gold"], parent)
    shell = cyl("tube_shell", 0.33, h, (x, y, z + 0.34 + h / 2), MAT["tube_glass"], parent, seg=40)
    shell.visible_shadow = False                  # the glass must not hold in the light inside it
    cyl("tube_core", 0.20, h - 0.05, (x, y, z + 0.34 + h / 2), MAT["coolant"], parent, seg=32)
    top = z + 0.34 + h
    torus("tube_collar", 0.37, 0.05, (x, y, top), MAT["gold"], parent)
    cyl("tube_cap", 0.44, 0.30, (x, y, top + 0.15), MAT["gold"], parent, seg=32)
    cyl("tube_spire", 0.18, 0.7, (x, y, top + 0.65), MAT["gold"], parent, r2=0.01, seg=16)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        cyl("tube_rod", 0.03, h, (x + 0.39 * math.cos(a), y + 0.39 * math.sin(a), z + 0.34 + h / 2), MAT["iron"], parent, seg=8)
    lt = bpy.data.lights.new("coolant", "POINT")
    lt.energy, lt.color, lt.shadow_soft_size = 160, (0.25, 0.80, 1.0), 0.3
    link(bpy.data.objects.new("coolant", lt), parent).location = (x, y + 0.5, z + 0.34 + h / 2)


def dressed(name, height, mat):
    """A loaded model with one material."""
    ob = Mo.load(name, height)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


PAINTED = {}


def cog_mechanicum(height, loc, parent=None, rot=(0, 0, 0)):
    """The Cog Mechanicum medallion painted as the icon is coloured: the cog
    brass, the field red behind the machine half of the skull and black
    behind the bone half, the bone half aged bone, the machine half worn
    gunmetal, the ribbed hoses dark iron, the grilled eye glowing red.

    The STL is 155 separate pieces - base disc and ring, the two skull
    halves, hose segments, bolts - and each piece takes one colour, except
    the disc, split into ring and field by radius and side, and the eye, cut
    out of the machine half by its circle. Painted once at 1 unit tall;
    copies share the mesh."""
    if "mesh" not in PAINTED:
        slots = ["gold", "enamel_red", "enamel_black", "bone", "gunmetal", "iron_dk", "eye"]
        ob = Mo.load("medallion", 1.0)
        ob.data = ob.data.copy()
        ob.data.materials.clear()
        for k in slots:
            ob.data.materials.append(MAT[k])
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.separate(type="LOOSE")
        bpy.ops.object.mode_set(mode="OBJECT")
        pieces = list(bpy.context.selected_objects)
        eye, eye_r = Vector((0.14, 0.5)), 0.072          # the grilled eye, on the machine half (+X)
        for p in pieces:
            me = p.data
            n = len(me.polygons)
            c = [Vector((q.center.x, q.center.z)) for q in me.polygons]
            lo = Vector((min(v.x for v in c), min(v.y for v in c)))
            hi = Vector((max(v.x for v in c), max(v.y for v in c)))
            mid, size = (lo + hi) / 2, hi - lo
            if max(size) > 0.6:                           # the disc and the cog ring
                idx = [0 if (v - Vector((0, 0.5))).length > 0.37 else (1 if v.x > 0 else 2) for v in c]
            elif size.y > 0.4:                            # a skull half
                if mid.x > 0:
                    idx = [6 if (v - eye).length < eye_r else 4 for v in c]
                else:
                    idx = [3] * n
            elif (mid - eye).length < eye_r:              # parts of the eye's grille
                idx = [6] * n
            elif max(size) < 0.035 and n > 3000:          # a segment of a ribbed hose
                idx = [5] * n
            else:                                         # bolts and fittings
                idx = [0] * n
            me.polygons.foreach_set("material_index", idx)
        bpy.context.view_layer.objects.active = pieces[0]
        bpy.ops.object.join()
        tmp = bpy.context.view_layer.objects.active
        PAINTED["mesh"] = tmp.data
        bpy.data.objects.remove(tmp)
    ob = link(bpy.data.objects.new("cog_mechanicum", PAINTED["mesh"]), parent)
    ob.location, ob.rotation_euler, ob.scale = loc, rot, (height,) * 3
    return ob


def painted(name, height, classify, slots, loc, yaw=0.0, parent=None):
    """A model painted by part: `classify` (src/paintfig.py) gives each face
    a class, `slots` the material for each class. The painted mesh is a copy
    made once per model and size."""
    key = (name, height)
    if key not in PAINTED:
        ob = Mo.load(name, height)
        me = ob.data.copy()
        me.materials.clear()
        for k in slots:
            me.materials.append(MAT[k])
        me.polygons.foreach_set("material_index", classify(me))
        PAINTED[key] = me
        ob.hide_render = ob.hide_viewport = True          # the loader keeps it as its template
    ob = link(bpy.data.objects.new(name, PAINTED[key]), parent)
    ob.location, ob.rotation_euler = loc, (0, 0, math.radians(yaw))
    return ob


def figure(name, height, mat, loc, yaw=0.0, sink=0.0, parent=None):
    """A model standing at `loc`, turned `yaw` degrees from facing the camera
    (180 faces the altar). `sink` lowers it by that fraction of its height,
    so a sculpted base goes under the floor."""
    ob = dressed(name, height, mat)
    ob.parent = parent
    ob.location = (loc[0], loc[1], loc[2] - sink * height - (0.004 if sink else 0))
    ob.rotation_euler = (0, 0, math.radians(yaw))
    return ob


# ------------------------------------------------------------------- build --
def nave():
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0))
    bpy.context.object.data.materials.append(MAT["floor"])
    walls = {k: dressed(k, STOREY, MAT["stone"]) for k in ("wall_a", "wall_b")}
    for w in walls.values():                       # templates; the nave uses copies
        w.hide_render = w.hide_viewport = True
    d = Mo.dims(walls["wall_a"])
    bay, depth = d.x, d.y
    for side in (-1, 1):
        for k in range(4):
            yc = 6.0 - k * bay
            for storey in (0, 1):
                ob = walls["wall_a" if (k + storey + (side > 0)) % 2 else "wall_b"].copy()
                ob.hide_render = ob.hide_viewport = False
                link(ob)
                # front face to the nave, the L-arm outwards
                ob.rotation_euler = (0, 0, side * math.pi / 2)
                ob.location = (side * (WALL_X + depth / 2 - 0.9), yc, storey * STOREY)
        band(f"frieze{side}", 4 * bay, 1.3, MAT["frieze"], (side * (WALL_X - 0.15), 6.0 - 1.5 * bay, STOREY - 0.4),
             rot=(0, 0, side * math.pi / 2), repeat=4 * bay / (1.3 * 4096 / 160))
        # stained glass behind the windows, lit from outside; in the close-ups
        # a painted window per bay (generated: saint, Machine God, Magos)
        if SHOT:
            for k in range(4):
                box(f"glass{side}{k}", (0.05, bay, 2 * STOREY), (side * (WALL_X + 2.2), 6.0 - k * bay, STOREY),
                    window_mat(f"window_{(k + (side > 0)) % 3}", side), bevel=0)
        else:
            box(f"glass{side}", (0.05, 4 * bay, 2 * STOREY), (side * (WALL_X + 2.2), 6.0 - 1.5 * bay, STOREY),
                MAT["glass"], bevel=0)
    for side in (-1, 1):
        for k in range(3):
            pillar(side * 12.6, 6.0 - bay / 2 - k * bay, side, bay)
    return bay


def pillar(x, y, side, bay):
    p = empty(f"pillar{x}{y}", (x, y, 0))
    box("plinth", (2.8, 2.8, 1.2), (0, 0, 0.6), MAT["stone"], p, 0.06)
    cyl("shaft", 0.95, 44, (0, 0, 22), MAT["pillar"], p)
    for k in range(8):
        a = 2 * math.pi * k / 8
        cyl("rib", 0.3, 44, (0.95 * math.cos(a), 0.95 * math.sin(a), 22), MAT["pillar"], p, seg=16)
    for zz in (1.35, 6.2, 12.5, 18.5):
        cyl("band", 1.42, 0.38, (0, 0, zz), MAT["gold"], p)
    # a priest statue on a corbel, facing the aisle
    box("corbel", (1.8, 1.8, 0.5), (-side * 1.4, 0, 6.9), MAT["gold"], p, 0.05)
    kind = ("statue_young", "statue_old", "statue_dark", "statue_skeleton")[int(abs(y) + (side > 0)) % 4]
    figure(kind, 3.0, MAT["statue"], (-side * 1.5, 0, 7.15), side * 90, parent=p)
    cog_mechanicum(1.7, (-side * 1.0, 0, 11.0), p, (0, 0, side * math.pi / 2))
    candles(p, [(-side * 1.2 + dx, dy, 1.2) for dx, dy in ((0, -0.8), (0.2, -0.35), (0, 0.1), (0.2, 0.55), (0, 0.95))],
            seed=int(abs(y)))
    # a banner hanging towards the camera from this pillar's side
    b = empty("banner_pivot", (-side * 0.6, bay / 2, 13.2), p, rot=(0, 0, side * math.pi / 2))
    n = int(abs(y) * 7 + (side > 0) * 3) % 6
    cloth("banner", 3.0, 8.2, MAT[f"banner{n}"], (0, 0, 0), b, folds=3, depth=0.10)
    for k, sx in enumerate((-1.35, 1.35)):
        seal(b, (sx * 0.85, 0.16, -0.35), n + k, length=1.6)
    off = (y * 0.07 + side * 0.2) % 1.0
    MOVERS.append((b, lambda ph, b=b, o=off, s=side:
                   setattr(b, "rotation_euler", (math.radians(1.6) * math.sin(2 * math.pi * (ph + o)), 0, s * math.pi / 2))))


def shrine(gpu, x, y):
    s = -1 if x > 0 else 1
    sh = empty(f"shrine{x}{y}", (x, y, 0), rot=(0, 0, s * math.radians(-18)))
    box("step", (4.4, 2.6, 0.3), (0, 0, 0.15), MAT["stone"], sh, 0.05)
    box("altar", (3.6, 1.5, 1.2), (0, 0, 0.9), MAT["iron"], sh, 0.05)
    box("altar_cap", (3.9, 1.8, 0.14), (0, 0, 1.57), MAT["gold"], sh, 0.02)
    cloth("altar_cloth", 1.6, 1.0, MAT["banner0"], (0, 0.80, 1.5), sh, folds=2, depth=0.02, seg=(8, 12))
    card(gpu, 2.2, (0, 0.15, 1.64), sh)
    for k, sx in enumerate((-1.2, -0.4, 0.9)):
        seal(sh, (sx, 0.97, 1.5), k + int(abs(y)), length=0.9 + 0.2 * k, width=0.2)
    halo = empty("halo", (0, -0.45, 2.1), sh)
    gear("halo_gear", 1.7, 24, 0.2, 1.45, 0.1, MAT["gold"], (0, 0, 0), halo)
    MOVERS.append((halo, lambda ph, h=halo: setattr(h, "rotation_euler", (0.0, 2 * math.pi / 24 * ph, 0.0))))
    cb = Mo.load("candelabra", 1.3)
    cb.parent = sh
    cb.location = (0, -0.4, 1.64)
    figure("reliquary", 1.0, MAT["gold"], (-1.55, 0.05, 1.64), parent=sh)
    # a worshipper kneels on the aisle side, facing the shrine, in profile to the camera
    kneeler = ("kneel_cloak", "kneel_monk", "kneel_saint", "kneel_cloak")[int(abs(y) // 12 + (x > 0) * 2) % 4]
    figure(kneeler, 1.35, MAT["robe"], (s * 2.9, 1.2, 0.3), -s * 90, sink=0.05, parent=sh)
    candles(sh, [(-1.6, 0.55, 1.64), (-1.3, 0.62, 1.64), (1.6, 0.55, 1.64), (1.3, 0.62, 1.64),
                 (-2.0, 1.0, 0.3), (2.0, 1.0, 0.3), (-1.7, 1.1, 0.3), (1.7, 1.1, 0.3)])
    lt = bpy.data.lights.new("candles", "POINT")
    lt.energy, lt.color, lt.shadow_soft_size = 70, (1.0, 0.55, 0.22), 0.6
    link(bpy.data.objects.new("candles", lt), sh).location = (0, 1.0, 2.2)


def altar(gpu):
    """The altar-machine at the end of the nave."""
    al = empty("altar", (0, ALTAR_Y, 0))
    al.scale = (ALTAR_SCALE,) * 3
    for k, (w, d, h) in enumerate(((22, 7.0, 0.35), (20, 5.6, 0.7), (18, 4.2, 1.05))):
        box(f"step{k}", (w, d, 0.35), (0, -d / 2 + 3.0, h - 0.175), MAT["stone"], al, 0.03)
        n = 26 - 3 * k                            # a row of candles along every step
        front = 3.0 - (7.0 - d) - 0.35
        candles(al, [(-w / 2 + 0.8 + i * (w - 1.6) / (n - 1), front + (i % 2) * 0.25, h) for i in range(n)], seed=k)
    box("table", (9.0, 2.6, 1.6), (0, -0.9, 1.85), MAT["iron"], al, 0.05)
    box("table_cap", (9.6, 3.0, 0.16), (0, -0.9, 2.73), MAT["gold"], al, 0.02)
    cloth("frontal", 3.6, 1.5, MAT["banner2"], (0, 0.42, 2.65), al, folds=3, depth=0.03, seg=(12, 16))
    for s in (-1, 1):
        cog_mechanicum(1.1, (s * 3.0, 0.42, 1.35), al)
        cb = Mo.load("candelabra", 1.6)
        cb.parent = al
        cb.location = (s * 2.85, -0.9, 2.81)
        if SHOT != "altar":
            figure("banner_cherubs", 2.0, MAT["statue"], (s * 4.0, -0.9, 2.81), -s * 12, parent=al)
    for k, sx in enumerate((-4.2, -2.2, -1.2, 1.2, 2.2, 4.2)):
        seal(al, (sx, 0.52, 2.62), k, length=1.0 + 0.25 * (k % 3), width=0.22)
    band("step_frieze", 17.6, 0.3, MAT["frieze"], (0, 3.0 - 4.2 + 0.01, 1.05 - 0.175), al, repeat=17.6 / (0.3 * 4096 / 160))
    box("screen_frame", (2.5, 0.22, 1.6), (0, -0.4, 3.75), MAT["relief2"], al, 0.03)
    sc = box("screen", (2.2, 0.05, 1.35), (0, -0.28, 3.75), MAT["screen"], al, 0)
    uv_box_front(sc)

    tw = empty("tower", (0, -3.5, 0), al)
    box("body", (12.0, 3.0, 13.2), (0, -1.5, 9.4), MAT["iron"], tw, 0.05)
    box("heart", (4.4, 0.2, 7.0), (0, 0.05, 6.8), MAT["cells"], tw, 0)
    lan = dressed("lancet", 7.0, MAT["gold"])
    lan.parent = tw
    lan.location = (0, 0.25, 3.1)
    box("stand", (1.6, 0.8, 2.6), (0, 0.9, 4.2), MAT["relief2"], tw, 0.04)
    for k, sx in enumerate((-0.55, 0.0, 0.55)):
        seal(tw, (sx, 1.32, 5.3), k + 1, length=1.2, width=0.22)
    card(gpu, 4.2, (0, 0.9, 5.5), tw)
    for s in (-1, 1):
        cyl(f"column{s}", 0.55, 12.2, (s * 3.3, 0.45, 8.9), MAT["pewter"], tw, seg=24)
        cyl(f"pinnacle{s}", 0.55, 2.6, (s * 3.3, 0.45, 16.3), MAT["pewter"], tw, r2=0.02, seg=12)
        rk = empty(f"rack{s}", (s * 7.6, 0.2, 2.8), tw)
        box("rack_back", (3.0, 0.3, 11.5), (0, -0.4, 5.75), MAT["iron_dk"], rk, 0)
        box("rack_cells", (2.8, 0.05, 11.2), (0, -0.22, 5.75), MAT["cells"], rk, 0)
        arch("rack_arch", 3.3, 10.0, 0.3, 0.4, MAT["pewter"], (0, 0.1, 0), rk)
        for k in range(8):
            card(gpu, 2.4, (0, 0.05, 0.4 + k * 1.2), rk)
        cloth(f"drape{s}", 3.2, 12.5, MAT["crimson"], (s * 5.2, 0.9, 16.0), tw, folds=4, depth=0.22,
              seg=(20, 60), taper=0.35)
    pq = box("plaque", (3.0, 0.1, 1.8), (0, 0.2, 11.2), MAT["plaque"], tw, 0)
    for s in (-1, 1):                             # a pair of cogs either side, turning against each other
        cg = empty(f"cog{s}", (s * 2.12, 0.35, 11.2), tw)
        gear("cog", 0.52, 16, 0.1, 0.18, 0.12, MAT["gold"], (0, 0, 0), cg)
        MOVERS.append((cg, lambda ph, c=cg, s=s: setattr(c, "rotation_euler", (0.0, s * 2 * math.pi / 16 * ph, 0.0))))
    uv_box_front(pq)
    sk = dressed("skull", 2.8, MAT["bone"])
    sk.parent = tw
    sk.location = (0, 1.0, 12.7)
    burst = empty("burst", (0, 0.35, 14.1), tw)
    n = 36
    for k in range(n):
        a = 2 * math.pi * k / n
        ln = 3.0 if k % 2 == 0 else 2.0
        ray = cyl("ray", 0.08, ln, (0, 0, 0), MAT["gold"], burst, r2=0.005, seg=6)
        ray.rotation_euler = (0, math.pi / 2 - a, 0)
        ray.location = (math.cos(a) * (2.0 + ln / 2), 0, math.sin(a) * (2.0 + ln / 2))
    # 72 segments of 5 degrees: the 20-degree turn per loop moves each ring by
    # exactly four segments
    torus("burst_ring", 2.0, 0.13, (0, 0, 0), MAT["gold"], burst, axis="Y", seg=72)
    torus("burst_glow", 1.88, 0.05, (0, 0.1, 0), MAT["halo"], burst, axis="Y", seg=72)
    # the rays alternate long and short, so the pattern repeats every two rays
    MOVERS.append((burst, lambda ph, b=burst: setattr(b, "rotation_euler", (0.0, 2 * 2 * math.pi / n * ph, 0.0))))
    for rank, (dy, x0, grow) in enumerate(((-3.4, 0.0, 12.0), (-4.6, 0.45, 18.0))):
        for k in range(-14, 15):
            x = k * 0.9 + x0
            if abs(x) > 12.5:
                continue
            h = 9.0 + grow * (1 - abs(x) / 13.0) ** 1.4
            r = 0.40 - 0.1 * abs(x) / 13.0
            cyl(f"pipe{rank}{k}", r, h, (x, dy, 15.9 + h / 2), MAT["pewter"], tw, seg=20)
    for k in range(9):
        s = -1 if k % 2 else 1
        x0 = s * (1.5 + k * 0.5)
        curve(f"cable{k}", [(x0, -2.1, 15.5 - k * 0.5), (x0 * 0.5, 0.0, 10.5 - k * 0.7),
                            (s * 6.8, 0.3, 4.0 + k * 0.5)], 0.07 + 0.02 * (k % 3), MAT["cable"], tw)
    lt = bpy.data.lights.new("heart_glow", "POINT")
    lt.energy, lt.color, lt.shadow_soft_size = 250 if SHOT else 900, (0.35, 1.0, 0.45), 1.5
    link(bpy.data.objects.new("heart_glow", lt), tw).location = (0, 1.4, 6.8)
    for s in (-1, 1):
        lt = bpy.data.lights.new("step_candles", "POINT")
        lt.energy, lt.color, lt.shadow_soft_size = 80 if SHOT else 500, (1.0, 0.55, 0.20), 3.0
        link(bpy.data.objects.new("step_candles", lt), al).location = (s * 5.5, 1.2, 1.8)
    return al, tw


STEP_TOP = 1.05 * 1.25                 # height of the top altar step in the world
STEPS_FRONT = ALTAR_Y + 1.25 * 3.0     # y of the altar steps' front edge

# the congregation, row by row towards the altar: (y, [(x, model), ...])
CONGREGATION = [
    (-18.0, [(-2.4, "kneel_cloak"), (-0.8, "kneel_monk"), (0.9, "kneel_hooded"), (2.5, "kneel_saint")]),
    (-22.5, [(-1.7, "kneel_monk"), (0.1, "kneel_cloak"), (1.8, "kneel_monk")]),
    (-27.0, [(-2.5, "kneel_saint"), (-0.8, "kneel_hooded"), (1.0, "kneel_cloak"), (2.6, "kneel_monk")]),
    (-31.5, [(-1.6, "kneel_cloak"), (0.3, "kneel_saint"), (2.0, "kneel_hooded")]),
]
KNEEL = {"kneel_cloak": (1.4, 0.03), "kneel_monk": (1.25, 0.0), "kneel_saint": (1.25, 0.05), "kneel_hooded": (1.8, 0.08)}


def catenary(a, b, sag, n=6):
    """Points of a cable hung between a and b, dropping `sag` at its middle."""
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, t) - Vector((0, 0, sag * 4 * t * (1 - t))) for t in (k / (n - 1) for k in range(n))]


def wires(parent, seed):
    """Heavy cabling across the front of the tower: bundles of cables of
    mixed thickness slung between the top of the machine and the racks,
    columns and relic stand, and fat ringed conduits dropping to the floor.
    Coordinates are the tower's own."""
    import random
    rnd = random.Random(seed)
    tops = [(x, 0.5, rnd.uniform(12.5, 16.0)) for x in (-5.8, -4.6, -3.0, -1.6, 1.4, 2.9, 4.4, 5.9)]
    lows = [(-7.6, 0.6, 9.5), (-7.6, 0.6, 6.0), (-3.3, 1.0, 7.0), (-1.0, 1.4, 4.4), (1.0, 1.4, 4.4),
            (3.3, 1.0, 7.0), (7.6, 0.6, 6.0), (7.6, 0.6, 9.5), (-5.0, 1.2, 3.0), (5.0, 1.2, 3.0)]
    mats = [MAT["cable"], MAT["cable"], MAT["cable_red"], MAT["conduit"]]
    for k in range(34):
        a = Vector(rnd.choice(tops)) + Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(0, 0.4), 0))
        b = Vector(rnd.choice(lows)) + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(0, 0.3), 0))
        sag = rnd.uniform(0.6, 2.6)
        for j in range(rnd.randint(2, 5)):                   # a bundle of parallel strands
            off = Vector((rnd.uniform(-0.12, 0.12), rnd.uniform(0, 0.15), rnd.uniform(-0.1, 0.1)))
            curve(f"wire{k}_{j}", catenary(a + off, b + off, sag + rnd.uniform(-0.15, 0.15)),
                  rnd.uniform(0.018, 0.05), rnd.choice(mats), parent)
    for k, (x, s) in enumerate(((-6.6, 1), (6.6, -1), (-2.3, 1), (2.3, -1))):   # conduits to the floor
        pts = [(x, 0.8, 15.5), (x + s * 0.4, 1.4, 9.0), (x + s * 0.9, 2.2, 3.0), (x + s * 1.6, 3.8, 0.2)]
        curve(f"conduit{k}", pts, 0.17, MAT["conduit"], parent)
        for a, b in zip(pts[:-1], pts[1:]):                  # brass rings along each stretch
            for t in (0.3, 0.7):
                ring = torus("conduit_ring", 0.2, 0.035, (0, 0, 0), MAT["gold"], parent)
                ring.location = Vector(a).lerp(Vector(b), t)
                ring.rotation_euler = (Vector(b) - Vector(a)).to_track_quat("Z", "Y").to_euler()


def dress_closeup(gpu, al, tw):
    """Detail only a close camera sees: Latin plaques and Mechanicum devices
    on the tower, a row of skulls and the embroidered antependium on the
    altar table, stoles on the relic stand, and the cabling."""
    wires(tw, 7)
    # plaques around the heart and between the columns and the racks
    spots = [(-4.6, 11.0), (4.6, 11.0), (-4.6, 8.9), (4.6, 8.9), (-4.6, 6.8), (4.6, 6.8), (-4.6, 4.7), (4.6, 4.7),
             (-1.6, 2.35), (1.6, 2.35), (-9.9, 1.9), (9.9, 1.9)]
    for n, (x, z) in enumerate(spots):
        pl = box(f"plaque{n}", (1.1, 0.06, 0.55), (x, 0.12, z), MAT[f"plaque{n % 12}"], tw, 0.01)
        uv_box_front(pl)
    # Mechanicum devices on round-topped plates, over the columns and the rack arches
    for n, (x, z) in enumerate(((-3.3, 14.2), (3.3, 14.2), (-7.6, 13.9), (7.6, 13.9), (-5.9, 12.2), (5.9, 12.2))):
        ic = box(f"icon{n}", (0.95, 0.06, 0.95), (x, 0.9 if abs(x) < 4 else 0.35, z), MAT[f"icon{n}"], tw, 0.01)
        uv_box_front(ic)
        gear(f"icon_rim{n}", 0.62, 16, 0.07, 0.5, 0.06, MAT["gold"], (x, (0.9 if abs(x) < 4 else 0.35) + 0.04, z), tw)
    # a band of binary prayer under the plaque, and across the table's edge
    band("binary_band", 5.0, 0.22, MAT["binary"], (0, 0.26, 9.95), tw, repeat=5.0 / (0.22 * 4096 / 96))
    band("table_binary", 9.4, 0.14, MAT["binary"], (0, 0.61, 2.62), al, repeat=9.4 / (0.14 * 4096 / 96))
    # the antependium on the table's front, over the plain frontal
    cloth("antependium", 5.6, 3.06, MAT["antependium"], (0, 0.47, 2.62), al, folds=4, depth=0.04, seg=(28, 16))
    # skulls in cog halos along the table's front edge, candles burnt down
    # between them, their wax running over the edge
    for k, x in enumerate((-4.0, -2.0, 0.0, 2.0, 4.0)):
        cog_mechanicum(0.6, (x, 0.32, 2.81), al, (math.radians(-6), 0, math.radians((k - 2) * 5)))
    for k, x in enumerate((-3.0, -1.0, 1.0, 3.0)):
        candle_cluster(al, x, 0.30, 2.81, 7, 20 + k, drips=4, edge=0.615)
    for s in (-1, 1):
        candle_cluster(al, s * 3.3, -1.75, 2.81, 9, 30 + s, spread=(0.45, 0.25), light=60)
        coolant_tube(al, (s * 4.35, -1.55, 2.81))
    # the screen smaller, under a pointed pediment with a skull
    for name, size in (("screen_frame", (1.95, 0.22, 1.30)), ("screen", (1.62, 0.05, 1.0))):
        ob = bpy.data.objects[name]
        ob.scale = (size[0] / ob.dimensions.x, 1.0, size[2] / ob.dimensions.z)
    plate("pediment", [(-1.05, 0.0), (1.05, 0.0), (0.0, 0.75)], 0.2, MAT["pewter"], (0, -0.4, 4.4), al)
    cog_mechanicum(0.42, (0, -0.27, 4.46), al)
    for s in (-1, 1):
        cyl("pinnacle", 0.07, 0.6, (s * 1.0, -0.4, 4.7), MAT["gold"], al, r2=0.005, seg=10)
    # crimson curtains gathered back either side of the relic, their hems on the table
    for s in (-1, 1):
        curtain(f"curtain{s}", 2.7, 6.7, 0.52, s, MAT["velvet"], (s * 3.55, 1.35, 9.6), tw)
    # crimson hangings with gold fringe over the table's ends, beside the antependium
    for k, s in enumerate((-1, 1)):
        cloth(f"end_cloth{s}", 1.9, 2.05, MAT[f"hanging{k}"], (s * 3.85, 0.64, 2.8), al, folds=3, depth=0.05, seg=(16, 24))
    # more purity seals pinned along the hem, their prayers hanging over the cloth
    for k, sx in enumerate((-3.3, -0.7, 0.7, 3.3)):
        seal(al, (sx, 0.70, 2.60), k + 3, length=0.8 + 0.3 * (k % 2), width=0.2)
    # brass bands up the columns
    for s in (-1, 1):
        for k in range(7):
            torus(f"column_band{s}{k}", 0.58, 0.07, (s * 3.3, 0.45, 3.6 + k * 1.75), MAT["gold"], tw)
    # embroidered stoles hanging either side of the relic stand
    for s in (-1, 1):
        cloth(f"stole{s}", 0.45, 3.2, MAT["velvet"], (s * 0.95, 1.33, 5.45), tw, folds=1, depth=0.03, seg=(4, 20))


def figures(gpu):
    """Everyone prays: the congregation kneels towards the altar, the priests
    lead the rite with raised arms, the servitors bow. In the close-up the two
    priests stand on the altar table either side of the relic, in profile, and
    two adepts kneel on the steps just in front of the camera."""
    for y, row in CONGREGATION:
        for k, (x, name) in enumerate(row):
            h, sink = KNEEL[name]
            jitter = ((x * 7.3 + y * 3.1) % 1.0 - 0.5) * 16
            figure(name, h, MAT["robe"], (x, y, 0), 180 + jitter, sink)
    # standing in prayer near the camera, hands pressed together, turned to the altar
    figure("pray_cultist", 1.95, MAT["robe"], (-4.2, -12.0, 0), 150)
    figure("pray_hooded", 1.95, MAT["robe"], (4.4, -13.0, 0), 210)
    if SHOT != "offering":
        figure("pray_cultist", 1.95, MAT["robe"], (5.0, -33.5, 0), 200)
        figure("pray_hooded", 1.95, MAT["robe"], (-5.2, -34.5, 0), 160)
    if SHOT == "offering":
        # as in the references: a card held up to the altar-machine, its fan
        # side turned back towards us, purity seals hanging from it
        pr = figure("shock_priest", 2.2, MAT["robe"], (OFFERING[0], OFFERING[1], 0), 164)
        card(gpu, 1.5, (0, 0.29, 1.62), pr, rot=(0, 0, math.pi))
        for k, sx in enumerate((-0.45, 0.25)):         # hung in the priest's frame, not the scaled card's
            seal(pr, (sx, 0.22, 1.60), k + 2, length=0.6, width=0.12)
        figure("kneel_cloak", 1.4, MAT["robe"], (0.5, OFFERING[1] + 0.5, 0), 185, 0.03)
        figure("magus", 2.7, MAT["robe"], (-3.2, STEPS_FRONT - 1.0, STEP_TOP), 185)
    elif SHOT == "altar":
        # a servitor bowed in profile before the altar, close to the camera;
        # it rises and falls by a centimetre once per loop, as if breathing
        sv = painted("servitor", 2.0, PF.servitor,
                     ["skin", "servitor_cloth", "near_servitor", "leather", "servitor_brass", "rubber"],
                     (*SERVITOR, 0), 95)
        MOVERS.append((sv, lambda ph, o=sv: setattr(o, "location", (*SERVITOR, 0.005 * (1 - math.cos(2 * math.pi * ph))))))
        priest = ["skin", "priest_robe", "near_servitor", "leather", "servitor_brass", "rubber"]
        painted("magus", 2.7, PF.magus, priest, (-4.4, TABLE_Y + 0.2, TABLE_TOP), -90)
        painted("shock_priest", 2.2, PF.shock_priest, priest, (4.4, TABLE_Y + 0.1, TABLE_TOP), 90)
    if SHOT in ("offering", "altar"):
        # two embroidered banners hang close, either side of the relic
        for s in (-1, 1):
            # in the altar shot they hang lower and nearer, framing the altar in crimson
            at = (s * 6.2, ALTAR_Y + 1.5, 10.5) if SHOT == "altar" else (s * 6.6, ALTAR_Y + 0.6, 14.5)
            b = empty(f"near_banner{s}", at, rot=(0, 0, -s * math.radians(14)))
            cloth("banner", 3.0, 8.2, MAT[f"banner{3 if s > 0 else 0}"], (0, 0, 0), b, folds=3, depth=0.10)
            for k, sx in enumerate((-1.15, 1.15)):
                seal(b, (sx, 0.16, -0.35), k + (s > 0), length=1.6)
            MOVERS.append((b, lambda ph, b=b, s=s: setattr(b, "rotation_euler", (
                math.radians(0.6) * math.sin(2 * math.pi * (ph + 0.3 * s)), 0, -s * math.radians(14)))))
    if SHOT in (None, "looming"):
        # the rite: the Magus and the shock priest on the top step, facing the altar
        figure("magus", 2.7, MAT["robe"], (-3.2, STEPS_FRONT - 1.0, STEP_TOP), 185)
        figure("shock_priest", 2.2, MAT["robe"], (3.2, STEPS_FRONT - 1.3, STEP_TOP), 175)
    # the Dominus and the Magos bless the congregation from the foot of the steps
    figure("dominus", 2.5, MAT["robe"], (-9.0, STEPS_FRONT + 1.6, 0), 20)
    figure("magos", 2.5, MAT["robe"], (9.0, STEPS_FRONT + 1.6, 0), -20, sink=0.04)
    # servitors bow at the steps; racked servitors hang at the sides
    figure("servitor", 2.0, MAT["servitor"], (-6.0, STEPS_FRONT + 2.0, 0), 190)
    figure("servitor", 2.0, MAT["servitor"], (6.0, STEPS_FRONT + 2.0, 0), 170)
    figure("servitor_rack", 2.8, MAT["servitor"], (-12.2, STEPS_FRONT + 2.4, 0), 30)
    figure("servitor_rack", 2.8, MAT["servitor"], (12.2, STEPS_FRONT + 2.4, 0), -30)
    # guardian reliefs on the far walls, facing the aisle
    for side in (-1, 1):
        figure("guardians", 3.4, MAT["statue"], (side * 13.4, STEPS_FRONT + 0.8, 0), side * 90)
    # servo-skulls drift over the congregation
    for k, (x, y, z) in enumerate(((-4.2, -27.0, 7.2), (5.0, -21.0, 8.6), (0.8, -35.0, 10.8))):
        piv = empty(f"skull{k}", (x, y, z))
        sk = dressed("servo_skull", 1.2, MAT["bone"])
        sk.parent = piv
        sk.location = (0, 0, -0.6)
        sphere("lens_glow", 0.1, (0.21, 0.53, 0.03), MAT["red_eye"], piv)
        o = k / 3
        MOVERS.append((piv, lambda ph, p=piv, x=x, y=y, z=z, o=o: (
            setattr(p, "location", (x + 0.35 * math.sin(2 * math.pi * (ph + o)),
                                    y + 0.25 * math.cos(2 * math.pi * (ph + o)),
                                    z + 0.22 * math.sin(4 * math.pi * (ph + o)))),
            setattr(p, "rotation_euler", (0, 0, math.radians(14) * math.sin(2 * math.pi * (ph + o)))))))
    # cherubs carry burning braziers near the altar, bobbing once per loop
    for k, (x, y) in enumerate(((-5.4, -23.0), (5.6, -21.5))):
        piv = empty(f"cherub{k}", (x, y, 5.6))
        figure("cherub_brazier", 3.2, MAT["gold"], (0, 0, 0), 20 if k else -20, parent=piv)
        sphere("brazier_fire", 0.17, (0, 0, 2.6), MAT["flame"], piv, (1.4, 1.4, 1.0))
        lt = bpy.data.lights.new("brazier", "POINT")
        lt.energy, lt.color, lt.shadow_soft_size = 60, (1.0, 0.5, 0.15), 0.3
        link(bpy.data.objects.new("brazier", lt), piv).location = (0, 0, 2.7)
        MOVERS.append((piv, lambda ph, p=piv, x=x, y=y, o=k * 0.5:
                       setattr(p, "location", (x, y, 5.6 + 0.25 * math.sin(2 * math.pi * (ph + o))))))


def censers():
    for k, (x, y) in enumerate(((-3.6, -11.0), (3.6, -17.0), (-3.2, -24.0), (3.4, -33.0))):
        piv = empty(f"censer{k}", (x, y, 30.0))
        cyl("chain", 0.03, 22.3, (0, 0, -11.15), MAT["iron"], piv, seg=8)
        th = Mo.load("thurible", 0.9, stack=True)
        th.data.materials.clear()
        th.data.materials.append(MAT["gold"])
        th.parent = piv
        th.location = (0, 0, -23.2)
        sphere("coals", 0.16, (0, 0, -22.95), MAT["amber"], piv)
        lt = bpy.data.lights.new("censer_glow", "POINT")
        lt.energy, lt.color, lt.shadow_soft_size = 40, (1.0, 0.45, 0.12), 0.3
        link(bpy.data.objects.new("censer_glow", lt), piv).location = (0, 0, -22.8)
        amp, off = math.radians(4.0), k * 0.25
        MOVERS.append((piv, lambda ph, p=piv, a=amp, o=off:
                       setattr(p, "rotation_euler", (0.0, a * math.sin(2 * math.pi * (ph + o)), 0.0))))
        # smoke rising from it: the box's centre sits 6.2 above the censer
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, 6.8 + 6.2))
        sm = bpy.context.object
        sm.name = "smoke"
        sm.scale = (3.4, 3.4, 12.4)
        sm.data.materials.append(MAT["smoke"])


def aisle(gpu):
    for x in (-2.2, -0.9, 0.9, 2.2):
        box(f"trace{x}", (0.06, 50, 0.01), (x, -14.0, 0.004), MAT["trace"], bevel=0)
    for x, y in ((-6.8, -14.0), (6.8, -14.0), (-6.8, -26.0), (6.8, -26.0)):
        shrine(gpu, x, y)


def atmosphere():
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0.002, 0.002, 0.0026, 1)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -15, 23))
    v = bpy.context.object
    v.name = "haze"
    v.scale = (90, 140, 50)                     # reaches below the floor
    m = bpy.data.materials.new("haze")
    m.use_nodes = True
    N = m.node_tree.nodes
    N.remove(N["Principled BSDF"])
    sc = N.new("ShaderNodeVolumeScatter")
    sc.inputs["Color"].default_value = (0.90, 0.82, 0.72, 1)
    sc.inputs["Density"].default_value = 0.005 if SHOT else 0.007
    sc.inputs["Anisotropy"].default_value = 0.5
    m.node_tree.links.new(sc.outputs[0], N["Material Output"].inputs["Volume"])
    v.data.materials.append(m)


def lights():
    def add(name, kind, loc, target, energy, colour, **kw):
        l = bpy.data.lights.new(name, kind)
        l.energy, l.color = energy, colour
        for k, v in kw.items():
            setattr(l, k, v)
        o = link(bpy.data.objects.new(name, l))
        o.location = loc
        if target:
            aim(o, target)
        return o

    # sunlight through the stained glass, down across the nave
    for side in (-1, 1) if not SHOT else ():
        for k, y in enumerate((-2.0, -18.0, -34.0)):
            add(f"window{side}{k}", "SPOT", (side * 55, y + 4, 45), (-side * 3.0, y - 4, 0), 9000000,
                (1.0, 0.88, 0.70), spot_size=math.radians(10), spot_blend=0.3, shadow_soft_size=0.8)
    add("relic_beam", "SPOT", (0, ALTAR_Y + 4, 32), RELIC, 180000, (1.0, 0.90, 0.72),
        spot_size=math.radians(5), spot_blend=0.4, shadow_soft_size=0.2)
    if SHOT:
        # low key, as in Rogue Trader: the candles, the relic and the coolant
        # carry the light, and one hard shaft through a lattice window throws
        # its pattern across the servitor and the steps
        # two shafts through leaded windows: a patch of lattice-patterned light
        # with darkness around it. `half` is the window's half-width as a slope
        # off the axis (its patch is 2 * half * distance wide), `pane` the
        # spacing of its cames as a slope
        for name, src, dst, energy, half, pane in (
                ("shaft", (-14.0, -30.0, 20.0), (0.5, -41.4, 2.6), 180000, 0.12, 0.022),        # the altar front
                ("face_shaft", (-3.1, -34.6, 6.8), (2.35, -36.5, 1.72), 15000, 0.09, 0.02)):    # the servitor's face
            sp = add(name, "SPOT", Vector(src), Vector(dst), energy, (1.0, 0.80, 0.55),
                     spot_size=2 * math.atan(2.6 * half), spot_blend=0.0, shadow_soft_size=0.02)
            window_light(sp.data, half, pane)
        # a small hard light before the relic: the cables in front of it throw
        # their shadows across the card
        add("relic_key", "SPOT", (1.5, ALTAR_Y - 0.5, 5.5), RELIC, 2500, (1.0, 0.78, 0.50),
            spot_size=math.radians(35), spot_blend=0.3, shadow_soft_size=0.05)
        # between the card and the gold lancet behind it: the lancet glows and
        # the card stands dark against it
        add("relic_back", "POINT", (0, RELIC[1] - 0.6, RELIC[2]), None, 500, (1.0, 0.62, 0.28), shadow_soft_size=0.1)
        # a soft warm light above and behind the camera, out of frame: the gold
        # and the embroidery thread glint in it, and it lifts the whole altar
        add("glint", "AREA", (4.5, -30.0, 9.0), (0, ALTAR_Y, 3.5), 1800, (1.0, 0.80, 0.55), size=3.0)
        if SHOT == "altar":                   # a hard rim on the servitor from the altar side
            add("servitor_rim", "SPOT", (SERVITOR[0] + 1.6, SERVITOR[1] - 3.4, 3.4), (*SERVITOR, 1.5), 2000,
                (1.0, 0.70, 0.45), spot_size=math.radians(40), spot_blend=0.4, shadow_soft_size=0.05)
            # the right banner's gold thread shows only what it mirrors: a soft warm
            # source where the camera's view of it reflects to, hidden from the camera
            add("banner_glint", "AREA", (-11.5, -40.1, 7.8), (-6.0, -40.5, 5.5), 1200, (1.0, 0.78, 0.50),
                size=3.0).visible_camera = False
        return
    add("altar_key", "AREA", (0, ALTAR_Y + 14, 26), (0, ALTAR_Y - 5, 11), 11000, (1.0, 0.78, 0.50), size=8)
    add("fill", "AREA", (0, 34, 16), (0, -18, 2), 5000, (1.0, 0.70, 0.45), size=14)


def window_light(light, half, pane=0.1):
    """Make a spot shine as if through a leaded window: its node tree dims
    each direction by the window's pattern, so the light lands and hangs in
    the haze in that pattern with no window geometry in the scene. A
    direction's (u, v) is its slope off the spot's axis; the window is a
    pointed arch `half` wide either side of the axis, with a mullion, a
    transom and a diamond lattice of cames `pane` apart."""
    light.use_nodes = True
    nt = light.node_tree
    N, L = nt.nodes, nt.links
    em = next(n for n in N if n.type == "EMISSION")

    def op(kind, a, b=0.0, clamp=False):
        n = N.new("ShaderNodeMath")
        n.operation, n.use_clamp = kind, clamp
        for sock, v in zip(n.inputs, (a, b)):
            if isinstance(v, bpy.types.NodeSocket):
                L.new(v, sock)
            else:
                sock.default_value = v
        return n.outputs[0]

    d = N.new("ShaderNodeSeparateXYZ")
    L.new(N.new("ShaderNodeTexCoord").outputs["Normal"], d.inputs[0])
    depth = op("MULTIPLY", d.outputs["Z"], -1.0)
    u = op("DIVIDE", d.outputs["X"], depth)
    v = op("DIVIDE", d.outputs["Y"], depth)
    au = op("ABSOLUTE", u)
    spring = 0.2 * half                               # the arch springs a little above the axis
    inside = op("LESS_THAN", au, half)
    inside = op("MULTIPLY", inside, op("GREATER_THAN", v, -1.8 * half))
    # above the springing line: inside both arcs of radius 2*half centred on the far springer
    arc = op("LESS_THAN", op("ADD", op("POWER", op("ADD", au, half), 2.0),
                              op("POWER", op("MAXIMUM", op("SUBTRACT", v, spring), 0.0), 2.0)), 4 * half * half)
    inside = op("MULTIPLY", inside, arc)
    bars = op("GREATER_THAN", au, 0.035 * half)                                   # the mullion
    bars = op("MULTIPLY", bars, op("GREATER_THAN", op("ABSOLUTE", op("SUBTRACT", v, -0.15 * half)), 0.03 * half))
    for sgn in (1.0, -1.0):                                                       # the lattice
        f = op("FRACT", op("DIVIDE", op("ADD", u, op("MULTIPLY", v, sgn)), pane))
        bars = op("MULTIPLY", bars, op("GREATER_THAN", op("ABSOLUTE", op("SUBTRACT", f, 0.5)), 0.06))
    L.new(op("MULTIPLY", inside, bars), em.inputs["Strength"])


def camera():
    cd = bpy.data.cameras.new("cam")
    cam = link(bpy.data.objects.new("cam", cd))
    if SHOT:
        CLOSE = SHOTS[SHOT]
        # at eye level among the worshippers, looking up at the relic; the
        # lens focuses on the Sacred A5000, so the nearest figures and candles blur
        cd.lens = CLOSE["lens"]
        cam.location = CLOSE["at"]
        aim(cam, CLOSE["look"])
        cd.dof.use_dof = True
        cd.dof.focus_distance = (Vector(CLOSE["focus"]) - Vector(CLOSE["at"])).length
        cd.dof.aperture_fstop = CLOSE["fstop"]
    else:
        cd.lens = 28
        cam.location = (0, 16.0, 3.4)
        aim(cam, (0, -40.0, 8.0))
    bpy.context.scene.camera = cam


def render_setup():
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = SAMPLES
    s.cycles.use_denoising = True
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for d in pr.devices:
        d.use = d.type == "CUDA"
    s.render.resolution_x, s.render.resolution_y = RES_X, RES_Y
    s.view_settings.view_transform = "AgX"
    # the close-ups are graded to the references' spread (median luminance
    # ~0.1, deep saturated crimson): darker and punchier than the nave
    s.view_settings.exposure = -0.15 if SHOT else 0.0
    looks = ("AgX - Punchy",) if SHOT else ()
    for look in (*looks, "AgX - Medium High Contrast", "Medium High Contrast", "None"):
        try:
            s.view_settings.look = look
            break
        except TypeError:
            continue


def sketch(shot, path):
    """A clay still of the composition - grey shading, cavity and outlines,
    no volumes - for approving a shot before rendering it."""
    s = bpy.context.scene
    for ob in bpy.data.objects:
        if ob.name.startswith(("haze", "smoke")):
            ob.hide_render = True
    s.render.engine = "BLENDER_WORKBENCH"
    sh = s.display.shading
    sh.light, sh.color_type = "STUDIO", "SINGLE"
    sh.single_color = (0.75, 0.72, 0.68)
    sh.show_cavity, sh.cavity_type = True, "BOTH"
    sh.show_object_outline = True
    sh.show_shadows = True
    s.view_settings.view_transform = "Standard"
    s.render.filepath = path
    for kind, node in CLOCKS:
        node.outputs[0].default_value = 0.0
    for ob, pose in MOVERS:
        pose(0.0)
    bpy.ops.render.render(write_still=True)


def build(shot=None):
    global SHOT, TICK, TICKS
    SHOT = shot
    TICK = 8 if shot else 4             # the close-ups change their lights and screen half as often
    TICKS = FRAMES // TICK
    bpy.ops.wm.read_factory_settings(use_empty=True)
    materials()
    gpu = a5000()
    nave()
    aisle(gpu)
    altar_parts = altar(gpu)
    figures(gpu)
    if SHOT:
        dress_closeup(gpu, *altar_parts)
    censers()
    atmosphere()
    lights()
    camera()
    render_setup()


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    shot = next((a[5:] for a in argv if a.startswith("shot=")), "offering" if "closeup" in argv else None)
    build(shot)
    if "sketch" in argv:
        sketch(shot, os.path.join(ROOT, "wip", "preview", f"sketch-{shot or 'nave'}.png"))
        return
    if "preview" in argv:                     # one colour still at low samples, for approval
        bpy.context.scene.cycles.samples = 24
        for kind, node in CLOCKS:
            node.outputs[0].default_value = 0.0
        for ob, pose in MOVERS:
            pose(0.0)
        bpy.context.scene.render.filepath = os.path.join(ROOT, "wip", "preview", f"preview-{shot or 'nave'}.png")
        bpy.ops.render.render(write_still=True)
        return
    sub = next((a[4:] for a in argv if a.startswith("out=")), f"frames-{shot}" if shot else "frames")
    outdir = os.path.join(ROOT, "wip", sub)
    os.makedirs(outdir, exist_ok=True)
    if "blend" in argv:                      # save the scene for inspection, render nothing
        bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, "wip", "mechanicum.blend"))
        return
    for i in ([int(a) for a in argv if a.isdigit()] or range(FRAMES + 1)):
        phase = i / FRAMES
        tick = float((i % FRAMES) // TICK)
        for kind, node in CLOCKS:
            node.outputs[0].default_value = phase if kind == "phase" else tick
        for ob, pose in MOVERS:
            pose(phase)
        bpy.context.view_layer.update()
        name = f"f{i:03d}.png" if i < FRAMES else "seam-check.png"
        bpy.context.scene.render.filepath = os.path.join(outdir, name)
        bpy.ops.render.render(write_still=True)
        print(f"FRAME {i + 1}/{FRAMES}", flush=True)
    print("RENDER_DONE", outdir)


main()
