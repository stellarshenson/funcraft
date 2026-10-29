"""The ornament of the Warhound's armour: mech-design/src/procession/ornament.py, the ornament of the procession's
mechs, drawn on the charts of the Warhound's plates (src/warhound.py, `plating`). Its plates are red and bone: the
grand ones carry a cog-tooth border, an emblem and a motto, the middle ones a gold trim with rivets and an engraved
field, the small ones a steel band.

    ~/.local/opt/blender-4.5.9-linux-x64/blender -b -P src/warhound.py -- plating     # wip/warhound/warhound.npz
    .venv-moge/bin/python src/warhoundlivery.py                                      # wip/warhound/livery/warhound_*.png
"""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(ROOT), "mech-design", "src", "procession"))
import ornament as O

O.PLATING = os.path.join(ROOT, "wip", "warhound")
O.OUT = os.path.join(ROOT, "wip", "warhound", "livery")
O.PREVIEW = os.path.join(ROOT, "wip", "preview")
O.LIVERY["warhound"] = dict(red=O.RED, bone=O.BONE)
O.draw("warhound")
