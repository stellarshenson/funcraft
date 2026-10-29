"""Candle flames of a scene, by gas dynamics, in metres and seconds.

The owner: "light in those candles must also be simulated flame". A flame drawn from the plate's own pixels and leaned
by the draft (DESIGN.md section 5.6) gives way to a candle that burns at its real size in the same air (src/air.py).

Each candle burns in its own box of air, N cells of DX, the wick standing on the wax in the middle of its floor. A
candle flame is a laminar diffusion flame: wax vapour leaves the wick, mixes with the air and burns where the two meet
in the proportion in which they burn. Its gas is hot and light and rises; the room's air crosses the box.

    du/dt + (u . grad) u = -grad p + nu lap u + g th z^           div u = 0
    dZ/dt + (u . grad) Z = D lap Z                                 Z = 1 in the wick
    th = TH(Z)
    dS/dt + (u . grad) S = form - burn

Z, the mixture fraction, is the share of the gas that left the wick as vapour. Burning is fast against mixing, so the
temperature follows from Z alone (Burke and Schumann): th = T / T0 - 1, as in src/fire.py, is highest (TH_FLAME) where
Z is Z_ST, where vapour and air meet in the proportion in which they burn, and falls to that of the air on the lean
side and to that of the wick on the rich side. Soot S forms on the rich side where the gas is hot, rises with it and
burns where it reaches the lean side while still hot: the yellow flame is this soot, glowing. Low on the flame, where
no soot has formed yet, the sheet where Z is Z_ST shows blue.

- **Open box** - the box is periodic: the gas the flame lifts came back down beside it, at up to 0.4 m/s in a box
  5 cm wide, and leaned the flame in still air. The air of the box rises instead, as much as the flame lifts through
  its middle height (about 8 cm/s): the air a flame draws in from an open room
- **Laminar** - viscosity and diffusion are those of the hot gas (NU): a candle flame does not flicker by itself.
  It leans, stretches and shortens in the air that crosses it
- **Air** - the draft of src/air.py at the wick, as the smoke of the scene feels it, and GUSTS of its gusts. Those
  gusts (0.35 m/s) were set to sway flames drawn from the plate, which leaned as a whole by atan(v / 1 m/s). The gas
  of a burning flame rises slowly near the wick, and in them the flame was torn off the wick and its light changed
  by 37 %: a breeze that makes a candle gutter. The air of a church near its candles moves at 0.05 to 0.15 m/s
- **Picture** - the box is turned about the vertical so that its depth lies along the camera's line of sight to the
  wick, and the light is summed along that line. The colours are those of the painted flames of the plate, by the
  rank of the light (as the fires of src/muster.py); faint light covers little of what is behind it
- **Loop** - the air of src/air.py repeats every loop. After a warm-up, the loop and CLOSE frames more are recorded;
  the last CLOSE frames are led over into the frames recorded before the first (as src/fire.py). Loop frame k shows
  the time k / fps of the loop, as the light and the smoke of the candle
- **Light** - per frame the light of the flame against its mean: the candle light of src/rig.py
- **Air before it** - the model's flame is 6 to 7 mm wide where a real candle's is 10 to 12 mm: gas that heats
  takes more room, which the model of air of one density cannot show (the term for it moved little: its flame stayed
  7 mm wide). The flame is seen through the smoky air of the church: its picture is blurred as the fires of
  src/muster.py are (SCATTER: 0.6 plate pixels and 0.45 more per 100 m), which shows it about as wide as a real one
- **Glow** - the painted flames carry a glow round them (HALO) that the flames taken out of the plate took with
  them; each simulated flame gets it round the middle of its light, as bright as its light at each frame
- **Size** - a flame shows at its real size at the depth of its wick, but not smaller than FLAME_PX plate pixels and
  not larger than the plate painted it (src/actors.py); its tip is where the smoke of its candle starts

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/candle.py test [still]   # wip/preview/candle-test.png
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/candle.py <name> [flame ...]
                                    # wip/sim/<name>/flames/<flame>.npz: its pictures, light and size; every flame or those named
"""
import os, sys, math, json
import numpy as np, torch
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import air
from smoke import smooth
from fire import Fire
from muster import SCATTER

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAU, G = 2 * math.pi, 9.81
FRAMES = int(os.environ.get("LOOP_FRAMES", 80))      # as src/scenes.py: the loop lasts air.LOOP seconds
FPS = FRAMES / air.LOOP
DX = 0.0005                                # m, one cell
N = (96, 64, 160)                          # cells: across, in depth, up; 4.8 x 3.2 x 8 cm
WAX = (0.010, 0.015)                       # m: the candle's radius, and the height of its top over the box floor
WICK = (0.0008, 0.007)                     # m: the wick's radius and how far it stands over the wax
NU = 3.0e-4                                # m2/s, viscosity of the gas of a flame (air at about 1800 K); its diffusion, the same
Z_ST = 0.064                               # the share of wax vapour at which vapour and air burn completely (paraffin)
TH_FLAME, TH_WICK = 4.3, 1.0               # th where Z is Z_ST (1600 K) and at the wick (600 K)
SOOT = (2.6, 3.6, 120.0, 600.0)            # soot forms and burns between these th, this fast and this fast per second
HOT = 6                                    # soot glows as the power HOT of its temperature: the visible light of a hot body
BLUE = (0.35, 0.10)                        # the light of the blue sheet against the brightest soot; its width in Z_ST
CLOSE = 20                                 # the frames led over at the end of the loop
# the glow round a painted flame of the plate: the light the smoky air and the lens spread round it. Its colour, its
# light at the flame (as the light of an emission) and its radius in plate pixels; measured on the saint plate, in rings
# of 3 px round 9 flames: about as much light as the flame itself, falling to half in 12 px; its light set so that
# the render matches those rings 9 to 20 px from the flame (0.08 gave a fifth of them)
HALO = ((1.0, 0.67, 0.4), 0.30, 11.0)
GUSTS = 0.3                                # the share of air.py's gusts a burning flame feels: see "Air"


class Candle:
    advect = Fire.advect                   # MacCormack advection with a limiter: needs self.idx and self.dx

    def __init__(self, dev):
        X, Y, Z = N
        self.dev, self.dx = dev, DX
        self.u = torch.zeros(3, X, Y, Z, device=dev)
        self.q = torch.zeros(2, X, Y, Z, device=dev)                  # Z, soot
        ax = [torch.arange(n, device=dev, dtype=torch.float32) for n in N]
        self.idx = torch.stack(torch.meshgrid(*ax, indexing="ij"), -1)
        k = [TAU * torch.fft.fftfreq(X, DX), TAU * torch.fft.fftfreq(Y, DX), TAU * torch.fft.rfftfreq(Z, DX)]
        self.k = torch.stack(torch.meshgrid(*[v.to(dev) for v in k], indexing="ij"))
        self.k2 = (self.k ** 2).sum(0)
        self.k2[0, 0, 0] = 1.0
        wall = lambda a, n, lo, hi: smooth(0.0, lo, (a + 0.5) * DX) * smooth(n * DX, n * DX - hi, (a + 0.5) * DX)      # even about the middle
        self.keep = (wall(ax[0], X, 0.006, 0.006)[:, None, None] * wall(ax[1], Y, 0.006, 0.006)[None, :, None]
                     * wall(ax[2], Z, 0.002, 0.015)[None, None, :])
        p = (self.idx + 0.5) * DX
        r = torch.sqrt((p[..., 0] - X * DX / 2) ** 2 + (p[..., 1] - Y * DX / 2) ** 2)
        self.solid = ((r < WAX[0]) & (p[..., 2] < WAX[1])).float()
        self.wick = ((r < WICK[0]) & (p[..., 2] < WAX[1] + WICK[1])).float()
        self.solid = torch.maximum(self.solid, self.wick)

    def temperature(self, z):
        """th by the mixture: TH_FLAME at Z_ST, 0 in the air, TH_WICK in pure vapour."""
        lean = TH_FLAME * z / Z_ST
        rich = TH_WICK + (TH_FLAME - TH_WICK) * (1 - z) / (1 - Z_ST)
        return torch.where(z < Z_ST, lean, rich)

    def step(self, dt, wind):
        """One step. wind: (across, in depth, up) in m/s."""
        adv = self.u + torch.tensor(wind, device=self.dev, dtype=torch.float32)[:, None, None, None]
        q = self.advect(torch.cat([self.u, self.q]), adv, dt)
        u, z, s = q[:3], q[3], q[4]
        z = torch.maximum(z * (1 - self.solid), self.wick)                       # the wick gives vapour; the wax none
        th = self.temperature(z)
        hot = smooth(SOOT[0], SOOT[1], th)
        s = s + dt * SOOT[2] * hot * (z > Z_ST) * ((z - Z_ST) / Z_ST).clamp(max=1)    # soot forms on the rich side
        s = s * torch.exp(-dt * SOOT[3] * hot * (z < Z_ST))                       # and burns on the lean side
        u[2] = u[2] + G * th * dt
        u = u * (1 - self.solid) * self.keep
        uh = torch.fft.rfftn(u, dim=(1, 2, 3)) * torch.exp(-NU * self.k2 * dt)
        uh = uh - self.k * (self.k * uh).sum(0) / self.k2
        uh[:, 0, 0, 0] = 0
        self.u = torch.fft.irfftn(uh, s=N, dim=(1, 2, 3))
        self.u[2] += self.u[2, :, :, N[2] // 2].clamp(min=0).mean()       # the open room: see "Open box"
        zh = torch.fft.rfftn(z * self.keep, dim=(0, 1, 2)) * torch.exp(-NU * self.k2 * dt)
        self.q = torch.stack([torch.fft.irfftn(zh, s=N, dim=(0, 1, 2)).clamp(0, 1), s * self.keep])

    def picture(self):
        """The flame seen along the box's depth: the light of the soot and of the blue sheet, each (across, up)."""
        z, s = self.q * (1 - self.solid)
        th = self.temperature(z)
        glow = (s * (th / TH_FLAME).clamp(min=0) ** HOT).sum(1) * DX
        sheet = torch.exp(-((z - Z_ST) / (BLUE[1] * Z_ST)) ** 2) * smooth(SOOT[0], SOOT[1], th) * (1 - (s / 0.02).clamp(max=1))
        return glow, sheet.sum(1) * DX


def simulate(wind, dev, frames=FRAMES, log=None):
    """The loop of one candle. wind(t): (across, in depth, up) m/s at the wick at time t. Returns the glow and the blue,
    each (frames, up from the top, across), the light per frame and the height of the flame over the wick in metres."""
    sim = Candle(dev)
    warm = frames - CLOSE - 1                                         # frames: recorded frame CLOSE + k then shows the time k / FPS of the loop
    rec, steps, t = [], 0, 0.0
    for i in range(warm + frames + CLOSE):
        fast = float(sim.u.abs().amax()) + 0.5                        # about the fastest gas, with the wind
        sub = max(1, math.ceil(fast / FPS / (1.5 * DX)))              # a step moves the gas 1.5 cells at most
        for j in range(sub):
            sim.step(1.0 / (FPS * sub), wind(t + j / (FPS * sub)))
        t, steps = (i + 1) / FPS, steps + sub
        if i >= warm:
            rec.append(torch.stack(sim.picture()))
    rec = torch.stack(rec)                                            # (frames + CLOSE, 2, across, up)
    k = torch.arange(frames, device=dev)
    w = smooth(frames - CLOSE, frames, k.float())[:, None, None, None]
    loop = (1 - w) * rec[CLOSE + k] + w * rec[(k - (frames - CLOSE)).clamp(min=0)]
    loop = loop.flip(-1).transpose(-1, -2)                            # (frames, 2, up from the top, across)
    glow, blue = loop[:, 0], loop[:, 1]
    peak = float(glow.amax())
    light = (glow + BLUE[0] * peak / max(float(blue.amax()), 1e-9) * blue).sum((1, 2))
    seen = (glow.amax(0) > 0.05 * peak).any(1).nonzero()
    wick_row = N[2] - 1 - (WAX[1] + WICK[1]) / DX
    height = (wick_row - float(seen.min())) * DX if len(seen) else 0.0
    if log is not None:
        lum = light.cpu().numpy()
        log(f"{steps} steps, fastest gas {float(sim.u.abs().amax()):.2f} m/s, flame {height * 100:.1f} cm over the wick, "
            f"light changes by {lum.std() / lum.mean():.0%} (largest {lum.max() / lum.mean():.2f}, least {lum.min() / lum.mean():.2f})")
    return glow.cpu().numpy(), blue.cpu().numpy(), light.cpu().numpy(), height


def sheet(glow, blue, path, every=8):
    """Frames of a loop side by side, the soot's light in warm white, the blue sheet in blue."""
    import cv2
    tiles = []
    g, b = glow / glow.max(), blue / max(blue.max(), 1e-9)
    for k in range(0, len(glow), every):
        img = np.dstack([255 * (1 - np.exp(-3 * g[k])) * 0.75 + 255 * BLUE[0] * b[k], 255 * (1 - np.exp(-3 * g[k])) * 0.9,
                         255 * (1 - np.exp(-3 * g[k]))])
        img = cv2.resize(img.clip(0, 255).astype(np.uint8), None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
        tiles.append(cv2.copyMakeBorder(img, 0, 0, 0, 3, cv2.BORDER_CONSTANT, value=(60, 60, 60)))
    cv2.imwrite(path, np.concatenate(tiles, 1))


def frame_axes(wick):
    """The box's axes in the world: across (to the right on the picture), in depth (along the line of sight), up."""
    v = np.array([wick[0], wick[1], 0.0])
    depth = v / np.linalg.norm(v)
    return np.array([depth[1], -depth[0], 0.0]), depth, np.array([0.0, 0.0, 1.0])


def feel(p, axes, t):
    """The air a flame at the world point p feels at the time t, in the box's axes: (across, in depth, up) m/s."""
    v = air.draft(p, t) + GUSTS * air.gust(p, t)
    return tuple(float(a @ v) for a in axes)


def middle(rgba, wick, cell):
    """The middle of a flame's light over the loop, from its pictures: (across, up) in metres from the top of the wick."""
    a = rgba[..., 3].astype(np.float32).mean(0)
    rows, cols = np.mgrid[:a.shape[0], :a.shape[1]]
    cx, cy = (a * cols).sum() / a.sum() + 0.5, (a * rows).sum() / a.sum() + 0.5
    return np.array([(cx - wick[0]) * cell, (wick[1] - cy) * cell])


def spread(rgba, sigma):
    """The pictures of a loop blurred by sigma of their pixels: the light and the cover, the colour kept as the colour
    of the light."""
    import cv2
    a = rgba[..., 3:].astype(np.float32) / 255
    lit = rgba[..., :3].astype(np.float32) / 255 * a
    out = []
    for c, k in zip(lit, a):
        k, c = cv2.GaussianBlur(k, (0, 0), sigma)[..., None], cv2.GaussianBlur(c, (0, 0), sigma)
        out.append(np.dstack([c / np.maximum(k, 1e-4), k]).clip(0, 1))
    return (np.stack(out) * 255).round().astype(np.uint8)


def colours(name):
    """The colours of the painted flames of the plate, darkest first: 256 steps."""
    import cv2
    from repaint import plate as before                             # the plate as painted: a window repaint covers the flame before it
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    plate = before(name).astype(np.float32) / 255
    seg = np.load(stem + "_seg.npz")
    masks = np.zeros(plate.shape[:2], np.uint8)
    for fl in json.loads(str(seg["flames"])):
        masks |= seg[fl["id"]].astype(np.uint8)
    wide = cv2.dilate(masks, np.ones((3, 3), np.uint8)) > 0
    pixels = plate[wide & (plate[..., 0] > 0.45) & (plate[..., 0] >= plate[..., 2])]
    pixels = pixels[np.argsort(pixels @ np.array([0.2126, 0.7152, 0.0722], np.float32))]
    ramp = np.stack([np.median(part, 0) for part in np.array_split(pixels, 64)])
    return cv2.resize(ramp[None], (256, 1), interpolation=cv2.INTER_LINEAR)[0]


def paint(glow, blue, ramp):
    """The pictures of a loop in the colours of the painted flames, by the rank of their light among the lit pixels
    of the loop; faint light covers little. The blue sheet adds its own colour. (frames, up, across, 4): colour and
    cover, half the size of the box's cells."""
    import cv2
    lit = glow[glow > 0.02 * glow.max()]
    rank = np.interp(glow, np.quantile(lit, np.linspace(0, 1, 256)), np.linspace(0, 1, 256), left=0.0)
    cover = 1 - np.exp(-glow / np.quantile(lit, 0.3))
    sheet = BLUE[0] * blue / blue.max()
    rgb = ramp[(rank * 255).astype(int)] * cover[..., None] + np.array([0.35, 0.5, 1.0]) * sheet[..., None]
    alpha = 1 - (1 - cover) * (1 - sheet.clip(0, 1))
    half = lambda a: cv2.resize(a, (a.shape[1] // 2, a.shape[0] // 2), interpolation=cv2.INTER_AREA)
    out = []
    for c, a in zip(rgb, alpha):
        a = half(a.astype(np.float32))
        c = half(c.astype(np.float32)) / np.maximum(a, 1e-4)[..., None]      # the colour itself: the renderer lays it by the cover
        out.append(np.dstack([c.clip(0, 1), a.clip(0, 1)]))
    return (np.stack(out) * 255).round().astype(np.uint8)


def main():
    dev = "cuda"
    if sys.argv[1] == "test":                                         # a candle 7 m before the camera, in the air of the loop or in still air
        p = np.array([0.0, 7.0, -0.5])
        ax = frame_axes(p)
        still = "still" in sys.argv
        wind = lambda t: (0.0, 0.0, 0.0) if still else feel(p, ax, t)
        glow, blue, light, height = simulate(wind, dev, log=print)
        sheet(glow, blue, os.path.join(ROOT, "wip", "preview", "candle-test.png"))
        return
    from actors import FLAME_PX, flame_scale
    name, only = sys.argv[1], sys.argv[2:]
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    meta = json.loads(str(np.load(stem + "_actors.npz")["meta"]))
    painted = {fl["id"]: fl for fl in json.loads(str(np.load(stem + "_seg.npz")["flames"]))}
    K = np.load(stem + ".npz")["intrinsics"]
    from PIL import Image
    f = float(K[0, 0]) * Image.open(stem + ".png").size[0]          # the focal length in plate pixels
    ramp = colours(name)
    out = os.path.join(ROOT, "wip", "sim", name, "flames")
    os.makedirs(out, exist_ok=True)
    for a in meta:
        if a["kind"] != "flame" or "parent" in a or (only and a["id"] not in only):
            continue
        p = np.array(a["bones"][0][1])                                # the wick
        axes = frame_axes(p)
        glow, blue, light, height = simulate(lambda t: feel(p, axes, t), dev, log=lambda m: print(a["id"], m, flush=True))
        fl = painted[a["id"]]
        z = float(p[1])
        shown = height * f / z                                        # plate pixels at its real size
        want = (fl["wick"][1] - fl["tip"][1]) * flame_scale(fl, z, f) if fl.get("edge") else \
            min(max(shown, FLAME_PX), max(fl["wick"][1] - fl["tip"][1], 1.0))
        grow = want / max(shown, 1e-6)
        wick, cell = np.array([N[0] / 2 / 2, (N[2] - (WAX[1] + WICK[1]) / DX) / 2]), 2 * DX * grow
        blur = (SCATTER[0][0] + SCATTER[0][1] * z / 100) * z / f / cell             # in pixels of its picture
        rgba = spread(paint(glow, blue, ramp), blur)
        np.savez_compressed(os.path.join(out, a["id"] + ".npz"), rgba=rgba, light=(light / light.mean()).astype(np.float32), cell=cell,
                            wick=wick, across=axes[0], tip=height * grow, origin=p, middle=middle(rgba, wick, cell),
                            halo=HALO[2] * z / f, glow=np.array([*HALO[0], HALO[1]]), blur=blur)
        print("FLAME", a["id"], f"{height * 100:.1f} cm, {shown:.1f} px at {z:.2f} m, shown {want:.1f} px", flush=True)
    print("FLAMES_DONE", name)


if __name__ == "__main__":
    main()
