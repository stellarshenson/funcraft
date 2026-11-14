"""The corridor of the saint scene, for the Warhound Titan that stands in it.

The opening between the black column and the gilded frame of the sun-gear is the mouth of a corridor. The owner
marked its outline (resources/assets/reference/paste-20261016-092418.png): the column's right edge and the frame's left edge, both
leaning, as every vertical of the plate does. MoGe-2 measured the inside as a flat wall 11 to 12 m away, at the
column's own depth: its 3D scene has no opening there. This script makes the opening in the 3D scene of the plate
(wip/scene3d/saint_clean.npz and _bg.png, read by src/backdrop.py):

- inside the outline the picture lies on the corridor's far end, a vertical wall BACK metres away, moved along the
  camera's rays, so the camera sees the plate unchanged
- the candlestick before the corridor (measured nearer than 8.5 m) keeps its measured depth
- the far depth behind each new depth break and the picture there are made again as src/img2geometry.py makes them

Vertical is not the camera's up: the 3D points along both marked edges lean back 13 degrees (the camera looks
slightly upward). UP holds that direction; the corridor's wall and the titan stand along it.

    python3 src/saintcorridor.py corridor    # writes the corridor into wip/scene3d/saint_clean.*; originals in wip/scene3d/before-corridor/
"""
import os, sys, shutil
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENE = os.path.join(ROOT, "wip", "scene3d", "saint")
BACK = 90.0                                   # metres: the corridor's far end, behind the titan
NEAR = 8.5                                    # metres: what is measured nearer stands before the corridor (the candlestick)
FILL = 25                                     # pixels, as src/img2geometry.py
# the owner's outline: (row, column) along the column's right edge and along the frame's left edge
LEFT = [(0, 1642), (64, 1629), (128, 1630), (191, 1636), (254, 1642), (317, 1649), (380, 1655), (443, 1662),
        (506, 1668), (570, 1675), (633, 1681), (696, 1687), (767, 1695)]
RIGHT = [(0, 2001), (67, 2005), (130, 2010), (193, 2015), (256, 2020), (320, 2025), (383, 2029), (446, 2034),
         (509, 2039), (572, 2043), (604, 2046), (667, 2042), (767, 2041)]
UP = np.array([-0.022, -0.974, 0.224])        # the vertical in camera coordinates (x right, y down, z forward), from the 3D points along both edges
UP /= np.linalg.norm(UP)


def outline(H, W):
    """The pixels inside the owner's outline."""
    rows = np.arange(H)
    lo = np.interp(rows, *zip(*LEFT))
    hi = np.interp(rows, *zip(*RIGHT))
    cols = np.arange(W)[None, :]
    return (cols >= lo[:, None]) & (cols < hi[:, None])


def corridor():
    import cv2                                     # not in Blender's Python, which reads only UP
    keep = os.path.join(ROOT, "wip", "scene3d", "before-corridor")
    os.makedirs(keep, exist_ok=True)
    for f in ("saint_clean.npz", "saint_clean_bg.png"):
        if not os.path.exists(os.path.join(keep, f)):
            shutil.copy2(SCENE + f[5:], os.path.join(keep, f))
    d = dict(np.load(os.path.join(keep, "saint_clean.npz")))
    H, W = d["depth"].shape
    K = d["intrinsics"]
    inside = outline(H, W) & ~(d["depth"] < NEAR)
    # the rays of the pixels, and the far wall: a vertical plane, its normal the camera's forward without its vertical part
    u = (np.arange(W) + 0.5) / W
    v = (np.arange(H) + 0.5) / H
    ray = np.stack(np.broadcast_arrays((u[None, :] - K[0, 2]) / K[0, 0], (v[:, None] - K[1, 2]) / K[1, 1], np.ones((H, W))), -1)
    n = np.array([0.0, 0.0, 1.0]) - UP[2] * UP
    n /= np.linalg.norm(n)
    t = BACK / (ray @ n)                          # the depth (z) at which each ray meets the wall
    d["points"][inside] = ray[inside] * t[inside, None]
    d["depth"][inside] = t[inside]
    d["mask"][inside] = True
    d["bg_depth"] = cv2.dilate(d["depth"], np.ones((FILL, FILL), np.uint8))
    np.savez_compressed(SCENE + "_clean.npz", **d)
    # the picture behind the new breaks: the near side of each break painted over from what lies round it
    near = (d["depth"] < 0.92 * d["bg_depth"]).astype(np.uint8) * 255
    near = cv2.dilate(near, np.ones((5, 5), np.uint8))
    clean = cv2.imread(SCENE + "_clean.png")
    old_near = cv2.dilate(((np.load(os.path.join(keep, "saint_clean.npz"))["depth"] < 0.92 * np.load(os.path.join(keep, "saint_clean.npz"))["bg_depth"])
                           .astype(np.uint8) * 255), np.ones((5, 5), np.uint8))
    new = (near > 0) & (old_near == 0)
    bg = cv2.imread(os.path.join(keep, "saint_clean_bg.png"))
    bg[new] = cv2.inpaint(clean, near, 9, cv2.INPAINT_TELEA)[new]
    cv2.imwrite(SCENE + "_clean_bg.png", bg)
    print(f"corridor: {int(inside.sum())} pixels moved to the far wall at {BACK} m; {int(new.sum())} pixels of fill painted anew")


if __name__ == "__main__":
    {"corridor": corridor}[sys.argv[1]]()
