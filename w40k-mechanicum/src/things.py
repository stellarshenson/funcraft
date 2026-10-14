"""A scene as a list of things. DESIGN.md section 5.13 states the principle; this file holds what every scene needs
to follow it.

A picture is not layered by the measured depth of each pixel. It is a list of things, and each thing has

- a mask: the pixels that are this thing, and no other thing's
- one surface: one depth, or one depth for each column of the picture (a wall that runs into the picture)
- a support: the thing it stands on, the edge of the picture it leaves through, or the far side
- an order: the things and the added elements (a crowd, a fire) it stands before or behind

    build(plate, depth, valid, things, given)   masks, surfaces and the faults of the list
    chart(plate, made, path)                    the map of things for the owner's review
    ground(plate, depth, valid, made, whole)    the far side and the wide things as one surface, without the other things
    covered(made, deep, whole, held)            faults of the ground: a thing or a cloth with ground before it
    planes(plate, made, skip)                   every other thing that stays, as a picture of its own at its depth

A thing is a dict:

    id, name    a short code and what the thing is, in plain words
    boxes       where it is cut from the plate: (x0, y0, x1, y1) each. Its pixels are those of a box that differ by
                more than `limit` from the colours round the whole thing carried into it; limit 0 takes the whole box.
                `dark`: only pixels that are darker than those colours, for a mast before bright dust or smoke
    without     the name of a mask in `given` whose pixels are not this thing's (the flame over a bowl)
    mirror      True for a thing that is the same on both sides and half hidden in the plate: its mask and its picture
                are made whole from the side that shows
    rods        boxes in which the thing is a straight rod from the upper to the lower edge. Where the plate does not
                show it there, it goes on as it is in the nearest rows that show it
    mask        instead of boxes: the name of a mask in `given`
    surface     "flat": one depth. Or the name of a depth by column in `given`
    on          the id of the thing it stands on, "frame" when it leaves the picture through an edge, "far" when it
                belongs to the far side of the picture, "floor" when it stands on the floor of the scene behind a
                thing that hides its foot (`behind`) or among the figures of an added crowd (`among`).
                A thing that stands on a thing has the depth of that thing where it stands: the measured depth of its
                own pixels is only compared with it. `feet`, the columns where it stands when there are several, give
                it a depth that goes evenly from one foot to the next
    before      what it stands before: ids of things, or names in `given` of an added element (a crowd), which is
                there as its nearest and its farthest depth by column. A thing that is behind its own support
                stands on the floor behind it, 3 % deeper, with its foot hidden
    behind      what it stands behind: the same
    among       the name in `given` of an added crowd among whose figures it stands on the floor: its depth lies
                between the nearest and the farthest figure in its columns. The figures before it hide its foot
    at          instead of boxes or mask, for a thing the scene builds and the plate does not show: its place
    keep        True; False for a thing that is taken out of the picture; None while the owner has not decided
    built       True for a thing that stays and that the scene builds as an object of its own (a post as a round
                rod, src/rods.py): its pixels are taken out of the ground, and no picture of it is cut from the plate
    holds       the added elements that are tied to it: a cloth, a fire. A thing on the far side takes the measured
                depth of what it holds, when `given` has it under that name
    beyond      "left" or "right", for a thin thing that stands before the edge of a far thing (a post before the edge
                of a tower): the far side of that side goes on behind it, colours and depth. Without it the colours of
                both sides are carried in evenly, and a camera that moves shows a soft band beside the thing

The list is in order from the nearest thing to the farthest: where two masks meet, the pixel is the nearer thing's.
What no thing takes is the far side, one thing of its own.
"""
import numpy as np
import cv2


def fill(colour, known):
    """The colours of the known pixels carried smoothly into the rest: each level of a pyramid holds the mean of the
    known pixels under it, and a pixel that is not known takes the colour of the level over it."""
    levels = [(colour * known[..., None], known.astype(np.float32))]
    while min(levels[-1][1].shape) > 2:
        c, k = levels[-1]
        size = (max(k.shape[1] // 2, 1), max(k.shape[0] // 2, 1))
        levels.append((cv2.resize(c, size, interpolation=cv2.INTER_AREA).reshape(size[1], size[0], -1), cv2.resize(k, size, interpolation=cv2.INTER_AREA)))
    c, k = levels[-1]
    out = np.ones_like(c) * c.sum((0, 1)) / max(k.sum(), 1e-6)
    for c, k in reversed(levels):
        out = cv2.resize(out, (k.shape[1], k.shape[0]), interpolation=cv2.INTER_LINEAR).reshape(k.shape[0], k.shape[1], -1)
        out = out * (1 - k[..., None]) + c
    return out


def cut(colour, thing, given, free):
    """The pixels of one thing among the pixels that no nearer thing has taken."""
    if "mask" in thing:
        return given[thing["mask"]] & free
    boxes = np.zeros(colour.shape[:2], bool)
    for x0, y0, x1, y1 in thing["boxes"]:
        boxes[y0:y1, x0:x1] = True
    out, limit = boxes, thing.get("limit", 0.05)
    if limit:                                                             # against the colours round the whole thing, without the things before it
        far = fill(colour, ~boxes & free) - colour
        out = boxes & ((far.mean(-1) if thing.get("dark") else np.abs(far).max(-1)) > limit)
    out = cv2.morphologyEx(out.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)).astype(bool) & free
    return out & ~given[thing["without"]] if "without" in thing else out


def build(plate, depth, valid, things, given):
    """The masks and surfaces of the things, and the faults of the list.

    plate: the picture (rows, columns, 3; 0 to 255). depth, valid: its measured depth and where that is known.
    given: masks and depths by column that the scene has from elsewhere, and under the name of what a thing holds
    the measured depth of that. Returns a dict: `label` (the number of the
    thing of every pixel, from 1 in list order; 0 is the far side), `things` (the list, each with `pixels`, `box`,
    `depth` by column, `measured`, `moved`), `faults` (what contradicts the list) and `notes` (what the build
    changed to keep the stated order)."""
    colour = plate.astype(np.float32) / 255
    H, W = colour.shape[:2]
    label, faults, notes, made = np.zeros((H, W), np.uint8), [], [], []
    named = {t["id"] for t in things}
    for n, thing in enumerate(things, 1):
        t = dict(thing)
        if "at" in t:                                                      # built by the scene: it has a place and no pixels of the plate
            t.update(pixels=0, box=tuple(t["at"]), measured=None, depth=np.full(W, np.nan, np.float32), moved=None)
            made.append(t)
            continue
        own = cut(colour, t, given, label == 0)
        if t.get("mirror") and own.any():                                 # the same on both sides, and the plate hides a part of one side: it is whole
            t["drawn"], cols = own, np.flatnonzero(own.any(0))
            flip = np.zeros_like(own)
            flip[:, cols[0]:cols[-1] + 1] = own[:, cols[0]:cols[-1] + 1][:, ::-1]
            own = (own | flip) & (label == 0)
        label[own] = n
        ys, xs = np.nonzero(own)
        if len(xs) < 12:
            faults.append(f"{t['id']}: {len(xs)} pixels found; the boxes do not hold the thing")
            t.update(pixels=len(xs), box=None, measured=None, depth=None, moved=None)
            made.append(t)
            continue
        t.update(pixels=len(xs), box=(int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1))
        known = own & valid
        t["measured"] = float(np.median(depth[known])) if known.any() else None
        if known.any():
            t["spread"] = float((np.quantile(depth[known], 0.9) - np.quantile(depth[known], 0.1)) / t["measured"])
        held = [float(given[name]) for name in t.get("holds", []) if name in given]
        if held and t.get("on") not in named:                             # a thin thing is measured too deep, with what lies behind it; the wide surface it holds is not
            notes.append(f"{t['id']}: measured at {t['measured'] or float('nan'):.1f} m; what it holds is wider and is measured at {held[0]:.1f} m, and it takes that depth")
            t["measured"] = held[0]
        made.append(t)
    by = {t["id"]: t for t in made}
    # one surface for each thing: a depth by column, the same in every row of the thing
    for t in made:
        if not t["pixels"] or t.get("keep") is False:
            continue
        cols = np.arange(t["box"][0], t["box"][2])
        t["depth"] = np.full(W, np.nan, np.float32)
        t["set"] = False
        if t.get("surface", "flat") == "flat":
            if t["measured"] is None:
                faults.append(f"{t['id']}: no measured depth under its pixels")
                continue
            t["depth"][cols] = t["measured"]
        else:
            t["depth"][cols] = given[t["surface"]][cols]
    def order(some):
        """The stated order decides: a surface that contradicts it is moved, and the move is noted."""
        for t in some:
            if t.get("depth") is None:
                continue
            cols = np.arange(t["box"][0], t["box"][2])
            for word, sign in (("before", -1), ("behind", 1)):
                for other in t.get(word, []):
                    if other in by:
                        if by[other].get("depth") is None:
                            continue
                        limit = by[other]["depth"][cols]
                    else:
                        limit = given[other][0 if sign < 0 else 1][cols]
                    wrong = np.isfinite(limit) & (sign * (limit - t["depth"][cols]) > 0)
                    if wrong.any():
                        was = float(np.nanmedian(t["depth"][cols]))
                        if t.get("surface", "flat") == "flat" and not t.get("feet"):
                            t["depth"][cols] = (0.97 * np.nanmin(limit[wrong]) if sign < 0 else 1.03 * np.nanmax(limit[wrong]))
                        else:
                            t["depth"][cols] = np.where(wrong, limit * (0.97 if sign < 0 else 1.03), t["depth"][cols])
                        t["moved"] = (t["moved"][0] if t.get("moved") else was, float(np.nanmedian(t["depth"][cols])))
                        notes.append(f"{t['id']}: measured at {was:.1f} m, set to {t['moved'][1]:.1f} m to stand {word} {other}")

    order([t for t in made if t.get("on") not in by])                 # first the things that stand on no other thing: what stands on one takes its depth as the order leaves it
    # a thing that stands on a thing has that thing's depth where it stands; a support is set before what stands on it
    waits = [(n, t) for n, t in enumerate(made, 1) if t.get("depth") is not None and t.get("on") in by]
    for _ in range(len(made)):
        for n, t in list(waits):
            on = by[t["on"]]
            if on.get("depth") is None or (on.get("on") in by and any(on is w for _, w in waits)):
                continue
            waits.remove((n, t))
            own = label == n
            low = own[max(t["box"][3] - 6, 0):t["box"][3]].any(0) if t["pixels"] else np.zeros(W, bool)
            feet = t.get("feet") or [int(np.median(np.flatnonzero(low))) if low.any() else (t["box"][0] + t["box"][2]) // 2]
            at = np.array([float(on["depth"][x]) for x in feet])
            if not np.isfinite(at).all():
                faults.append(f"{t['id']}: stands on {t['on']} at column {feet}, where {t['on']} is not")
                continue
            cols = np.arange(t["box"][0], t["box"][2])
            was = float(np.nanmedian(t["depth"][cols])) if t["pixels"] else None
            t["stood"] = (feet, at)
            back = t["on"] in t.get("behind", [])                         # it stands behind its support, on the floor there: its foot is hidden
            t["depth"][cols] = (1.03 if back else 1.0) * (np.interp(cols, feet, at) if len(feet) > 1 else at[0])
            if was is not None or back:
                t["moved"] = (was, float(np.nanmedian(t["depth"][cols])))
                notes.append(f"{t['id']}: " + (f"measured at {was:.1f} m; " if was is not None else "") + f"stands {'behind' if back else 'on'} {t['on']}, which is "
                             f"{' and '.join(f'{v:.1f}' for v in at)} m deep there, and takes {'3 % more than ' if back else ''}that depth")
    order(made)
    for t in made:                                                        # a thing still has the depth of its support where it stands
        if t.get("stood") is not None and by[t["on"]].get("depth") is not None:
            there = np.array([float(by[t["on"]]["depth"][x]) for x in t["stood"][0]])
            if (np.abs(there - t["stood"][1]) > 1e-3 * there).any():
                faults.append(f"{t['id']}: stands on {t['on']}, and the stated order moved {t['on']} to another depth after that")
    for t in made:                                                        # and it is checked once more, whole
        if t.get("depth") is None:
            continue
        cols = np.arange(t["box"][0], t["box"][2])
        for word, sign in (("before", -1), ("behind", 1)):
            for other in t.get(word, []):
                if other in by:
                    limit = by[other]["depth"][cols] if by[other].get("depth") is not None else np.full(len(cols), np.nan)
                else:
                    limit = given[other][0 if sign < 0 else 1][cols]
                if (np.isfinite(limit) & (sign * (limit - t["depth"][cols]) > 1e-3)).any():
                    faults.append(f"{t['id']}: cannot stand {word} {other} and keep its other relations")
    # every thing that stays is in one piece, with its rods whole
    for n, t in enumerate(made, 1):
        if not t["pixels"] or t.get("keep") is False or "mask" in t:
            continue
        whole = label == n
        for x0, y0, x1, y1 in t.get("rods", []):
            whole[y0:y1, x0:x1] = True
        sizes = cv2.connectedComponentsWithStats(cv2.morphologyEx(whole.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)), connectivity=8)[2][1:, cv2.CC_STAT_AREA]
        pieces = int((sizes >= 0.02 * sizes.sum()).sum())
        if pieces > 1:
            faults.append(f"{t['id']}: is in {pieces} pieces; the list does not say where it goes on between them (rods)")
    # every thing that stays has a support
    edge = np.zeros((H, W), bool)
    edge[0], edge[-1], edge[:, 0], edge[:, -1] = True, True, True, True
    for n, t in enumerate(made, 1):
        if not t["pixels"] or t.get("keep") is False:
            continue
        own, on = label == n, t.get("on")
        if on is None:
            faults.append(f"{t['id']}: stands on nothing; the list names no support")
        elif on == "frame":
            if not (own & edge).any():
                faults.append(f"{t['id']}: is said to leave the picture, and touches no edge of it")
        elif on in by:
            if not by[on]["pixels"]:                                      # a built support: its place is under the thing
                x0, y0, x1, y1 = by[on]["box"]
                if not own[max(y0 - 6, 0):y1, max(x0 - 12, 0):x1 + 12].any():
                    faults.append(f"{t['id']}: is said to stand on {on}, and no pixel of it is over the place of {on}")
                continue
            under = cv2.dilate(own.astype(np.uint8), np.ones((13, 9), np.uint8)) > 0
            support = label == (made.index(by[on]) + 1)
            if not (under & support).any():
                faults.append(f"{t['id']}: is said to stand on {on}, and no pixel of it is within 6 pixels of {on}")
        elif on == "floor" and "among" in t:                              # it stands on the floor among the figures of a crowd
            near, far = (limit[np.arange(t["box"][0], t["box"][2])] for limit in given[t["among"]])
            deep = t["depth"][np.arange(t["box"][0], t["box"][2])]
            if not ((deep >= near) & (deep <= far)).all():
                faults.append(f"{t['id']}: is said to stand among {t['among']}, whose figures are {np.nanmin(near):.1f} to {np.nanmax(far):.1f} m deep in its columns, at {np.nanmedian(deep):.1f} m")
        elif on == "floor":                                               # it stands on the floor behind a thing that hides its foot
            hides = [made.index(by[b]) + 1 for b in t.get("behind", []) if b in by]
            whole = own.copy()
            for x0, y0, x1, y1 in t.get("rods", []):
                whole[y0:y1, x0:x1] = True
            if not hides:
                faults.append(f"{t['id']}: stands on the floor, and the list does not say what hides its foot (behind)")
            elif not (cv2.dilate(whole.astype(np.uint8), np.ones((13, 9), np.uint8)) > 0)[np.isin(label, hides)].any():
                faults.append(f"{t['id']}: is said to stand on the floor behind {', '.join(t['behind'])}, and it does not reach down to it")
        elif on != "far":
            faults.append(f"{t['id']}: its support {on} is not in the list")
    for t in made:
        if t.get("spread") is not None and t.get("surface", "flat") == "flat" and t["spread"] > 0.4 and t.get("keep") is not False:
            notes.append(f"{t['id']}: the measured depth of its pixels differs by {t['spread']:.0%}; it gets the one depth {np.nanmedian(t['depth']):.1f} m")
    return dict(label=label, things=made, faults=faults, notes=notes)


def chart(plate, made, path, fires=(), zoom=()):
    """The map of things for the owner: the picture with every thing outlined and numbered, the same for each box of
    `zoom` enlarged twice, and the list with depth, support and order under it. Green: stays. Red: is taken out.
    Yellow: the owner decides. Blue: the part of the picture behind a crowd. White: built by the scene, as an object."""
    from PIL import Image, ImageDraw, ImageFont
    font = lambda size, bold=False: ImageFont.truetype(f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if bold else ''}.ttf", size)
    label, things = made["label"], made["things"]
    H, W = label.shape
    tone = {True: (70, 230, 90), False: (255, 70, 60), None: (255, 215, 0)}
    colour_of = lambda t: (90, 170, 255) if t.get("region") else (255, 255, 255) if "at" in t or t.get("built") else tone[t.get("keep", True)]
    base = plate.astype(np.float32) * 0.62
    for n, t in enumerate(things, 1):
        own = label == n
        if not own.any():
            continue
        c = np.array(colour_of(t), np.float32)
        base[own] = base[own] * 0.72 + c * (0.28 if not t.get("region") else 0.14)
        rim = own & ~(cv2.erode(own.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0)
        base[rim] = c
    shown = Image.fromarray(base.clip(0, 255).astype(np.uint8))

    def tags(picture, x0, y0, k):
        draw = ImageDraw.Draw(picture)
        for n, t in enumerate(things, 1):
            if t["box"] is None:
                continue
            bx = t["box"]
            x, y = (bx[0] - x0) * k, (bx[1] - y0) * k
            if not (0 <= x < picture.width and -20 <= y < picture.height):
                continue
            if "at" in t:
                draw.rectangle([(bx[0] - x0) * k, (bx[1] - y0) * k, (bx[2] - x0) * k, (bx[3] - y0) * k], outline=(255, 255, 255), width=2)
            text = str(n)
            f = font(15 if k == 1 else 18, True)
            w = draw.textlength(text, font=f)
            y = max(y - 19, 0)
            draw.rectangle([x, y, x + w + 6, y + 19], fill=(0, 0, 0))
            draw.text((x + 3, y + 1), text, fill=colour_of(t), font=f)
        return picture

    parts = [tags(shown.copy(), 0, 0, 1)]
    for x0, y0, x1, y1 in zoom:
        parts.append(tags(shown.crop((x0, y0, x1, y1)).resize(((x1 - x0) * 2, (y1 - y0) * 2), Image.LANCZOS), x0, y0, 2))
    lines = [("Things of the picture, from the nearest to the farthest. Green: stays. Red: taken out. Yellow: for the owner to decide. "
              "Blue: the picture behind a crowd. White: built by the scene, as an object.", (255, 255, 255), True)]
    for n, t in enumerate(things, 1):
        if t.get("depth") is not None and np.isfinite(t["depth"]).any():
            lo, hi = float(np.nanmin(t["depth"])), float(np.nanmax(t["depth"]))
            deep = f"{lo:.0f} m" if hi - lo < 0.5 else f"{lo:.0f} to {hi:.0f} m"
            if t.get("moved") and t["moved"][0] is not None:
                deep += f" (measured {t['moved'][0]:.0f})"
        else:
            deep = "-"
        order = "; ".join(f"{word} {', '.join(t[word])}" for word in ("before", "behind") if t.get(word))
        state = ({True: "stays", False: "TAKEN OUT", None: "DECIDE: stay or out"}[t.get("keep", True)] if "at" not in t and not t.get("built")
                 else "built by the scene" + ", as an object" * bool(t.get("built")))
        text = f"{n:2d}  {t['id']:4s} {t['name']}  |  depth {deep}  |  on: {t.get('on') or '-'}  |  {order or '-'}  |  {state}"
        if t.get("holds"):
            text += f"  |  holds {', '.join(t['holds'])}"
        if t.get("note"):
            text += f"  |  {t['note']}"
        lines.append((text, colour_of(t), False))
    if fires:
        lines.append(("Fires: each is tied to a thing and is shown only over the upper outline of that thing.", (255, 255, 255), True))
        lines += [(f"      {text}", (255, 170, 90), False) for text in fires]
    lines.append((f"Faults of the list: {len(made['faults'])}", (255, 255, 255), True))
    lines += [(f"      {text}", (255, 110, 100), False) for text in made["faults"]] or [("      none", (120, 230, 120), False)]
    lines.append((f"What the build changed to keep the stated order: {len(made['notes'])}", (255, 255, 255), True))
    lines += [(f"      {text}", (200, 200, 200), False) for text in made["notes"]] or [("      nothing", (200, 200, 200), False)]
    wide = max(p.width for p in parts)
    page = Image.new("RGB", (wide, sum(p.height + 8 for p in parts) + 24 * len(lines) + 20), (18, 16, 16))
    y = 0
    for p_ in parts:
        page.paste(p_, (0, y))
        y += p_.height + 8
    draw = ImageDraw.Draw(page)
    for text, c, bold in lines:
        draw.text((10, y + 4), text, fill=c, font=font(15, bold))
        y += 24
    page.save(path)
    return page.size


def ground(plate, depth, valid, made, whole):
    """The one surface that the far side makes together with the wide things named in `whole` (a railing, the part
    of the picture behind a crowd): its picture without every other thing, its depth, and where that depth is known.

    whole: for the id of each wide thing its whole extent, also where a nearer thing covers it: a thing goes on
    behind what stands before it. Where another thing stood, the colours and the measured depth of the far side
    round it are carried in (`fill`), the colours with the grain of the plate; behind a thing with `beyond`, the
    far side of the side it names. A wide thing has its own depth by column in every pixel of its extent."""
    colour = plate.astype(np.float32) / 255
    label, things = made["label"], made["things"]
    wide = {t["id"]: (n, t) for n, t in enumerate(things, 1) if t["id"] in whole}
    own = (label == 0) | np.isin(label, [n for n, _ in wide.values()])
    seen = cv2.erode(own.astype(np.uint8), np.ones((5, 5), np.uint8)) > 0       # without the soft edge of a thing that stood beside it
    grain = (colour - cv2.GaussianBlur(colour, (0, 0), 1.2)).mean(-1)
    ring = seen & (cv2.dilate((~seen).astype(np.uint8), np.ones((41, 41), np.uint8)) > 0)
    noise = cv2.GaussianBlur(np.random.default_rng(5).normal(0, 1, grain.shape).astype(np.float32), (0, 0), 0.6)
    noise *= 1.48 * np.median(np.abs(grain[ring])) / noise.std()      # by the middle of the grain, which the edges of things do not raise
    soft = cv2.GaussianBlur((~seen).astype(np.float32), (0, 0), 1.2)[..., None]
    carried = fill(colour, seen)
    beside = cv2.dilate((~own).astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))) > 0
    far = (label == 0) & valid & ~beside                               # the depth model spreads the depth of a thing over the pixels round it
    deep =np.where(far, depth, fill(np.repeat(np.where(far, depth, 0)[..., None], 3, 2), far)[..., 0]).astype(np.float32)
    for n, t in enumerate(things, 1):                                  # `beyond`: the far side of one side goes on behind the thing
        if "beyond" not in t:
            continue
        stood = (cv2.dilate((label == n).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0) & ~seen
        ys, xs = np.nonzero(stood)
        first, last = np.full(stood.shape[0], stood.shape[1]), np.full(stood.shape[0], -1)
        np.minimum.at(first, ys, xs)
        np.maximum.at(last, ys, xs)
        twin = np.clip(2 * last[ys] + 1 - xs if t["beyond"] == "right" else 2 * first[ys] - 1 - xs, 0, stood.shape[1] - 1)      # its picture in the edge of the thing, as in a mirror
        ok = seen[ys, twin]
        ys, xs, twin = ys[ok], xs[ok], twin[ok]
        carried[ys, xs], noise[ys, xs], deep[ys, xs] = colour[ys, twin], 0, deep[ys, twin]      # the plate's own pixels have their grain
    picture = colour * (1 - soft) + (carried + noise[..., None]) * soft
    known = valid | (label > 0)
    for name, (n, t) in wide.items():
        cols = np.flatnonzero(np.isfinite(t["depth"]))
        by = np.interp(np.arange(deep.shape[1]), cols, t["depth"][cols]).astype(np.float32)      # beyond its own columns: as at its end
        deep = np.where(whole[name], by[None], deep)
        known |= whole[name]
    return np.clip(picture * 255, 0, 255).astype(np.uint8), deep, known


def covered(made, deep, whole, held=()):
    """Faults of the ground: a thing that stays, or a surface that a thing holds, with ground before it. The ground
    lies behind everything else; where it is nearer than a thing, the plate holds a thing that the list does not
    name, or the thing has the wrong depth.

    deep: the depth of the ground (`ground`). whole: the wide things that are part of the ground. held: for every
    surface that a thing holds its name, its box on the plate and its depth by column."""
    label, faults = made["label"], []
    seen = [(t["id"], label == n, t["depth"]) for n, t in enumerate(made["things"], 1)
            if t["pixels"] and t.get("keep") is not False and t["id"] not in whole and t.get("depth") is not None]
    for name, (x0, y0, x1, y1), by in held:
        box = np.zeros(label.shape, bool)
        box[y0:y1, x0:x1] = True
        seen.append((name, box, by))
    for name, own, by in seen:
        near = own & (deep < 0.97 * np.nan_to_num(by, nan=0.0)[None])
        if near.sum() > 12:
            ys, xs = np.nonzero(near)
            faults.append(f"{name}: the ground is nearer than it in {len(xs)} pixels, columns {xs.min()}-{xs.max()}, rows {ys.min()}-{ys.max()}: "
                          f"{deep[near].min():.1f} m against {np.nanmedian(by[xs]):.1f} m")
    return faults


def planes(plate, made, skip, margin=12, reach=10):
    """Every thing that stays, is not part of the ground and is not built as an object, as a picture of its own: id -> (picture with cover,
    its box on the plate, its depth for each column of that box). A thing that stands on a thing with a picture lies
    in that picture, at that thing's depth: two pictures at one depth lie in each other, and the renderer shows one or
    the other from frame to frame (a painted mast under its crossbar). The thing's own colours are carried out beyond its
    outline, so that a soft edge has no colour of what stood beside it. Where a thing that is nearer in depth covers
    it, the thing goes straight on behind that thing for `reach` rows: a camera that moves sees it there. A thing that
    stands on its support at the support's own depth ends at its outline. In a box of `rods` the thing has no gap."""
    colour = plate.astype(np.float32) / 255
    label, things = made["label"], made["things"]
    H, W = label.shape
    stays = {t["id"]: n for n, t in enumerate(things, 1)
             if not (t["id"] in skip or not t["pixels"] or t.get("keep", True) is not True or t.get("depth") is None or t.get("built"))}
    sets = {}                                                             # the things of one surface, under the id of the one that the others stand on
    for name, n in stays.items():
        first = name
        while things[stays[first] - 1].get("on") in stays:
            first = things[stays[first] - 1]["on"]
        sets.setdefault(first, []).append(n)
    out = {}
    for name, members in sets.items():
        boxes = np.array([things[n - 1]["box"] for n in members])
        x0, y0, x1, y1 = max(boxes[:, 0].min() - margin, 0), max(boxes[:, 1].min() - margin, 0), min(boxes[:, 2].max() + margin, W), min(boxes[:, 3].max() + margin, H)
        inside = label[y0:y1, x0:x1]
        own = np.isin(inside, members)
        cols = np.flatnonzero(np.isfinite(things[stays[name] - 1]["depth"]))
        by = np.interp(np.arange(x0, x1), cols, things[stays[name] - 1]["depth"][cols]).astype(np.float32)
        nearer = np.zeros_like(own)                                       # where a thing that is nearer than this one covers the plate
        for k in np.unique(inside):
            other = things[k - 1] if k else None
            if other is not None and k not in members and other.get("depth") is not None and other.get("keep", True) is True:
                theirs = other["depth"][x0:x1]
                nearer |= (inside == k) & (np.where(np.isfinite(theirs), theirs, np.inf) < 0.995 * by)[None]
        down = cv2.dilate(own.astype(np.uint8), np.ones((2 * reach + 1, 1), np.uint8)) > 0      # straight on, up and down: a mast goes on behind a railing
        cover = own | (down & nearer)
        part = colour[y0:y1, x0:x1]
        for t in (things[n - 1] for n in members):
            if "drawn" in t:                                              # the part that the plate hides is drawn as the same part of the other side
                cols = np.flatnonzero(t["drawn"].any(0))
                other = np.clip(cols[0] + cols[-1] - x0 - np.arange(x1 - x0), 0, x1 - x0 - 1)
                part = np.where((own & ~t["drawn"][y0:y1, x0:x1])[..., None], part[:, other], part)
        rgb = np.where(own[..., None], part, fill(part, own))
        for bx0, by0, bx1, by1 in (rod for n in members for rod in things[n - 1].get("rods", [])):      # a rod is whole: a row that does not show it is drawn as the nearest rows that show it
            cols, rows = slice(bx0 - x0, bx1 - x0), np.arange(by0 - y0, by1 - y0)
            shown = own[rows, cols].sum(1) >= 3
            for r in rows[~shown] if shown.any() else []:
                near = rows[shown][np.argsort(np.abs(rows[shown] - r))[:24]]
                there = own[near][:, cols]
                thick = there.mean(0) > 0.5
                rgb[r, cols][thick] = ((part[near][:, cols] * there[..., None]).sum(0) / np.maximum(there.sum(0), 1)[:, None])[thick]
                cover[r, cols] = thick
        alpha = cv2.GaussianBlur(cover.astype(np.float32), (0, 0), 0.5)
        out[name] = (np.clip(np.dstack([rgb, alpha]) * 255, 0, 255).astype(np.uint8), (x0, y0, x1, y1), by)
    return out
