"""The image generator of the sibling project w40k-mechanicum
(src/gentextures.py, Z-Image-Turbo), set to write its drafts into this
project: wip/gen/<stem>_<seed>.png. A module that imports this runs in that
project's environment, ../w40k-mechanicum/.venv-moge/bin/python, which also
holds MoGe-2 and OpenCV."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))    # mech-design
sys.path.append(os.path.join(os.path.dirname(ROOT), "w40k-mechanicum", "src"))
import gentextures as G
G.GEN = os.path.join(ROOT, "wip", "gen")
PREVIEW = os.path.join(ROOT, "wip", "preview", "procession")
