#!/usr/bin/env python3
"""Seamless-looping 19:6 banner: three BattleTech-style mechs walking.

The gait is computed, not hand-drawn. Each foot follows a stance/swing
trajectory; the knee comes from a two-bone IK solve, so the leg bends the way
the chassis says it should - reverse-jointed for the Timber Wolf, knee-forward
for the BattleMaster and the Atlas.

Each mech is rendered into its own RGBA layer. The layer's alpha is the
silhouette, so the rim light is taken from the real outline: a warm edge on the
side facing the city glow, a cold edge on top from the sky.

Everything periodic is a function of `phase` in [0,1), and every scrolling
layer advances a whole number of its own pattern periods across the loop, so
the last frame hands over to the first with no jump.
"""

import math
import random
from PIL import Image, ImageDraw, ImageChops, ImageFilter

# ---------------------------------------------------------------- canvas ----
W, H = 1140, 360                   # 19:6
SS = 2                             # supersample factor
FRAMES = 30
GROUND_Y = 302

CW, CH = W * SS, H * SS
GY = GROUND_Y * SS

# --------------------------------------------------------------- palette ----
SKY_TOP   = (7, 10, 16)
SKY_BOT   = (27, 36, 50)
HORIZON   = (72, 47, 28)
MOUNTAIN  = (15, 20, 29)
CITY      = (10, 14, 21)
GROUND    = (11, 15, 21)
GROUND_LN = (34, 43, 55)
HAZARD    = (58, 41, 19)

BODY      = (19, 24, 32)           # silhouette fill
BODY_FAR  = (46, 57, 73)           # limbs on the far side
DETAIL    = (10, 13, 18)           # panel lines cut into the silhouette
RIM_WARM  = (255, 166, 88)
RIM_COOL  = (104, 148, 198)
GLOW      = (255, 198, 104)

HAZE = {"back": 0.46, "mid": 0.24, "front": 0.07}


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return tuple(int(round(lerp(c1[i], c2[i], t))) for i in range(3))


# ------------------------------------------------------------ kinematics ----
def foot_track(phase, stride, lift, duty=0.62):
    """Foot offset (x, y) from the hip's ground point; y negative is up."""
    phase %= 1.0
    if phase < duty:                        # stance: planted, sliding back
        t = phase / duty
        return (stride * 0.5 - stride * t, 0.0)
    t = (phase - duty) / (1.0 - duty)       # swing: arc forward
    return (-stride * 0.5 + stride * t, -lift * math.sin(math.pi * t))


def two_bone(hip, foot, l1, l2, bend):
    """Knee position for a two-segment limb. `bend` selects the elbow side."""
    dx, dy = foot[0] - hip[0], foot[1] - hip[1]
    d = math.hypot(dx, dy)
    d = max(min(d, l1 + l2 - 0.001), abs(l1 - l2) + 0.001)
    cos_a = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    ang = math.atan2(dy, dx) + bend * a
    return (hip[0] + l1 * math.cos(ang), hip[1] + l1 * math.sin(ang))


# --------------------------------------------------------------- helpers ----
def limb(d, p0, p1, width, colour):
    d.line([p0, p1], fill=colour, width=max(1, int(width)), joint="curve")
    r = width * 0.5
    for p in (p0, p1):
        d.ellipse([p[0] - r, p[1] - r, p[0] + r, p[1] + r], fill=colour)


def poly(d, pts, colour):
    d.polygon(pts, fill=colour)


def tapered(d, p0, p1, w0, w1, colour):
    """Armour segment: a quad that narrows from p0 to p1, with a capped joint."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    d.polygon([(p0[0] + nx * w0 / 2, p0[1] + ny * w0 / 2),
               (p1[0] + nx * w1 / 2, p1[1] + ny * w1 / 2),
               (p1[0] - nx * w1 / 2, p1[1] - ny * w1 / 2),
               (p0[0] - nx * w0 / 2, p0[1] - ny * w0 / 2)], fill=colour)
    d.ellipse([p0[0] - w0 / 2, p0[1] - w0 / 2, p0[0] + w0 / 2, p0[1] + w0 / 2], fill=colour)


# ----------------------------------------------------------------- mechs ----
class Mech:
    def __init__(self, kind, x, scale, depth, phase_off, facing=1):
        self.kind, self.x, self.sc = kind, x, scale
        self.depth, self.phase_off, self.f = depth, phase_off, facing

        if kind == "timberwolf":                # Mad Cat: reverse-jointed
            self.hip_h, self.thigh, self.shin = 92, 50, 56
            self.stride, self.lift, self.bend = 78, 26, -1
            self.leg_w, self.foot_w, self.lean = 26, 48, 0.16
        elif kind == "battlemaster":            # upright humanoid
            self.hip_h, self.thigh, self.shin = 100, 54, 54
            self.stride, self.lift, self.bend = 70, 22, 1
            self.leg_w, self.foot_w, self.lean = 27, 44, 0.05
        else:                                   # atlas: hulking humanoid
            self.hip_h, self.thigh, self.shin = 86, 46, 48
            self.stride, self.lift, self.bend = 62, 18, 1
            self.leg_w, self.foot_w, self.lean = 34, 56, 0.10

    # ---------------------------------------------------------------- pose --
    def pose(self, phase):
        p = (phase + self.phase_off) % 1.0
        bob = -3.6 * math.cos(4 * math.pi * p)
        sway = 2.0 * math.sin(2 * math.pi * p)
        return p, bob, sway

    def render(self, phase):
        """Return (layer, glow_spots). Layer alpha is the silhouette."""
        layer = Image.new("RGBA", (CW, CH), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        s = self.sc * SS
        p, bob, sway = self.pose(phase)

        hip_y = GY - self.hip_h * s + bob * s
        hx = self.x * SS + sway * s

        feet = []
        for off in (0.5, 0.0):                  # far leg first
            fx, fy = foot_track(p + off, self.stride, self.lift)
            hip = (hx, hip_y)
            foot = (hx + fx * s * self.f, GY + fy * s)
            knee = two_bone(hip, foot, self.thigh * s, self.shin * s,
                            self.bend * self.f)
            feet.append((hip, knee, foot))

        self._leg(d, feet[0], s, BODY_FAR)
        self._arm(d, hx, hip_y, p, s, BODY_FAR, back=True)
        glow = getattr(self, "_torso_" + self.kind)(d, hx, hip_y, s)
        self._leg(d, feet[1], s, BODY, gap=2 * SS)
        self._arm(d, hx, hip_y, p, s, BODY, back=False)
        return layer, glow

    # --------------------------------------------------------------- parts --
    def _leg(self, d, leg, s, colour, gap=0):
        """gap > 0 cuts a dark outline first, so the near leg reads clear of the far one."""
        hip, knee, foot = leg
        lw = self.leg_w * s
        f = self.f
        for pad, col in (((gap, DETAIL) if gap else (None, None)), (0, colour)):
            if pad is None:
                continue
            g = pad * 2
            tapered(d, hip, knee, lw * 1.28 + g, lw * 0.82 + g, col)
            tapered(d, knee, foot, lw * 0.86 + g, lw * 0.58 + g, col)
            k = lw * 0.46 + pad
            d.polygon([(knee[0] - k, knee[1] - k * 0.55), (knee[0] - k * 0.3, knee[1] - k),
                       (knee[0] + k, knee[1] - k * 0.45), (knee[0] + k, knee[1] + k * 0.5),
                       (knee[0] + k * 0.3, knee[1] + k), (knee[0] - k, knee[1] + k * 0.5)],
                      fill=col)
            fw, fh = self.foot_w * s + g, 13 * s + g
            poly(d, [(foot[0] - fw * 0.40 * f, foot[1] - fh * 0.42),
                     (foot[0] + fw * 0.40 * f, foot[1] - fh * 0.46),
                     (foot[0] + fw * 0.64 * f, foot[1] - fh * 0.06),
                     (foot[0] + fw * 0.58 * f, foot[1] + fh * 0.44),
                     (foot[0] - fw * 0.48 * f, foot[1] + fh * 0.44)], col)

    def _arm(self, d, hx, hip_y, p, s, colour, back):
        f = self.f
        swing = math.sin(2 * math.pi * (p + (0.5 if back else 0.0)))
        out = (-1 if back else 1)

        if self.kind == "timberwolf":
            sy = hip_y - 46 * s
            ax = hx + (10 + out * 5) * s * f + swing * 5 * s * f
            poly(d, [(ax - 14 * s * f, sy + 2 * s), (ax + 40 * s * f, sy + 10 * s),
                     (ax + 40 * s * f, sy + 30 * s), (ax - 14 * s * f, sy + 30 * s)],
                 colour)
            poly(d, [(ax + 38 * s * f, sy + 14 * s), (ax + 52 * s * f, sy + 16 * s),
                     (ax + 52 * s * f, sy + 25 * s), (ax + 38 * s * f, sy + 27 * s)],
                 colour)
        elif self.kind == "battlemaster":
            sx, sy = hx + out * 26 * s * f, hip_y - 62 * s
            ex = sx + (swing * 9 + out * 4) * s * f
            ey = sy + 44 * s
            limb(d, (sx, sy), (ex, ey), 17 * s, colour)
            if not back:                        # PPC barrel
                poly(d, [(ex - 9 * s * f, ey - 7 * s), (ex + 46 * s * f, ey - 12 * s),
                         (ex + 46 * s * f, ey + 3 * s), (ex - 9 * s * f, ey + 9 * s)],
                     colour)
                poly(d, [(ex + 40 * s * f, ey - 15 * s), (ex + 50 * s * f, ey - 15 * s),
                         (ex + 50 * s * f, ey + 6 * s), (ex + 40 * s * f, ey + 6 * s)],
                     colour)
            else:
                limb(d, (ex, ey), (ex + 10 * s * f, ey + 18 * s), 13 * s, colour)
        else:                                   # atlas
            sx, sy = hx + out * 34 * s * f, hip_y - 54 * s
            ex = sx + (swing * 7 + out * 3) * s * f
            ey = sy + 40 * s
            limb(d, (sx, sy), (ex, ey), 23 * s, colour)
            if not back:                        # AC/20
                poly(d, [(ex - 14 * s * f, ey - 12 * s), (ex + 44 * s * f, ey - 16 * s),
                         (ex + 44 * s * f, ey + 9 * s), (ex - 14 * s * f, ey + 13 * s)],
                     colour)
                poly(d, [(ex + 40 * s * f, ey - 19 * s), (ex + 49 * s * f, ey - 19 * s),
                         (ex + 49 * s * f, ey + 12 * s), (ex + 40 * s * f, ey + 12 * s)],
                     colour)
            else:
                limb(d, (ex, ey), (ex + 6 * s * f, ey + 20 * s), 19 * s, colour)

    # -------------------------------------------------------------- torsos --
    def _torso_timberwolf(self, d, cx, hip_y, s):
        f = self.f
        top = hip_y - 58 * s
        # forward-slung wedge, nose down - the Mad Cat crouch
        poly(d, [(cx - 34 * s * f, top + 10 * s), (cx + 30 * s * f, top + 0 * s),
                 (cx + 46 * s * f, top + 24 * s), (cx + 30 * s * f, hip_y + 6 * s),
                 (cx - 30 * s * f, hip_y + 8 * s), (cx - 42 * s * f, top + 30 * s)],
             BODY)
        # shoulder LRM racks, the chassis signature
        for dx, dy, w, h in ((-62, -22, 42, 26), (18, -30, 46, 28)):
            x0 = cx + dx * s * f
            poly(d, [(x0, top + dy * s), (x0 + w * s * f, top + (dy - 6) * s),
                     (x0 + w * s * f, top + (dy + h) * s), (x0, top + (dy + h + 6) * s)],
                 BODY)
            for k in range(4):                  # launch tubes
                yy = top + (dy + 3 + k * 6) * s
                d.line([(x0 + 5 * s * f, yy), (x0 + (w - 5) * s * f, yy - 4 * s)],
                       fill=DETAIL, width=max(1, int(2.2 * s)))
        # low forward cockpit
        hx, hy = cx + 30 * s * f, top + 18 * s
        poly(d, [(hx - 18 * s * f, hy - 11 * s), (hx + 16 * s * f, hy - 5 * s),
                 (hx + 16 * s * f, hy + 10 * s), (hx - 18 * s * f, hy + 13 * s)], BODY)
        return [((hx + 1 * s * f, hy + 2 * s), 4.6 * s, "slit", f)]

    def _torso_battlemaster(self, d, cx, hip_y, s):
        f = self.f
        top = hip_y - 72 * s
        poly(d, [(cx - 33 * s * f, top + 6 * s), (cx + 33 * s * f, top + 6 * s),
                 (cx + 28 * s * f, hip_y + 8 * s), (cx - 28 * s * f, hip_y + 8 * s)], BODY)
        for k in range(4):                      # heat-sink louvres
            yy = top + (26 + k * 10) * s
            d.line([(cx - 19 * s, yy), (cx + 19 * s, yy)], fill=DETAIL,
                   width=max(1, int(3.0 * s)))
        for dx in (-50, 26):                    # pauldrons
            x0 = cx + dx * s * f
            poly(d, [(x0, top + 2 * s), (x0 + 26 * s * f, top - 6 * s),
                     (x0 + 24 * s * f, top + 32 * s), (x0 + 2 * s * f, top + 36 * s)], BODY)
        hx, hy = cx + 3 * s * f, top - 10 * s
        poly(d, [(hx - 15 * s * f, hy - 15 * s), (hx + 15 * s * f, hy - 15 * s),
                 (hx + 17 * s * f, hy + 8 * s), (hx - 17 * s * f, hy + 8 * s)], BODY)
        return [((hx, hy - 3 * s), 9 * s, "visor", f)]

    def _torso_atlas(self, d, cx, hip_y, s):
        f = self.f
        top = hip_y - 66 * s
        poly(d, [(cx - 40 * s * f, top + 12 * s), (cx + 40 * s * f, top + 8 * s),
                 (cx + 34 * s * f, hip_y + 10 * s), (cx - 34 * s * f, hip_y + 10 * s)], BODY)
        for dx, w in ((-70, 34), (36, 36)):     # the slab pauldrons
            x0 = cx + dx * s * f
            poly(d, [(x0, top + 14 * s), (x0 + 8 * s * f, top - 12 * s),
                     (x0 + w * s * f, top - 14 * s), (x0 + (w + 4) * s * f, top + 34 * s),
                     (x0 + 4 * s * f, top + 40 * s)], BODY)
        x0 = cx - 68 * s * f                    # LRM box
        poly(d, [(x0, top - 14 * s), (x0 + 30 * s * f, top - 20 * s),
                 (x0 + 30 * s * f, top - 2 * s), (x0, top + 4 * s)], BODY)
        # death's-head cockpit
        hx, hy = cx + 2 * s * f, top - 8 * s
        poly(d, [(hx - 19 * s * f, hy - 20 * s), (hx + 19 * s * f, hy - 20 * s),
                 (hx + 22 * s * f, hy + 2 * s), (hx + 11 * s * f, hy + 17 * s),
                 (hx - 11 * s * f, hy + 17 * s), (hx - 22 * s * f, hy + 2 * s)], BODY)
        for k in range(5):                      # teeth
            tx = hx + (-11 + k * 5.5) * s * f
            d.line([(tx, hy + 5 * s), (tx, hy + 16 * s)], fill=DETAIL,
                   width=max(1, int(2.0 * s)))
        return [((hx - 10 * s * f, hy - 9 * s), 7 * s, "socket", f),
                ((hx + 10 * s * f, hy - 9 * s), 7 * s, "socket", f)]


# ------------------------------------------------------------ background ----
def build_background():
    img = Image.new("RGB", (CW, CH), SKY_TOP)
    d = ImageDraw.Draw(img)

    for y in range(GY):
        t = y / GY
        c = mix(SKY_TOP, SKY_BOT, t ** 0.7)
        if t > 0.68:
            c = mix(c, HORIZON, ((t - 0.68) / 0.32) ** 1.4 * 0.75)
        d.line([(0, y), (CW, y)], fill=c)

    rng = random.Random(11)
    for base, amp, col, step in ((0.60, 0.11, mix(MOUNTAIN, SKY_BOT, 0.58), 78 * SS),
                                 (0.69, 0.07, mix(MOUNTAIN, SKY_BOT, 0.26), 54 * SS)):
        pts, x, y = [(0, CH)], 0, GY * base
        while x <= CW + step:
            pts.append((x, y))
            x += step
            y = GY * base + rng.uniform(-amp, amp) * GY
        pts.append((CW, CH))
        d.polygon(pts, fill=col)

    rng2 = random.Random(23)                    # skyline
    x = -20 * SS
    while x < CW + 40 * SS:
        bw, bh = rng2.randint(16, 50) * SS, rng2.randint(20, 82) * SS
        d.rectangle([x, GY - bh, x + bw, GY], fill=CITY)
        for wy in range(int(GY - bh) + 7 * SS, int(GY) - 5 * SS, 10 * SS):
            for wx in range(int(x) + 5 * SS, int(x + bw) - 5 * SS, 9 * SS):
                if rng2.random() < 0.15:
                    d.rectangle([wx, wy, wx + 2 * SS, wy + 3 * SS], fill=(96, 74, 40))
        x += bw + rng2.randint(5, 20) * SS

    d.rectangle([0, GY, CW, CH], fill=GROUND)
    for y in range(GY, CH):
        t = (y - GY) / max(1, CH - GY)
        d.line([(0, y), (CW, y)], fill=mix(GROUND, (4, 6, 9), t * 0.85))
    d.line([(0, GY), (CW, GY)], fill=GROUND_LN, width=2 * SS)
    return img


def draw_scroll(img, phase):
    d = ImageDraw.Draw(img)
    P, S = 190 * SS, 190 * SS                   # mid: pylons, 1 period per loop
    shift = -phase * S
    n = -2
    while n * P + shift < CW + P:
        x = n * P + shift
        col = mix(CITY, SKY_BOT, 0.38)
        d.rectangle([x, GY - 52 * SS, x + 6 * SS, GY], fill=col)
        d.rectangle([x - 11 * SS, GY - 55 * SS, x + 17 * SS, GY - 50 * SS], fill=col)
        n += 1

    P2, S2 = 57 * SS, 171 * SS                  # near: hazard dashes, 3 per loop
    shift2 = -phase * S2
    n = -3
    while n * P2 + shift2 < CW + P2:
        x = n * P2 + shift2
        d.polygon([(x, GY + 28 * SS), (x + 30 * SS, GY + 28 * SS),
                   (x + 23 * SS, GY + 35 * SS), (x - 7 * SS, GY + 35 * SS)], fill=HAZARD)
        d.rectangle([x + 44 * SS, GY + 13 * SS, x + 51 * SS, GY + 15 * SS],
                    fill=mix(GROUND, GROUND_LN, 0.7))
        n += 1


# ---------------------------------------------------------------- compose ---
def rim_masks(alpha):
    """Right-facing (warm) and top-facing (cold) edge bands of a silhouette."""
    w = 2 * SS
    warm = ImageChops.subtract(alpha, ImageChops.offset(alpha, -w, 0))
    cool = ImageChops.subtract(alpha, ImageChops.offset(alpha, 0, w))
    return warm, cool


def paint_mech(canvas, layer, glow, depth):
    alpha = layer.split()[3]
    rgb = layer.convert("RGB")

    grad = Image.new("RGB", rgb.size)
    gd = ImageDraw.Draw(grad)
    for y in range(rgb.size[1]):
        t = y / rgb.size[1]
        gd.line([(0, y), (rgb.size[0], y)], fill=mix((58, 71, 89), (6, 8, 12), t ** 0.6))
    rgb = Image.blend(rgb, ImageChops.multiply(rgb, grad), 0.0)
    rgb = ImageChops.add(rgb, Image.eval(grad, lambda v: int(v * 0.42)))

    haze = HAZE[depth]
    if haze:
        rgb = Image.blend(rgb, Image.new("RGB", rgb.size, SKY_BOT), haze)

    warm, cool = rim_masks(alpha)
    cool = cool.point(lambda v: int(v * 0.55))
    warm = warm.point(lambda v: int(v * 0.88))
    rgb.paste(Image.new("RGB", rgb.size, mix(RIM_COOL, SKY_BOT, haze * 0.8)), (0, 0), cool)
    rgb.paste(Image.new("RGB", rgb.size, mix(RIM_WARM, SKY_BOT, haze * 0.8)), (0, 0), warm)

    canvas.paste(rgb, (0, 0), alpha)

    for (x, y), r, kind, f in glow:             # cockpits, drawn over the rim
        d = ImageDraw.Draw(canvas)
        c = mix(GLOW, SKY_BOT, haze * 0.55)
        if kind == "slit":
            d.polygon([(x - r * 1.9 * f, y - r * 0.5), (x + r * 1.5 * f, y - r * 0.2),
                       (x + r * 1.5 * f, y + r * 0.7), (x - r * 1.9 * f, y + r * 0.9)], fill=c)
        elif kind == "visor":
            d.rectangle([x - r * 1.3, y - r * 0.42, x + r * 1.3, y + r * 0.42], fill=c)
        else:
            d.polygon([(x - r * 0.75, y - r * 0.7), (x + r * 0.75, y - r * 0.7),
                       (x + r * 0.55, y + r * 0.55), (x - r * 0.55, y + r * 0.55)], fill=c)


def soft_shadows(canvas, mechs, phase):
    layer = Image.new("RGB", canvas.size, (0, 0, 0))
    mask = Image.new("L", canvas.size, 0)
    md = ImageDraw.Draw(mask)
    for m in mechs:
        s = m.sc * SS
        r = 52 * s
        md.ellipse([m.x * SS - r, GY - 8 * SS, m.x * SS + r, GY + 12 * SS], fill=150)
    mask = mask.filter(ImageFilter.GaussianBlur(9 * SS))
    canvas.paste(layer, (0, 0), mask)


def dust(canvas, mechs, phase):
    d = ImageDraw.Draw(canvas)
    for m in mechs:
        p = (phase + m.phase_off) % 1.0
        s = m.sc * SS
        for off in (0.0, 0.5):
            age = (p + off) % 1.0               # zero at the moment of footfall
            if age > 0.34:
                continue
            t = age / 0.34
            fx, _ = foot_track(p + off, m.stride, m.lift)
            x = m.x * SS + fx * s * m.f
            r = (7 + 30 * t) * s
            a = (1 - t) ** 1.8
            col = mix(GROUND, (118, 128, 142), 0.55 * a)
            d.ellipse([x - r, GY - r * 0.48, x + r, GY + r * 0.28], fill=col)


# ------------------------------------------------------------------ main ----
def main(out_path):
    base = build_background()
    mechs = [
        Mech("battlemaster", 232, 0.84, "back",  0.33),
        Mech("timberwolf",   566, 1.00, "mid",   0.00),
        Mech("atlas",        900, 1.16, "front", 0.66),
    ]

    vig = Image.new("L", (CW, CH), 0)
    ImageDraw.Draw(vig).ellipse([-CW * 0.22, -CH * 0.95, CW * 1.22, CH * 1.95], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(42 * SS))

    scan = Image.new("RGB", (CW, CH), (0, 0, 0))
    sd = ImageDraw.Draw(scan)
    for y in range(0, CH, 3 * SS):
        sd.line([(0, y), (CW, y)], fill=(12, 14, 18))

    frames = []
    for i in range(FRAMES):
        phase = i / FRAMES
        img = base.copy()
        draw_scroll(img, phase)
        soft_shadows(img, mechs, phase)
        dust(img, mechs, phase)
        for m in mechs:                          # back to front
            layer, glow = m.render(phase)
            paint_mech(img, layer, glow, m.depth)
        img = Image.composite(img, Image.new("RGB", img.size, (2, 3, 5)), vig)
        img = Image.blend(img, scan, 0.09)
        frames.append(img.resize((W, H), Image.LANCZOS))

    pal = frames[0].quantize(colors=160, method=Image.MEDIANCUT)
    out = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
    out[0].save(out_path, save_all=True, append_images=out[1:],
                duration=50, loop=0, optimize=True, disposal=1)
    print("wrote", out_path)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "mech-walk.gif")
