"""Smoke of the candles and censers of a scene, by gas dynamics.

Each source gets its own box of air, 0.4 x 0.4 x 0.8 m, around the path its
wick follows through the loop. In the box the air obeys the incompressible
Navier-Stokes equations with Boussinesq buoyancy:

    du/dt + (u . grad) u = -grad p + nu lap u + g beta T z^ + f
    div u = 0
    dT/dt + (u . grad) T = -T / tau + source

u is the air velocity, T the temperature above the room's, held at T_SRC
kelvin at the wick; warm air rises and draws the smoke with it. f is the
room: weak eddies (wavelengths 8 to 20 cm, a whole number of cycles per
loop) and vorticity confinement, which returns the swirl the grid's
advection loses. The room's draft (src/air.py) carries everything sideways.
Velocity and temperature move by MacCormack advection with a limiter;
viscosity and the pressure projection are exact in Fourier space (the box
is periodic, with a damping layer at every wall so nothing comes round).

The smoke itself is particles, not a grid field: 3000 per frame leave the
wick, each carried by the air (second-order Runge-Kutta) with a small
random walk, each fading out by LIFE seconds. A particle shows only from
the age SEEN: the gas that leaves a flame is hot and clear, and its soot
shows as smoke a few centimetres higher, where it has cooled. Without this
the densest smoke sits on the flame tip and reads as a larger, whiter
flame. Particles keep a filament
thin where a grid would blur it. Per frame they are counted into a grid of
3.1 mm cells: the density the renderer sees.

Loop. The air is not periodic by itself. After a warm-up, 2 x 80 frames
are recorded; loop frame k is (1 - k/80) of record 80 + k plus k/80 of
record k. Frame 80 then equals frame 0. The source is at the same place in
both records, so the young smoke near the wick coincides in them.

    CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/smoke.py <name>      # wip/sim/<name>/<source>.npz
    CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/smoke.py test         # wip/preview/smoke-test.png
"""
import os, sys, math, json
import numpy as np, torch
import torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import air

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU = 2 * math.pi
FRAMES, FPS, SUB = 80, 20, 2
WARM = 240                 # frames before recording
DX = 0.00625               # m, one cell of the velocity grid
N = (64, 64, 128)          # cells
FINE = 2                   # density cells per velocity cell
SRC_Z = 0.10               # m, the source above the box floor
NU = 1.5e-5                # m2/s, viscosity of air
G_BETA = 9.81 / 300        # m/s2 per kelvin
T_SRC = 45.0               # K above the room at the wick
T_TAU = 3.0                # s, the warm air mixes away
EDDY = 0.02                # m/s2, forcing of the room's eddies
CONFINE = 0.2              # vorticity confinement
EMIT = 1500                # particles per substep
R_SRC = 0.005              # m, radius of the source
DIFF = 6e-6                # m2/s, random walk of a particle: the eddies smaller than a cell
LIFE = 4.5                 # s
SEEN = (0.10, 0.45)        # s, the age at which smoke starts to show and shows fully


def smooth(e0, e1, x):
    x = ((x - e0) / (e1 - e0)).clamp(0, 1)
    return x * x * (3 - 2 * x)


def sample(f, pos, mode="bilinear"):
    """Field f (C, X, Y, Z) at points pos (..., 3) in cell units, periodic."""
    C, X, Y, Z = f.shape
    fp = F.pad(f[None], (0, 1, 0, 1, 0, 1), mode="circular")
    size = torch.tensor([X, Y, Z], device=f.device, dtype=pos.dtype)
    g = (2 * torch.remainder(pos, size) / size - 1).flip(-1)
    out = F.grid_sample(fp, g.reshape(1, -1, 1, 1, 3), mode=mode, padding_mode="border", align_corners=True)
    return out.reshape(C, *pos.shape[:-1])


class Plume:
    def __init__(self, dev, seed=0):
        X, Y, Z = N
        self.dev = dev
        self.rng = torch.Generator(device=dev).manual_seed(seed)
        self.u = torch.zeros(3, X, Y, Z, device=dev)
        self.T = torch.zeros(1, X, Y, Z, device=dev)
        ax = [torch.arange(n, device=dev, dtype=torch.float32) for n in N]
        self.idx = torch.stack(torch.meshgrid(*ax, indexing="ij"), -1)
        k = [TAU * torch.fft.fftfreq(X, DX), TAU * torch.fft.fftfreq(Y, DX), TAU * torch.fft.rfftfreq(Z, DX)]
        self.k = torch.stack(torch.meshgrid(*[q.to(dev) for q in k], indexing="ij"))
        self.k2 = (self.k ** 2).sum(0)
        self.k2[0, 0, 0] = 1.0
        wall = lambda a, n, lo, hi: smooth(0.0, lo, a * DX) * smooth(n * DX, n * DX - hi, a * DX)
        self.keep = (wall(ax[0], X, 0.04, 0.04)[:, None, None] * wall(ax[1], Y, 0.04, 0.04)[None, :, None]
                     * wall(ax[2], Z, 0.05, 0.14)[None, None, :])
        # the room's eddies: divergence-free waves on the box's own lattice
        g = np.random.default_rng(seed + 100)
        self.eddy = []
        pos = self.idx * DX
        for cycles in (1, 2, 3):
            A, B = torch.zeros_like(self.u), torch.zeros_like(self.u)
            for field in (A, B):
                for _ in range(4):
                    m = np.array([g.integers(-4, 5), g.integers(-4, 5), g.integers(-8, 9)])
                    kv = TAU * m / (np.array(N) * DX)
                    lam = TAU / max(np.linalg.norm(kv), 1e-6)
                    if not 0.08 <= lam <= 0.20:
                        continue
                    a = np.cross(kv, g.normal(size=3))
                    a = a / np.linalg.norm(a)
                    ph = g.uniform(0, TAU)
                    w = torch.sin((pos * torch.tensor(kv, device=dev, dtype=torch.float32)).sum(-1) + ph)
                    field += torch.tensor(a, device=dev, dtype=torch.float32)[:, None, None, None] * w
            self.eddy.append((cycles, A, B))
        self.p = torch.zeros(0, 3, device=dev)
        self.born = torch.zeros(0, device=dev)

    def advect(self, q, adv, dt):
        def trace(p, sign):
            v = sample(adv, p).movedim(0, -1)
            v = sample(adv, p - sign * 0.5 * dt / DX * v).movedim(0, -1)
            return p - sign * dt / DX * v
        pb = trace(self.idx, 1.0)
        q1 = sample(q, pb)
        q2 = sample(q1, trace(self.idx, -1.0))
        lo = -sample(F.max_pool3d(-q[None], 3, 1, 1)[0], pb, "nearest")
        hi = sample(F.max_pool3d(q[None], 3, 1, 1)[0], pb, "nearest")
        return torch.minimum(torch.maximum(q1 + 0.5 * (q - q2), lo), hi)

    def step(self, t, dt, src, wind):
        """One step of the air. src: the wick in cell units; wind: (3,) m/s."""
        adv = self.u + wind[:, None, None, None]
        q = self.advect(torch.cat([self.u, self.T]), adv, dt)
        u, T = q[:3], q[3:]
        blob = torch.exp(-((self.idx - src) ** 2).sum(-1) / (2 * 1.3 ** 2))
        T = T + (T_SRC - T) * blob * min(1.0, 20 * dt)
        T = T * math.exp(-dt / T_TAU)
        u[2] = u[2] + G_BETA * T[0] * dt
        for cycles, A, B in self.eddy:
            a = TAU * cycles * t / air.LOOP
            u = u + EDDY * dt * (math.cos(a) * A + math.sin(a) * B)
        d = lambda f, ax: (torch.roll(f, -1, ax) - torch.roll(f, 1, ax)) / (2 * DX)
        w = torch.stack([d(u[2], 1) - d(u[1], 2), d(u[0], 2) - d(u[2], 0), d(u[1], 0) - d(u[0], 1)])
        mag = w.norm(dim=0)
        eta = torch.stack([d(mag, 0), d(mag, 1), d(mag, 2)])
        eta = eta / (eta.norm(dim=0) + 1e-6)
        u = u + CONFINE * DX * dt * torch.linalg.cross(eta, w, dim=0)
        u, T = u * self.keep, T * self.keep
        uh = torch.fft.rfftn(u, dim=(1, 2, 3)) * torch.exp(-NU * self.k2 * dt)
        uh = uh - self.k * (self.k * uh).sum(0) / self.k2
        uh[:, 0, 0, 0] = 0
        self.u, self.T = torch.fft.irfftn(uh, s=N, dim=(1, 2, 3)), T

    def particles(self, t, dt, src, wind):
        adv = self.u + wind[:, None, None, None]
        if len(self.p):
            v = sample(adv, self.p).T
            v = sample(adv, self.p + 0.5 * dt / DX * v).T
            self.p = self.p + dt / DX * v + torch.randn(self.p.shape, device=self.dev, generator=self.rng) \
                * math.sqrt(2 * DIFF * dt) / DX
            size = torch.tensor(N, device=self.dev, dtype=torch.float32)
            ok = (t - self.born < LIFE) & (self.p > 2).all(1) & (self.p < size - 2).all(1)
            self.p, self.born = self.p[ok], self.born[ok]
        new = src + torch.randn(EMIT, 3, device=self.dev, generator=self.rng) * R_SRC / DX
        self.p = torch.cat([self.p, new])
        self.born = torch.cat([self.born, torch.full((EMIT,), t, device=self.dev)])

    def density(self, t):
        """Particles counted into the fine grid, each weighted by its fade."""
        X, Y, Z = (n * FINE for n in N)
        age = t - self.born
        z = self.p[:, 2] * DX
        wgt = smooth(*SEEN, age) * (1 - smooth(0.3 * LIFE, LIFE, age)) \
            * (1 - smooth(N[2] * DX - 0.20, N[2] * DX - 0.06, z)) / 40.0
        q = self.p * FINE
        i0 = q.floor()
        f = q - i0
        i0 = i0.long()
        dens = torch.zeros(X * Y * Z, device=self.dev)
        for ox in (0, 1):
            for oy in (0, 1):
                for oz in (0, 1):
                    w = (f[:, 0] if ox else 1 - f[:, 0]) * (f[:, 1] if oy else 1 - f[:, 1]) * (f[:, 2] if oz else 1 - f[:, 2])
                    lin = ((i0[:, 0] + ox).clamp(0, X - 1) * Y + (i0[:, 1] + oy).clamp(0, Y - 1)) * Z \
                        + (i0[:, 2] + oz).clamp(0, Z - 1)
                    dens.index_add_(0, lin, w * wgt)
        dens = dens.reshape(1, 1, X, Y, Z)
        k = torch.tensor([0.25, 0.5, 0.25], device=self.dev)
        for ax in range(3):
            shape = [1, 1, 1, 1, 1]
            shape[2 + ax] = 3
            pad = [0, 0, 0, 0, 0, 0]
            pad[2 * (2 - ax)] = pad[2 * (2 - ax) + 1] = 1
            dens = F.conv3d(F.pad(dens, pad), k.reshape(shape))
        return dens[0, 0]


def simulate(path, dev, seed=0, log=None):
    """Looping smoke of one source. path: (FRAMES, 3) world positions of the
    wick, metres. Returns the density (FRAMES, x, y, z) cropped to where
    smoke is, the world position of the crop's first cell, the cell size."""
    path = np.asarray(path, np.float64)
    mean = path.mean(0)
    origin = mean - np.array([N[0] * DX / 2, N[1] * DX / 2, SRC_Z])
    cells = torch.tensor((path - origin) / DX, device=dev, dtype=torch.float32)
    sim = Plume(dev, seed)
    dt = 1.0 / (FPS * SUB)
    rec = []
    for frame in range(WARM + 2 * FRAMES):
        for s in range(SUB):
            t = (frame + s / SUB) / FPS
            a, b = cells[frame % FRAMES], cells[(frame + 1) % FRAMES]
            src = a + (b - a) * s / SUB
            wind = torch.tensor(air.draft(mean, t), device=dev, dtype=torch.float32)
            sim.step(t, dt, src, wind)
            sim.particles(t, dt, src, wind)
        if frame >= WARM:
            rec.append(sim.density((frame + 1) / FPS).half())
    if log is not None:
        z = sim.p[:, 2] * DX - SRC_Z
        age = (WARM + 2 * FRAMES) / FPS - sim.born
        h = [float(z[(age > a - 0.1) & (age < a + 0.1)].mean()) for a in (1, 2, 3, 4)]
        log(f"particles {len(sim.p)}, height after 1, 2, 3, 4 s: " + ", ".join(f"{v:.2f}" for v in h)
            + f" m, peak speed {float(sim.u.norm(dim=0).max()):.2f} m/s")
    loop = torch.stack([(1 - k / FRAMES) * rec[FRAMES + k].float() + k / FRAMES * rec[k].float() for k in range(FRAMES)])
    used = (loop.amax(0) > 2e-3).nonzero()
    lo, hi = used.min(0).values, used.max(0).values + 1
    crop = loop[:, lo[0]:hi[0], lo[1]:hi[1], lo[2]:hi[2]].half().cpu().numpy()
    return crop, origin + lo.cpu().numpy() * DX / FINE, DX / FINE


def sheet(dens, path):
    """Four loop frames seen from the camera's side (density summed along the depth)."""
    import cv2
    tiles = []
    for k in (0, 20, 40, 60):
        img = 1 - np.exp(-0.5 * dens[k].astype(np.float32).sum(1))
        img = (255 * img.T[::-1]).clip(0, 255).astype(np.uint8)
        tiles.append(cv2.copyMakeBorder(cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC), 0, 0, 0, 6,
                                        cv2.BORDER_CONSTANT, value=60))
    cv2.imwrite(path, np.concatenate(tiles, 1))


def main():
    dev = "cuda"
    name = sys.argv[1]
    if name == "test":                               # a candle moved 2 cm side to side
        ph = TAU * np.arange(FRAMES) / FRAMES
        path = np.stack([0.02 * np.sin(ph), 4.0 + 0 * ph, 1.4 + 0.004 * np.sin(2 * ph)], 1)
        dens, origin, cell = simulate(path, dev, 0, print)
        sheet(dens, os.path.join(ROOT, "wip", "preview", "smoke-test.png"))
        print("cells", dens.shape[1:], "origin", origin.round(3), "peak", float(dens.max()))
        return
    src = json.load(open(os.path.join(ROOT, "wip", "scene3d", name + "_sources.json")))
    out = os.path.join(ROOT, "wip", "sim", name)
    os.makedirs(out, exist_ok=True)
    for k, s in enumerate(src):
        dens, origin, cell = simulate(s["path"], dev, k, lambda m, s=s: print(s["id"], m, flush=True))
        np.savez_compressed(os.path.join(out, s["id"] + ".npz"), density=dens, origin=origin, cell=cell)
    print("SMOKE_DONE", name, len(src))


if __name__ == "__main__":
    main()
