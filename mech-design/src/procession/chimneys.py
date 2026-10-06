"""Smoke of the backdrop's factory chimneys, simulated as a gas by the solver
of the sibling project w40k-mechanicum (src/smoke.py): the Navier-Stokes
equations with buoyancy for the air, particles for the smoke.

The solver works on a candle, in a box of air of 0.4 x 0.4 x 0.8 m. The
scene (src/procession/effects.py) shows its plume about a hundred times
larger, over a chimney a kilometre away. Smoke that far away moves slowly
in the picture, so the loop does not show the candle in its own time: after
a warm-up of WARM seconds the solver's air is recorded for FRAMES frames
that are 1 / (FPS * SLOW) seconds apart, the loop's time divided by SLOW.

A chimney is not a wick. Its mouth is MOUTH wide, and the solver heats
only a point, so the air over the whole mouth is heated here as well, to
HEAT kelvin over the room: a wide, fast, rolling column in place of a
thread. The smoke particles wander more (DIFF), as soot in rolling air
does, so the column is a dense body and not single threads.

Loop. The record is read twice, half a loop apart. Each reading runs
through the whole record and starts again; it is faded out while it starts
again, and the other reading is at its full weight then. Frame FRAMES is
frame 0, and the smoke is equally soft in every frame.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \\
        ../w40k-mechanicum/.venv-moge/bin/python src/procession/chimneys.py

writes wip/procession/chimneys/<k>.npz (density per loop frame, the place of
its first cell from the chimney's mouth, the cell size; in the solver's
metres) and wip/preview/procession/chimneys.png.
"""
import os, sys
import numpy as np
import cv2
import torch
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))    # mech-design
sys.path.append(os.path.join(os.path.dirname(ROOT), "w40k-mechanicum", "src"))
import smoke

FRAMES, FPS = 88, 30               # frame.FRAMES and 1 / frame.FRAME_S; frame.py needs Blender and cannot be imported here
SLOW = 24                          # the loop shows FRAMES / FPS / SLOW seconds of the plume
WARM = 8.0                         # seconds before the record: the plume stands and fills the box
MOUTH = 0.022                      # m: radius of the chimney's mouth in the box
HEAT = 90.0                        # K over the room, across the mouth
PLUMES = 3
WIND = (-0.02, 0.0, 0.0)           # m/s in the box: the plumes lean to the right of the picture, as the painted smoke does
OUT = os.path.join(ROOT, "wip", "procession", "chimneys")


def plume(seed):
    """One looping plume: density (FRAMES, x, y, z) cut to where smoke is,
    the place of its first cell from the source, the cell size."""
    sim = smoke.Plume("cuda", seed)
    src = torch.tensor([smoke.N[0] / 2, smoke.N[1] / 2, smoke.SRC_Z / smoke.DX], device="cuda")
    at = np.array([3.0 * seed, 0.0, 0.0])              # each plume stands in another place of the draft
    emit = smoke.EMIT
    mouth = torch.exp(-((sim.idx - src) ** 2).sum(-1) / (2 * (MOUTH / smoke.DX) ** 2))

    def run(t, dt):
        wind = torch.tensor(smoke.air.draft(at, t) + WIND, device="cuda", dtype=torch.float32)
        sim.step(t, dt, src, wind)
        sim.T = sim.T + (HEAT - sim.T) * mouth * min(1.0, 20 * dt)
        sim.particles(t, dt, src, wind)

    t, dt = 0.0, 1.0 / (smoke.FPS * smoke.SUB)
    while t < WARM:
        run(t, dt)
        t += dt
    rec = []
    fine = 1.0 / (FPS * SLOW)
    smoke.EMIT = max(1, round(emit * smoke.FPS * smoke.SUB * fine))                        # as much smoke per second as before
    for _ in range(FRAMES):
        run(t, fine)
        t += fine
        rec.append(sim.density(t).half())
    smoke.EMIT = emit
    k = np.arange(FRAMES)
    w = 1 - np.abs(2 * k / FRAMES - 1)                 # 0 where the first reading starts again
    loop = torch.stack([float(w[i]) * rec[i].float() + float(1 - w[i]) * rec[(i + FRAMES // 2) % FRAMES].float() for i in k])
    used = (loop.amax(0) > 2e-3).nonzero()
    lo, hi = used.min(0).values, used.max(0).values + 1
    crop = loop[:, lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]].half().cpu().numpy()
    cell = smoke.DX / smoke.FINE
    origin = lo.cpu().numpy() * cell - np.array([smoke.N[0] * smoke.DX / 2, smoke.N[1] * smoke.DX / 2, smoke.SRC_Z])
    return crop, origin, cell


if __name__ == "__main__":
    smoke.R_SRC = MOUTH
    smoke.EMIT = 4000                                  # particles per step of the warm-up: a dense body needs many
    smoke.LIFE = 2.6                                   # s: the smoke thins out before it reaches the lid of the box
    smoke.DIFF = 1.5e-5                                # m2/s: soot in rolling air
    smoke.CONFINE = 0.4                                # more of the swirl the grid loses is given back
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for k in range(PLUMES):
        dens, origin, cell = plume(k)
        np.savez_compressed(os.path.join(OUT, f"{k}.npz"), density=dens, origin=origin, cell=cell)
        print("CHIMNEY", k, dens.shape, "peak", float(dens.max()), "height", round(dens.shape[3] * cell, 2), "m", flush=True)
        side = [(255 * (1 - np.exp(-0.5 * dens[f].astype(np.float32).sum(1))).T[::-1]).clip(0, 255).astype(np.uint8)
                for f in range(0, FRAMES, FRAMES // 4)]                      # four loop frames seen from the camera's side
        rows.append(cv2.resize(np.concatenate(side, 1), (1200, 600)))
    cv2.imwrite(os.path.join(ROOT, "wip", "preview", "procession", "chimneys.png"), np.concatenate(rows, 0))
    print("CHIMNEYS_DONE")
