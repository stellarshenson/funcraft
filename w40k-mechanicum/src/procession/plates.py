"""Backdrop plates of the procession scene: the far world behind the three
walking mechs, generated with Z-Image-Turbo as the plates of scenes 04 to 13
are (src/genplates.py, src/gentextures.py).

The scene camera stands 8.6 m above flat ground and looks level along it;
its horizon is at row 295 of a 2432 x 768 plate. The moving ground covers
everything below the horizon, so the backdrop has only the 295 rows above
it to show its subject: far away, standing on the horizon, with sky over
it. A draft is therefore a strip, 2432 x 336: the model lays a skyline out
over most of a picture's height, which in this strip is about
290 rows. `pick` measures the horizon of the strip and sets the strip into
a 2432 x 768 plate with that horizon on row 295. Drafts named <name>x are
generated 1.5 times larger and reduced, for finer detail.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 \\
        .venv-moge/bin/python src/procession/plates.py gen all 1 2 3 4     # wip/gen/plate_terra_<name>_<seed>.png
    .venv-moge/bin/python src/procession/plates.py sheet                   # wip/preview/procession/plates-<name>.jpg
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 \\
        .venv-moge/bin/python src/procession/plates.py pick <name> <seed>  # wip/scene3d/terra_<name><seed>.png and .npz
    .venv-moge/bin/python src/procession/plates.py edit <name><seed>       # wip/scene3d/terra_<name><seed>_fx.npz
"""
import os, sys, glob
import numpy as np
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import gentextures as G

W, H, STRIP, HORIZON = 2432, 768, 336, 295
PREVIEW = os.path.join(G.ROOT, "wip", "preview", "procession")

FRAME = ("A very wide panorama seen from far away across a vast empty plaza, level with the ground, through a long "
         "lens. Everything stands miles away along the horizon and rises into the sky, with open sky above the "
         "tallest spire. A narrow strip of empty flat plaza of dark stone slabs lies along the bottom, with nothing "
         "standing on it. No people, no vehicles, no robots, no text. ")
STYLE = ("Grimdark gothic Warhammer 40,000 concept art, cinematic ultra-wide matte painting, extremely detailed and "
         "ornate: every wall carved, riveted and buttressed, thousands of tiny lit windows, pinnacles, statues, "
         "pipes and gantries, blackened iron and tarnished gold, centuries of soot and grime, thick amber smog with "
         "strong aerial perspective so that each farther layer is paler and bluer, cold shafts of light through the "
         "smog against warm furnace glow, rich colour, sharp focus throughout, no text, no watermark")

PLATES = {
    "palace": "The Imperial Palace of Holy Terra as a skyline: a mountain range of gothic cathedral spires, domes "
              "of tarnished gold, flying buttresses and bastion walls, layer behind layer. Over the central gate "
              "a colossal golden double-headed eagle spreads its wings. Colossal statues of armoured saints stand "
              "on the bastions. Enormous crimson banners with gold emblems hang down the walls. Fires burn in "
              "giant bowls on the battlements, void ships hang in the sky.",
    "forge": "A forge-cathedral of the Adeptus Mechanicus as a skyline: gothic spires of blackened iron fused with "
             "smokestacks, cooling towers, colossal cog wheels and pipes as thick as towers. In the central tower "
             "a colossal emblem: a cog wheel enclosing a skull that is half bone and half machine, glowing red. "
             "Furnace mouths glow orange in the walls, flames stand on the smokestacks, enormous crimson banners "
             "with gold cog emblems hang down the walls, red warning lights, black smoke rising into the smog.",
    "gate": "The Eternity Gate of Holy Terra: one colossal wall across the whole horizon, of gold and blackened "
            "stone, with a towering pointed gate in its centre from which white-gold light pours into the smog. "
            "Rows of colossal statues of hooded tech-priests and winged saints stand in niches along the wall, "
            "pinnacles and spires rise behind it, enormous crimson banners with gold emblems hang between the "
            "statues, braziers burn along the wall top.",
    "basilica": "One colossal basilica of the Machine God in the centre of the horizon with lower spires spreading "
                "to both sides: a gothic west front with two towers, a giant rose window in the shape of a cog "
                "wheel glowing red and gold, a skull above the portal, statues of hooded tech-priests in hundreds "
                "of niches, flying buttresses, smokestacks behind, enormous crimson banners with gold cog emblems, "
                "fires in giant bowls on the towers.",
    "hive": "A hive city of Holy Terra as a skyline: cathedral spires a mile high standing in layers behind each "
            "other, bridges and buttresses between them, colossal statues of hooded tech-priests with cog-topped "
            "staffs standing among the spires as tall as towers, a giant golden cog wheel with a skull in it on "
            "the tallest spire, enormous crimson banners, furnace glow from below, gothic void ships low in the sky.",
    "statues": "A row of colossal statues along the horizon: hooded tech-priests of bronze and blackened iron, each "
               "a thousand feet tall, holding cog-topped staffs and censers from which smoke rises, with mechanical "
               "arms and skull faces under the hoods. Between and behind them the spires, domes and smokestacks of "
               "a gothic cathedral city, a golden double-headed eagle on the central dome, crimson banners hanging "
               "from the statues' arms, furnace glow at their feet.",
}
for name, what in PLATES.items():
    G.JOBS[f"plate_terra_{name}"] = (W, STRIP, FRAME + what + " " + STYLE)
    G.JOBS[f"plate_terra_{name}x"] = (W * 3 // 2, STRIP * 3 // 2, FRAME + what + " " + STYLE)


def horizon(d):
    """Row of the horizon from the MoGe-2 result: fit a plane to the points
    whose normal points up, and find where a ray along it meets the picture."""
    P, N, M, K = d["points"], d["normal"], d["mask"], d["intrinsics"]
    h, w = M.shape
    g = M & (N[..., 1] < -0.85)
    g[: h // 3] = False
    p = P[g][::7]
    c = p.mean(0)
    n = np.linalg.svd(p - c, full_matrices=False)[2][-1]
    n = n if n[1] < 0 else -n
    y = -n[2] / n[1]                                   # the ray (0, y, 1) along the plane, in the centre column
    return float((K[1, 2] + K[1, 1] * y) * h), float(np.degrees(2 * np.arctan(0.5 / K[0, 0]))), float(abs(n @ c))


def sheet():
    os.makedirs(PREVIEW, exist_ok=True)
    for name in PLATES:
        fs = sorted(glob.glob(os.path.join(G.GEN, f"plate_terra_{name}_*.png")) +
                    glob.glob(os.path.join(G.GEN, f"plate_terra_{name}x_*.png")))
        if not fs:
            continue
        out = Image.new("RGB", (1520, 280 * len(fs)))
        for k, f in enumerate(fs):
            out.paste(Image.open(f).convert("RGB").resize((1520, 280), Image.LANCZOS), (0, 280 * k))
        out.save(os.path.join(PREVIEW, f"plates-{name}.jpg"), quality=88)
        print("sheet", name, [os.path.basename(f) for f in fs])


def pick(name, seed):
    """Measure one strip with MoGe-2 and set it into a 2432 x 768 plate with
    its horizon on row 295: wip/scene3d/terra_<name><seed>.png, and .npz with
    the depth along the view axis, the mask of measured pixels and the
    normals, all in plate rows, plus the rows the strip fills."""
    import torch
    from moge.model.v2 import MoGeModel
    strip = np.asarray(Image.open(os.path.join(G.GEN, f"plate_terra_{name}_{seed}.png")).convert("RGB"))
    model = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval()
    x = torch.from_numpy(strip.astype(np.float32) / 255).permute(2, 0, 1).cuda()
    with torch.no_grad():
        d = {k: v.cpu().numpy() for k, v in model.infer(x).items() if torch.is_tensor(v)}
    row, fov, height = horizon(d)
    top = int(round(row)) - HORIZON                    # the strip row that lands on plate row 0
    r0, r1 = max(0, -top), min(H, len(strip) - top)    # the plate rows the strip fills
    plate = np.empty((H, W, 3), np.uint8)
    plate[r0:r1] = strip[r0 + top:r1 + top]
    plate[:r0] = plate[r0:2 * r0][::-1]                # sky above: the first rows mirrored
    plate[r1:] = plate[r1 - 1]                         # ground below: hidden by the moving ground
    depth, mask, normal = np.zeros((H, W), np.float32), np.zeros((H, W), bool), np.zeros((H, W, 3), np.float32)
    depth[r0:r1], mask[r0:r1], normal[r0:r1] = d["points"][r0 + top:r1 + top, :, 2], d["mask"][r0 + top:r1 + top], d["normal"][r0 + top:r1 + top]
    stem = os.path.join(G.ROOT, "wip", "scene3d", f"terra_{name}{seed}")
    Image.fromarray(plate).save(stem + ".png")
    np.savez_compressed(stem + ".npz", depth=depth, mask=mask, normal=normal, rows=np.array([r0, r1]))
    print(f"PICK {name} {seed}: horizon at strip row {row:.1f} of {len(strip)}, MoGe field of view {fov:.1f} deg, "
          f"MoGe camera height {height:.2f}; strip fills plate rows {r0} to {r1}; measured {mask.mean() * 100:.0f} % of the plate")


def edit(name):
    """Correct the measured depth of a plate and find what may move in it:
    wip/scene3d/terra_<name>_fx.npz and a check picture.

    sky    MoGe-2 leaves most of the sky unmeasured, but takes calm sky
           between towers for a wall. Sky is every calm pixel (little local
           detail) above the horizon that is connected to the top edge.
           Far spires lost in haze fall under it too; they are the farthest
           things, so nothing is lost.
    depth  measured depth outside the sky, holes filled from the nearest
           measured pixel, then a 5 px median; the sky gets 0 and is placed
           behind everything by the scene.
    flow   where the picture may drift: the sky, 0 at 14 px from any
           structure, so no tower is pulled along.
    fire   flames and embers: very bright orange pixels, grown and
           feathered."""
    import cv2
    stem = os.path.join(G.ROOT, "wip", "scene3d", f"terra_{name}")
    d = np.load(stem + ".npz")
    im = np.asarray(Image.open(stem + ".png").convert("RGB"))
    r0 = int(d["rows"][0])
    grey = cv2.cvtColor(im, cv2.COLOR_RGB2GRAY).astype(np.float32)
    detail = cv2.blur(np.abs(cv2.Laplacian(cv2.GaussianBlur(grey, (0, 0), 1.0), cv2.CV_32F)), (9, 9))
    calm = (detail < 1.6).astype(np.uint8)
    calm[HORIZON:] = 0
    lab = cv2.connectedComponents(calm, connectivity=4)[1]
    sky = np.isin(lab, np.unique(lab[r0 + 1][calm[r0 + 1] > 0])) & (calm > 0)
    sky[:r0 + 1] = True
    sky = cv2.morphologyEx(sky.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)) > 0
    known = d["mask"] & ~sky
    hole = (~known).astype(np.uint8)
    near = cv2.distanceTransformWithLabels(hole, cv2.DIST_L2, 3, labelType=cv2.DIST_LABEL_PIXEL)[1]
    ys, xs = np.nonzero(known)
    src = np.zeros(near.max() + 1, np.int64)
    src[near[ys, xs]] = np.arange(len(ys))
    depth = d["depth"][ys[src[near]], xs[src[near]]]
    depth = cv2.medianBlur(depth.astype(np.float32), 5)
    depth[sky] = 0
    flow = np.clip(cv2.distanceTransform(sky.astype(np.uint8), cv2.DIST_L2, 3) / 14.0, 0, 1)
    flow = cv2.GaussianBlur(flow.astype(np.float32), (0, 0), 3)
    r, g, b = (im[..., k].astype(np.int32) for k in range(3))
    fire = ((r > 232) & (g > 95) & (g < 0.8 * r) & (b < 115)).astype(np.uint8)      # orange; gold highlights are paler
    fire = cv2.GaussianBlur(cv2.dilate(fire, np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 2.5)
    np.savez_compressed(stem + "_fx.npz", depth=depth, sky=sky, flow=flow, fire=np.clip(fire, 0, 1), normal=d["normal"],
                        mask=d["mask"], rows=d["rows"])
    r1 = int(d["rows"][1])
    vis = im[:r1].copy()
    vis[sky[:r1]] = (0.55 * vis[sky[:r1]] + 0.45 * np.array([60, 140, 255])).astype(np.uint8)
    vis[fire[:r1] > 0.3] = (0, 255, 0)
    z = np.log(np.where(sky, depth[~sky].max(), np.maximum(depth, 1e-3)))[:r1]
    col = cv2.applyColorMap((255 - (z - z.min()) / (z.max() - z.min()) * 255).astype(np.uint8), cv2.COLORMAP_TURBO)[..., ::-1].copy()
    col[sky[:r1]] = 40
    Image.fromarray(np.concatenate([vis, col])).resize((1520, int(2 * r1 * 1520 / W)), Image.LANCZOS).save(
        os.path.join(PREVIEW, f"edit-{name}.jpg"), quality=88)
    print(f"EDIT {name}: sky {sky[:HORIZON].mean() * 100:.0f} % of the rows above the horizon, holes filled "
          f"{(~known & ~sky).mean() * 100:.1f} %, fire pixels {(fire > 0.3).sum()}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "gen":
        for n in (PLATES if sys.argv[2] == "all" else sys.argv[2].split(",")):
            G.generate(f"plate_terra_{n}", tuple(int(a) for a in sys.argv[3:]) or (1, 2, 3, 4))
    elif cmd == "sheet":
        sheet()
    elif cmd == "pick":
        pick(sys.argv[2], int(sys.argv[3]))
    elif cmd == "edit":
        edit(sys.argv[2])
