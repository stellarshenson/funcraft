"""The armour plates of a mech as flat charts in one picture, the atlas, so
that ornament can be drawn on each plate in the plate's own plane and lie
on the mesh as if it were sculpted there. Blender 4.5.

Plate. src/paint.py groups the faces of a mesh into patches:
neighbours whose normals differ by under 10 degrees. A patch of at least
MACHINE_AREA is armour, a smaller one machinery. A patch that bends by more
than BEND from its mean direction is cut into parts that do not; those
parts are marked `curved`, because their borders are not edges of a plate.

Chart. Each plate is projected on its own plane: `up` is the world's up
(the mech stands at rest, facing +Y) laid into the plane, or the mech's
forward for a plate that lies flat; `right` is up x normal, so that a
viewer in front of the plate sees right on the right. Coordinates are
metres. All charts are packed into the atlas at one scale, DENSITY pixels
per metre, the largest at which they fit. Plates smaller than CHART_AREA
are not charted and keep plain enamel.

`chart(obj, name)` cuts the canopy glass in as paint.py does, writes the UV
layer `plate`, and returns what a painter needs. Run alone it writes
wip/procession/plating/<name>.npz for src/procession/ornament.py:

    blender -b -P src/procession/plating.py -- [chassis ...] [atlas side]     # without a chassis: the three of frame.PLACEMENT
"""
import bpy, bmesh, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F

P = F.mechpaint
OUT = os.path.join(F.WIP, "plating")
ATLAS = 8192                       # pixels, the side of the atlas of one mech
CHART_AREA = 0.05                  # square metres: a smaller plate is not charted
BEND = math.radians(35)            # a chart's faces lie within this angle of its direction
MARGIN = 6                         # pixels round every chart


def _split(faces):
    """Cut a set of connected faces into parts, each within BEND of its own
    mean direction. Returns a list of (faces, curved)."""
    def mean(fs):
        n = sum((f.normal * f.calc_area() for f in fs), start=F.Vector((0, 0, 0)))
        return n.normalized() if n.length > 1e-12 else fs[0].normal.copy()

    n = mean(faces)
    if all(f.normal.angle(n, math.pi) <= BEND for f in faces):
        return [(faces, False)]
    parts, rest = [], set(faces)
    while rest:
        seed = max(rest, key=lambda f: f.calc_area())
        n = seed.normal.copy()
        for _ in range(3):                             # settle the direction on what it gathers
            sel = [f for f in rest if f.normal.angle(n, math.pi) <= BEND]
            n = mean(sel)
        sel = set(f for f in rest if f.normal.angle(n, math.pi) <= BEND) or {seed}
        todo = set(sel)
        while todo:                                    # connected pieces of the selection
            f0 = todo.pop()
            piece, stack = [f0], [f0]
            while stack:
                f = stack.pop()
                for e in f.edges:
                    for g in e.link_faces:
                        if g in todo:
                            todo.discard(g)
                            piece.append(g)
                            stack.append(g)
            parts.append((piece, True))
        rest -= sel
    return parts


def _pack(sizes, side):
    """Shelf packing of rectangles (w, h) in pixels into a square of `side`.
    Returns the corner of each, or None if they do not fit."""
    order = sorted(range(len(sizes)), key=lambda k: -sizes[k][1])
    at, x, y, shelf = [None] * len(sizes), 0, 0, 0
    for k in order:
        w, h = sizes[k]
        if w > side:
            return None
        if x + w > side:
            x, y, shelf = 0, y + shelf, 0
        if y + h > side:
            return None
        at[k] = (x, y)
        x, shelf = x + w, max(shelf, h)
    return at


def chart(obj, name, side=ATLAS):
    """Cut the glass in, find the plates, write the UV layer `plate`.
    Returns a dict: glass, rim, machine (face indices), plain (face index ->
    colour class of paint.py's scheme), charted (face indices), patch (the
    patch of every face), and the arrays of the charts."""
    sc = P.SCHEMES[name]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    g = sc["glass"]
    glass = [bm.faces[i] for i in P._glass_faces(bm, g)]
    rim = bmesh.ops.inset_region(bm, faces=glass, thickness=g["inset"], depth=g["depth"], use_even_offset=True)["faces"]
    bm.faces.ensure_lookup_table()
    bm.faces.index_update()
    skip = set(f.index for f in glass) | set(f.index for f in rim)
    pid, area = P._patches(bm)
    groups = {}
    for f in bm.faces:
        if f.index not in skip:
            groups.setdefault(pid[f.index], []).append(f)
    machine, plain, charts = [], {}, []

    def klass(c, n):
        return next((k for test, k in sc["regions"] if test(c, n)), "primary")

    for p, faces in groups.items():
        if area[p] < P.MACHINE_AREA:
            machine += [f.index for f in faces]
            continue
        for part, curved in _split(faces):
            a = sum(f.calc_area() for f in part)
            if a < CHART_AREA:
                for f in part:
                    plain[f.index] = klass(f.calc_center_median(), f.normal)
                continue
            n = sum((f.normal * f.calc_area() for f in part), start=F.Vector((0, 0, 0))).normalized()
            c = sum((f.calc_center_median() * f.calc_area() for f in part), start=F.Vector((0, 0, 0))) / a
            up = F.Vector((0, 0, 1)) if abs(n.z) < 0.9 else F.Vector((0, 1, 0))
            up = (up - up.dot(n) * n).normalized()
            right = up.cross(n)
            charts.append(dict(faces=part, n=n, c=c, up=up, right=right, area=a, curved=curved, klass=klass(c, n)))

    # every chart's corners in its own plane, in metres
    for ch in charts:
        uv = np.array([[(l.vert.co.dot(ch["right"]), l.vert.co.dot(ch["up"])) for l in f.loops] for f in ch["faces"]
                       if len(f.loops) == 3], np.float64).reshape(-1, 3, 2)
        ch["tri"] = uv
        ch["lo"], ch["size"] = uv.reshape(-1, 2).min(0), np.ptp(uv.reshape(-1, 2), 0)
    lo_d, hi_d = 10.0, 2000.0
    for _ in range(24):                                # the largest density at which all charts fit
        d = (lo_d + hi_d) / 2
        at = _pack([(int(math.ceil(ch["size"][0] * d)) + 2 * MARGIN, int(math.ceil(ch["size"][1] * d)) + 2 * MARGIN) for ch in charts], side)
        lo_d, hi_d = (d, hi_d) if at else (lo_d, d)
    density = lo_d
    at = _pack([(int(math.ceil(ch["size"][0] * density)) + 2 * MARGIN, int(math.ceil(ch["size"][1] * density)) + 2 * MARGIN) for ch in charts], side)
    layer = bm.loops.layers.uv.new("plate")
    for ch, (x, y) in zip(charts, at):
        ch["at"] = (x + MARGIN, y + MARGIN)            # the pixel of the chart's lowest corner; row 0 is the bottom
        for f in ch["faces"]:
            for l in f.loops:
                q = (np.array([l.vert.co.dot(ch["right"]), l.vert.co.dot(ch["up"])]) - ch["lo"]) * density
                l[layer].uv = ((ch["at"][0] + q[0]) / side, (ch["at"][1] + q[1]) / side)
    charted = [f.index for ch in charts for f in ch["faces"]]
    bm.to_mesh(obj.data)
    out = dict(glass=[f.index for f in glass], rim=[f.index for f in rim], machine=machine, plain=plain, charted=charted,
               patch=pid,
               density=density, side=side, classes=sorted(sc["colours"]),
               at=np.array([ch["at"] for ch in charts], np.int32),
               size=np.array([np.ceil(ch["size"] * density) for ch in charts], np.int32),
               lo=np.array([ch["lo"] for ch in charts]), n=np.array([ch["n"] for ch in charts]),
               c=np.array([ch["c"] for ch in charts]), up=np.array([ch["up"] for ch in charts]),
               area=np.array([ch["area"] for ch in charts]), curved=np.array([ch["curved"] for ch in charts]),
               klass=np.array([sorted(sc["colours"]).index(ch["klass"]) for ch in charts], np.int32),
               tri=np.concatenate([(ch["tri"] - ch["lo"]) * density + ch["at"] for ch in charts]).astype(np.float32),
               tri_chart=np.concatenate([np.full(len(ch["tri"]), k, np.int32) for k, ch in enumerate(charts)]))
    bm.free()
    obj.data.update()
    armour = sum(a for a in out["area"]) + 0.0
    print(f"PLATING {name}: {len(charts)} charts ({int(out['curved'].sum())} curved), {armour:.0f} m2 charted, "
          f"{len(plain)} plain armour faces, {len(machine)} machine faces, {density:.0f} px per metre in {side} px")
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    side = next((int(a) for a in argv if a.isdigit()), ATLAS)
    for name in [a for a in argv if not a.isdigit()] or [name for name, _ in F.PLACEMENT]:
        F.mechrig.clear_scene()
        info = chart(F.load(name), name, side)
        np.savez_compressed(os.path.join(OUT, f"{name}.npz"), **{k: v for k, v in info.items() if isinstance(v, np.ndarray)},
                            density=info["density"], side=info["side"], classes=np.array(info["classes"]))
    print("PLATING_DONE")
