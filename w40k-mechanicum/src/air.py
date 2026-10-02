"""The air of a scene, shared by every flame (src/rig.py) and every smoke
plume (src/smoke.py): a slow draft that differs from place to place and
repeats once per loop, and the response of a candle flame to it.

Draft. A sum of travelling waves. Each wave has a whole number of cycles
per loop, so the draft at loop time LOOP equals the draft at time 0. The
wavelengths are 1.5 to 5 m: flames a metre apart get different gusts.

Flame. A candle flame is a column of hot gas that rises at about
W_FLAME = 1 m/s (the buoyant speed sqrt(g L (T_flame / T_air - 1)) of a
3 cm flame at 1400 K in 300 K air). Air crossing it at speed v pushes it
over by the angle atan(v / W_FLAME): the flame follows the vector sum of
its own rise and the wind it feels, which is the draft less the candle's
own velocity. A flame blown sideways burns less wax vapour and gives less
light; an updraft stretches it and gives more. No shadowing is modelled.

Gusts. The draft is the slow air of the room (0.25 to 1.75 Hz); the smoke
follows it. A flame also answers the small, fast eddies of the air round
it: gust() adds waves of 1 to 6.75 Hz and 0.3 to 1.2 m, their amplitude
falling with frequency as f^(-5/6) (the velocity spectrum of turbulence,
E ~ f^(-5/3)). They make the flame dance; candles a hand apart get
different gusts.
"""
import math
import numpy as np

TAU = 2 * math.pi
LOOP = 4.0                 # seconds per loop
W_FLAME = 1.0              # m/s, rise speed of the flame gas
RMS = 0.10                 # m/s, strength of the draft
GUST = 0.35                # m/s, strength of the gusts a flame feels


def _waves(seed, parts, lengths, rms, rise):
    """Travelling waves: (cycles per loop, amplitude) pairs, two waves each,
    wavelengths (m) drawn from `lengths`, vertical share `rise`."""
    rng = np.random.default_rng(seed)
    rows = []
    for cycles, amp in parts:
        for _ in range(2):
            th, kd = rng.uniform(0, TAU, 2)
            k = TAU / rng.uniform(*lengths)
            rows.append((cycles, amp, math.cos(th), math.sin(th), rise * rng.uniform(-1, 1),
                         k * math.cos(kd), k * math.sin(kd), rng.uniform(0, TAU)))
    w = np.array(rows)
    w[:, 1] *= rms / math.sqrt(0.5 * (w[:, 1] ** 2).sum())
    return w


WAVES = _waves(11, ((1, 1.0), (2, 0.7), (3, 0.45), (5, 0.3), (7, 0.2)), (1.5, 5.0), RMS, 0.25)
GUSTS = _waves(23, [(c, c ** (-5 / 6)) for c in (4, 6, 9, 13, 17, 22, 27)], (0.3, 1.2), GUST, 0.7)


def _air(w, p, t):
    p = np.asarray(p, float)
    c, a, dx, dy, dz, kx, ky, ph = w.T
    s = np.sin(TAU * c * t / LOOP - (p[..., 0:1] * kx + p[..., 1:2] * ky) + ph) * a
    return np.stack([(s * dx).sum(-1), (s * dy).sum(-1), (s * dz).sum(-1)], -1)


def draft(p, t):
    """Air velocity (m/s; x right, y away from the camera, z up) at world
    point p = (x, y, z) and time t in seconds. p may be an (n, 3) array."""
    return _air(WAVES, p, t)


def gust(p, t):
    """The fast eddies a flame feels on top of the draft, same units."""
    return _air(GUSTS, p, t)


def flame(wind):
    """Response of a flame to the wind it feels (m/s, world axes): the unit
    direction of the flame, its length and its light, both relative to
    still air."""
    wind = np.asarray(wind, float)
    axis = np.array([wind[0], wind[1], W_FLAME + wind[2]])
    n = float(np.linalg.norm(axis))
    cross = math.hypot(wind[0], wind[1]) / W_FLAME
    up = wind[2] / W_FLAME
    length = float(np.clip(1 + 0.9 * up - 0.5 * cross, 0.55, 1.4))
    light = float(np.clip(1 + 0.5 * up - 0.8 * cross, 0.7, 1.2))
    return axis / n, length, light
