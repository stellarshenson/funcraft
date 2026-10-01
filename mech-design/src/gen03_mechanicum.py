#!/usr/bin/env python3
"""Machine-cathedral: a behemoth mainframe mid-calculation, 19:6, seamless loop.

Built on the same hand-written 3D pipeline as the mech walk (mech3d.py): boxes,
a look-at camera, a z-buffered flat-shaded rasteriser. Added here:

  * a bloom pass, so the sanctified lumens actually bleed
  * an emissive-heavy material set - cold cyan for compute, warm amber for the
    devotional lamps
  * a floor with an inlaid circuit pattern that carries the data flow

The calculation is the animation: a wave of indicator lumens travels down the
GPU ranks, the cooling fans turn a whole number of revolutions per loop, the
core pulses twice, and the censers swing once. Every one of those is a function
of `phase` in [0,1), so the last frame hands over to the first with no seam.

The design is original. It borrows the grammar of gothic industrial machine
worship - ribbed buttresses, reliquary niches, hanging censers, hooded
adepts - and none of anyone's artwork.
"""

import math
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image

import mech3d as M

W, H = 1140, 360
SS = 2
RW, RH = W * SS, H * SS
FRAMES = 36

# --------------------------------------------------------------- materials --
IRON      = np.array([0.082, 0.085, 0.100])
IRON_DK   = np.array([0.040, 0.042, 0.052])
IRON_LT   = np.array([0.140, 0.144, 0.164])
BRONZE    = np.array([0.240, 0.160, 0.072])
BRONZE_DK = np.array([0.098, 0.064, 0.030])
PCB       = np.array([0.055, 0.075, 0.070])
ROBE      = np.array([0.135, 0.070, 0.062])

COMPUTE   = np.array([0.30, 2.40, 2.75])     # cold sanctified compute light
LUMEN     = np.array([2.90, 1.55, 0.50])     # warm devotional lamp
CORE      = np.array([0.55, 2.10, 2.60])

LIGHT = {"dir": M.normalise(np.array([0.30, 0.72, 0.62])),
         "col": np.array([0.52, 0.40, 0.27]),
         "rim": np.array([0.30, 0.19, 0.08])}
FILL  = {"dir": M.normalise(np.array([-0.45, 0.35, 0.80])),
         "col": np.array([0.10, 0.20, 0.26])}
AMBIENT = np.array([0.048, 0.052, 0.068])
FOG = {"start": 95.0, "end": 460.0, "col": np.array([0.022, 0.019, 0.026])}

FLOOR_PERIOD = 6.0            # circuit inlay period along x
SCROLL = 12.0                 # 2 periods per loop


# --------------------------------------------------------------- the build --
def wave(u, phase, sharp=7.0):
    """Travelling pulse in [0,1]; u is a position along the flow, 0..1."""
    t = (u - phase) % 1.0
    return math.exp(-sharp * min(t, 1.0 - t) ** 2 * 6.0)


def gpu_card(s, x, y, z, phase, flow_u, w=5.0):
    """One reliquary GPU: shroud, PCB, edge lumens, two turning fans."""
    s.box(M.translate(x, y, z) @ M.scale(w, 1.15, 2.6), IRON)
    s.box(M.translate(x, y - 0.66, z + 0.1) @ M.scale(w * 0.96, 0.22, 2.4), PCB)
    s.box(M.translate(x - w * 0.52, y, z) @ M.scale(0.18, 1.5, 2.7), BRONZE_DK)

    lit = wave(flow_u, phase)
    s.box(M.translate(x + w * 0.44, y + 0.12, z + 1.34)
          @ M.scale(w * 0.10, 0.20, 0.10), COMPUTE * (0.25 + 1.5 * lit), emissive=True)
    s.box(M.translate(x, y - 0.60, z + 1.30) @ M.scale(w * 0.80, 0.10, 0.06),
          COMPUTE * (0.18 + 0.95 * lit), emissive=True)

    spin = 2 * math.pi * 3.0 * phase                  # 3 whole turns per loop
    for fi, fx in enumerate((-w * 0.22, w * 0.22)):
        cx = x + fx
        s.box(M.translate(cx, y, z + 1.32) @ M.scale(1.30, 1.30, 0.10), IRON_DK)
        for b in range(4):
            a = spin + b * math.pi / 2 + fi * 0.4
            s.box(M.translate(cx, y, z + 1.38) @ M.rot_z(a)
                  @ M.translate(0.42, 0, 0) @ M.scale(0.78, 0.20, 0.07), IRON_LT)
        s.box(M.translate(cx, y, z + 1.42) @ M.scale(0.22, 0.22, 0.09),
              LUMEN * 0.30, emissive=True)


def rack_bank(s, x0, z0, cols, rows, phase, flow_base, card_w=5.0):
    for c in range(cols):
        for r in range(rows):
            x = x0 + c * (card_w + 0.9)
            y = 2.6 + r * 1.85
            u = (flow_base + (r * cols + c) * 0.035) % 1.0
            gpu_card(s, x, y, z0, phase, u, card_w)
            s.box(M.translate(x, y + 0.95, z0 - 0.2)
                  @ M.scale(card_w + 0.8, 0.22, 2.9), IRON_DK)
    h = 2.6 + rows * 1.85
    for c in range(cols + 1):                          # rack ribs
        x = x0 - card_w * 0.5 - 0.45 + c * (card_w + 0.9)
        s.box(M.translate(x, h / 2, z0 - 0.35) @ M.scale(0.55, h, 3.2), IRON_DK)
    s.box(M.translate(x0 + (cols - 1) * (card_w + 0.9) / 2, h + 0.7, z0 - 0.3)
          @ M.scale(cols * (card_w + 0.9) + 1.2, 1.1, 3.6), BRONZE_DK)


def censer(s, x, y_top, z, phase, idx):
    """Hanging lamp on a chain, swinging once per loop."""
    a = 0.22 * math.sin(2 * math.pi * phase + idx * 1.7)
    L = 5.2
    tip = np.array([x + math.sin(a) * L, y_top - math.cos(a) * L, z])
    top = np.array([x, y_top, z])
    s.segment(top, tip, 0.10, 0.10, IRON_DK)
    s.box(M.translate(*tip) @ M.scale(0.85, 0.95, 0.85), BRONZE)
    s.box(M.translate(tip[0], tip[1] - 0.15, tip[2]) @ M.scale(0.52, 0.55, 0.52),
          LUMEN * (0.85 + 0.25 * math.sin(2 * math.pi * 2 * phase + idx)),
          emissive=True)


def adept(s, x, z, phase, idx, k=1.95):
    """Hooded adept, kept large enough to give the mainframe its scale."""
    b = 0.06 * math.sin(2 * math.pi * phase + idx * 2.1)
    s.box(M.translate(x, 0.95 * k + b, z) @ M.scale(1.15 * k, 1.9 * k, 0.95 * k),
          ROBE, taper=(0.58, 0.66))
    s.box(M.translate(x, 2.10 * k + b, z) @ M.scale(0.80 * k, 0.72 * k, 0.78 * k), ROBE)
    s.box(M.translate(x, 2.52 * k + b, z) @ M.scale(0.94 * k, 0.22 * k, 0.92 * k), ROBE)
    s.box(M.translate(x, 2.10 * k + b, z + 0.42 * k)
          @ M.scale(0.34 * k, 0.12 * k, 0.05 * k),
          LUMEN * (0.5 + 0.35 * math.sin(2 * math.pi * 2 * phase + idx)), emissive=True)
    for sgn in (-1, 1):                                 # mechadendrites
        s.segment(np.array([x + 0.2 * k * sgn, 1.8 * k + b, z + 0.2 * k]),
                  np.array([x + 0.9 * k * sgn, 1.0 * k + b, z + 0.8 * k]),
                  0.11 * k, 0.11 * k, IRON_DK)


def build(phase):
    s = M.Scene()

    # --- the behemoth: central core, running off the top of the frame -------
    s.box(M.translate(0, 23.0, -9.0) @ M.scale(24.0, 46.0, 12.0), IRON_DK)
    s.box(M.translate(0, 20.0, -5.4) @ M.scale(19.0, 40.0, 4.0), IRON)
    for i in range(9):                                  # ribbed buttresses
        x = -16.8 + i * 4.2
        s.box(M.translate(x, 21.0, -3.6) @ M.scale(1.2, 42.0, 1.8), IRON_DK)
    # reliquary core, pulsing twice per loop
    pulse = 0.62 + 0.38 * math.sin(2 * math.pi * 2 * phase)
    s.box(M.translate(0, 15.0, -3.2) @ M.scale(14.0, 14.0, 1.2), IRON_DK)
    s.box(M.translate(0, 15.0, -2.7) @ M.scale(12.2, 12.2, 0.5),
          CORE * (0.30 + 0.95 * pulse), emissive=True)
    # rose window: radial tracery over the core light
    for k in range(16):
        a = k * math.pi / 8 + 0.10 * math.sin(2 * math.pi * phase)
        s.box(M.translate(0, 15.0, -2.5) @ M.rot_z(a)
              @ M.translate(0, 4.1, 0) @ M.scale(0.34, 8.2, 0.4), IRON_DK)
    for ring, rad in enumerate((2.3, 4.2, 6.0)):
        seg = 20 + ring * 6
        for k in range(seg):
            a = 2 * math.pi * k / seg
            s.box(M.translate(rad * math.cos(a), 15.0 + rad * math.sin(a), -2.45)
                  @ M.rot_z(a) @ M.scale(0.34, 2 * math.pi * rad / seg * 1.25, 0.4),
                  IRON_DK)
    s.box(M.translate(0, 15.0, -2.35) @ M.scale(2.0, 2.0, 0.6),
          LUMEN * (0.8 + 0.5 * pulse), emissive=True)
    s.box(M.translate(0, 21.6, -3.0) @ M.scale(16.0, 1.6, 2.4), BRONZE_DK)
    s.box(M.translate(0, 8.2, -3.0) @ M.scale(16.0, 1.4, 2.4), BRONZE_DK)

    # --- flanking rack banks ------------------------------------------------
    rack_bank(s, -48.0, -1.0, 4, 9, phase, 0.00)
    rack_bank(s,  19.0, -1.0, 4, 9, phase, 0.50)

    # --- outer machine wall, receding --------------------------------------
    for i in range(6):
        for sgn in (-1, 1):
            x = sgn * (58.0 + i * 12.0)
            z = -14.0 - i * 9.0
            h = 26.0 - i * 2.0
            s.box(M.translate(x, h / 2, z) @ M.scale(9.0, h, 8.0), IRON_DK)
            s.box(M.translate(x, h + 0.6, z) @ M.scale(10.0, 1.0, 9.0), BRONZE_DK)
            for r in range(3):
                s.box(M.translate(x + 4.6 * sgn * -1, 4.0 + r * 5.0, z + 4.1)
                      @ M.scale(0.5, 1.6, 0.3),
                      COMPUTE * (0.15 + 0.7 * wave((i * 0.17 + r * 0.09) % 1.0, phase)),
                      emissive=True)

    # --- cable runs across the nave ----------------------------------------
    for i, y in enumerate((29.5, 27.6, 25.9)):
        sag = 2.2 + i * 0.6
        pts = [np.array([-78 + k * 19.5, y - sag * math.sin(math.pi * k / 8), 8.0 + i * 1.8])
               for k in range(9)]
        for a, b in zip(pts[:-1], pts[1:]):
            s.segment(a, b, 0.34 - i * 0.06, 0.34 - i * 0.06, IRON_DK)

    # --- censers and adepts in the foreground ------------------------------
    for i, x in enumerate((-40.0, -14.0, 14.0, 40.0)):
        censer(s, x, 30.5, 13.0, phase, i)
    for i, x in enumerate((-34.0, -22.0, -10.0, 9.0, 21.0, 33.0)):
        adept(s, x, 26.0 + (i % 3) * 3.4, phase, i)

    # --- framing pillars close to the camera --------------------------------
    for sgn in (-1, 1):
        x = sgn * 31.0
        s.box(M.translate(x, 24.0, 50.0) @ M.scale(7.0, 48.0, 7.0), IRON_DK)
        s.box(M.translate(x, 47.0, 50.0) @ M.scale(9.0, 2.0, 9.0), BRONZE_DK)
        s.box(M.translate(x - 4.6 * sgn, 34.0, 50.0) @ M.rot_z(-0.55 * sgn)
              @ M.scale(2.6, 13.0, 6.0), IRON_DK)
        for r in range(4):
            s.box(M.translate(x - 3.7 * sgn, 9.0 + r * 7.0, 53.6)
                  @ M.scale(0.6, 2.6, 0.4),
                  COMPUTE * (0.2 + 0.8 * wave((r * 0.25) % 1.0, phase)), emissive=True)

    # --- brazier plinths ----------------------------------------------------
    for sgn in (-1, 1):
        x = sgn * 52.0
        s.box(M.translate(x, 1.6, 15.0) @ M.scale(3.0, 3.2, 3.0), IRON_DK, taper=(0.7, 0.7))
        s.box(M.translate(x, 3.5, 15.0) @ M.scale(2.4, 0.7, 2.4),
              LUMEN * (0.9 + 0.3 * math.sin(2 * math.pi * 3 * phase + sgn)), emissive=True)
    return s


# ------------------------------------------------------------- background ---
def background(cam_pos, view, proj, shift):
    inv = np.linalg.inv(proj @ view)
    ys, xs = np.mgrid[0:RH, 0:RW]
    ndc_x = ((xs + 0.5) / RW) * 2 - 1
    ndc_y = 1 - ((ys + 0.5) / RH) * 2
    pts = np.stack([ndc_x, ndc_y, np.full_like(ndc_x, 0.5), np.ones_like(ndc_x)], -1)
    wpt = pts @ inv.T
    wpt = wpt[..., :3] / wpt[..., 3:4]
    ray = wpt - cam_pos[None, None, :]
    ray /= np.linalg.norm(ray, axis=-1, keepdims=True)

    t = np.clip(ray[..., 1] * 2.4, 0, 1)[..., None]
    colour = (np.array([0.006, 0.006, 0.010]) * t
              + np.array([0.018, 0.013, 0.012]) * (1 - t))
    # devotional haze behind the mainframe
    halo = np.exp(-((ray[..., 0] / 0.16) ** 2 + ((ray[..., 1] - 0.06) / 0.13) ** 2))
    colour = colour + halo[..., None] * np.array([0.085, 0.045, 0.022])
    depth = np.zeros((RH, RW))

    denom = ray[..., 1]
    hit = denom < -1e-6
    tt = np.where(hit, -cam_pos[1] / np.where(hit, denom, -1.0), 0.0)
    P = cam_pos[None, None, :] + ray * tt[..., None]
    gx, gz = P[..., 0] + shift, P[..., 2]

    g = np.broadcast_to(np.array([0.040, 0.040, 0.050]), colour.shape).copy()
    plate = (np.minimum(np.abs(((gx / 12.0) % 1.0) - 0.5),
                        np.abs(((gz / 12.0) % 1.0) - 0.5)) < 0.014)
    g[plate] = np.array([0.070, 0.068, 0.082])

    # inlaid circuit traces carrying the data flow
    trace = (np.abs(((gx / FLOOR_PERIOD) % 1.0) - 0.5) < 0.026) & (gz > -6) & (gz < 26)
    g[trace] = np.array([0.10, 0.52, 0.60])
    rung = (np.abs(((gz / 4.0) % 1.0) - 0.5) < 0.022) & (np.abs(gx) < 62)
    g[rung] = np.array([0.08, 0.34, 0.40])

    dist = np.linalg.norm(P - cam_pos[None, None, :], axis=-1)
    fg = np.clip((dist - FOG["start"]) / (FOG["end"] - FOG["start"]), 0, 1)[..., None]
    g = g * (1 - fg) + FOG["col"][None, None, :] * fg
    colour = np.where(hit[..., None], g, colour)

    fwd = -view[2, :3]
    along = ((P - cam_pos[None, None, :]) * fwd[None, None, :]).sum(-1)
    depth = np.where(hit & (along > 1e-3), 1.0 / np.where(along > 1e-3, along, 1.0), 0.0)
    return colour, depth


def bloom(img):
    """Two-scale bloom on the values that exceed display white."""
    hot = np.maximum(img - 0.95, 0.0)
    b1 = gaussian_filter(hot, sigma=(5 * SS, 5 * SS, 0))
    b2 = gaussian_filter(hot, sigma=(22 * SS, 22 * SS, 0))
    return img + b1 * 1.05 + b2 * 0.75


# ------------------------------------------------------------------ main ----
def main(out):
    cam = np.array([0.0, 12.0, 98.0])
    view = M.look_at(cam, np.array([0.0, 13.0, 0.0]))
    proj = M.perspective(21.0, W / H, 0.4, 800.0)

    # patch mech3d's render-time constants to this frame size
    M.RW, M.RH = RW, RH

    frames = []
    for i in range(FRAMES):
        phase = i / FRAMES
        scene = build(phase)
        shift = phase * SCROLL

        def sky_fn(_s=shift):
            return background(cam, view, proj, _s)

        colour, _ = M.render(scene, view, proj, cam, LIGHT, FILL, AMBIENT, FOG,
                             sky_fn, RW, RH)
        img = bloom(colour)
        img = np.clip(img, 0, 1) ** (1 / 2.2)
        frames.append(Image.fromarray((img * 255).astype(np.uint8))
                      .resize((W, H), Image.LANCZOS))
        print(f"  frame {i + 1}/{FRAMES}", flush=True)

    pal = frames[0].quantize(colors=220, method=Image.MEDIANCUT)
    outf = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
    outf[0].save(out, save_all=True, append_images=outf[1:],
                 duration=55, loop=0, optimize=True, disposal=1)
    print("wrote", out)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "mechanicum.gif")
