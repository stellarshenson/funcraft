"""Paint a figure model by region, as design-blender prescribes for a fused
sculpt: every face gets a material slot from rules on its centre and normal,
measured on orthographic clay views of the model (front +Y, +X on the image
left). The rules return one class per face; the scene maps classes to
materials.
"""
import numpy as np

SKIN, CLOTH, MACHINE, LEATHER, BRASS, RUBBER = 0, 1, 2, 3, 4, 5


def faces(me):
    n = len(me.polygons)
    c = np.zeros(n * 3); me.polygons.foreach_get("center", c)
    nr = np.zeros(n * 3); me.polygons.foreach_get("normal", nr)
    return c.reshape(-1, 3), nr.reshape(-1, 3)


def servitor(me):
    """johnthemaker's servitor at 2.0 tall: a bald human head (z 1.58-1.85,
    face towards +Y), a human arm and hand on -X, a claw arm on +X, a
    backpack behind (y down to -0.53), a torn tabard in front and a long
    cloak behind below the belt (z ~1.08), mechanical legs, sandalled feet."""
    c, nr = faces(me)
    x, y, z = c.T
    cls = np.full(len(c), MACHINE)
    head = np.linalg.norm((c - (-0.01, 0.04, 1.71)) * (1, 1, 0.85), axis=1) < 0.155
    neck = (np.abs(x) < 0.06) & (y > 0.02) & (z > 1.45) & (z < 1.60)
    arm = (x < -0.25) & (z > 0.76) & (z < 1.28) & ~((z > 0.97) & (z < 1.10))    # the bracer stays metal
    toes = (z < 0.07) & (y > 0.10)
    cls[head | neck | arm | toes] = SKIN
    tabard = (np.abs(x) < np.where(z < 0.65, 0.11, 0.17)) & (y > -0.06) & (z > 0.36) & (z < 1.06)
    chest = (np.abs(x) < 0.19) & (y > -0.08) & (z > 1.12) & (z < 1.48) & (nr[:, 1] > 0.2)
    cloak = (y < -0.10) & (z > 0.18) & (z < 1.07)
    skirt = (x > -0.29) & (x < np.where(z < 0.75, 0.18, 0.24)) & (y > -0.12) & (y < 0.24) & (z > 0.55) & (z < 1.05)
    legs = (np.abs(x) > 0.04) & (np.abs(x) < 0.26) & (y > -0.22) & (z < 0.62)
    cls[(tabard | chest | cloak | skirt) & ~(legs & ~tabard)] = CLOTH
    belt = (z > 1.055) & (z < 1.125) & (np.abs(x) < 0.2) & (y > -0.2) & (y < 0.1)
    cls[belt] = LEATHER
    fins = (y < -0.33) & (z > 1.40) & (z < 1.68) & (np.abs(x) > 0.20)         # the backpack's radiator
    antenna = (z > 1.80) & (y < -0.18)
    bracer = (x < -0.25) & (z > 0.97) & (z < 1.10)
    plaque = (np.abs(x) < 0.07) & (z > 1.28) & (z < 1.43) & (y > 0.02)         # the skull plate on the chest
    # the head's implants: a ringed disc over each ear, and the tubes that
    # hang from cheeks and ears to the chest, behind the face's plane
    ears = np.linalg.norm(c - np.stack([np.sign(x) * 0.118, np.full_like(x, -0.005), np.full_like(x, 1.672)], 1), axis=1) < 0.05
    tubes = (z > 1.44) & (z < 1.635) & (y < 0.045) & (y > -0.06) & (np.abs(x) > 0.035) & (np.abs(x) < 0.13)
    crown = np.linalg.norm(c - (-0.095, 0.02, 1.80), axis=1) < 0.045       # the ringed implant on the crown
    cls[tubes & (cls != CLOTH)] = RUBBER
    cls[fins | antenna | bracer | plaque | ears | crown] = BRASS
    return cls


def _near_segment(c, a, b, r):
    a, b = np.asarray(a, float), np.asarray(b, float)
    t = np.clip(((c - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
    return np.linalg.norm(c - (a + t[:, None] * (b - a)), axis=1) < r


def magus(me):
    """The Magus at 2.7 tall: robed, body centred near x -0.3 (the loader
    centres the whole model, staff included), a mechanical skull mask and
    crown above z 1.6, claw hands at z 1.1-1.45, a staff held on +X running
    from (0.0, 0.38) to (0.64, 2.52) in (x, z) at y -0.1 with an axe blade
    and a cog finial at its top."""
    c, nr = faces(me)
    x, y, z = c.T
    cls = np.full(len(c), CLOTH)
    staff = _near_segment(c, (0.0, -0.1, 0.30), (0.66, -0.1, 2.62), 0.075)
    cls[staff] = MACHINE
    cls[staff & (z > 1.80)] = BRASS                                       # axe blade and cog finial
    cls[(z > 1.80) & (x > 0.15)] = BRASS
    head = (z > 1.60) & (x < 0.05)
    cls[head] = MACHINE                                                    # the skull mask
    cls[head & (z > 1.74)] = BRASS                                         # the crown
    hands = ((x < -0.62) | ((x > 0.2) & (x < 0.5))) & (z > 1.05) & (z < 1.48) & ~staff
    cls[hands] = MACHINE
    return cls


def shock_priest(me):
    """The shock priest at 2.2 tall, one fused sculpt, symmetric about x = 0:
    a riveted dome helmet (z > 1.62) under a spiked halo, armoured shoulders
    and arms (z 1.2-1.62), a belt (z 1.0-1.15) with a cog-skull buckle and
    side canisters, the robe below, sandals, a pack and rod on the back."""
    c, nr = faces(me)
    x, y, z = c.T
    cls = np.full(len(c), MACHINE)
    cls[(z > 0.12) & (z < 1.0)] = CLOTH
    cls[(z > 1.0) & (z < 1.16) & (np.abs(x) < 0.30)] = LEATHER
    charms = (np.abs(x) < 0.13) & (z > 0.45) & (z < 1.0) & (y > 0.12)
    cls[charms] = MACHINE
    cls[(np.abs(x) < 0.07) & (z > 0.98) & (z < 1.22) & (y > 0.05)] = BRASS   # the cog-skull buckle
    cls[(np.abs(x) > 0.28) & (z > 1.02) & (z < 1.2) & (np.abs(x) < 0.45)] = BRASS   # the canisters
    halo = (z > 1.75) & ((np.abs(x) > 0.13) | (z > 1.97))
    cls[halo] = BRASS
    cls[(z < 0.12)] = LEATHER
    cls[(y < -0.15) & (z > 1.0)] = MACHINE                                  # the pack
    return cls
