"""Fire of an outdoor scene, by gas dynamics, in metres and seconds.

The owner on flames that were the plate's own pixels carried upward: "the flames don't look real, they move too
fast and they seem to be animated, not simulated", "the fire is far away, there is no way convection will move the
fire so fast". The rule of this project (DESIGN.md sections 5.6 and 5.7): fire and smoke are simulated, and their
pace on the screen follows from their real size and their distance.

Each fire burns in its own box of air, BOX widths of the fire in size. In the box the air obeys the same equations
as the smoke of the candles (src/smoke.py), with fuel and soot as further fields:

    du/dt + (u . grad) u = -grad p + nu lap u + g' th z^ + f            div u = 0
    dth/dt + (u . grad) th = HEAT r - cooling
    dY/dt + (u . grad) Y = -r                 r: the fuel that burns per second
    dS/dt + (u . grad) S = r - S / t_soot
    dF/dt + (u . grad) F = r - F / t_glow

u is the air velocity; th = T / T0 - 1 the temperature over that of the air, in units of the air's own; Y the
fuel gas, 1 where it leaves the bed; F the soot that has just formed, which glows while it is hot: the flame; S the
soot that is left when it has cooled: dark smoke. Hot gas is lighter than the air by the share th, so it rises with g th. A wind crosses the box and
changes in gusts.

- **Pace** - every time of the model is a multiple of sqrt(width / g): a fire four times as wide burns, cools and
  turns over half as fast. This is the similarity of buoyant flows (Froude), and it is why a large fire seen from
  far moves slowly
- **Checked against measurements** - `test` prints three measures of a round fire in still air beside those of
  measured fires: how often it sheds a ring of flame (1.5 / sqrt(D) times per second, Cetegen and Ahmed 1993), how
  fast its gas rises (6.84 sqrt(z) m/s in the flame, McCaffrey 1979) and how tall its flame is (Heskestad 1983).
  With g itself the gas of the model rose at the measured speed, within 25 %, and the model shed rings 2.1 times
  as often as measured fires, at every width. Its time is therefore stretched by PACE (g' = g / PACE^2): the rings
  come at the measured rate, which is what the eye follows in a fire seen from far, and the gas rises at about
  half the measured speed
- **Picture** - the box is seen from far along its depth: the glow of the hot soot is summed along each line of
  sight, less what the soot before it takes. One picture per frame: glow, and how much the soot covers
- **Loop** - the fire does not repeat by itself. After a warm-up, the loop and CLOSE more frames are recorded; the
  last CLOSE frames of the loop are led over into the frames before its first, so the last frame meets the first

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/fire.py test [width m]   # wip/preview/fire-test.png
    ... src/fire.py muster [fire ...] # wip/sim/muster/<fire>.npz and .png: the loop of every fire of src/muster.py, or of those named
"""
import os, sys, math
import numpy as np, torch
import torch.nn.functional as F
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke import sample, smooth

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU, G = 2 * math.pi, 9.81
N = (128, 96, 192)                         # cells: across, in depth, up
BOX = (4.0, 3.0, 6.0)                      # the box, in widths of the fire
BED = (1.3, 1.5, 0.6)                      # the middle of the bed in the box, in widths; the wind carries the flame to +x
DEEP = 0.5                                 # the bed is this deep, in widths: an ellipse
# times in units of sqrt(width / g): a parcel of fuel burns out; hot gas cools; soot thins out of sight; fresh soot
# burns up or cools and stops glowing
T_BURN, T_COOL, T_SOOT, T_GLOW = 0.25, 5.0, 3.5, 0.3
HEAT, HOTTEST = 7.0, 4.2                   # the heat of the fuel, as th per unit of fuel; the hottest gas (1500 K)
PACE = 2.1                                 # the model's time runs this many times slower than it would with g itself: see "Checked"
CONFINE = 1.2                              # vorticity confinement: returns the swirl the grid's advection loses; per unit of the fire's time
EDDY = 0.08                                # the unrest of the air: forcing by eddies of 0.15 to 0.5 widths, in widths per unit of time squared
LUMPS = 7                                  # the bed is this many heaps of fuel, each at its own height
GLOW = (2.0, 3.4)                          # soot starts to glow at this th (870 K) and glows fully at this one (1280 K)
DARK = 0.9                                 # how much a unit of soot per width takes of the light behind it
CLOSE = 40                                 # the frames led over at the end of the loop


class Fire:
    def __init__(self, width, dev, seed=0, deep=None, fine=1.0, lumps=None, tall=1.0, pace=None):
        self.N = X, Y, Z = tuple(8 * round(n * fine / 8) for n in N)
        self.pace = pace or PACE
        self.dev, self.W, self.t0 = dev, width, self.pace * math.sqrt(width / G)
        self.dx = dx = BOX[0] * width / X
        self.u = torch.zeros(3, X, Y, Z, device=dev)
        self.q = torch.zeros(4, X, Y, Z, device=dev)                  # th, fuel, soot, glowing soot
        ax = [torch.arange(n, device=dev, dtype=torch.float32) for n in self.N]
        self.idx = torch.stack(torch.meshgrid(*ax, indexing="ij"), -1)
        k = [TAU * torch.fft.fftfreq(X, dx), TAU * torch.fft.fftfreq(Y, dx), TAU * torch.fft.rfftfreq(Z, dx)]
        self.k = torch.stack(torch.meshgrid(*[v.to(dev) for v in k], indexing="ij"))
        self.k2 = (self.k ** 2).sum(0)
        self.k2[0, 0, 0] = 1.0
        wall = lambda a, n, lo, hi: smooth(0.0, lo * width, a * dx) * smooth(n * dx, n * dx - hi * width, a * dx)
        self.keep = (wall(ax[0], X, 0.25, 0.5)[:, None, None] * wall(ax[1], Y, 0.25, 0.25)[None, :, None]
                     * wall(ax[2], Z, 0.2, 0.9)[None, None, :])
        # the bed: heaps of fuel inside an ellipse, each at its own height; each burns stronger and weaker in its own slow course
        g = np.random.default_rng(seed)
        p = self.idx * dx / width
        deep = deep or DEEP
        self.heaps = []
        if lumps == 0:                                                # one even bed, as the fires of the measurements
            r = torch.sqrt(((p[..., 0] - BED[0]) / 0.5) ** 2 + ((p[..., 1] - BED[1]) / (0.5 * deep)) ** 2)
            self.heaps.append(((1 - smooth(0.8, 1.0, r)) * torch.exp(-((p[..., 2] - BED[2]) / (1.5 * dx / width)) ** 2), 0.0, 0.0))
        for _ in range(LUMPS if lumps is None else lumps):
            r, a = 0.42 * math.sqrt(g.uniform(0, 1)), g.uniform(0, TAU)
            cx, cy, cz, size = BED[0] + r * math.cos(a), BED[1] + r * deep * math.sin(a), BED[2] + g.uniform(-0.07, 0.07), g.uniform(0.10, 0.20)
            heap = torch.exp(-(((p[..., 0] - cx) / size) ** 2 + ((p[..., 1] - cy) / (size * max(deep, 0.6))) ** 2 + ((p[..., 2] - cz) / (0.35 * size)) ** 2))
            self.heaps.append((heap, g.uniform(0, TAU), g.uniform(0.1, 0.35)))
        self.burns = T_BURN * tall
        self.rich = (1 - sum(heap for heap, _, _ in self.heaps).clamp(max=1)) ** 2      # at the fuel itself the gas is too rich to glow
        # the unrest of the air: waves without divergence on the box's own lattice
        self.eddies = []
        for rate in (0.3, 0.5, 0.8):
            A, B = torch.zeros_like(self.u), torch.zeros_like(self.u)
            for field in (A, B):
                for _ in range(5):
                    lam = g.uniform(0.15, 0.5) * width
                    m = g.normal(size=3)
                    m = np.round(m / np.linalg.norm(m) * np.array([X, Y, Z]) * dx / lam)
                    kv = TAU * m / (np.array([X, Y, Z]) * dx)
                    if not np.any(m):
                        continue
                    a = np.cross(kv, g.normal(size=3))
                    wave = torch.sin((self.idx * dx * torch.tensor(kv, device=dev, dtype=torch.float32)).sum(-1) + g.uniform(0, TAU))
                    field += torch.tensor(a / np.linalg.norm(a), device=dev, dtype=torch.float32)[:, None, None, None] * wave
            self.eddies.append((rate, A, B))
        self.nu = 3e-4 * width ** 2 / self.t0                         # the eddies smaller than a cell, as a viscosity

    def advect(self, q, adv, dt):
        """MacCormack advection with a limiter (as src/smoke.py)."""
        def trace(p, sign):
            v = sample(adv, p).movedim(0, -1)
            v = sample(adv, p - sign * 0.5 * dt / self.dx * v).movedim(0, -1)
            return p - sign * dt / self.dx * v
        pb = trace(self.idx, 1.0)
        q1 = sample(q, pb)
        q2 = sample(q1, trace(self.idx, -1.0))
        lo = -sample(F.max_pool3d(-q[None], 3, 1, 1)[0], pb, "nearest")
        hi = sample(F.max_pool3d(q[None], 3, 1, 1)[0], pb, "nearest")
        return torch.minimum(torch.maximum(q1 + 0.5 * (q - q2), lo), hi)

    def step(self, t, dt, wind):
        """One step. wind: (across, in depth) in m/s."""
        t0, dx = self.t0, self.dx
        adv = self.u.clone()
        adv[0] += wind[0]
        adv[1] += wind[1]
        q = self.advect(torch.cat([self.u, self.q]), adv, dt)
        u, th, fuel, soot, flame = q[:3], q[3], q[4], q[5], q[6]
        bed = sum(heap * (0.65 + 0.35 * math.sin(ph + TAU * rate * t / t0)) for heap, ph, rate in self.heaps).clamp(max=1)
        fuel = torch.maximum(fuel, bed)
        th = torch.maximum(th, 1.5 * bed)                             # the bed is alight
        burn = torch.minimum(fuel, dt / (self.burns * t0) * (0.3 + 0.7 * fuel)) * (th > 0.3)
        fuel = fuel - burn
        th = (th + HEAT * burn).clamp(max=HOTTEST)
        soot = (soot + burn) * math.exp(-dt / (T_SOOT * t0))
        flame = (flame + burn) * math.exp(-dt / (T_GLOW * t0))
        th = th / (1 + dt / (T_COOL * t0) * (1 + (th / 2) ** 3))       # hot gas radiates: it cools faster the hotter it is
        u[2] = u[2] + G / self.pace ** 2 * th * dt
        for rate, A, B in self.eddies:
            a = TAU * rate * t / t0
            u = u + EDDY * self.W / t0 ** 2 * dt * (math.cos(a) * A + math.sin(a) * B)
        d = lambda f, ax: (torch.roll(f, -1, ax) - torch.roll(f, 1, ax)) / (2 * dx)
        w = torch.stack([d(u[2], 1) - d(u[1], 2), d(u[0], 2) - d(u[2], 0), d(u[1], 0) - d(u[0], 1)])
        mag = w.norm(dim=0)
        eta = torch.stack([d(mag, 0), d(mag, 1), d(mag, 2)])
        eta = eta / (eta.norm(dim=0) + 1e-6)
        u = u + CONFINE * dx * dt / t0 * torch.linalg.cross(eta, w, dim=0)      # by the fire's own time, as every term: per second it filled the box of a slow fire with noise
        u = u * self.keep
        uh = torch.fft.rfftn(u, dim=(1, 2, 3)) * torch.exp(-self.nu * self.k2 * dt)
        uh = uh - self.k * (self.k * uh).sum(0) / self.k2
        uh[:, 0, 0, 0] = 0
        self.u = torch.fft.irfftn(uh, s=self.N, dim=(1, 2, 3))
        self.q = torch.stack([th, fuel, soot, flame]) * self.keep

    def picture(self):
        """The box seen along its depth: the glow that reaches the eye and the soot along each line of sight, both
        (across, up), per width of the fire."""
        th, _, soot, flame = self.q
        step = self.dx / self.W
        before = (torch.cumsum(soot, 1) - soot) * step
        glow = (flame * self.rich * smooth(*GLOW, th) ** 2 * torch.exp(-3 * DARK * before)).sum(1) * step
        return glow, (soot * self.rich).sum(1) * step


def gusts(t, loop, course, mean, phases):
    """The wind speed at the time t: `mean` times a course that repeats every `loop` seconds."""
    return mean * (1 + sum(share * math.sin(TAU * (cycles * t / loop + ph)) for (cycles, share), ph in zip(course, phases)))


def pace(width, like):
    """The stretch of the model's time for a fire `width` metres wide that is to move as a fire `like` metres wide."""
    return PACE * math.sqrt(like / width) if like else PACE


def simulate(width, dev, frames=120, fps=30, wind=(1.1, 1.0), course=((1, 0.25), (2, 0.20), (3, 0.15)), seed=0, deep=None, fine=1.0, lumps=None,
             tall=1.0, like=None, log=None):
    """The loop of one fire `width` metres wide: glow and soot, each (frames, up, across) with row 0 at the top; the
    light of the whole fire per frame; the size of a cell in metres; the cell of the middle of the bed (across, up
    from the lowest row). `deep` is the depth of its bed in widths; `fine` makes the cells that many times smaller;
    `lumps` is the number of heaps of its bed; `tall` makes its fuel burn that many times longer, which makes its flame
    taller; `like` gives it the pace of a fire that many metres wide, by a stretch of its time."""
    slow = pace(width, like)
    sim = Fire(width, dev, seed, deep, fine, lumps, tall, slow)
    fast = 3.0 * math.sqrt(G * width) / slow                          # about the fastest gas
    sub = max(1, math.ceil(fast / fps / (2.5 * sim.dx)))              # a step moves the gas 2.5 cells at most
    dt = 1.0 / (fps * sub)
    loop = frames / fps
    warm = math.ceil(14 * sim.t0 / loop) * loop                       # seconds: whole loops, so the wind's course goes on unbroken
    phases = np.random.default_rng(seed + 50).uniform(0, 1, len(course))
    steps = math.ceil(warm / min(2.0 * sim.dx / fast, 1.0 / fps))     # the warm-up in steps as long as the gas allows
    for k in range(steps):
        t = k * warm / steps
        blow = gusts(t, loop, course, 1.0, phases)
        sim.step(t, warm / steps, (wind[0] * blow / slow, wind[1] * blow / slow))
    rec, speed = [], []
    for frame in range(frames + CLOSE):
        for s in range(sub):
            t = warm + (frame + s / sub) / fps
            blow = gusts(t, loop, course, 1.0, phases)
            sim.step(t, dt, (wind[0] * blow / slow, wind[1] * blow / slow))      # the wind in the model's time
        rec.append(torch.stack(sim.picture()))
        speed.append(sim.u[2].amax().item())
    rec = torch.stack(rec)                                            # (frames + CLOSE, 2, across, up)
    k = torch.arange(frames, device=dev)
    w = smooth(frames - CLOSE, frames, k.float())[:, None, None, None]
    loop = (1 - w) * rec[CLOSE + k] + w * rec[(k - (frames - CLOSE)).clamp(min=0)]
    loop = loop.flip(-1).transpose(-1, -2)                            # (frames, 2, up from the top, across)
    if log is not None:
        lum = loop[:, 0].sum((1, 2)).cpu().numpy()
        log(f"width {width:.1f} m, cell {sim.dx:.2f} m, time stretched {slow:.1f} times, {sub} steps per frame, warm-up {warm:.0f} s in {steps} steps; "
            f"fastest gas {np.mean(speed):.1f} m/s; "
            f"the light of the fire rises and falls {rate(lum, fps):.2f} times per second and changes by {lum.std() / lum.mean():.0%}")
    return loop[:, 0].cpu().numpy(), loop[:, 1].cpu().numpy(), loop[:, 0].sum((1, 2)).cpu().numpy(), sim.dx, \
        (BED[0] / BOX[0] * sim.N[0], BED[2] / BOX[2] * sim.N[2])


def rate(light, fps, least=0.0):
    """How often per second the light of a fire rises and falls: the strongest rate of its course over `least`."""
    a = np.abs(np.fft.rfft(light - light.mean())) ** 2
    f = np.fft.rfftfreq(len(light), 1 / fps)
    a[f <= least] = 0
    return float(f[a.argmax()])


def sheet(glow, soot, path, every=6):
    """Frames of a loop side by side: the glow in white on the soot in grey."""
    import cv2
    tiles = []
    for k in range(0, len(glow), every):
        img = 90 * (1 - np.exp(-DARK * soot[k].astype(np.float32))) + 255 * (1 - np.exp(-glow[k].astype(np.float32) / (0.25 * glow.max())))
        tiles.append(cv2.copyMakeBorder(img.clip(0, 255).astype(np.uint8), 0, 0, 0, 3, cv2.BORDER_CONSTANT, value=60))
    rows = [np.concatenate(tiles[a:a + 10], 1) for a in range(0, len(tiles) - len(tiles) % 10 or len(tiles), 10)]
    cv2.imwrite(path, np.concatenate(rows, 0))


def main():
    dev = "cuda"
    if sys.argv[1] == "test":
        width = float(sys.argv[2]) if len(sys.argv) > 2 else 9.0
        for arg in sys.argv[3:]:                                      # a trial value for a constant: NAME=value
            if "=" in arg:
                globals()[arg.split("=")[0]] = eval(arg.split("=")[1])
        fps = 30
        print(f"round fire {width:.1f} m wide in still air")
        for what, lumps in (("an even bed", 0), ("a bed of heaps", 24)):
            sim = Fire(width, dev, deep=1.0, lumps=lumps)
            if not lumps:
                sim.eddies = []                                       # and air at rest
            sub = max(1, math.ceil(3.0 * math.sqrt(G * width) / PACE / fps / (2.5 * sim.dx)))
            X, Y, Z = sim.N
            bz = round(BED[2] / BOX[2] * Z)
            up = lambda z: bz + round(z * width / sim.dx)
            light, rise, tall, count = [], 0, 0, 0
            for frame in range(int(36 * sim.t0 * fps)):
                for k in range(sub):
                    sim.step((frame + k / sub) / fps, 1.0 / (fps * sub), (0.0, 0.0))
                glow = sim.picture()[0]
                light.append(glow[:, up(0.4):up(0.6)].sum().item())   # the glow in a band half a width over the bed: a ring passes it
                if frame > 12 * sim.t0 * fps:
                    rise, tall, count = rise + sim.u[2], tall + (glow > 0.1 * torch.quantile(glow.flatten(), 0.999)).float(), count + 1
            light = np.array(light[len(light) // 3:])
            often = (tall / count).amax(0)                            # how often each height glows somewhere
            height = float((often[bz:] > 0.5).sum()) * sim.dx
            heat = ((height + 1.02 * width) / 0.235) ** 2.5           # kW, by the flame height of measured fires (Heskestad)
            def measured(z):                                          # the rise on the axis of a fire of that heat (McCaffrey)
                return 6.84 * math.sqrt(z) if z < 0.08 * heat ** 0.4 else 1.93 * heat ** 0.2 if z < 0.2 * heat ** 0.4 else 1.12 * heat ** (1 / 3) / z ** (1 / 3)
            fastest = lambda z: float((rise / count)[:, :, up(z)].amax())
            print(f"  {what}: flame {height:.1f} m tall, as a measured fire of {heat / 1000 / (math.pi * width ** 2 / 4):.2f} MW per m2 (wood: 0.3 to 1)")
            print("    rise of the gas: " + ", ".join(f"{fastest(z):.1f} m/s at {z * width:.1f} m (measured {measured(z * width):.1f})" for z in (0.1, 0.25, 0.5, 1.0)))
            if not lumps:
                print(f"    rings shed per second: {rate(light, fps, 0.2 / sim.t0):.2f} (slow drift under {0.2 / sim.t0:.2f} left out); "
                      f"measured fires: {1.5 / math.sqrt(width):.2f}")
        if "sheet" in sys.argv:
            glow, soot, lum, cell, bed = simulate(width, dev, log=print)
            sheet(glow, soot, os.path.join(ROOT, "wip", "preview", "fire-test.png"))
        return
    import muster
    out = os.path.join(ROOT, "wip", "sim", sys.argv[1])
    os.makedirs(out, exist_ok=True)
    for k, (name, bed) in enumerate(muster.beds()):
        if sys.argv[2:] and name not in sys.argv[2:]:
            continue
        glow, soot, lum, cell, at = simulate(bed["width"], dev, muster.FRAMES, muster.RATE, wind=tuple(bed["wind"] * np.array(muster.WIND_TO[:2])),
                                             course=muster.GUSTS, seed=k, deep=bed.get("deep"), fine=bed.get("fine", 1.0), lumps=bed.get("lumps"), tall=bed.get("tall", 1.0),
                                             like=bed["like"],
                                             log=lambda m, name=name: print(name, m, flush=True))
        np.savez_compressed(os.path.join(out, name + ".npz"), glow=glow.astype(np.float16), soot=soot.astype(np.float16), light=lum, cell=cell,
                            bed=np.array(at), width=bed["width"])
        sheet(glow, soot, os.path.join(out, name + ".png"), 12)


if __name__ == "__main__":
    main()
