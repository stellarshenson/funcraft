"""A straight round rod of a picture as an object: a post, a pole, a mast. DESIGN.md section 5.14.

A rod is not cut from the picture as a patch of pixels. It is measured in the picture and built: a surface of
revolution about a straight axis, with the radius and the colour that the picture shows at each place along it.

    measure(picture, a, b, top, foot)    the rod between the plate places a and b: axis, radius and colour along it
    shaped(a, b, radius, colour)         a rod that the picture does not show clearly: its shape and colour are given
    outline(shape, rod, grow)            the pixels of the picture that show it
    lathe(rod, space, depth)             its surface as four-cornered faces with a colour per corner, for a mesh

Places are in plate pixels, (x, y), y down; the axis runs from a to b, and "across" is at a right angle to it,
positive to the right of a rod that runs down. `lathe` needs numpy only: Blender's Python has no OpenCV.
"""
import numpy as np

WIDE, FINE = 12, 4                             # a rod is looked for this many pixels to each side of its axis, at this many places per pixel
SEARCH = 2.5                                   # the middle of a rod lies within this many pixels of the axis given
CONTRAST = 0.07                                # a side of a rod is free where the picture differs from the rod by more than this, far from it
THIN = 1.6                                     # under this radius in pixels the picture does not show the colour of a rod along it
ROUND = 0.3                                    # the edge of a rod, which is turned away from the camera, is darker than its middle by this share


def straight(picture, a, b, wide=WIDE, fine=FINE):
    """The picture along the axis from a to b: (stations, places across, 3), a station per pixel along the axis, and
    the places across in pixels."""
    import cv2
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    n = max(int(round(np.linalg.norm(b - a))) + 1, 2)
    along = (b - a) / np.linalg.norm(b - a)
    side = np.array([along[1], -along[0]])
    u = np.arange(-wide * fine, wide * fine + 1) / fine
    at = a[None, None] + np.arange(n)[:, None, None] * along[None, None] + u[None, :, None] * side[None, None]
    return cv2.remap(picture, at[..., 0].astype(np.float32), at[..., 1].astype(np.float32), cv2.INTER_LINEAR), u


def edges(strip, u, limit, found=False):
    """For each station of a straightened rod: the place of its middle, and its edge to each side where that side is
    free, else nan. The middle is the darkest place near the axis, or the axis itself once that is `found`. An edge
    is where the picture is half-way from the colour of the middle to the colour further out than `limit` on that
    side."""
    import cv2
    strip = cv2.blur(strip, (3, 3))                                       # over 3 stations and under a pixel across
    near = np.abs(u) <= SEARCH
    mid = np.flatnonzero(near)[0] + np.argmin((strip @ np.array([0.2126, 0.7152, 0.0722], np.float32))[:, near], 1)
    if found:
        mid[:] = len(u) // 2
    core = strip[np.arange(len(strip)), mid]
    away = np.linalg.norm(strip - core[:, None], axis=2)                  # how much each place differs from the middle
    out = np.full((len(strip), 2), np.nan)
    for k in range(len(strip)):
        for s, sign in enumerate((-1, 1)):
            far = (sign * (u - u[mid[k]]) > limit)
            if far.sum() < FINE:
                continue
            ground = float(np.median(away[k, far]))
            if ground < CONTRAST:
                continue
            walk = np.arange(mid[k], len(u) if sign > 0 else -1, sign)
            over = np.flatnonzero(away[k, walk] > 0.5 * ground)
            if len(over) and abs(u[walk[over[0]]] - u[mid[k]]) <= limit:
                j = walk[over[0]]
                lo, hi = away[k, j - sign], away[k, j]                    # between the last place inside and the first outside
                out[k, s] = u[j] - sign * (hi - 0.5 * ground) / max(hi - lo, 1e-6) / FINE
    return u[mid], out


def measure(picture, a, b, top=None, foot=None, thick=None, plain=(), joints=()):
    """The rod that the picture shows between a and b, two places on its axis given to SEARCH pixels.

    picture: (rows, columns, 3), 0 to 1. top, foot: the rows at which the rod begins and ends where the picture does
    not show that (behind a cloth, behind a railing); it goes straight on to them. thick: its radius where no
    station shows it free on both sides. plain: stretches of rows (first, last) in which the rod has no joint: what
    the picture shows wider there is a thing that stands beside it or crosses it. joints: balls on the rod that the
    measure does not find, each as the row of its middle and its radius.

    Returns a dict: `a`, `b`, the ends of the axis; `at`, the place of every station on the axis, a pixel apart;
    `r`, the radius there; `colour`, the colour of its middle there; `seen`, where the picture shows it free on a
    side; `span`, the first station at a and the one after b; `base`, its radius by the middle of the stations that
    are free on both sides; `lean`, by what share the picture shows its right half brighter than its left half."""
    import cv2
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    wide = max(WIDE, int(np.ceil(4 * thick))) if thick else WIDE          # a thick rod is looked for further out
    for _ in range(2):                                                    # the second time along the axis found the first time
        strip, u = straight(picture, a, b, wide)
        mid, side = edges(strip, u, wide / 2)
        both = np.isfinite(side).all(1)
        base = float(np.median((side[both, 1] - side[both, 0]) / 2)) if both.sum() >= 8 else thick
        if base is None:
            raise ValueError("the rod is nowhere free on both sides: its radius must be given (thick)")
        centre = np.where(both, side.mean(1), np.where(np.isfinite(side[:, 1]), side[:, 1] - base, side[:, 0] + base))
        k = np.flatnonzero(np.isfinite(centre))
        for _ in range(4):                                                # a straight line through the middles, without those far from it
            line = np.polyfit(k, centre[k], 1)
            k = k[np.abs(np.polyval(line, k) - centre[k]) <= max(0.5 * base, 0.5)]
        along = (b - a) / np.linalg.norm(b - a)
        across = np.array([along[1], -along[0]])
        a, b = a + across * np.polyval(line, 0), b + across * np.polyval(line, len(strip) - 1)
    strip, u = straight(picture, a, b, wide)
    mid, side = edges(strip, u, 0.6 * wide, found=True)                   # further out: a joint is wider than the rod
    left, right = -side[:, 0], side[:, 1]
    both = np.isfinite(left) & np.isfinite(right)
    seen = np.isfinite(left) | np.isfinite(right)
    # its own radius along the axis: a straight line through the radius of the stations that are free on both sides
    # and alike on both, without those far from it. A post is seen in perspective and can be thicker at one end
    k = np.flatnonzero(both & (np.abs(left - right) < 0.3 * (left + right)))
    own = np.full(len(strip), base)
    if len(k) >= 16:
        for _ in range(4):
            line = np.polyfit(k, ((left + right) / 2)[k], 1)
            k = k[np.abs(np.polyval(line, k) - ((left + right) / 2)[k]) <= 0.25 * base]
        own = np.clip(np.polyval(line, np.arange(len(strip))), 0.7 * base, 1.3 * base)
    r = np.where(both, np.where(np.abs(left - right) < 0.3 * (left + right), (left + right) / 2, np.minimum(left, right)),
                 np.where(seen, np.where(np.isfinite(left), left, right), own))
    gaps = np.flatnonzero(np.diff(np.r_[False, ~seen, False].astype(np.int8)))
    for first, after in zip(gaps[::2], gaps[1::2]):                      # a few stations that do not show it, inside a joint: as the stations beside them
        if 0 < first and after < len(r) and after - first <= 8:
            r[first:after] = np.interp(np.arange(first, after), [first - 1, after], [r[first - 1], r[after]])
    r = cv2.medianBlur(np.clip(r, 0.6 * own, 3.0 * own).astype(np.float32)[None], 3)[0]
    # a rod is wider than itself only at a joint, which is short. A longer stretch is a thing that stands beside it
    ends = np.flatnonzero(np.diff(np.r_[False, r > 1.4 * own, False].astype(np.int8)))
    for first, after in zip(ends[::2], ends[1::2]):
        if after - first > 5 * base + 4:
            r[first:after] = own[first:after]
    rows = a[1] + np.arange(len(strip)) * along[1]
    for first, last in plain:
        r = np.where((rows >= first) & (rows <= last), own, r)
    for row, ball in joints:
        r = np.maximum(r, np.sqrt(np.maximum(ball ** 2 - ((rows - row) / along[1]) ** 2, 0)))
    # the light on it, as the picture shows it: its right half against its left half, where it is wide enough to show two halves
    luma = cv2.blur(strip, (3, 3)) @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    k = np.flatnonzero(both & (r >= 3.5) & (r <= 1.2 * own))       # a narrower rod shows the colours beside it in both halves
    half = lambda sign: np.array([luma[j, np.argmin(np.abs(u - sign * 0.5 * r[j]))] for j in k])
    lean = float(np.median((half(1) - half(-1)) / (half(1) + half(-1) + 1e-6))) if len(k) >= 16 else 0.0
    colour = np.zeros((len(strip), 3), np.float32)
    for k in range(len(strip)):                                           # the colour of its middle: the half of its width about the axis
        colour[k] = strip[k, np.abs(u) <= max(0.5 * r[k], 0.3)].mean(0)
    known = np.flatnonzero(seen)
    for ch in range(3):                                                   # a station that does not show the rod has the colour of the stations beside it
        colour[:, ch] = np.interp(np.arange(len(strip)), known, colour[known, ch])
        colour[:, ch] = cv2.medianBlur(np.pad(colour[:, ch], 2, mode="edge")[None], 5)[0, 2:-2]
    # a rod under THIN pixels in radius shows in every pixel the colours of what is behind it, a fire or bright air: it
    # has one colour, the middle one of the darkest third of its stations
    if base < THIN:
        bright = colour[seen] @ np.array([0.2126, 0.7152, 0.0722], np.float32)
        colour[:] = np.median(colour[seen][bright <= np.quantile(bright, 1 / 3)], 0)
    r = r.astype(np.float32)
    at = a[None] + np.arange(len(strip))[:, None] * along[None]
    # straight on to its top and to its foot, as it is at its nearest end
    ends = []
    for row, end, step in ((top, 0, -1), (foot, len(strip) - 1, 1)):
        more = int(round((row - at[end, 1]) / along[1])) * step if row is not None else 0
        ends.append(max(more, 0))
    grow = lambda v, fill=None: np.concatenate([np.repeat(v[:1] if fill is None else fill, ends[0], 0), v, np.repeat(v[-1:] if fill is None else fill, ends[1], 0)])
    at = np.concatenate([at[0] - np.arange(ends[0], 0, -1)[:, None] * along[None], at, at[-1] + np.arange(1, ends[1] + 1)[:, None] * along[None]])
    return dict(a=a, b=b, at=at, r=np.concatenate([np.full(ends[0], r[0]), r, np.full(ends[1], r[-1])]), colour=grow(colour), seen=grow(seen, np.array([False])), base=base,
                span=(ends[0], ends[0] + len(strip)), lean=lean)


def shaped(a, b, radius, colour):
    """A rod from a to b that is not measured: the picture shows it before a thing as dark as itself. radius: its
    radius along it, as points (share of its length, radius). It has one colour."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    n = max(int(round(np.linalg.norm(b - a))) + 1, 2)
    share = np.arange(n) / (n - 1)
    r = np.interp(share, [v[0] for v in radius], [v[1] for v in radius]).astype(np.float32)
    return dict(a=a, b=b, at=a[None] + share[:, None] * (b - a)[None], r=r, colour=np.tile(np.asarray(colour, np.float32)[None], (n, 1)), seen=np.ones(n, bool),
                base=float(np.median(r)), span=(0, n), lean=0.0)


def outline(shape, rod, grow=1.5):
    """The pixels of a picture of that shape at the place of the rod, `grow` pixels wider than it for its soft
    edge, over its whole length."""
    import cv2
    k = np.arange(len(rod["r"]))
    along = rod["at"][-1] - rod["at"][0]
    along /= np.linalg.norm(along)
    across = np.array([along[1], -along[0]])
    wide = (rod["r"][k] + grow)[:, None] * across[None]
    ring = np.concatenate([rod["at"][k] - wide, (rod["at"][k] + wide)[::-1]])
    mask = np.zeros(shape, np.uint8)
    cv2.fillPoly(mask, [np.round(ring * 16).astype(np.int32)], 1, shift=4)
    return mask > 0


def lathe(rod, space, depth, sides=12):
    """The surface of the rod at one depth: faces (n, 4, 3) and a colour for each corner (n, 4, 3).

    space(x, y, z): the place in the scene of the plate place (x, y) at the depth z. The middle of the rod, which
    faces the camera, has the colour that the picture shows there. Its surface is brighter towards the side on
    which the picture shows it brighter (`lean`), and darker towards its edge, where it is turned away from the
    camera. Both ends are closed."""
    at, r, colour = rod["at"], rod["r"].astype(np.float64), rod["colour"].astype(np.float64)
    at = np.concatenate([at[:1], at, at[-1:]])                            # a ring of no width at each end
    r, colour = np.concatenate([[0.0], r, [0.0]]), np.concatenate([colour[:1], colour, colour[-1:]])
    centre = space(at[:, 0], at[:, 1], depth)
    one = space(at[:, 0] + 1.0, at[:, 1], depth) - centre                 # a plate pixel to the right, in the scene
    along = at[-1] - at[0]
    along /= np.linalg.norm(along)
    size = np.linalg.norm(one, axis=1)
    right = one / size[:, None]
    up = np.cross(right, np.array([0.0, 1.0, 0.0]))                       # a plate pixel upwards, in the scene
    side = along[1] * right + along[0] * up                               # across the rod, in the plane that faces the camera
    turn = 2 * np.pi * np.arange(sides + 1) / sides
    normal = np.cos(turn)[None, :, None] * side[:, None] + np.sin(turn)[None, :, None] * np.array([0.0, -1.0, 0.0])
    ring = centre[:, None] + (r * size)[:, None, None] * normal
    shade = np.clip(1 + 2 * float(rod["lean"]) * np.cos(turn), 0.4, 1.8) * (1 - ROUND * (1 - np.abs(np.sin(turn))))      # at half its radius: as the picture
    lit = colour[:, None] * shade[None, :, None]
    quads = np.stack([ring[1:, :-1], ring[1:, 1:], ring[:-1, 1:], ring[:-1, :-1]], 2).reshape(-1, 4, 3)
    tint = np.stack([lit[1:, :-1], lit[1:, 1:], lit[:-1, 1:], lit[:-1, :-1]], 2).reshape(-1, 4, 3)
    return quads.astype(np.float32), tint.astype(np.float32)
