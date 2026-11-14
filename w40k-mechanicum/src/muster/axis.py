"""The long axis of each street banner on its flat cloth against the line through its sigils (src/goldwork.py).

    .venv-moge/bin/python src/muster/axis.py street
"""
import os, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import goldwork as G

scene = sys.argv[1]
plate = np.asarray(Image.open(os.path.join(G.folder(scene), "cleared.png")).convert("RGB")).astype(np.float32)
actors = np.load(os.path.join(ROOT, "wip", "scene3d", f"{scene}_actors.npz"))
H, W = plate.shape[:2]
ang = lambda c: np.degrees(np.arctan2(-c.real, c.imag))
for cloth in G.DRAPES[scene]["cloths"]:
    x0, y0, x1, y1 = cloth["region"]
    ok, z, zv = G.element_chart(cloth, actors, plate[y0:y1, x0:x1], (H, W))
    p = zv[np.isfinite(zv)]
    p = p - p.mean()
    w, v = np.linalg.eigh(np.cov(np.stack([p.real, p.imag])))
    axis = v[0, 1] + 1j * v[1, 1]
    axis = axis if axis.imag > 0 else -axis
    places = [z[s[2] - y0, s[1] - x0] for s in cloth["sigils"]]
    print(f"{cloth['actor']}: long axis of the banner leans {ang(axis):+.1f} degrees from the picture's; the line through its sigils {ang(places[-1] - places[0]):+.1f}; "
          f"length and width of the cloth {2 * np.sqrt(w[1]):.2f}, {2 * np.sqrt(w[0]):.2f} m (2 standard deviations)")

# in the picture: the direction of each sigil's own vertical (the cloth's way down, carried from the flat cloth into the
# picture by the chart's slope at the sigil), against the edges of the banner (lines fitted to its left and right edge)
for cloth in G.DRAPES[scene]["cloths"]:
    x0, y0, x1, y1 = cloth["region"]
    ok, z, zv = G.element_chart(cloth, actors, plate[y0:y1, x0:x1], (H, W))
    places = [z[s[2] - y0, s[1] - x0] for s in cloth["sigils"]]
    down = (places[-1] - places[0]) / abs(places[-1] - places[0])
    if len(sys.argv) > 2:                                                 # the way down that src/goldwork.py lay printed
        down = dict(zip(sys.argv[2::2], [complex(v) for v in sys.argv[3::2]]))[cloth["actor"]]
    gx, gy = np.gradient(z.real, axis=1) + 1j * np.gradient(z.imag, axis=1), np.gradient(z.real, axis=0) + 1j * np.gradient(z.imag, axis=0)
    for name, x, y, *_ in cloth["sigils"]:
        J = np.array([[gx[y - y0, x - x0].real, gy[y - y0, x - x0].real], [gx[y - y0, x - x0].imag, gy[y - y0, x - x0].imag]])
        d = np.linalg.solve(J, [down.real, down.imag])
        print(f"{cloth['actor']} {name}: its vertical in the picture leans {np.degrees(np.arctan2(-d[0], d[1])):+.1f} degrees")
    rows = [r for r in range(0, 330, 5) if ok[r].any()]
    for side, pick in (("left", lambda m: np.nonzero(m)[0].min()), ("right", lambda m: np.nonzero(m)[0].max())):
        xs = np.array([pick(ok[r]) for r in rows])
        k = np.polyfit(rows, xs, 1)[0]
        print(f"{cloth['actor']} {side} edge of the cloth in rows 0 to 330 leans {np.degrees(np.arctan(-k)):+.1f} degrees")
