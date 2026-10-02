"""Motion maps of the plate scenes (src/scenes.py): which elements of a
plate move, and how.

Every element except a stream is cut out of the plate into its own mesh
(src/actors.py): the map gives the box and points SAM 2.1 cuts its mask
from (src/segment.py), and how the mesh moves. A priest has a skeleton and
the map gives the rotations of its bones; a thing a priest carries is bound
to that priest's forearm. A rigid thing spins about its own axis, swings
about a pivot or hovers. Cloth hangs from its top edge on a chain of bones.
A stream stays in the plate and flows: its texture is carried along flow
lines, written as one clean plate per loop frame. Every motion is a whole
number of cycles per loop, so frame 80 equals frame 0.

    python3 src/motion.py map <name>      # wip/preview/motion-<name>.png: masks, skeletons, legend
    python3 src/motion.py flow <name>     # wip/scene3d/<name>_flow/p0001..p0080.png (clean plate, streams flowing)
    python3 src/motion.py plan <name>     # wip/preview/plan-<name>.png: the scene from above, and a table of depths
    python3 src/motion.py proof <name>    # measured motion per element in wip/frames-<name>, head crops
"""
import os, sys, math
import numpy as np, cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = 80
CYCLE = 20                 # frames per flow cycle of a molten stream: 4 per loop
TAU = 2 * math.pi


def priest(id, who, box, pos, phase, neg=(), head=0.2, **moves):
    """A figure. head: share of the mask's height above the neck. Moves, as
    peak bone rotations in degrees: turn (head left and right), nod (head
    forward and back up), tilt (head to the shoulder), sway (lean from the
    feet), robe (the robe below the hips swings, lagging the body);
    breathe: chest stretch in percent."""
    moves.setdefault("robe", 0.6 if head < 1.0 else 0.0)        # a hood alone has no robe to swing
    return dict(kind="priest", id=id, who=who, box=box, pos=pos, neg=neg, phase=phase, head=head, **moves)


def carry(id, who, parent, box, pos, hand, lift=0.0, neg=(), grip=None, stands=False):
    """A thing `parent` holds, or a free hand: one rigid piece that moves
    with the hand at plate pixel `hand` and keeps its orientation; the
    forearm swings `lift` degrees. grip=(box, point): the hand that holds
    the thing, cut with it, so thing and hand move as one. stands: a staff
    on the floor, which turns about its foot and follows the hand."""
    el = dict(kind="carry", id=id, who=who, parent=parent, box=box, pos=pos, neg=neg, hand=hand, lift=lift, stands=stands)
    if grip:
        el["cuts"] = [dict(box=box, pos=pos, neg=neg), dict(box=grip[0], pos=[grip[1]], neg=())]
    return el


def stream(id, who, box, pos, line, speed):
    """Texture flowing along `line` at `speed` px per frame: molten metal,
    fire, scrolling screen text, a painted smoke wisp."""
    return dict(kind="stream", id=id, who=who, box=box, pos=pos, neg=(), line=line, speed=speed)


def spin(id, who, box, pos, neg=(), turns=1, rock=0.0, rim="outer"):
    """A wheel on its own axis; pos[0] is the hub. It makes `turns` whole
    turns per loop, or rocks `rock` degrees each way. rim "inner": only the
    disc inside the mask turns (a fan in its frame); "outer": the whole
    mask turns (a cog with its teeth)."""
    return dict(kind="spin", id=id, who=who, box=box, pos=pos, neg=neg, turns=turns, rock=rock, rim=rim)


def smoke(id, who, of=None, at=None):
    """A smoke source, simulated by src/smoke.py: the flame of the carried
    candle `of`, or the fixed plate pixel `at`."""
    return dict(kind="smoke", id=id, who=who, of=of, at=at)


# per scene: the seed of the chosen clean plate (src/cleanplate.py); 1 where none is listed
CLEAN_SEED = {"foundry": 2, "choir": 3}
# per scene: boxes (x0, y0, x1, y1) where a white-hot blob is no flame (molten metal, burning wreck)
NOFLAME = {"foundry": [(300, 240, 1760, 768)], "voidshrine": [(1650, 0, 2432, 768)]}
# per scene: boxes where every white-hot blob is a flame, whatever its size (a lamp flame behind glass)
FLAMES = {"forge": [(935, 300, 1000, 385)]}
# per scene: boxes round the smoke painted into the plate, which src/cleanplate.py paints over
WISPS = {
    "choir": [(820, 30, 1030, 300), (430, 140, 670, 335), (1085, 215, 1175, 325), (1520, 70, 1690, 310),
              (1845, 140, 1965, 300)],
    "reliquary": [(1150, 0, 1490, 380)],
}


def swing(id, who, box, pos, pivot, deg, phase=0.0, neg=()):
    """A rigid thing hanging from plate pixel `pivot`, swinging `deg` degrees."""
    return dict(kind="swing", id=id, who=who, box=box, pos=pos, neg=neg, pivot=pivot, deg=deg, phase=phase)


def hover(id, who, box, pos, px, phase=0.0, neg=()):
    """A rigid thing floating: it rises and sinks `px` plate pixels."""
    return dict(kind="hover", id=id, who=who, box=box, pos=pos, neg=neg, px=px, phase=phase)


def cloth(id, who, box, pos, deg=0.5, phase=0.0, neg=()):
    """Cloth hanging from its top edge: four bones top to bottom, each
    swinging `deg` degrees a little later than the one above."""
    return dict(kind="cloth", id=id, who=who, box=box, pos=pos, neg=neg, deg=deg, phase=phase)


MAPS = {
    "foundry": [
        priest("1", "Priest, front left", (55, 446, 220, 766), [(135, 620), (130, 500)], 0.00, turn=10, sway=0.8, breathe=1.2),
        priest("2", "Priest by the crucible", (236, 450, 346, 711), [(290, 590), (292, 490)], 0.30, nod=12, breathe=1.2),
        priest("3", "Priest in the smoke", (925, 440, 984, 578), [(955, 520)], 0.55, turn=12, sway=0.6),
        priest("4", "Priest at the channel, far", (1063, 445, 1134, 613), [(1100, 540)], 0.75, nod=10, tilt=3),
        priest("5", "Priest at the channel, near", (1271, 445, 1375, 684), [(1325, 580), (1322, 480)], 0.15, turn=10, sway=0.8),
        priest("6", "Priest, front right", (1710, 442, 1858, 739), [(1785, 620), (1782, 490)], 0.45, nod=10, turn=8, breathe=1.2),
        stream("7", "Molten pour from the crucible", (535, 269, 627, 492), [(575, 320), (580, 420)],
               [(575, 272), (578, 380), (590, 490)], 4.0),
        stream("8", "Molten spill over the lip", (600, 470, 800, 640), [(680, 520), (730, 580)],
               [(640, 488), (700, 540), (760, 615)], 3.0),
        stream("9", "Molten channel", (640, 570, 1720, 768), [(760, 640), (1000, 680), (1250, 720), (1450, 752)],
               [(680, 610), (1000, 670), (1300, 725), (1720, 778)], 2.5),
        cloth("10", "Banner, far left", (43, 0, 195, 440), [(118, 200)], phase=0.0),
        cloth("11", "Banner 2", (1086, 49, 1165, 421), [(1125, 230)], phase=0.15),
        cloth("12", "Banner 3", (1269, 6, 1373, 421), [(1320, 210)], phase=0.3),
        cloth("13", "Banner 4", (1488, 0, 1623, 421), [(1555, 210)], phase=0.45),
        cloth("14", "Banner 5", (1787, 0, 1946, 415), [(1866, 210)], phase=0.6),
        cloth("15", "Banner 6", (2050, 0, 2184, 415), [(2117, 210)], phase=0.75),
        cloth("16", "Banner 7", (2263, 0, 2385, 409), [(2324, 200)], phase=0.9),
        smoke("s1", "Smoke of a wall candle", at=(846, 596)),
        smoke("s2", "Smoke of a wall candle", at=(1445, 596)),
    ],
    "forge": [
        swing("1", "Lantern on its chain", (885, 0, 1045, 455), [(965, 300), (964, 60)], (964, 0), 1.2, 0.0),
        swing("2", "Hook on its chain", (605, 0, 675, 210), [(640, 150), (640, 50)], (640, 0), 1.5, 0.3),
        swing("3", "Pendant on its chain", (1260, 0, 1320, 92), [(1292, 60)], (1290, 0), 1.5, 0.6),
        swing("4", "Magnifier arm", (402, 180, 628, 356), [(572, 305), (470, 232)], (409, 207), 0.8, 0.15),
        swing("5", "Lens on the right arm", (1060, 100, 1150, 272), [(1104, 232)], (1135, 118), 2.0, 0.45),
        spin("6", "Left fan of the card", (833, 484, 955, 574), [(893, 529), (866, 522), (920, 544)], rim="inner"),
        spin("7", "Right fan of the card", (955, 501, 1079, 593), [(1017, 547), (990, 540), (1046, 560)], rim="inner"),
        cloth("8", "Velvet drape on its stand", (1314, 64, 1890, 690), [(1600, 300), (1650, 500)], phase=0.2),
        smoke("s1", "Smoke of the candle", at=(470, 420)),
    ],
    "vault": [
        priest("1", "Kneeling priest", (789, 325, 1133, 755), [(940, 560), (920, 400)], 0.0, head=0.28, nod=8, breathe=1.5,
               sway=0.3),
        swing("2", "Seal tag 1", (195, 355, 265, 515), [(230, 450)], (229, 250), 1.0, 0.0),
        swing("3", "Seal tag 2", (430, 355, 497, 512), [(465, 450)], (466, 250), 1.0, 0.15),
        swing("4", "Seal tag 3", (1108, 370, 1160, 498), [(1135, 450)], (1136, 270), 1.0, 0.3),
        swing("5", "Seal tag 4", (1278, 365, 1337, 505), [(1308, 450)], (1309, 260), 1.0, 0.45),
        swing("6", "Seal tag 5", (1482, 360, 1548, 510), [(1515, 450)], (1516, 250), 1.0, 0.6),
        swing("7", "Seal tag 6", (1733, 345, 1808, 515), [(1770, 450)], (1772, 240), 1.0, 0.75),
        swing("8", "Seal tag 7", (2015, 340, 2094, 518), [(2055, 450)], (2056, 235), 1.0, 0.9),
        stream("9", "Screen text scrolls upward", (662, 222, 775, 388), [(718, 300)], [(718, 386), (718, 224)], 0.6),
        spin("10", "Gear on the arch", (1375, 34, 1448, 100), [(1411, 67)]),
        smoke("s1", "Smoke of floor candle 1", at=(1058, 600)),
        smoke("s2", "Smoke of floor candle 2", at=(1390, 640)),
        smoke("s3", "Smoke of floor candle 3", at=(1852, 690)),
    ],
    "street": [
        priest("1", "Priest, left", (604, 690, 650, 768), [(627, 735)], 0.00, turn=10, sway=1.0),
        priest("2", "Priest 2", (658, 704, 688, 764), [(673, 735)], 0.20, sway=1.0),
        priest("3", "Priest 3", (824, 703, 855, 761), [(840, 735)], 0.40, turn=10, sway=1.0),
        priest("4", "Priest 4", (866, 698, 903, 768), [(885, 735)], 0.60, sway=1.0, nod=8),
        priest("5", "Priest, right", (1010, 682, 1063, 768), [(1036, 730)], 0.80, turn=10, sway=1.0),
        priest("6", "Far priest 1", (639, 706, 656, 756), [(647, 732)], 0.10, sway=1.2),
        priest("7", "Far priest 2", (695, 713, 709, 743), [(702, 729)], 0.30, sway=1.2),
        priest("8", "Far priest 3", (722, 714, 737, 744), [(729, 730)], 0.50, sway=1.2),
        priest("9", "Far priest 4", (779, 712, 795, 743), [(787, 729)], 0.70, sway=1.2),
        priest("10", "Far priest 5", (804, 712, 819, 742), [(811, 728)], 0.90, sway=1.2),
        cloth("11", "Banner, front left", (135, 0, 411, 654), [(270, 200), (260, 450)], phase=0.0),
        cloth("12", "Banner 2", (446, 242, 565, 685), [(505, 400)], phase=0.2),
        cloth("13", "Banner 3", (986, 173, 1112, 687), [(1048, 350)], phase=0.4),
        cloth("14", "Banner, front right", (1326, 0, 1571, 652), [(1445, 250), (1450, 450)], phase=0.6),
        cloth("15", "Banner 5", (864, 391, 933, 696), [(898, 520)], phase=0.8),
        cloth("16", "Banner 6", (793, 512, 840, 701), [(816, 600)], phase=0.5),
        smoke("s1", "Smoke of the brazier candle", at=(1747, 486)),
        smoke("s2", "Smoke of a street candle", at=(1226, 592)),
    ],
    "saint": [
        priest("1", "The saint", (567, 101, 1015, 761), [(800, 450), (795, 160)], 0.0, head=0.2, turn=5, robe=0),
        carry("1l", "Left hand of the saint", "1", (572, 238, 652, 312), [(604, 275)], hand=(604, 275), lift=1.5),
        carry("1r", "Right hand of the saint", "1", (952, 278, 1022, 348), [(990, 315)], hand=(990, 315), lift=1.5),
        cloth("2", "Banner, left", (1, 1, 169, 568), [(80, 250)], phase=0.0),
        cloth("3", "Banner, right", (1429, 0, 1596, 587), [(1510, 250)], phase=0.4),
        spin("4", "Sun-gear", (2049, 1, 2432, 382), [(2265, 180), (2150, 100)], rock=3),
        smoke("s1", "Smoke of a candle, left", at=(219, 353)),
        smoke("s2", "Smoke of a candle by the niche", at=(450, 468)),
        smoke("s3", "Smoke of a candle, centre", at=(1364, 365)),
        smoke("s4", "Smoke of a candle, right", at=(1964, 505)),
    ],
    "hall": [
        cloth("1", "Banner, left 1", (49, 0, 305, 640), [(180, 250)], phase=0.0),
        cloth("2", "Banner, left 2", (329, 73, 415, 600), [(372, 330)], phase=0.1),
        cloth("3", "Banner, left 3", (421, 226, 464, 588), [(442, 400)], phase=0.2),
        cloth("4", "Banner, right 1", (1982, 0, 2432, 690), [(2200, 300)], phase=0.5),
        cloth("5", "Banner, right 2", (1421, 0, 1873, 680), [(1640, 300)], phase=0.6),
        cloth("6", "Banner, right 3", (1147, 49, 1360, 636), [(1250, 330)], phase=0.7),
        cloth("7", "Banner, right 4", (1000, 183, 1110, 612), [(1055, 400)], phase=0.8),
        cloth("8", "Banner, right 5", (915, 268, 976, 600), [(945, 430)], phase=0.9),
        cloth("9", "Banner, right 6", (854, 323, 903, 588), [(878, 450)], phase=0.0),
        smoke("s1", "Smoke of a floor candle, left", at=(40, 645)),
        smoke("s2", "Smoke of a floor candle, centre", at=(1376, 614)),
        smoke("s3", "Smoke of a floor candle, right", at=(1954, 638)),
    ],
    "reliquary": [
        spin("1", "Turbine of the right shrine", (2105, 180, 2400, 480), [(2251, 329), (2200, 280), (2300, 380)], rim="inner"),
        spin("2", "Cog with the red gem", (735, 70, 827, 162), [(781, 116)]),
        spin("3", "Gear between the fans", (770, 236, 840, 306), [(805, 271)]),
        smoke("s1", "Smoke of the censer", at=(1311, 376)),
        spin("5", "Left fan of the card", (535, 222, 785, 472), [(660, 347), (620, 300), (700, 400)], rim="inner"),
        spin("6", "Right fan of the card", (838, 223, 1072, 457), [(955, 340), (915, 300), (995, 385)], rim="inner"),
    ],
    "scriptorium": [
        hover("1", "Servo-skull, left", (435, 270, 515, 376), [(475, 320)], 4, 0.0),
        hover("2", "Servo-skull, right", (1032, 188, 1117, 303), [(1075, 240)], 4, 0.4),
        swing("3", "Quill writes", (840, 228, 912, 370), [(872, 300)], (868, 232), 2.0, 0.1),
        swing("4", "Hanging scroll 1", (256, 18, 415, 311), [(335, 170)], (335, 25), 0.4, 0.0),
        swing("5", "Hanging scroll 2", (518, 37, 647, 329), [(582, 190)], (582, 45), 0.4, 0.2),
        swing("6", "Hanging scroll 3", (1275, 122, 1403, 342), [(1339, 230)], (1339, 128), 0.4, 0.4),
        swing("7", "Hanging scroll 4", (1566, 90, 1722, 360), [(1647, 230), (1600, 108), (1690, 108)], (1647, 98), 0.4, 0.6),
        swing("8", "Hanging scroll 5", (1867, 49, 2025, 305), [(1946, 180)], (1946, 55), 0.4, 0.8),
        smoke("s1", "Smoke of the candle, left", at=(61, 353)),
        smoke("s2", "Smoke of a shelf candle", at=(1447, 365)),
    ],
    "voidshrine": [
        hover("1", "Ringed station, near", (1708, 220, 2007, 403), [(1855, 300)], 3, 0.0),
        hover("2", "Ringed station, far", (1964, 55, 2324, 232), [(2140, 140)], 2, 0.5),
        stream("3", "Fire of the burning ship", (1732, 439, 2257, 640), [(1850, 580), (1950, 560)],
               [(2135, 488), (1769, 610)], 1.5),
        cloth("4", "Banner, left", (98, 0, 305, 732), [(200, 300)], phase=0.0),
        cloth("5", "Banner, right", (1190, 85, 1391, 732), [(1290, 350)], phase=0.4),
        swing("6", "Hanging parchment", (1428, 405, 1498, 688), [(1462, 540)], (1462, 410), 0.6, 0.2),
        smoke("s1", "Smoke of altar candle 1", at=(467, 452)),
        smoke("s2", "Smoke of altar candle 4", at=(1087, 468)),
    ],
    "choir": [
        priest("1", "Priest, front left", (58, 201, 370, 765), [(215, 480), (215, 265)], 0.00, head=0.26, turn=8, sway=0.8, breathe=1.2),
        carry("1a", "Lamp staff of 1", "1", (70, 40, 170, 765), [(122, 160), (122, 620)], hand=(102, 430),
              grip=((78, 405, 128, 455), (102, 430)), stands=True),
        carry("1b", "Candle of 1", "1", (300, 285, 378, 440), [(338, 350)], hand=(340, 442), lift=1.5,
              grip=((316, 415, 366, 470), (340, 442))),
        priest("2", "Priest, second row left", (349, 245, 568, 763), [(450, 470), (462, 300)], 0.20, nod=8, turn=10),
        carry("2a", "Candle of 2", "2", (528, 318, 578, 432), [(552, 370)], hand=(549, 430), lift=1.5,
              grip=((530, 410, 568, 450), (549, 430))),
        priest("3", "Priest, front centre left", (550, 142, 992, 764), [(790, 480), (770, 260)], 0.40,
               neg=[(652, 420)], head=0.3, turn=10, tilt=4, sway=0.8),
        carry("3a", "Banner staff of 3", "3", (562, 0, 722, 765), [(645, 90), (655, 520)], hand=(646, 440),
              grip=((610, 404, 682, 482), (646, 440)), stands=True),
        carry("3b", "Candle of 3", "3", (900, 258, 992, 462), [(950, 330)], hand=(952, 475), lift=1.5,
              grip=((915, 430, 990, 520), (952, 475))),
        priest("4", "Priest, second row centre", (945, 258, 1159, 764), [(1060, 470), (1058, 330)], 0.60, nod=10, breathe=1.2),
        carry("4a", "Candle of 4", "4", (1118, 304, 1167, 422), [(1143, 350)], hand=(1143, 430), lift=1.5,
              grip=((1122, 404, 1164, 454), (1143, 430))),
        priest("5", "Priest, third row", (1172, 256, 1307, 757), [(1235, 450)], 0.80, turn=12, sway=0.6),
        priest("6", "Priest, front centre", (1258, 140, 1700, 763), [(1450, 520), (1475, 270), (1647, 560)], 0.10,
               head=0.3, turn=10, breathe=1.2),
        carry("6h", "Right hand of 6", "6", (1356, 458, 1462, 540), [(1405, 500)], hand=(1405, 500), lift=3),
        carry("6a", "Candle of 6", "6", (1598, 262, 1702, 440), [(1645, 340)], hand=(1645, 462), lift=1.5,
              grip=((1610, 430, 1680, 495), (1645, 462))),
        priest("7", "Priest, second row right", (1695, 194, 1933, 766), [(1810, 470), (1830, 280)], 0.50, nod=10, sway=0.6),
        carry("7a", "Candle of 7", "7", (1903, 268, 1967, 382), [(1938, 320)], hand=(1942, 396), lift=1.5,
              grip=((1922, 370, 1962, 420), (1942, 396))),
        priest("8", "Priest, front right", (1910, 108, 2421, 763), [(2180, 560), (2185, 250)], 0.70,
               head=0.3, turn=8, tilt=4, breathe=1.2),
        carry("8h", "Right hand of 8", "8", (2030, 480, 2140, 565), [(2085, 522)], hand=(2085, 522), lift=3),
        priest("9", "Priest at the right edge", (2294, 209, 2432, 766), [(2395, 330)], 0.30, turn=10, sway=0.6),
        priest("10", "Hood behind candle 3b", (860, 285, 932, 362), [(895, 322)], 0.90, head=1.0, nod=10),
        priest("11", "Hood behind candle 6a", (1535, 255, 1612, 362), [(1572, 300)], 0.25, head=1.0, nod=8, turn=8),
        cloth("12", "Carried banner 1", (278, 0, 393, 250), [(335, 120)], phase=0.0),
        cloth("13", "Carried banner 2", (842, 134, 903, 305), [(872, 220)], phase=0.12),
        cloth("14", "Carried banner 3", (988, 30, 1086, 275), [(1037, 150)], phase=0.25),
        cloth("15", "Carried banner 4", (1214, 0, 1330, 275), [(1272, 140)], phase=0.37),
        cloth("16", "Carried banner 5", (1464, 79, 1549, 262), [(1506, 170)], phase=0.5),
        cloth("17", "Carried banner 6", (1775, 0, 1885, 238), [(1830, 120)], phase=0.62),
        cloth("18", "Carried banner 7", (2050, 37, 2135, 232), [(2092, 135)], phase=0.75),
        cloth("19", "Carried banner 8", (2300, 0, 2428, 220), [(2364, 110)], phase=0.87),
        smoke("s1", "Smoke of candle 1b", of="1b"),
        smoke("s2", "Smoke of candle 2a", of="2a"),
        smoke("s3", "Smoke of candle 3b", of="3b"),
        smoke("s4", "Smoke of candle 4a", of="4a"),
        smoke("s6", "Smoke of candle 6a", of="6a"),
        smoke("s7", "Smoke of candle 7a", of="7a"),
    ],
}


def masks(name):
    seg = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_seg.npz"))
    return {el["id"]: seg[el["id"]] for el in MAPS[name] if el["kind"] != "smoke"}


def flow_setup(plate, streams):
    """Per stream: soft mask, flow vectors (px per frame) along its line,
    a per-pixel phase offset, and the plate with stream colours spread
    outward so an upstream look-up never fetches the surroundings."""
    H, W = plate.shape[:2]
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    rng = np.random.default_rng(7)
    for el in streams:
        m = el["mask"].astype(np.float32)
        best, fx, fy = np.full((H, W), np.inf, np.float32), np.zeros((H, W), np.float32), np.zeros((H, W), np.float32)
        for (x0, y0), (x1, y1) in zip(el["line"][:-1], el["line"][1:]):
            vx, vy = x1 - x0, y1 - y0
            L = math.hypot(vx, vy)
            s = np.clip(((X - x0) * vx + (Y - y0) * vy) / (L * L), 0, 1)
            d = np.hypot(X - (x0 + s * vx), Y - (y0 + s * vy))
            near = d < best
            best[near], fx[near], fy[near] = d[near], vx / L, vy / L
        g = cv2.GaussianBlur(m, (0, 0), 12) + 1e-6
        fx = cv2.GaussianBlur(fx * m, (0, 0), 12) / g
        fy = cv2.GaussianBlur(fy * m, (0, 0), 12) / g
        n = np.hypot(fx, fy) + 1e-6
        el["F"] = (fx / n * el["speed"], fy / n * el["speed"])
        noise = cv2.GaussianBlur(rng.random((H, W)).astype(np.float32), (0, 0), 20)
        el["offset"] = (noise - noise.min()) / (noise.max() - noise.min() + 1e-6)
        el["ws"] = cv2.GaussianBlur(cv2.dilate(el["mask"].astype(np.uint8), np.ones((5, 5), np.uint8)).astype(np.float32), (0, 0), 2)
        fill, done = np.zeros_like(plate), m > 0
        for sg in (6, 20, 60):
            wb = cv2.GaussianBlur(m, (0, 0), sg)
            spread = cv2.GaussianBlur(plate * m[..., None], (0, 0), sg) / (wb[..., None] + 1e-6)
            new = ~done & (wb > 1e-3)
            fill[new], done = spread[new], done | new
        el["src"] = np.where(m[..., None] > 0, plate, fill)


def flow_frame(plate, streams, k):
    """The plate at loop frame k. Each stream is two copies of its texture,
    each carried downstream for CYCLE frames and then reset, half a cycle
    apart, cross-faded so a copy is invisible when it resets."""
    H, W = plate.shape[:2]
    Y, X = np.mgrid[0:H, 0:W].astype(np.float32)
    f32 = lambda a: a.astype(np.float32)
    out = plate.copy()
    for el in streams:
        fx, fy = el["F"]
        col = np.zeros_like(plate)
        for i in (0.0, 0.5):
            p = (k / CYCLE + el["offset"] + i) % 1.0
            tau = (p - 0.5) * CYCLE
            wgt = (1 - np.abs(2 * p - 1))[..., None]
            col += wgt * cv2.remap(el["src"], f32(X - fx * tau), f32(Y - fy * tau), cv2.INTER_CUBIC,
                                   borderMode=cv2.BORDER_REFLECT)
        out = out * (1 - el["ws"][..., None]) + col * el["ws"][..., None]
    return np.clip(out, 0, 255)


def write_flow(name):
    mk = masks(name)
    streams = [dict(el, mask=mk[el["id"]]) for el in MAPS[name] if el["kind"] == "stream"]
    if not streams:
        return
    plate = cv2.imread(os.path.join(ROOT, "wip", "scene3d", name + "_clean.png"), cv2.IMREAD_COLOR).astype(np.float32)
    flow_setup(plate, streams)
    seq = os.path.join(ROOT, "wip", "scene3d", f"{name}_flow")
    os.makedirs(seq, exist_ok=True)
    for k in range(FRAMES):
        cv2.imwrite(os.path.join(seq, f"p{k + 1:04d}.png"), flow_frame(plate, streams, k).astype(np.uint8),
                    [cv2.IMWRITE_PNG_COMPRESSION, 1])
    print("FLOW_DONE", seq)


COLOURS = [(255, 229, 0), (3, 255, 118), (0, 214, 255), (249, 0, 213), (255, 121, 41), (0, 145, 255),
           (118, 230, 0), (129, 64, 255), (218, 255, 100), (252, 128, 234), (255, 255, 255), (80, 180, 255)]


def describe(el):
    """The element's motion in plain words."""
    if el["kind"] == "stream":
        return f"texture flows along the arrows at {el['speed']:g} px per frame ({el['speed'] * 20:g} px/s)"
    if el["kind"] == "spin":
        return f"flat disc rocks \u00b1{el['rock']:g}\u00b0 about its axis" if el["rock"] else \
            f"flat disc turns about its axis, {el['turns']:g} turn per loop"
    if el["kind"] == "swing":
        return f"rigid mesh swings \u00b1{el['deg']:g}\u00b0 about its pivot; phase {el['phase']:.2f}"
    if el["kind"] == "hover":
        return f"rigid mesh rises and sinks {el['px']:g} px; phase {el['phase']:.2f}"
    if el["kind"] == "cloth":
        return f"four bones top to bottom, each swings \u00b1{el['deg']:g}\u00b0 after the one above; phase {el['phase']:.2f}"
    if el["kind"] == "carry":
        if el.get("stands"):
            return f"stands on the floor, turns about its foot, follows the hand of priest {el['parent']}"
        s = f"moves with the hand of priest {el['parent']}, stays upright"
        return s + (f"; forearm swings \u00b1{el['lift']:g}\u00b0" if el["lift"] else "")
    if el["kind"] == "smoke":
        return "simulated gas: warm air rises from the " + ("flame, follows the candle" if el.get("of") else "flame or censer")
    parts = []
    if el.get("turn"):
        parts.append(f"head turn \u00b1{el['turn']:g}\u00b0")
    if el.get("nod"):
        parts.append(f"head nod {el['nod']:g}\u00b0")
    if el.get("tilt"):
        parts.append(f"head tilt \u00b1{el['tilt']:g}\u00b0")
    if el.get("sway"):
        parts.append(f"body lean \u00b1{el['sway']:g}\u00b0")
    if el.get("breathe"):
        parts.append(f"chest breathes {el['breathe']:g} %")
    if el.get("robe"):
        parts.append(f"robe \u00b1{el['robe']:g}\u00b0")
    return ", ".join(parts) + f"; phase {el['phase']:.2f}"


def arrow(img, a, b, c, both=True):
    """Arrow from a to b with a 14 px head; `both`: heads at both ends."""
    a, b = tuple(int(v) for v in a), tuple(int(v) for v in b)
    tip = 14 / max(math.dist(a, b), 1)
    for u, v in ((a, b), (b, a)) if both else ((a, b),):
        cv2.arrowedLine(img, u, v, (0, 0, 0), 7, cv2.LINE_AA, tipLength=tip)
        cv2.arrowedLine(img, u, v, c, 3, cv2.LINE_AA, tipLength=tip)


def draw_map(name):
    """Each moving element filled in its own colour and outlined, numbered;
    its bones in white (joints as dots, the bones that move ringed in the
    element's colour); flow arrows on streams; every flame marked F; every
    smoke source marked with the box its smoke is simulated in; a legend."""
    from PIL import Image, ImageDraw, ImageFont
    import actors as A
    plate = cv2.imread(os.path.join(ROOT, "wip", "scene3d", name + ".png"), cv2.IMREAD_COLOR).astype(np.float32)
    H, W = plate.shape[:2]
    lay, K, _, flames = A.layout(name)
    rig = {e["id"]: e for e in lay}
    seg = np.load(os.path.join(ROOT, "wip", "scene3d", name + "_seg.npz"))
    els = MAPS[name]
    mk = {e["id"]: seg[e["id"]] for e in els if e["kind"] != "smoke"}
    f = float(K[0, 0]) * W
    img = plate * 0.55
    colour, n = {}, 0
    for el in els:
        if el["kind"] == "carry":
            colour[el["id"]] = colour[el["parent"]]
        elif el["kind"] == "smoke" and el.get("of"):
            colour[el["id"]] = colour[el["of"]]
        else:
            colour[el["id"]], n = COLOURS[n % len(COLOURS)], n + 1
    yy, xx = np.mgrid[0:H, 0:W]
    for el in els:
        if el["id"] not in mk:
            continue
        m = mk[el["id"]].astype(np.float32)[..., None]
        if el["kind"] == "carry":                          # hatched: held by the priest of that colour
            m = m * (((xx + yy) // 6) % 2 == 0)[..., None]
        img = img * (1 - 0.45 * m) + np.array(colour[el["id"]], np.float32)[::-1] * 0.45 * m
    img = img.astype(np.uint8)
    for el in els:
        if el["id"] in mk:
            cs, _ = cv2.findContours(mk[el["id"]].astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(img, cs, -1, colour[el["id"]][::-1], 2, cv2.LINE_AA)
    pt = lambda j: (int(np.clip(j[0], 0, W - 1)), int(np.clip(j[1], 0, H - 1)))

    def ring(q, c, r=11):
        cv2.circle(img, pt(q), r, (0, 0, 0), 5, cv2.LINE_AA)
        cv2.circle(img, pt(q), r, c, 3, cv2.LINE_AA)

    tags = []
    for el in els:
        c = colour[el["id"]][::-1]
        if el["kind"] == "smoke":
            if el.get("of"):                                # the tip of the carried candle's flame, at its shown size
                fe = next(e for e in lay if e["kind"] == "flame" and e.get("owner") == el["of"])
                (wx, wy), (tx, ty) = fe["wick"], fe["tip"]
                x, y = wx + fe["scale"] * (tx - wx), wy + fe["scale"] * (ty - wy)
                z = float(fe["z"][int(wy), int(wx)])
            else:
                (x, y), z = A.source(el, flames, A.load(name)[0], f)
            w, h = 0.2 * f / z, 0.5 * f / z                 # the part of the box the smoke fills, in pixels
            for i in range(0, int(2 * (w + h)), 14):       # dashed box
                for a, b in (((x - w / 2 + i, y - h), (x - w / 2 + i + 7, y - h)),) if i < w else \
                        (((x - w / 2, y - h + i - w), (x - w / 2, y - h + i - w + 7)),
                         ((x + w / 2, y - h + i - w), (x + w / 2, y - h + i - w + 7))) if i < w + h else ():
                    cv2.line(img, pt(a), pt(b), c, 2, cv2.LINE_AA)
            arrow(img, (x, y - 6), (x, y - 0.5 * h), c, both=False)
            tags.append((el["id"], (x + w / 2 + 16, y - h + 20), c))
            continue
        ys, xs = np.nonzero(mk[el["id"]])
        cx, cy = float(xs.mean()), float(ys.mean())
        r = rig.get(el["id"])
        if r is not None and el["kind"] != "carry":
            for b in r["bones"]:
                cv2.line(img, pt(b[1]), pt(b[2]), (0, 0, 0), 6, cv2.LINE_AA)
                cv2.line(img, pt(b[1]), pt(b[2]), (255, 255, 255), 2, cv2.LINE_AA)
            for b in r["bones"]:
                for j in b[1:3]:
                    cv2.circle(img, pt(j), 5, (0, 0, 0), -1, cv2.LINE_AA)
                    cv2.circle(img, pt(j), 3, (255, 255, 255), -1, cv2.LINE_AA)
            for b in r["bones"]:
                if b[0] in r["moving"] and not b[0].startswith("f"):
                    ring(b[1], c)
        if el["kind"] == "priest":
            tags.append((el["id"], (r["joints"]["top"][0], ys.min() - 30), c))
        elif el["kind"] == "carry":
            tags.append((el["id"], (xs.max() + 28, ys.min() + 18), c))
        elif el["kind"] == "stream":
            for a, b in zip(el["line"][:-1], el["line"][1:]):
                arrow(img, a, b, c, both=False)
            (x0, y0), (x1, y1) = el["line"][:2]
            tags.append((el["id"], (x0 + 0.5 * (x1 - x0) + 34, y0 + 0.5 * (y1 - y0) - 30), c))
        elif el["kind"] == "spin":
            hub = el["pos"][0]
            rr = int(max(10, 0.3 * min(xs.max() - xs.min(), ys.max() - ys.min())))
            cv2.ellipse(img, pt(hub), (rr, rr), 0, 20, 320, (0, 0, 0), 7, cv2.LINE_AA)
            cv2.ellipse(img, pt(hub), (rr, rr), 0, 20, 320, c, 3, cv2.LINE_AA)
            arrow(img, (hub[0] + rr * 0.77, hub[1] - rr * 0.64 - 1), (hub[0] + rr * 0.94, hub[1] + rr * 0.34), c, both=False)
            ring(hub, c)
            tags.append((el["id"], (cx, ys.min() + 26), c))
        elif el["kind"] == "hover":
            arrow(img, (cx, cy - 20), (cx, cy + 20), c)
            tags.append((el["id"], (cx, ys.min() + 26), c))
        elif el["kind"] == "swing":
            arrow(img, (cx - 18, cy), (cx + 18, cy), c)
            tags.append((el["id"], (xs.max() + 26, cy), c))
        else:
            tags.append((el["id"], (cx, ys.min() + 26), c))
    for fl in flames:                                        # every flame: F and a ring; a small dot when it has no mesh
        x, y = fl["tip"]
        if fl["mesh"]:
            cv2.circle(img, pt(fl["wick"]), 9, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.circle(img, pt(fl["wick"]), 9, (40, 220, 255), 2, cv2.LINE_AA)
            cv2.putText(img, "F", (int(x) - 6, max(int(y) - 8, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 4, cv2.LINE_AA)
            cv2.putText(img, "F", (int(x) - 6, max(int(y) - 8, 14)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 220, 255), 1, cv2.LINE_AA)
        else:
            cv2.circle(img, pt(fl["wick"]), 4, (40, 220, 255), 1, cv2.LINE_AA)
    for tid, (x, y), c in tags:
        x, y = int(np.clip(x, 24, W - 24)), int(np.clip(y, 24, H - 24))
        cv2.circle(img, (x, y), 21, (0, 0, 0), -1, cv2.LINE_AA)
        cv2.circle(img, (x, y), 21, c, 3, cv2.LINE_AA)
        fs = 0.75 if len(tid) < 2 else 0.6
        (tw, th), _ = cv2.getTextSize(tid, cv2.FONT_HERSHEY_SIMPLEX, fs, 2)
        cv2.putText(img, tid, (x - tw // 2, y + th // 2), cv2.FONT_HERSHEY_SIMPLEX, fs, c, 2, cv2.LINE_AA)
    rows = (len(els) + 2) // 2
    pane = Image.new("RGB", (W, 70 + 38 * rows), (16, 16, 16))
    d = ImageDraw.Draw(pane)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 22)
    fr = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 19)
    d.text((20, 14), f"{name}: moving elements. White lines: bones; ringed joints and pivots rotate. Angles are peak "
           "rotations; one cycle per 4 s loop. Hatched: held by the priest of that colour. Dashed box: simulated smoke.",
           font=fr, fill=(220, 220, 220))
    for i, el in enumerate(els):
        x, y = 20 + (i // rows) * (W // 2), 56 + (i % rows) * 38
        c = colour[el["id"]]
        d.rectangle((x, y + 4, x + 22, y + 26), fill=c)
        d.text((x + 34, y + 2), el["id"], font=fb, fill=c)
        d.text((x + 82, y + 2), el["who"], font=fb, fill=(235, 235, 235))
        d.text((x + 380, y + 4), describe(el), font=fr, fill=(200, 200, 200))
    x, y = 20 + (len(els) // rows) * (W // 2), 56 + (len(els) % rows) * 38
    d.rectangle((x, y + 4, x + 22, y + 26), fill=(255, 220, 40))
    d.text((x + 34, y + 2), "F", font=fb, fill=(255, 220, 40))
    nm = sum(fl["mesh"] for fl in flames)
    d.text((x + 82, y + 2), f"{len(flames)} flames", font=fb, fill=(235, 235, 235))
    d.text((x + 380, y + 4), f"{nm} with two bones: lean and stretch with the draft and the candle's motion; all change their light",
           font=fr, fill=(200, 200, 200))
    top = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    out = Image.new("RGB", (W, H + pane.height))
    out.paste(top, (0, 0))
    out.paste(pane, (0, H))
    path = os.path.join(ROOT, "wip", "preview", f"motion-{name}.png")
    out.save(path)
    print("wrote", path)


def plan(name):
    """Where things are, checked from above. Draws every actor mesh as seen
    from the top (x across, depth up the page, 100 px per metre), every
    flame and every smoke source with the box its smoke is simulated in.
    Prints, per held thing, its depth against the chest of the priest that
    holds it, and per smoke source its distance from the flame it rises
    from. A held thing more than 0.8 m from its priest's chest, or smoke
    more than 5 cm from its flame, is flagged."""
    import json
    stem = os.path.join(ROOT, "wip", "scene3d", name)
    d = np.load(stem + "_actors.npz")
    meta = json.loads(str(d["meta"]))
    src = json.load(open(stem + "_sources.json")) if os.path.exists(stem + "_sources.json") else []
    centre = {a["id"]: np.median(d[a["id"] + "/V"], 0) for a in meta}
    xs = np.concatenate([d[a["id"] + "/V"][::40, 0] for a in meta])
    ys = np.concatenate([d[a["id"] + "/V"][::40, 1] for a in meta])
    x0, x1, y0, y1 = xs.min() - 0.5, xs.max() + 0.5, 0.0, min(ys.max() + 0.5, 30.0)
    S = 100
    W, H = int((x1 - x0) * S), int((y1 - y0) * S)
    img = np.full((H, W, 3), 24, np.uint8)
    P = lambda x, y: (int((x - x0) * S), int(H - (y - y0) * S))
    for m in range(int(y0), int(y1) + 1):
        cv2.line(img, P(x0, m), P(x1, m), (60, 60, 60), 1)
        cv2.putText(img, f"{m} m", (4, P(x0, m)[1] - 3), 0, 0.45, (150, 150, 150), 1, cv2.LINE_AA)
    cv2.circle(img, P(0, 0.02), 6, (255, 255, 255), -1)
    cv2.putText(img, "camera", (P(0, 0)[0] + 10, H - 6), 0, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    col = {}
    for i, a in enumerate(a for a in meta if a["kind"] != "carry"):
        col[a["id"]] = COLOURS[i % len(COLOURS)][::-1]
    for a in meta:
        c = col[a["parent"]] if a["kind"] == "carry" else col[a["id"]]
        V = d[a["id"] + "/V"][::25]
        for x, y in V[:, :2]:
            if y < y1:
                cv2.circle(img, P(x, y), 1, c, -1)
    for a in meta:
        if a["kind"] in ("priest", "carry", "spin", "swing", "hover"):
            x, y = centre[a["id"]][:2]
            cv2.putText(img, a["id"], (P(x, y)[0] + 4, P(x, y)[1] - 4), 0, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
    flame_at = {}
    for a in meta:                                           # flames: the head of their first bone
        if a["kind"] == "flame" and "parent" in a:           # on a carried candle: listed under the candle's id
            par = next(p for p in meta if p["id"] == a["parent"])
            flame_at[a["owner"]] = np.array(next(b[1] for b in par["bones"] if b[0] == a["names"][0]))
        elif a["kind"] == "flame":
            flame_at[a["id"]] = np.array(a["bones"][0][1])
    for k, p in flame_at.items():
        cv2.drawMarker(img, P(p[0], p[1]), (40, 220, 255), cv2.MARKER_TILTED_CROSS, 10, 2)
    sources = json.loads(str(d["sources"]))
    print(f"{name}: depths in metres from the camera")
    print(f"{'held thing':>12} {'its depth':>10} {'priest chest':>13} {'difference':>11}")
    for a in meta:
        if a["kind"] == "carry":
            par = next(p for p in meta if p["id"] == a["parent"])
            chest = next(b[1] for b in par["bones"] if b[0] == "chest")[1]
            z = float(centre[a["id"]][1])
            print(f"{a['id']:>12} {z:10.2f} {chest:13.2f} {z - chest:+11.2f}" + ("   FLAG" if abs(z - chest) > 0.8 else ""))
    print(f"{'smoke':>12} {'its depth':>10} {'flame depth':>13} {'distance':>11}")
    for s_ in src:
        p = np.array(s_["path"]).mean(0)
        cv2.rectangle(img, P(p[0] - 0.2, p[1] + 0.2), P(p[0] + 0.2, p[1] - 0.2), (255, 255, 255), 1)
        cv2.putText(img, s_["id"], (P(p[0] + 0.2, p[1] + 0.2)[0] + 3, P(p[0], p[1] + 0.2)[1] + 4), 0, 0.42, (255, 255, 255), 1, cv2.LINE_AA)
        of = next((q.get("of") for q in sources if q["id"] == s_["id"]), None)
        if of in flame_at:                                   # the source sits at the flame's tip
            fpos = flame_at[of]
            dist = float(np.hypot(p[0] - fpos[0], p[1] - fpos[1]))
            print(f"{s_['id']:>12} {p[1]:10.2f} {fpos[1]:13.2f} {dist:11.3f}" + ("   FLAG" if dist > 0.05 else ""))
        else:
            print(f"{s_['id']:>12} {p[1]:10.2f} {'fixed point':>13}")
    path = os.path.join(ROOT, "wip", "preview", f"plan-{name}.png")
    cv2.imwrite(path, img)
    print("wrote", path)


def proof(name):
    """Measured motion in the rendered frames wip/frames-<name>: optical
    flow (Farneback) from frame 0 to every frame, averaged over a priest's
    head or a carried thing, less the flow of a ring around the element
    (the camera's drift). Reported in GIF pixels: the largest excursion, and
    r, the share of the motion's timing that the commanded bone rotations
    explain. A stream: the mean flow from each frame to the next along its
    line. Also writes the head crops at four loop phases,
    wip/preview/rig-<name>-heads.png."""
    import actors as A
    d = os.path.join(ROOT, "wip", f"frames-{name}")
    full = [cv2.imread(os.path.join(d, f"f{k:03d}.png")) for k in range(FRAMES)]
    h, w = full[0].shape[:2]
    g = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in full]
    flows = [cv2.calcOpticalFlowFarneback(g[0], g[k], None, 0.5, 4, 21, 5, 7, 1.5, 0) for k in range(FRAMES)]
    els = A.layout(name)[0]
    by = {e["id"]: e for e in els}
    small = lambda m: cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST) > 0
    t = np.arange(FRAMES) / FRAMES
    gif = 1140 / w
    body = lambda e: {"sway": np.sin(TAU * (t + e["phase"])), "breathe": 0.5 * (1 - np.cos(TAU * (t + e["phase"] + 0.1)))}
    print(f"{'id':>4}  {'element':28s} {'part':8s} {'excursion':>10s}  {'r':>5s}  commanded")
    crops = []
    for el in els:
        if el["kind"] == "priest":
            sel = el["mask"] & (np.arange(el["mask"].shape[0])[:, None] < el["joints"]["neck"][1])
            ph = t + el["phase"]
            curves = {"turn": np.sin(TAU * (ph + 0.15)), "nod": 0.5 * (1 - np.cos(TAU * (ph + 0.25))),
                      "tilt": np.sin(TAU * (ph + 0.4)), "sway": np.sin(TAU * ph)}
            cmd = {k: v for k, v in {**curves, **body(el)}.items() if el.get(k)}
            part = "head"
        elif el["kind"] == "carry":
            sel = el["mask"]
            pa = by[el["parent"]]
            cmd = {"lift": np.sin(TAU * (t + pa["phase"] + 0.2))} if el["lift"] else {}
            cmd.update({"parent " + k: v for k, v in body(pa).items() if pa.get(k)})
            part = "all"
        else:
            sel, cmd, part = el["mask"], {}, el["kind"]
        ms = cv2.erode(small(sel).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        if ms.sum() < 6:
            ms = small(sel)
        sm = small(el["mask"]).astype(np.uint8)
        rg = (cv2.dilate(sm, np.ones((41, 41), np.uint8)) > 0) & ~(cv2.dilate(sm, np.ones((17, 17), np.uint8)) > 0)
        v = np.array([f[ms].mean(0) - f[rg].mean(0) for f in flows])
        v = v - v.mean(0)
        exc = float(np.hypot(v[:, 0], v[:, 1]).max() * 2 * gif)
        A_ = np.stack(list(cmd.values()) + [np.ones(FRAMES)], 1) if cmd else None
        r = float("nan")
        if cmd:                                              # share of the motion explained by the commanded curves
            fit = A_ @ np.linalg.lstsq(A_, v, rcond=None)[0]
            r = float(np.sqrt(max(0.0, 1 - ((v - fit) ** 2).sum() / max((v ** 2).sum(), 1e-9))))
        print(f"{el['id']:>4}  {el.get('who', ''):28s} {part:8s} {exc:7.2f} px  {r:5.2f}  "
              + (", ".join(cmd) or "-"))
        if el["kind"] == "priest":
            ys, xs = np.nonzero(small(sel))
            cx, cy, s = int(xs.mean()), int(ys.mean()), int(max(xs.max() - xs.min(), ys.max() - ys.min()) * 0.75 + 12)
            x0, y0 = int(np.clip(cx - s, 0, w - 2 * s)), int(np.clip(cy - s, 0, h - 2 * s))
            row = [cv2.resize(full[k][y0:y0 + 2 * s, x0:x0 + 2 * s], (220, 220), interpolation=cv2.INTER_CUBIC)
                   for k in (0, 20, 40, 60)]
            row = np.concatenate(row, 1)
            cv2.putText(row, f"{el['id']}  frames 0 20 40 60", (6, 20), 0, 0.55, (0, 255, 255), 2)
            crops.append(row)
    mk = masks(name)
    for el in MAPS[name]:
        if el["kind"] != "stream":
            continue
        ms = cv2.erode(small(mk[el["id"]]).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        (x0, y0), (x1, y1) = el["line"][0], el["line"][-1]
        ux, uy = (x1 - x0) / math.hypot(x1 - x0, y1 - y0), (y1 - y0) / math.hypot(x1 - x0, y1 - y0)
        along = [float((f[..., 0][ms] * ux + f[..., 1][ms] * uy).mean()) for f in
                 (cv2.calcOpticalFlowFarneback(g[k], g[k + 1], None, 0.5, 4, 15, 5, 5, 1.1, 0) for k in range(0, FRAMES - 1, 4))]
        print(f"{el['id']:>4}  {el['who']:28s} {'stream':8s} {np.mean(along) * gif:5.2f} px per frame downstream; "
              f"commanded {el['speed'] * 1140 / 2432:.2f}")
    cols = 2 if len(crops) > 6 else 1
    crops += [np.zeros_like(crops[0])] * (-len(crops) % cols)
    sheet = np.concatenate([np.concatenate(crops[i::cols], 0) for i in range(cols)], 1)
    path = os.path.join(ROOT, "wip", "preview", f"rig-{name}-heads.png")
    cv2.imwrite(path, sheet)
    print("wrote", path)


if __name__ == "__main__":
    cmd, name = sys.argv[1], sys.argv[2]
    {"map": draw_map, "flow": write_flow, "proof": proof, "plan": plan}[cmd](name)
