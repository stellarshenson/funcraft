"""Shift of a leg armour plate (kit frame) that lays its inner face on the leg: most plate points within 0.3 mm of the
leg's surface, fewest inside it (signed distance by the nearest leg vertex's normal).
    .venv-moge/bin/python src/warhound/fit_armour.py left|right"""
import sys, numpy as np, trimesh
from scipy.spatial import cKDTree
side = sys.argv[1]
leg = trimesh.load(f'resources/models/warhound/leg_{side}.stl'); arm = trimesh.load(f'resources/models/warhound/leg_armour_{side}.stl')
rng = np.random.default_rng(0)
lv, ln = leg.vertices, leg.vertex_normals
tree = cKDTree(lv)
A = arm.vertices[rng.choice(len(arm.vertices), 6000, replace=False)]
best = []
for dx in np.arange(-1.5, 1.51, 0.5):
    for dy in np.arange(-10, 6.01, 0.5):
        for dz in np.arange(-4, 8.01, 0.5):
            P = A + [dx, dy, dz]; d, i = tree.query(P, distance_upper_bound=3)
            ok = np.isfinite(d); s = np.zeros(len(P)); s[ok] = ((P[ok] - lv[i[ok]]) * ln[i[ok]]).sum(1)
            contact = (ok & (np.abs(s) < 0.3)).mean(); inside = (ok & (s < -0.4)).mean()
            best.append((contact - 3 * inside, contact, inside, dx, dy, dz))
best.sort(key=lambda b: -b[0])
for b in best[:6]: print([round(v, 3) for v in b])
