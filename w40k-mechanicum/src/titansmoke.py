"""The smoke round the saint scene's Warhound Titan: the exhaust of the two grilles of its head and the hot machinery
of its waist (src/titan.py writes where they are through the loop), by the gas dynamics of src/smoke.py at the
titan's scale. The box of air is five times the candle's, 2 x 2 x 4 m in cells of 3.1 cm, the eddies of the corridor
0.4 to 1 m long, the exhaust 120 K above the air of the chapel. The smoke is thick enough to be lit by the titan's
lamps: each file carries the coefficients src/scenes.py gives its volume (emission by the plate's light behind it,
absorption, scattering).

    blender -b -P src/scenes.py -- saint sources                                   # wip/scene3d/saint_titan_sources.json
    CUDA_VISIBLE_DEVICES=1 LOOP_FRAMES=120 .venv-moge/bin/python src/titansmoke.py  # wip/sim/saint/t1.npz ...
"""
import os, sys, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import smoke as S

S.DX = 0.03125
S.SRC_Z = 0.5
S.R_SRC = 0.12
S.R_HEAT = 0.15
S.T_SRC = 120.0
S.T_TAU = 4.0
S.EDDY = 0.06
S.EDDIES = (0.4, 1.0)
S.WALLS = (0.2, 0.25, 0.7)
S.TOP = (1.0, 0.3)
S.DIFF = 1e-4
S.SEEN = (0.05, 0.3)
S.EMIT = 3000
COEFF = dict(emit=20.0, absorb=15.0, scatter=10.0)

if __name__ == "__main__":
    src = json.load(open(os.path.join(S.ROOT, "wip", "scene3d", "saint_titan_sources.json")))
    out = os.path.join(S.ROOT, "wip", "sim", "saint")
    os.makedirs(out, exist_ok=True)
    for k, s in enumerate(src):
        dens, origin, cell = S.simulate(s["path"], "cuda", 10 + k, lambda m, s=s: print(s["id"], m, flush=True))
        tau = COEFF["absorb"] + COEFF["scatter"]
        depth = (dens.astype(np.float32).sum(2) * cell * tau).max(0)
        print(s["id"], "cells", dens.shape[1:], "peak density", float(dens.max()), "optical depth across, 99th percentile",
              round(float(np.percentile(depth[depth > 0.01], 99)), 2), flush=True)
        np.savez_compressed(os.path.join(out, s["id"] + ".npz"), density=dens, origin=origin, cell=cell, **COEFF)
    print("TITANSMOKE_DONE", len(src))
