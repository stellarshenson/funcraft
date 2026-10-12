"""Dust over a crowd, by gas dynamics, in metres and seconds.

The owner on the crowd of the muster plate: "let the crowd be also a little interwoven with dust and dirtiness". The
rule of this project (DESIGN.md sections 5.6 and 5.7): smoke and dust are simulated, not drawn.

A strip of air stands across a walk, BOX metres long and high, seen from its side. The feet of the crowd raise dust
from the floor; the wind carries it along the strip and the eddies of the air lift it and tear it into banks:

    du/dt + (u . grad) u = -grad p + f - u / T_CALM            div u = 0
    dD/dt + ((u + wind - sink z^) . grad) D = K lap D + raised - D / T_SETTLE

u is the unrest of the air and f what keeps it up: eddies 1.5 to 5 m wide. The wind grows with the height over the
floor as over rough ground. D is the dust, 1 where the feet raise it most. The strip is periodic along its length,
so a curtain of dust across a walk (src/muster.py) takes its dust from any place of it.

- **Loop** - the air does not repeat by itself. After a warm-up, the loop and CLOSE more frames are recorded; the
  last CLOSE frames of the loop are led over into the frames before its first, as src/fire.py does

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/dust.py muster      # wip/sim/muster/dust<n>.npz and .png
"""
import os, sys, math
import numpy as np, torch
import torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke import smooth

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 2 * math.pi
BOX, N = (128.0, 16.0), (1024, 128)        # the strip: length and height in metres; cells
FLOOR, KEPT = 1.5, 8.0                     # the floor lies this far over the lower edge of the strip; the height over the floor that is kept
ROUGH = 0.3                                # the roughness of a crowd for the wind, in metres
EDDY, T_CALM = 0.12, 5.0                   # the forcing of the eddies in m/s2; the seconds in which the unrest of the air dies down
K, SINK, T_SETTLE = 0.02, 0.03, 30.0       # mixing by eddies smaller than a cell, m2/s; how fast dust sinks, m/s; the seconds in which it settles
RAISED = (0.6, 0.35)                       # dust is raised up to this height over the floor; and this much per second where the feet raise it most
CLOSE = 90                                 # the frames led over at the end of the loop


def sample(f, pos):
    """Field f (C, X, Y) at points pos (..., 2) in cell units; periodic along X."""
    C, X, Y = f.shape
    fp = F.pad(f[None], (0, 0, 0, 1), mode="circular")
    g = torch.stack([2 * pos[..., 1].clamp(0, Y - 1) / (Y - 1) - 1, 2 * torch.remainder(pos[..., 0], X) / X - 1], -1)
    return F.grid_sample(fp, g[None], mode="bilinear", padding_mode="border", align_corners=True)[0]


class Strip:
    def __init__(self, dev, seed=0):
        X, Y = N
        self.dev, self.dx = dev, BOX[0] / X
        dx = self.dx
        self.u = torch.zeros(2, X, Y, device=dev)
        self.d = torch.zeros(1, X, Y, device=dev)
        ax = [torch.arange(n, device=dev, dtype=torch.float32) for n in N]
        self.idx = torch.stack(torch.meshgrid(*ax, indexing="ij"), -1)
        k = [TAU * torch.fft.fftfreq(X, dx), TAU * torch.fft.rfftfreq(Y, dx)]
        self.k = torch.stack(torch.meshgrid(*[v.to(dev) for v in k], indexing="ij"))
        self.k2 = (self.k ** 2).sum(0)
        self.k2[0, 0] = 1.0
        high = ax[1] * dx - FLOOR                                     # metres over the floor
        self.keep = (smooth(-0.3, 0.2, high) * smooth(BOX[1] - FLOOR, BOX[1] - FLOOR - 3.0, high))[None, :]      # no air moves under the floor or leaves at the top
        self.wind = (torch.log((high.clamp(min=0) + ROUGH) / ROUGH) / math.log((2.0 + ROUGH) / ROUGH))[None, :]      # 1 at 2 m over the floor
        g = np.random.default_rng(seed)
        self.eddies = []
        for rate in (0.11, 0.19, 0.31):                               # turns per second
            A, B = torch.zeros_like(self.u), torch.zeros_like(self.u)
            for field in (A, B):
                for _ in range(8):
                    lam = g.uniform(1.5, 5.0)
                    m = g.normal(size=2)
                    m = np.round(m / np.linalg.norm(m) * np.array(BOX) / lam)
                    if not np.any(m):
                        continue
                    kv = TAU * m / np.array(BOX)
                    wave = torch.sin((self.idx * dx * torch.tensor(kv, device=dev, dtype=torch.float32)).sum(-1) + g.uniform(0, TAU))
                    a = np.array([-kv[1], kv[0]]) / np.linalg.norm(kv)        # across the wave: no divergence
                    field += torch.tensor(a, device=dev, dtype=torch.float32)[:, None, None] * wave
            self.eddies.append((rate, A, B))
        # where the feet raise dust: patches along the floor, each stronger and weaker in its own slow course
        x = ax[0] * dx
        low = (smooth(-0.1, 0.1, high) * smooth(RAISED[0], 0.0, high))[None, :]
        self.patches = []
        for _ in range(26):
            at, size = g.uniform(0, BOX[0]), g.uniform(1.5, 6.0)
            far = torch.remainder(x - at + BOX[0] / 2, BOX[0]) - BOX[0] / 2
            self.patches.append((torch.exp(-(far / size) ** 2)[:, None] * low, g.uniform(0, TAU), g.uniform(0.03, 0.09), g.uniform(0.4, 1.0)))
        self.even = 0.25 * low.expand(X, Y)

    def advect(self, q, adv, dt):
        """MacCormack advection with a limiter (as src/smoke.py)."""
        def trace(p, sign):
            v = sample(adv, p).movedim(0, -1)
            v = sample(adv, p - sign * 0.5 * dt / self.dx * v).movedim(0, -1)
            return p - sign * dt / self.dx * v
        pb = trace(self.idx, 1.0)
        q1 = sample(q, pb)
        q2 = sample(q1, trace(self.idx, -1.0))
        lo = -sample(F.max_pool2d(-q[None], 3, 1, 1)[0], pb)
        hi = sample(F.max_pool2d(q[None], 3, 1, 1)[0], pb)
        return torch.minimum(torch.maximum(q1 + 0.5 * (q - q2), lo), hi)

    def step(self, t, dt, wind, raised):
        """One step. wind: m/s along the strip at 2 m over the floor; raised: how much dust the feet raise, against RAISED."""
        adv = self.u.clone()
        adv[0] += wind * self.wind
        u = self.advect(self.u, adv, dt)
        adv[1] -= SINK
        d = self.advect(self.d, adv, dt)[0]
        d = d + raised * RAISED[1] * dt * (self.even + sum(patch * much * (0.5 + 0.5 * math.sin(ph + TAU * rate * t)) for patch, ph, rate, much in self.patches))
        d = d * math.exp(-dt / T_SETTLE)
        for rate, A, B in self.eddies:
            a = TAU * rate * t
            u = u + EDDY * dt * (math.cos(a) * A + math.sin(a) * B)
        u = u * self.keep * math.exp(-dt / T_CALM)
        uh = torch.fft.rfftn(u, dim=(1, 2))
        uh = uh - self.k * (self.k * uh).sum(0) / self.k2
        uh[:, 0, 0] = 0
        self.u = torch.fft.irfftn(uh, s=N, dim=(1, 2))
        dh = torch.fft.rfftn(d, dim=(0, 1)) * torch.exp(-K * self.k2 * dt)
        self.d = (torch.fft.irfftn(dh, s=N, dim=(0, 1)) * self.keep.clamp(max=1)).clamp(min=0)[None]


def simulate(dev, frames, fps, wind, raised, seed=0, log=None):
    """The loop of the dust of one strip: (frames, up from the floor, along), 8 m high; the size of a cell in metres."""
    sim = Strip(dev, seed)
    sub = max(1, math.ceil((2.5 * abs(wind) + 1.5) / fps / (1.5 * sim.dx)))      # a step moves the air 1.5 cells at most
    dt = 1.0 / (fps * sub)
    warm = math.ceil(3 * T_SETTLE * fps * sub)
    rec, speed = [], []
    for step in range(warm + (frames + CLOSE) * sub):
        sim.step(step * dt, dt, wind, raised)
        if step >= warm and (step - warm) % sub == sub - 1:
            rec.append(sim.d[0])
            speed.append(sim.u.norm(dim=0).pow(2).mean().sqrt().item())
    rec = torch.stack(rec)                                            # (frames + CLOSE, along, up)
    k = torch.arange(frames, device=dev)
    w = smooth(frames - CLOSE, frames, k.float())[:, None, None]
    loop = (1 - w) * rec[CLOSE + k] + w * rec[(k - (frames - CLOSE)).clamp(min=0)]
    a, b = round(FLOOR / sim.dx), round((FLOOR + KEPT) / sim.dx)
    loop = loop[:, :, a:b].transpose(1, 2)
    if log is not None:
        high = (loop.mean((0, 2)) > 0.1 * loop.mean((0, 2)).max()).sum().item() * sim.dx
        log(f"wind {wind:.1f} m/s, {sub} steps per frame, warm-up {warm * dt:.0f} s; the unrest of the air is {np.mean(speed):.2f} m/s; "
            f"dust up to {high:.1f} m over the floor, {loop.mean().item():.3f} on average, {torch.quantile(loop.flatten()[::97], 0.99).item():.3f} where it is thick")
    return loop.cpu().numpy(), sim.dx


def sheet(dust, path, every=45):
    """Frames of a loop, one under the other, the floor at the bottom of each."""
    import cv2
    tiles = [cv2.copyMakeBorder((255 * (1 - np.exp(-3 * dust[k, ::-1].astype(np.float32)))).astype(np.uint8), 0, 3, 0, 0, cv2.BORDER_CONSTANT, value=90)
             for k in range(0, len(dust), every)]
    cv2.imwrite(path, np.concatenate(tiles, 0))


def main():
    import muster
    out = os.path.join(ROOT, "wip", "sim", sys.argv[1])
    os.makedirs(out, exist_ok=True)
    for n, (wind, raised) in enumerate(muster.DUST):
        dust, cell = simulate("cuda", muster.FRAMES, muster.RATE, wind, raised, seed=n, log=lambda m, n=n: print(f"dust{n}", m, flush=True))
        np.savez_compressed(os.path.join(out, f"dust{n}.npz"), dust=dust.astype(np.float16), cell=cell)
        sheet(dust, os.path.join(out, f"dust{n}.png"))


if __name__ == "__main__":
    main()
