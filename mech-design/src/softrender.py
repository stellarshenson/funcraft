#!/usr/bin/env python3
"""3D BattleMech walk cycle, rendered to a seamless 19:6 GIF.

There is no 3D library on this machine, so this file carries its own:

  * a small 4x4 transform stack and a look-at / perspective camera
  * box and segment mesh primitives, which is all a BattleMech really needs
  * a z-buffered triangle rasteriser in numpy, flat-shaded with a key light,
    a sky fill and a view-dependent rim term
  * an analytic ground plane and sky, computed per pixel from the camera rays

The geometry is original. It is built to the silhouette language of the
chassis - the Timber Wolf's reverse knees and shoulder missile racks, the
Atlas's death's-head cockpit and slab pauldrons, the BattleMaster's upright
box torso and PPC arm - not copied from any game asset.

Every periodic quantity is a function of `phase` in [0,1), so frame N-1 hands
over to frame 0 with no seam.
"""

import math
import numpy as np
from PIL import Image

# ---------------------------------------------------------------- output ----
W, H = 1140, 360                    # 19:6
SS = 2
FRAMES = 30
RW, RH = W * SS, H * SS

# ------------------------------------------------------------------ maths ---
def ident():
    return np.eye(4)


def translate(x, y, z):
    m = np.eye(4); m[:3, 3] = (x, y, z); return m


def scale(x, y=None, z=None):
    if y is None:
        y = z = x
    m = np.eye(4); m[0, 0], m[1, 1], m[2, 2] = x, y, z; return m


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4); m[1, 1], m[1, 2], m[2, 1], m[2, 2] = c, -s, s, c; return m


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4); m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c; return m


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4); m[0, 0], m[0, 1], m[1, 0], m[1, 1] = c, -s, s, c; return m


def normalise(v):
    n = np.linalg.norm(v)
    return v / n if n else v


def look_at(eye, target, up=(0.0, 1.0, 0.0)):
    eye, target, up = map(lambda v: np.asarray(v, float), (eye, target, up))
    f = normalise(target - eye)
    r = normalise(np.cross(f, up))
    u = np.cross(r, f)
    m = np.eye(4)
    m[0, :3], m[1, :3], m[2, :3] = r, u, -f
    m[:3, 3] = -m[:3, :3] @ eye
    return m


def perspective(fov_y_deg, aspect, near=0.4, far=900.0):
    t = 1.0 / math.tan(math.radians(fov_y_deg) * 0.5)
    m = np.zeros((4, 4))
    m[0, 0] = t / aspect
    m[1, 1] = t
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = 2 * far * near / (near - far)
    m[3, 2] = -1.0
    return m


# ------------------------------------------------------------- primitives ---
# unit cube centred on the origin, 6 quads, outward winding
_CUBE_V = np.array([
    [-.5, -.5, -.5], [.5, -.5, -.5], [.5, .5, -.5], [-.5, .5, -.5],
    [-.5, -.5,  .5], [.5, -.5,  .5], [.5, .5,  .5], [-.5, .5,  .5],
])
_CUBE_Q = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
           (3, 7, 6, 2), (0, 4, 7, 3), (1, 2, 6, 5)]


class Scene:
    """Collects world-space triangles with a flat colour each."""

    def __init__(self):
        self.v = []          # (3,) world verts, flattened per triangle
        self.c = []          # rgb per triangle
        self.emissive = []   # bool per triangle

    def box(self, m, colour, emissive=False, taper=None):
        v = _CUBE_V.copy()
        if taper is not None:           # shrink the +Y face for wedge shapes
            tx, tz = taper
            top = v[:, 1] > 0
            v[top, 0] *= tx
            v[top, 2] *= tz
        vh = np.concatenate([v, np.ones((8, 1))], 1) @ m.T
        vw = vh[:, :3]
        for q in _CUBE_Q:
            a, b, c, d = (vw[i] for i in q)
            self.v.append((a, b, c)); self.c.append(colour); self.emissive.append(emissive)
            self.v.append((a, c, d)); self.c.append(colour); self.emissive.append(emissive)

    def segment(self, p0, p1, w, d, colour, roll=0.0):
        """A box whose local +Y axis runs from p0 to p1 - one armour section."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        axis = p1 - p0
        L = np.linalg.norm(axis)
        if L < 1e-6:
            return
        yv = axis / L
        ref = np.array([0.0, 0.0, 1.0]) if abs(yv[2]) < 0.9 else np.array([1.0, 0.0, 0.0])
        xv = normalise(np.cross(ref, yv))
        zv = np.cross(xv, yv)
        m = np.eye(4)
        m[:3, 0], m[:3, 1], m[:3, 2] = xv, yv, zv
        m[:3, 3] = (p0 + p1) * 0.5
        self.box(m @ rot_y(roll) @ scale(w, L, d), colour)

    def arrays(self):
        return (np.asarray(self.v, float),
                np.asarray(self.c, float),
                np.asarray(self.emissive, bool))


# ----------------------------------------------------------- rasterisation --
def render(scene, view, proj, cam_pos, light, fill, ambient, fog, sky_fn,
           width, height):
    tri, col, emis = scene.arrays()
    n = len(tri)

    # ---- shading (flat, per triangle, in world space) ----------------------
    e0 = tri[:, 1] - tri[:, 0]
    e1 = tri[:, 2] - tri[:, 0]
    nrm = np.cross(e0, e1)
    ln = np.linalg.norm(nrm, axis=1, keepdims=True)
    ln[ln == 0] = 1
    nrm /= ln
    centre = tri.mean(axis=1)
    vdir = cam_pos[None, :] - centre
    vdir /= np.linalg.norm(vdir, axis=1, keepdims=True)

    # face away from the camera -> drop it
    facing = (nrm * vdir).sum(1)
    keep = facing > 0.0
    flip = ~keep
    nrm[flip] *= -1.0                       # meshes are closed; be forgiving
    keep = np.ones(n, bool)

    kd = np.clip((nrm * light["dir"][None, :]).sum(1), 0, 1)[:, None]
    fd = np.clip((nrm * fill["dir"][None, :]).sum(1), 0, 1)[:, None]
    rim = np.clip(1.0 - np.abs((nrm * vdir).sum(1)), 0, 1)[:, None] ** 3.0

    shade = (col * (ambient[None, :] + kd * light["col"][None, :]
                    + fd * fill["col"][None, :])
             + rim * np.array(light["rim"])[None, :])
    shade = np.where(emis[:, None], col, shade)

    # ---- project -----------------------------------------------------------
    flat = tri.reshape(-1, 3)
    hom = np.concatenate([flat, np.ones((len(flat), 1))], 1)
    clip = hom @ (proj @ view).T
    w = clip[:, 3]
    ok = w > 1e-3
    inv_w = np.where(ok, 1.0 / np.where(ok, w, 1.0), 0.0)
    ndc = clip[:, :3] * inv_w[:, None]
    sx = (ndc[:, 0] * 0.5 + 0.5) * width
    sy = (1.0 - (ndc[:, 1] * 0.5 + 0.5)) * height
    sx, sy = sx.reshape(-1, 3), sy.reshape(-1, 3)
    iw = inv_w.reshape(-1, 3)
    valid = ok.reshape(-1, 3).all(1) & keep

    # distance fog, evaluated at the face centre
    dist = np.linalg.norm(centre - cam_pos[None, :], axis=1)
    fg = np.clip((dist - fog["start"]) / (fog["end"] - fog["start"]), 0, 1)[:, None]
    fg = np.where(emis[:, None], fg * 0.25, fg)
    shade = shade * (1 - fg) + np.array(fog["col"])[None, :] * fg

    # ---- z-buffer fill -----------------------------------------------------
    colour_buf, depth_buf = sky_fn()
    order = np.argsort(-dist)                # far to near helps nothing but is tidy
    for i in order:
        if not valid[i]:
            continue
        x, y, z = sx[i], sy[i], iw[i]
        x0 = max(int(math.floor(x.min())), 0)
        x1 = min(int(math.ceil(x.max())) + 1, width)
        y0 = max(int(math.floor(y.min())), 0)
        y1 = min(int(math.ceil(y.max())) + 1, height)
        if x0 >= x1 or y0 >= y1:
            continue

        px = np.arange(x0, x1) + 0.5
        py = np.arange(y0, y1) + 0.5
        gx, gy = np.meshgrid(px, py)

        d0 = (x[1] - x[0]) * (gy - y[0]) - (y[1] - y[0]) * (gx - x[0])
        d1 = (x[2] - x[1]) * (gy - y[1]) - (y[2] - y[1]) * (gx - x[1])
        d2 = (x[0] - x[2]) * (gy - y[2]) - (y[0] - y[2]) * (gx - x[2])
        area = (x[1] - x[0]) * (y[2] - y[0]) - (y[1] - y[0]) * (x[2] - x[0])
        if abs(area) < 1e-9:
            continue
        if area > 0:
            inside = (d0 >= 0) & (d1 >= 0) & (d2 >= 0)
        else:
            inside = (d0 <= 0) & (d1 <= 0) & (d2 <= 0)
        if not inside.any():
            continue

        l0 = d1 / area
        l1 = d2 / area
        l2 = 1.0 - l0 - l1
        depth = l0 * z[0] + l1 * z[1] + l2 * z[2]      # 1/w, larger is nearer

        sub_z = depth_buf[y0:y1, x0:x1]
        m = inside & (depth > sub_z)
        if not m.any():
            continue
        sub_z[m] = depth[m]
        colour_buf[y0:y1, x0:x1][m] = shade[i]

    return colour_buf, depth_buf


# ------------------------------------------------- sky and analytic ground --
def make_background(cam_pos, view, proj, width, height, ground_shift, fog):
    """Per-pixel sky and ground plane, with a matching 1/w depth buffer."""
    inv = np.linalg.inv(proj @ view)
    ys, xs = np.mgrid[0:height, 0:width]
    ndc_x = ((xs + 0.5) / width) * 2 - 1
    ndc_y = 1 - ((ys + 0.5) / height) * 2
    pts = np.stack([ndc_x, ndc_y, np.full_like(ndc_x, 0.5), np.ones_like(ndc_x)], -1)
    wpt = pts @ inv.T
    wpt = wpt[..., :3] / wpt[..., 3:4]
    ray = wpt - cam_pos[None, None, :]
    ray /= np.linalg.norm(ray, axis=-1, keepdims=True)

    # --- sky -----------------------------------------------------------------
    t = np.clip(ray[..., 1] * 3.2, 0, 1)[..., None]
    sky = np.array([0.026, 0.036, 0.062]) * t + np.array([0.070, 0.086, 0.126]) * (1 - t)
    horizon = np.clip(1.0 - np.abs(ray[..., 1]) * 11.0, 0, 1)[..., None] ** 2
    sky = sky + horizon * np.array([0.46, 0.24, 0.09])
    colour = sky
    depth = np.zeros((height, width))       # 1/w == 0 is infinitely far

    # --- ground plane at y = 0 ----------------------------------------------
    denom = ray[..., 1]
    hit = denom < -1e-6
    tt = np.where(hit, -cam_pos[1] / np.where(hit, denom, -1.0), 0.0)
    P = cam_pos[None, None, :] + ray * tt[..., None]

    gx = P[..., 0] + ground_shift
    gz = P[..., 2]

    base = np.array([0.034, 0.042, 0.056])
    g = np.broadcast_to(base, colour.shape).copy()

    # plating seams
    seam = (np.minimum(np.abs(((gx / 9.0) % 1.0) - 0.5),
                       np.abs(((gz / 9.0) % 1.0) - 0.5)) < 0.018)
    g[seam] = np.array([0.062, 0.076, 0.098])

    # hazard chevrons along the walkway
    band = (np.abs(gz - 11.0) < 1.6)
    chev = band & ((((gx * 0.5 + gz * 0.5) / 2.25) % 1.0) < 0.5)   # period 4.5 in x; 9.0 = 2 periods
    g[chev] = np.array([0.30, 0.20, 0.07])
    g[band & ~chev] = np.array([0.075, 0.085, 0.100])

    forward = normalise(np.array([0.0, 0.0, -1.0]) @ view[:3, :3])
    dist = np.linalg.norm(P - cam_pos[None, None, :], axis=-1)
    fg = np.clip((dist - fog["start"]) / (fog["end"] - fog["start"]), 0, 1)[..., None]
    g = g * (1 - fg) + np.array(fog["col"])[None, None, :] * fg

    colour = np.where(hit[..., None], g, colour)
    # 1/w for the plane: w == distance along the camera forward axis
    fwd = -view[2, :3]
    along = ((P - cam_pos[None, None, :]) * fwd[None, None, :]).sum(-1)
    depth = np.where(hit & (along > 1e-3), 1.0 / np.where(along > 1e-3, along, 1.0), 0.0)
    return colour, depth


# ------------------------------------------------------------------ gait ----
def foot_track(phase, stride, lift, duty=0.62):
    phase %= 1.0
    if phase < duty:
        t = phase / duty
        return stride * 0.5 - stride * t, 0.0
    t = (phase - duty) / (1.0 - duty)
    return -stride * 0.5 + stride * t, lift * math.sin(math.pi * t)


def knee_point(hip, foot, l1, l2, bend):
    """2D sagittal solve. hip/foot are (forward, up)."""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = math.hypot(dx, dy)
    d = max(min(d, l1 + l2 - 1e-4), abs(l1 - l2) + 1e-4)
    a = math.acos(max(-1, min(1, (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d))))
    ang = math.atan2(dy, dx) + bend * a
    return hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang)
