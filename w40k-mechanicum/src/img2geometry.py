"""Estimate the 3D geometry of a reference image with MoGe-2 (Microsoft,
monocular geometry): a metric point map, normals, a validity mask and the
camera intrinsics, saved as one .npz beside the image for src/backdrop.py.

Also the fill behind edges, for a camera that moves: `bg_depth`, the depth
pushed out from every depth break (the farthest depth within FILL pixels),
and <stem>_bg.png, the image with the near side of every break painted over
from its surroundings (OpenCV inpainting).

Run with the project's MoGe venv, GPU chosen by nvidia-smi index:
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 \\
        .venv-moge/bin/python src/img2geometry.py wip/scene3d/altar-rite.png
"""
import sys
import cv2
import numpy as np
import torch
from PIL import Image
from moge.model.v2 import MoGeModel

path = sys.argv[1]
model = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval()
img = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
x = torch.from_numpy(img).permute(2, 0, 1).cuda()
with torch.no_grad():
    out = model.infer(x)
res = {k: v.cpu().numpy() for k, v in out.items() if torch.is_tensor(v)}
FILL = 25                                          # pixels: wider than any gap the camera move opens
depth = res["depth"]
far = cv2.dilate(depth, np.ones((FILL, FILL), np.uint8))
near = (depth < 0.92 * far).astype(np.uint8) * 255   # the near side of a depth break
near = cv2.dilate(near, np.ones((5, 5), np.uint8))
bgr = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
cv2.imwrite(path.rsplit(".", 1)[0] + "_bg.png", cv2.inpaint(bgr, near, 9, cv2.INPAINT_TELEA))
res["bg_depth"] = far
np.savez_compressed(path.rsplit(".", 1)[0] + ".npz", **res)
print({k: (v.shape, v.dtype) for k, v in res.items()})
