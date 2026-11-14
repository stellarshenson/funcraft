"""The saint scene seen from above: python3 src/warhound/plan.py <head px> <row> <depth> <scale> <turn> [out]
x to the right as in the picture, depth upwards, the camera at the bottom. Grey dots: the plate's measured points
(wip/scene3d/before-corridor/saint_clean.npz), coloured by the picture; red: the opening of the corridor between the
column and the frame (the owner's outline); the titan's parts as boxes seen from above (rest pose, src/warhound.py),
its head filled, an arrow where it looks."""
import sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

px, row, D, k, turn = map(float, sys.argv[1:6])
out = sys.argv[6] if len(sys.argv) > 6 else "wip/preview/saint-plan.png"
d = np.load("wip/scene3d/before-corridor/saint_clean.npz")
P, m = d["points"], d["mask"]
K = d["intrinsics"]
pic = np.asarray(Image.open("wip/scene3d/saint_clean.png").convert("RGB"))
H, W = m.shape
S, X0, X1, Z1 = 60, -6.0, 8.0, 22.0                 # pixels per metre, the window in metres
im = Image.new("RGB", (int((X1 - X0) * S), int(Z1 * S)), (18, 18, 22))
dr = ImageDraw.Draw(im)
F = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
to = lambda x, z: ((x - X0) * S, (Z1 - z) * S)
ys, xs = np.mgrid[0:H:3, 0:W:3]
sel = m[ys, xs]
for yy, xx in zip(ys[sel], xs[sel]):
    x, _, z = P[yy, xx]
    if z < Z1 and X0 < x < X1:
        dr.point(to(x, z), fill=tuple(int(c) for c in pic[yy, xx]))
# the camera's field of view
for u in (0.0, 1.0):
    xn = (u - K[0, 2]) / K[0, 0]
    dr.line([to(0, 0), to(xn * Z1, Z1)], fill=(90, 90, 90))
# the opening's edges: the rays of the owner's outline at row 300, from the column and the frame inwards
for col, z in ((1649, 11.1), (2025, 9.4)):
    xn = ((col + 0.5) / W - K[0, 2]) / K[0, 0]
    dr.line([to(xn * z, z), to(xn * Z1, Z1)], fill=(220, 50, 40), width=2)
# the titan: rest-pose parts (metres, model frame: x its left, -y its front, z up), from src/warhound.py
PARTS = {"body": ((-5.42, -3.71), (5.43, 5.65)), "head": ((-1.72, -8.39), (1.77, -3.47)), "top_cover": ((-2.81, -3.41), (2.81, 5.43)),
         "plasma": ((-6.6, -6.73), (-3.85, 2.76)), "megabolter": ((4.32, -5.1), (6.5, 1.75)),
         "leg_left": ((2.42, -0.68), (4.58, 3.33)), "leg_right": ((-4.53, -0.41), (-2.36, 3.58)),
         "foot_left": ((0.55, -2.86), (6.44, 4.04)), "foot_right": ((-6.55, -3.15), (-0.39, 4.21))}
HEAD = (0.025, -5.93)
t = math.radians(turn)
front = np.array([-math.cos(t), -math.sin(t)])     # in the plan: (x, depth)
side = np.array([front[1], -front[0]])             # the model's +x, its left
def world(lx, ly):                                 # model x, y (metres, scale 1) -> plan (x, depth), before the shift
    return k * (lx * side - ly * front)
xn = ((px + 0.5) / W - K[0, 2]) / K[0, 0]
shift = np.array([xn * D, D]) - world(*HEAD)
for name, ((a, b), (c, e)) in PARTS.items():
    q = [world(*p) + shift for p in ((a, b), (c, b), (c, e), (a, e))]
    poly = [to(*p) for p in q]
    if name == "head":
        dr.polygon(poly, fill=(200, 40, 30), outline=(255, 200, 200))
    else:
        dr.polygon(poly, outline=(255, 220, 120) if name in ("plasma", "megabolter") else (120, 200, 255))
hc = np.array([xn * D, D])
dr.line([to(*hc), to(*(hc + 2.0 * front))], fill=(255, 255, 0), width=3)
for name, x, z in (("camera", 0, 0.3), ("saint", -2.1, 12.2), ("column", 1.94, 11.14), ("frame", 3.14, 9.05),
                   ("candlestick", 3.1, 6.7), ("left banner", 1.61, 11.9), ("sun-gear", 4.6, 9.9)):
    dr.ellipse([to(x, z)[0] - 4, to(x, z)[1] - 4, to(x, z)[0] + 4, to(x, z)[1] + 4], outline=(255, 255, 255))
    dr.text((to(x, z)[0] + 6, to(x, z)[1] - 8), name, fill=(255, 255, 255), font=F)
dr.text((10, 10), f"from above: head at plate pixel ({px:.0f}, {row:.0f}), {D:.1f} m; scale {k}; turned {turn:.0f} deg towards the camera",
        fill=(255, 255, 0), font=F)
for zz in range(0, int(Z1) + 1, 2):
    dr.text((2, to(0, zz)[1] - 8), f"{zz} m", fill=(150, 150, 150), font=F)
im.save(out)
print("wrote", out)
