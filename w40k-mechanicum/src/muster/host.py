"""The crowd of the muster plate, set figure by figure on the floors of the two walks in the perspective of the plate.

    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/muster/host.py clear
    ... host.py tries left 3 4 5 6         # wip/muster/tries-left.png: the far side of one walk painted with several seeds
    python3 src/muster/host.py stand       # wip/gen/plate_musterP.png and wip/preview/muster-plate.png
    python3 src/muster/host.py sheet       # wip/preview/muster-plate-sheet.png: the plate beside the prototype and the user's picture
    python3 src/muster/host.py export      # wip/scene3d/muster_crowd.npz, muster_atlas_<view>.png, muster_plate.png: the crowd for src/muster.py

`clear` reads wip/gen/plate_muster_banners.png (src/muster/banners.py) and writes wip/gen/plate_muster_empty.png: the
plate without the large figures that the image model painted on the walks. `stand` sets the crowd on that plate.

The user's words on the crowd laid as one flat picture (src/muster/pack.py lay): "the crowd must be facing the
longitudal direction, they are facing left", "it looks as if you ignored the perspective", "on the right crowd looks
as if they are piling one over another". That crowd had one figure size across the whole walk. Here every figure is
a picture of its own (src/muster/figures.py) and stands on the floor:

- **Facing** - a first crowd of side views that walked to the right got: "must face the direction of walk, not right
  or left". A walk runs into the picture, so a figure that walks along it is seen from behind or from the front. On
  the left walk the crowd walks away from the camera, to the bridge: rear views (`view` "away"). On the right
  terrace it stands and faces the camera: front views ("near"). Half of the figures are mirrored

- **Horizon** - the lines of both walks meet on row HORIZON of the plate. That row is the height of the camera
- **Size by place** - the camera stands `eye` figure heights over the floor of a walk. A figure whose feet are y rows
  below the horizon is then y / eye rows tall: this one rule gives every figure its size, far figures small, near
  figures large
- **How large** - the plate's own figures stood about 190 rows tall at the left edge of the left walk and about 115
  at the right edge of the right terrace: a camera 1.2 and 1.0 figure heights over the floors. A first crowd with the
  camera 6.5 heights up had figures of 38 rows there. The user: "figures are too small; make them bigger; they should
  be roughly 0.5 the initial size proposed". `eye` is therefore twice the camera height of the plate's own figures
- **Floor** - each walk is a strip of floor between two lines that run to its vanishing point: the line where the
  floor meets the parapet, and the far edge of the floor. Figures stand on a grid on that floor, FILE apart across
  the walk and RANK apart along it, each a little off its grid point
- **Order** - far figures are drawn first, so near figures stand before them; the parapet stands before all
- **Kinds** - KINDS gives the share of adepts, workers, skitarii and enginseers. Every figure is darkened as worn and
  dirty (WORN, DIRT), and the pictures are evened in brightness (EVEN): the crowd of the user's picture is one dark
  mass in which a person differs little from the next
- **Light of the scene** - the figures are drawn in flat white light. The user on the crowd set as drawn: "the crowd
  is different colour and grayed out compared to the rest". Every figure is therefore multiplied by LIGHT, the mean
  colour of the mid-tones of the plate, gets more contrast (GAMMA), and is darker towards its feet (SHADE), where
  the figures round it take the light. Dirt takes a little colour out, never all of it: the plate has no neutral grey
- **Haze** - with distance a figure takes the colour of the air behind it, as much as the parapet beside it does
- **Not one flat surface** - the user on a crowd of one height, one mix and one light everywhere: "it is uniformly
  flat". Four things now differ from place to place:
  - **Blocks** - the floor is divided into blocks, BLOCK figure heights long and wide. Each block is of one kind; the
    share PURE of its figures is of that kind
  - **Heights** - each kind has its own height, and in a crowd that stands one figure in 1 / BEARERS[0] carries a
    tall standard
  - **Persons** - the user: "there must be small variation of height from person to person". Every figure has a
    height, a girth, a lean and a place in its step of its own (PERSON): the heads of a block no longer lie in one
    plane. A figure stands anywhere in its cell of the floor, not near the middle of it, and LOOSE takes figures
    out in patches, so that no rows and files show
  - **Fires** - the fires of the plate behind a walk light the figures near them (GLOW, in the colour FIRE)
  - **Shade** - the brightness of the crowd changes slowly over the floor between the two values of SHADOW, as under
    drifting smoke
- **End of the right terrace** - its parapet ends at a corner, so its floor ends at the depth of that corner: `end`
  is the row of the feet there. A first crowd went on to the vanishing point and stood in the air beyond the corner
- **Floor under the railing** - the floor of the right terrace first lay 16 rows under the top of its railing, where
  the feet of the plate's own large figures were. Figures of half that size were hidden to the shin only, and the
  user saw: "crowd seems to be over the railing - at the top of railing", "figures are so far out that they almost
  fall off". The floor now lies 40 rows under the railing at the plate's edge, half a figure height or more
  everywhere: the railing hides a figure up to its chest. `eye` rose from 2.0 to 2.55 with it, which keeps the
  size of the figures. The crowd also begins 15 columns inside the corner and ends 10 rows before the end of the
  floor. On the left walk the railing hid 22 to 50 % of a front figure; its floor went down by the same rule
  (near edge from row 690 to 725 at the plate's edge, `eye` from 2.4 to 2.77), so it hides 55 %
- **Far end of the right terrace** - after that the user saw on the draft loop: "on the right the crowd overhangs
  still". The crowd ended at one row of the plate, 70 columns from the corner post: a block with a level upper
  edge and an upright end that lay on the railing over its first section. A try that let the last rows cover less
  and less got: "you have used alpha to hide that part - this is not good". Every figure is solid. The crowd then
  ended behind the two dark masts, 170 columns from the corner post, and the user asked: "what about missing crowd
  by the railing on the right side?". It now stands up to the last rank of the terrace, the rank through the
  corner post (`corner` of the walk, `last`), and no figure stands beyond that rank. Its floor also lies 4 rows
  lower, so the railing hides 59 % of a front figure at the plate's edge, as on the left walk
- **Far crowd** - a figure under SMALL rows is drawn as a short stroke in the mean colour of its picture
- **Width of a walk** - the far edge of the floor is set so that the farthest figure across the walk is still about
  half as tall as the nearest. A first try with a floor 350 m wide, which reached up to the heads of the plate's own
  figures, gave a field of dots: at that depth a figure is 5 rows tall
- **Far side** - over the far heads the plate showed the bodies of its own large figures. `clear` lets the image
  model paint smoke there on the left walk. MASTS are kept. The painting takes its tone from the plate round it.
  On the right terrace the image model is not used: ten paintings all began at the straight upper edge of the
  painted part with a scene of their own and ended the banner masts there, and the first one, toned to the air over
  it, stood as a pale rectangle beside the dark far wall. There `haze` carries the air round the part into it, lets
  the row over the part and the column beside it go on into it and fade into that air, and lets every mast that
  crosses the upper edge go on down to the crowd.
  The far rows of the crowd go into the smoke over the share `veil` of the walk's width: there a figure takes the
  colour of the air and fewer figures stand (FEWER). Every figure stays solid: figures that covered less showed and
  hid by chance from frame to frame once the crowd walked. A painted far parapet with the crowd filling the floor up
  to it was tried first: its figures were 8 rows tall at the far side, and the crowd read as a flat red surface
"""
import os, sys
import numpy as np, cv2
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
import muster as M                         # the scene: where a figure stands at each moment of the loop, its shade, its fire light
GEN, FIGURES = os.path.join(ROOT, "wip", "gen"), os.path.join(ROOT, "wip", "muster", "figures")
SIZE = (2432, 768)
HORIZON, FOCAL = 448, 2000.0               # row of the horizon; focal length in pixels
FILE, RANK = 0.36, 0.50                    # the cell of floor of one figure: across and along the walk, in figure heights
LOOSE, FEWER = 0.3, 0.6                    # the share of figures taken out where the crowd is loosest; and more at the far side, where it stands in smoke
# from person to person: the spread of height and of girth (standard deviation, and the most), the greatest lean in
# rows per row of height, and the greatest rise in a step as a share of the height
PERSON = dict(height=(0.035, 0.08), girth=(0.05, 0.12), lean=0.07, step=0.025)
SMALL, TALLEST = 3, 256                    # figures under SMALL rows are strokes; the tallest picture of a figure
# how bright a figure is and how much of its colour the dirt takes, each between two values; how far the mean
# brightness of a picture is moved to that of all pictures. The user on a crowd of bright red robes, pale heads and
# grey rags side by side: "the differences between the individuals must be less prominent, so the repeating pattern
# won't be so striking", "still have some differences between them but not too much"
WORN, DIRT, EVEN = (0.46, 0.66), (0.55, 0.85), 0.7
LEVELS = 7                                 # in the 3D scene each figure is kept at this many sizes, each half the one before
DEEPER = 1.06                              # in the 3D scene the nearest figures stand this many times as deep as the parapet
HAZE = 90.0                                # a figure whose feet are FOCAL / HAZE rows below the horizon has 63 % of the air's colour
LIGHT = np.array([1.0, 0.74, 0.58], np.float32)      # the light of the scene: the mean colour of the mid-tones of the plate, its red as 1
GAMMA, SHADE = 1.3, 0.6                    # the contrast added to a figure; the brightness of its feet against its head
# each walk: the height of the camera over its floor, in figure heights; the column of its vanishing point; a point of
# the line where floor and parapet meet; a point of the far edge of the floor
# span: the columns of the plate the walk is seen in
# far: the row of the far edge of the crowd, where a figure is still about 0.4 times as tall as at the near edge
# veil: the share of the walk's width, at its far edge, over which the crowd goes into the smoke
# corner: the column at which the parapet of the walk ends at a corner post: the floor ends at the rank through that
#   point of the near line. None: the walk goes on to its vanishing point
# view: how the crowd is seen: "away" from behind, "near" from the front
# pace: how fast the crowd walks along the walk, away from the camera, in m/s on average; 0: it stands
WALKS = {"left": dict(eye=2.77, vanish=1140, near=(0, 725), far=(0, 559), span=(0, 1100), veil=0.22, corner=None, view="away", pace=0.45),
         "right": dict(eye=2.62, vanish=1203, near=(2432, 600), far=(2432, 520), span=(1845, 2432), veil=0.1, corner=1852, view="near", pace=0.0)}
# what `clear` paints again: the part of the plate the image model sees (x0, y0, x1, y1, both sides multiples of 8), and
# the row over which nothing is changed at the first and at the last column of the walk
SIDES = {"left": dict(view=(0, 400, 1216, 704), top=(452, 446)), "right": dict(view=(1792, 400, 2432, 592), top=(440, 436))}
MASTS = [(366, 400, 388, 704)]             # boxes that stay as they are: a banner mast that stands before the figures
# the upper edge of a far side the image model painted, where air lies on both sides of it: the columns; the rows over
# and under the edge whose tone is compared; the rows over which the change fades out under the edge
SEAM = {"left": ((0, 165), 12, 40)}
FARSIDE = ("Thick rolling brown and black smoke and dust drift low over a rampart walk on a forge world and hide its "
           "floor and its far side, lit from behind by dirty orange fires{behind}. No floor visible, no people, no "
           "figures, no crowd, no building in front. A frame from a war film, muted colours, soot and grime, "
           "everything dark, no white stone, no bright surface")
# the walks whose far side the image model paints: the seed; the share of its own tone the painting gives up for the
# tone of the plate round it; what stands behind the smoke
SEED, TONED = {"left": 3}, {"left": 0.5}
BEHIND = {"left": "; the feet of tall iron banner masts and iron braziers stand in the smoke, and behind it the dark wall of a gothic cathedral"}
# on the other walks: a dark thing wider than MAST at the upper edge is no mast; the rows over which the sky goes on
# down into the part; the columns over which the far wall beside the part goes on into it
MAST, REACH, BESIDE = 20, 36, 150
# the figures in use, by kind; a name with "<" is mirrored, because that figure faces left
# each kind: its share of the crowd and its height against the rule
KINDS = {"adepts": (0.55, 1.0), "workers": (0.17, 0.95), "skitarii": (0.20, 1.04), "magi": (0.08, 1.10)}
# the figures in use, by view and kind, as "<seed>_<number>" of the sheet "<kind>-<view>" of src/muster/figures.py
MEMBERS = {
    "away": dict(adepts="1_1 1_2 1_3 1_5 1_6 1_7 2_1 2_2 2_3 2_4 2_5", workers="1_1 1_2 1_3 1_4 1_5 1_6 1_7 1_8 2_1 2_2 2_4 2_5 2_6 2_7",
                 skitarii="1_1 1_2 1_3 1_4 1_5 1_6 1_7 1_8", magi="1_1 1_2 1_3 1_4 1_5 1_7 1_8 1_9"),
    "near": dict(adepts="1_1 1_2 1_3 1_4 1_5 1_6 1_7 2_1 2_2 2_3 2_4 2_5 2_6 2_7", workers="1_1 1_2 1_3 1_4 1_5 1_6 2_1 2_2 2_3 2_4 2_5 2_6 2_7 2_8 2_9",
                 skitarii="1_1 1_2 1_3 1_4 1_5 1_7 1_8 2_1 2_2 2_3 2_4 2_5 2_6 2_7", magi="1_2 1_3 1_4 1_5 1_8 2_1 2_2 2_3 2_4 2_5 2_6 2_7"),
}
# the bearers of standards: their share of all figures; by view, each picture with its height against the bearer in it.
# No censer with painted smoke (away 1_3 and 2_2, near 1_3 and 2_3): a bearer repeats along its file every PERIOD ranks,
# and the same pale smoke on every one of them showed as a row of pale marks along the far edge of the crowd. For the
# same reason a crowd that walks has no bearers: a row of one standard was its most striking repeating pattern
BEARERS = (0.005, {"away": "1_2@1.8 1_5@1.8 1_6@1.8 2_4@1.55 2_5@1.55",
                   "near": "1_2@1.8 1_5@1.8 1_6@1.8 1_7@1.8 1_8@1.8 1_9@1.8 2_1@1.75 2_2@1.75 2_4@1.75 2_5@1.75 "
                           "2_6@1.75 2_7@1.5 2_8@1.5 2_9@1.5"})
BLOCK, PURE = (16.0, 5.0), 0.6              # a block of one kind: its length along the walk and its width, in figure heights
FIRE, GLOW = np.array([1.5, 0.7, 0.25], np.float32), 6.0      # the light of a fire on a figure beside it; its reach in sizes of the fire
SHADOW = (0.65, 1.25)                      # the brightness of the crowd in the darkest and in the brightest place
LUM = np.array([0.2126, 0.7152, 0.0722], np.float32)
WARM = LIGHT / (LIGHT @ LUM)               # a grey of brightness 1 in the light of the scene: the colour of dirt
# the scene works the crowd out again for every frame, by the same numbers
assert (SIZE, HORIZON, FOCAL, RANK, SMALL, DEEPER, HAZE, GLOW, SHADOW) == (M.PLATE, M.HORIZON, M.FOCAL, M.RANK, M.SMALL, M.DEEPER, M.MURK, M.REACH, M.SHADOW)


def figures(view):
    """Every figure of one view, in the light of the scene: its picture, its height against the rule, its mean colour;
    the figures of each kind; the share of each kind; the bearers."""
    figs, kinds = [], []
    sets = [(kind, size, MEMBERS[view][kind].split()) for kind, (_, size) in KINDS.items()] + [("bearers", None, BEARERS[1][view].split())]
    for kind, size, members in sets:
        at = len(figs)
        for member in members:
            member, _, own = member.partition("@")
            a = np.asarray(Image.open(os.path.join(FIGURES, f"{kind}-{view}{member}.png")).convert("RGBA"), np.float32) / 255
            a[..., :3] = a[..., :3] ** GAMMA * LIGHT
            figs.append(dict(a=a, size=float(own) if own else size, at={}, mean=(a[..., :3] * a[..., 3:]).sum((0, 1)) / a[..., 3].sum() * (1 + SHADE) / 2))
        kinds.append(np.arange(at, len(figs)))
    bright = np.array([fig["mean"] @ LUM for fig in figs])
    for fig, gain in zip(figs, (np.median(bright) / bright) ** EVEN):      # no picture much brighter or darker than the others
        a = fig.pop("a")
        a[..., :3] = np.clip(a[..., :3] * gain, 0, 1)
        fig.update(im=Image.fromarray((a * 255).astype(np.uint8), "RGBA"), mean=fig["mean"] * gain)
    shares = np.array([share for share, _ in KINDS.values()])
    return figs, kinds[:-1], shares / shares.sum(), kinds[-1]


def sized(fig, h, girth=1.0, lean=0.0, mirrored=False):
    """A figure h rows tall, as colour times alpha and alpha, darker towards its feet, and the column of the middle of
    its feet. `girth` is its width against the picture; `lean` is how far its head stands beside its feet, in rows
    per row of height."""
    key = (h, round(girth, 2), round(lean, 2), bool(mirrored))
    if key not in fig["at"]:
        im = fig["im"].transpose(Image.FLIP_LEFT_RIGHT) if mirrored else fig["im"]
        w = max(round(im.width * h / im.height * girth), 1)
        im = im.resize((w, h), Image.LANCZOS)
        push = abs(lean) * h
        if push >= 0.5:                                               # each row is moved by its height over the feet times the lean
            im = im.transform((w + int(np.ceil(push)), h), Image.AFFINE, (1, lean, -max(lean, 0) * h, 0, 1, 0), Image.BICUBIC)
        small = np.asarray(im, np.float32) / 255
        body = h / fig["size"]                                        # the rows of the figure itself, under its standard
        shade = np.clip(1 - (1 - SHADE) * (np.arange(h, dtype=np.float32) - (h - body)) / body, SHADE, 1)
        fig["at"][key] = (small[..., :3] * small[..., 3:] * shade[:, None, None], small[..., 3:], w / 2 + (push if lean < 0 else 0))
    return fig["at"][key]


def parapet():
    """Where the parapets of both walks stand before the crowd. SAM 2.1 cut them (wip/muster/parapet.png) and left out
    parts of the railing: its upper edge, finials, the corner post of the right terrace, the stretch at the left
    edge. There the crowd was drawn before the railing, and the user saw: "figures stand on the gallery railing".
    The measured depth of the plate completes the mask: a pixel belongs to the parapet as well if it is no deeper
    than 1.2 times the parapet of its column and lies no more than one figure height over the near edge of the
    floor."""
    front = np.asarray(Image.open(os.path.join(ROOT, "wip", "muster", "parapet.png"))) > 127
    d = np.load(os.path.join(ROOT, "wip", "scene3d", "muster_clean.npz"))
    H, W = front.shape
    xs, rows = np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32)[:, None]
    more = np.zeros_like(front)
    for walk in WALKS.values():
        xa, xb = walk["span"]
        near = lines(walk, xs)[1]
        zp = np.full(W, np.nan, np.float32)
        for x in range(xa, min(xb, W - 1) + 1):
            r = np.flatnonzero(front[:, x] & d["mask"][:, x])
            if len(r):
                zp[x] = d["depth"][r[:12], x].max()
        known = np.flatnonzero(np.isfinite(zp))
        zp = np.exp(cv2.GaussianBlur(cv2.medianBlur(np.log(np.interp(xs, known, zp[known]))[None].astype(np.float32), 5), (0, 0), 20)[0])
        more |= (d["mask"] & (d["depth"] < 1.2 * zp[None]) & (rows >= (near - (near - HORIZON) / walk["eye"])[None])
                 & ((xs >= xa) & (xs <= xb))[None])
    return front | more


def fires(plate, walk):
    """The fires of the plate behind one walk: place across and depth, and size, in figure heights. A fire is taken to
    stand at the far edge of the floor."""
    H, W = plate.shape[:2]
    xs, rows = np.arange(W, dtype=np.float32), np.arange(H, dtype=np.float32)[:, None]
    far = np.maximum(ending(walk, xs), HORIZON + 4)
    hot = (plate[..., 0] > 0.8) & (plate[..., 1] > 0.3) & (plate[..., 1] < 0.8) & (plate[..., 2] < 0.45)
    hot &= (rows > far[None] - 130) & (rows < far[None]) & ((xs >= walk["span"][0]) & (xs <= walk["span"][1]))[None]
    count, _, stats, centres = cv2.connectedComponentsWithStats(cv2.dilate(hot.astype(np.uint8), np.ones((5, 5), np.uint8)))
    out = []
    for k in range(1, count):
        if stats[k, cv2.CC_STAT_AREA] >= 80:
            depth = FOCAL * walk["eye"] / (far[int(centres[k, 0])] - HORIZON)
            out.append(((centres[k, 0] - W / 2) * depth / FOCAL, depth, np.sqrt(stats[k, cv2.CC_STAT_AREA]) * depth / FOCAL))
    return out


def stand(walk, rng, bare=False):
    """The crowd of one walk: the walk as src/muster.py place() takes it; its chains as src/muster.py way() takes
    them; of every figure that is in the picture at some moment of the loop its chain and its turn; the number of
    lanes.

    A walking crowd (`pace`): the loop closes only if the figure that arrives at a place equals the one that left
    it. A chain is one figure on one way. Its copies follow it, each one loop behind the one before it, so at the
    end of the loop every copy stands where the one before it stood at the start. A lane holds one of M.CHAINS
    chains and has a pace of its own: the figures of two lanes pass each other, and no group of figures stands a
    second time. Every chain has its own uneven pace (M.UNEVEN). A chain that is left empty walks with the crowd:
    a gap that stayed in its place would swallow the figures that walk into it.

    A standing crowd: every figure is a chain of its own and keeps its place."""
    eye = walk["eye"]
    world = lambda x, y: np.array([(x - SIZE[0] / 2) * eye / (y - HORIZON), FOCAL * eye / (y - HORIZON)])     # across, depth
    along = np.array([(walk["vanish"] - SIZE[0] / 2) / FOCAL, 1.0])
    along /= np.linalg.norm(along)
    a, b = world(*walk["near"]), world(*walk["far"])
    across = (b - a) - ((b - a) @ along) * along
    wide = np.linalg.norm(across)
    across /= wide
    last = (world(walk["corner"], lines(walk, walk["corner"])[1]) - a) @ along if walk["corner"] else np.inf      # the last rank of the walk
    g = dict(a=a, along=along, across=across, eye=eye, span=walk["span"], last=last, wide=wide)
    if bare:                                                          # the walk alone
        return g
    lanes = np.arange(0, wide, FILE)
    if walk["pace"]:
        n = rng.choice(M.CHAINS, len(lanes))                           # the chains of each lane
        go = walk["pace"] * M.LOOP / 1.8 * rng.uniform(0.9, 1.1, len(lanes))      # the figure heights a lane walks in a loop: each lane a little more or less
        lane = np.repeat(np.arange(len(lanes)), n)
        first = np.concatenate([np.arange(k) for k in n])
        ch = dict(r=np.zeros(len(lane)), go=go[lane],                 # every lane starts at its own place, and no figure stands in the middle of its cell
                  late=(first + rng.uniform(-0.3, 0.3, len(lane))) / n[lane] + rng.random(len(lanes))[lane])
        turns = np.arange(np.floor(-200 / ch["go"].min()) - 2, np.ceil(FOCAL * eye / ch["go"].min()) + 3)      # to the depth where a figure is 1 row tall
    else:
        ranks = np.arange(-200, FOCAL * eye, RANK)
        lane = np.repeat(np.arange(len(lanes)), len(ranks))
        ch = dict(r=np.tile(ranks, len(lanes)) + rng.uniform(-RANK / 2, RANK / 2, len(lane)), go=np.zeros(len(lane)), late=np.zeros(len(lane)))
        turns = np.zeros(1)
    count, walks = len(lane), ch["go"] > 0
    ch.update(lane=lane, f=lanes[lane] + rng.uniform(-FILE / 2, FILE / 2, count),
              part=np.array(M.UNEVEN[0]) * rng.uniform(0.6, 1.0, (count, 1)) * walks[:, None], every=rng.uniform(*M.UNEVEN[1], (count, 3)),
              start=rng.uniform(0, 2 * np.pi, (count, 3)),
              side=np.stack([M.ASIDE[0] * rng.random(count) * walks, rng.uniform(*M.ASIDE[1], count), rng.uniform(0, 2 * np.pi, count)], 1),
              step=rng.uniform(*M.STEP, count), steps=rng.choice(M.STEPS, count), sways=rng.choice(M.SWAYS, count), at=rng.random(count), to=rng.random(count),
              drift=np.stack([rng.uniform(*M.DRIFT[0], count)] + [rng.uniform(0, 2 * np.pi, count) for _ in range(3)], 1))
    of, turn = np.repeat(np.arange(count), len(turns)), np.tile(turns, count)
    seen = np.zeros(len(of), bool)
    for t in np.linspace(0, 1, 13):
        f, r = M.way(ch, of, turn, t)[:2]
        seen |= M.place(g, f, r)[4]
    smoke = 1 - np.clip((1 - ch["f"] / wide) / walk["veil"], 0, 1)      # the far side of the walk stands in smoke: fewer figures there
    seen &= (rng.random(count) > LOOSE / 2 + FEWER * smoke)[of]
    kept, of = np.unique(of[seen], return_inverse=True)               # the chains that have a figure in the picture
    return g, {key: value[kept] for key, value in ch.items()}, of, turn[seen], len(lanes)


def ending(walk, xs):
    """The row of the far end of a walk's floor at the columns xs: its far edge, or the line of its last rank where the
    walk ends at a corner. Beyond the corner there is no floor: the row is infinite there."""
    far = lines(walk, xs)[0]
    if not walk["corner"]:
        return far
    g = stand(walk, np.random.default_rng(0), bare=True)
    f = np.linspace(0, g["wide"], 60)
    x, y = M.place(g, f, g["last"] + 0 * f)[:2]
    order = np.argsort(x)
    return np.maximum(far, np.interp(xs, x[order], y[order], left=np.inf, right=-np.inf))


def lines(walk, xs):
    """The rows of the far edge of the floor and of its near edge at the columns xs."""
    vx = walk["vanish"]
    line = lambda point: HORIZON + (point[1] - HORIZON) * (xs - vx) / (point[0] - vx)
    return line(walk["far"]), line(walk["near"])


def fill(colour, known):
    """The colours of the known pixels, carried smoothly into the rest: each level of a pyramid holds the mean of the
    known pixels under it, and a pixel that is not known takes the colour of the level over it."""
    levels = [(colour * known[..., None], known.astype(np.float32))]
    while min(levels[-1][1].shape) > 2:
        c, k = levels[-1]
        size = (max(k.shape[1] // 2, 1), max(k.shape[0] // 2, 1))
        levels.append((cv2.resize(c, size, interpolation=cv2.INTER_AREA), cv2.resize(k, size, interpolation=cv2.INTER_AREA)))
    c, k = levels[-1]
    out = np.ones_like(c) * c.sum((0, 1)) / max(k.sum(), 1e-6)
    for c, k in reversed(levels):
        out = cv2.resize(out, (k.shape[1], k.shape[0]), interpolation=cv2.INTER_LINEAR)
        out = out * (1 - k[..., None]) + c
    return out


def hole(name, front):
    """The part of the plate where the plate's own large figures of one walk stood."""
    walk = WALKS[name]
    xs, rows = np.arange(SIZE[0], dtype=np.float32), np.arange(SIZE[1], dtype=np.float32)[:, None]
    xa, xb = walk["span"]
    top = np.interp(xs, [xa, xb], SIDES[name]["top"])
    part = (rows >= top[None]) & (rows <= lines(walk, xs)[1][None] + 2) & ((xs >= xa) & (xs <= xb))[None] & ~front
    for x0, y0, x1, y1 in MASTS:
        part[y0:y1, x0:x1] = False
    return part, top


def seam(plate, front):
    """The plate with the upper edge of each painted far side toned to the plate over it. The image model painted the
    far side of a walk under a straight line (`hole`), lighter than the smoke over that line, and the line showed
    as a straight edge in the smoke; the user: "look also at somoke clipping". Per column, the colour of the rows
    over the line less that of the rows under it, without thin things and smoothed along the line, is added under
    the line and fades out downwards; the 7 rows at the line go evenly from the row over them to the row under them."""
    out = plate.astype(np.float32)
    for name, ((xa, xb), n, fade) in SEAM.items():
        part, top = hole(name, front)
        cols = np.arange(xa, xb + 16)
        t = np.round(top[cols]).astype(int)
        over = np.stack([out[t - 3 - k, cols] for k in range(n)]).mean(0)
        under = np.stack([out[t + 3 + k, cols] for k in range(n)]).mean(0)
        step = cv2.medianBlur(np.clip(over - under + 128, 0, 255).astype(np.uint8)[None], 81).astype(np.float32) - 128
        here = np.clip((xb + 15 - cols) / 15, 0, 1)[:, None] * part[t + 4, cols][:, None]
        step = cv2.GaussianBlur(step, (0, 0), sigmaX=25, sigmaY=0.01)[0] * here
        for d in range(4 * fade):
            rows = np.minimum(t + d, out.shape[0] - 1)
            out[rows, cols] += step * np.exp(-d / fade) * part[rows, cols][:, None]
        over, under = out[t - 4, cols].copy(), out[t + 4, cols].copy()      # the rows at the line itself, which the painting blurred: from one side to the other
        for d in range(-3, 4):
            out[t + d, cols] = out[t + d, cols] * (1 - here) + (over + (under - over) * (d + 4) / 8) * here
    return np.clip(out, 0, 255).astype(np.uint8)


def far_side(pipe, plate, front, name, seed):
    """The plate with the far side of one walk painted by the image model."""
    import torch
    plate = plate.copy()
    x0, y0, x1, y1 = SIDES[name]["view"]
    crop, part = plate[y0:y1, x0:x1], hole(name, front)[0][y0:y1, x0:x1].astype(np.uint8)
    big = (2 * (x1 - x0), 2 * (y1 - y0))
    gen = pipe(prompt=FARSIDE.format(behind=BEHIND[name]), image=Image.fromarray(cv2.resize(crop, big, interpolation=cv2.INTER_CUBIC)),
               mask_image=Image.fromarray(cv2.resize(part, big, interpolation=cv2.INTER_NEAREST) * 255), strength=1.0,
               height=big[1], width=big[0], num_inference_steps=9, guidance_scale=0.0,
               generator=torch.Generator("cuda").manual_seed(seed)).images[0]
    gen = cv2.resize(np.asarray(gen), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA).astype(np.float32)
    # tone: the painting keeps its detail and takes its tone from the plate round it, without the masts that cross its edge
    soft = lambda m: cv2.GaussianBlur(m, (0, 0), 18)
    known = cv2.erode(1 - part, np.ones((5, 5), np.uint8)) > 0
    target = fill(cv2.medianBlur(crop, 31).astype(np.float32), known)
    gen = np.clip(gen - soft(gen) * TONED[name] + soft(target) * TONED[name], 0, 255)
    a = cv2.GaussianBlur(part.astype(np.float32), (0, 0), 2)[..., None]
    plate[y0:y1, x0:x1] = (crop * (1 - a) + gen * a).astype(np.uint8)
    print(f"far side of the {name} walk painted with seed {seed}: {int(part.sum())} px", flush=True)
    return plate


def haze(plate, front, name):
    """The plate with the far side of one walk as air: the colours over and beside the part carried into it, the
    masts that cross its upper edge drawn on down, and the grain of the plate."""
    plate = plate.copy()
    x0, y0, x1, y1 = SIDES[name]["view"]
    part, top = hole(name, front)
    near = lines(WALKS[name], np.arange(SIZE[0], dtype=np.float32))[1]
    known = ~part & ~front & (np.arange(SIZE[1])[:, None] < near[None])           # not the parapet, nothing under the floor
    known = cv2.erode(known[y0:y1, x0:x1].astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    crop, part, top = plate[y0:y1, x0:x1].astype(np.float32), part[y0:y1, x0:x1], top[x0:x1].astype(int) - y0
    calm = cv2.medianBlur(plate[y0:y1, x0:x1], 31).astype(np.float32)             # the plate without thin things
    air = fill(calm, known)
    # masts: per column, how much darker than the air the 8 rows over the part are, and their colour
    cols = np.arange(x1 - x0)
    over = np.stack([crop[top - k, cols] for k in range(3, 11)])                  # 8 rows, every column
    dark = ((np.stack([calm[top - k, cols] for k in range(3, 11)]) - over) @ LUM).mean(0) / 255
    mast = (dark > 0.04) & (over.mean(0) @ LUM < 0.3 * 255)                      # darker than the air, and dark: no flame
    edges = np.flatnonzero(np.diff(np.concatenate([[0], mast.astype(np.int8), [0]])))
    for a, b in zip(edges[::2], edges[1::2]):
        if b - a > MAST or not part[top[a] + 2, a]:
            mast[a:b] = False
        else:
            print(f"mast of the {name} walk goes on down at columns {x0 + a} to {x0 + b - 1}", flush=True)
    # the row just over the part goes on down into it and, ever more blurred, gives way to the air: no straight edge
    last = (crop[top - 2, cols] + crop[top - 3, cols])[None] / 2
    for d in range(REACH):
        share = 1 - (d / REACH) ** 2 * (3 - 2 * d / REACH)
        down = cv2.GaussianBlur(last, (0, 0), sigmaX=0.5 + 0.4 * d, sigmaY=0.01)[0]
        rows = np.minimum(top + d, y1 - y0 - 1)
        air[rows, cols] = air[rows, cols] * (1 - share) + down * share
    # and so does the column beside the first column of the part: the far wall goes on behind the crowd and into the air
    xa = WALKS[name]["span"][0] - x0
    last = (crop[:, xa - 2] + crop[:, xa - 3])[:, None] / 2
    for d in range(BESIDE):
        share = 1 - (d / BESIDE) ** 2 * (3 - 2 * d / BESIDE)
        air[:, xa + d] = air[:, xa + d] * (1 - share) + cv2.GaussianBlur(last, (0, 0), sigmaX=0.01, sigmaY=0.5 + 0.15 * d)[:, 0] * share
    alpha = cv2.GaussianBlur(mast.astype(np.float32)[None], (0, 0), 0.8)[0][None, :, None]
    air = air * (1 - alpha) + over.mean(0)[None] * alpha
    fine = ((crop - cv2.GaussianBlur(crop, (0, 0), 1.5)) @ LUM)[:int(top.min()) - 12]      # the grain of the air over the part
    grain = 1.48 * np.median(np.abs(fine - np.median(fine)))
    air += cv2.GaussianBlur(np.random.default_rng(7).normal(0, 1, air.shape[:2]).astype(np.float32), (0, 0), 0.7)[..., None] * grain * 1.3
    a = cv2.GaussianBlur(part.astype(np.float32), (0, 0), 1.2)[..., None]
    plate[y0:y1, x0:x1] = np.clip(crop * (1 - a) + air * a, 0, 255).astype(np.uint8)
    print(f"far side of the {name} walk set as air: {int(part.sum())} px", flush=True)
    return plate


def painter():
    """The image model, and the plate with the parapet mask."""
    import torch
    from diffusers import ZImageInpaintPipeline
    plate = np.asarray(Image.open(os.path.join(GEN, "plate_muster_banners.png")).convert("RGB")).copy()
    front = np.asarray(Image.open(os.path.join(ROOT, "wip", "muster", "parapet.png"))) > 127
    return ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda"), plate, front


def clear():
    """The plate without the large figures on its walks: the image model paints the far side of each walk."""
    pipe, plate, front = painter()
    for name in WALKS:
        plate = far_side(pipe, plate, front, name, SEED[name]) if name in SEED else haze(plate, front, name)
    Image.fromarray(plate).save(os.path.join(GEN, "plate_muster_empty.png"))
    print("wrote wip/gen/plate_muster_empty.png")


def tries(name, *seeds):
    """The far side of one walk painted with several seeds, one under the other, to choose SEED from."""
    pipe, plate, front = painter()
    x0, y0, x1, y1 = SIDES[name]["view"]
    page = np.concatenate([far_side(pipe, plate, front, name, int(seed))[y0:y1, x0:x1] for seed in seeds])
    out = os.path.join(ROOT, "wip", "muster", f"tries-{name}.png")
    Image.fromarray(page).save(out)
    print("wrote", out, "seeds from the top:", *seeds)


def main(base=os.path.join(GEN, "plate_muster_empty.png")):
    rng = np.random.default_rng(40000)
    plate = np.asarray(Image.open(base).convert("RGB")).astype(np.float32) / 255
    front = cv2.GaussianBlur(parapet().astype(np.float32), (0, 0), 0.8)
    air = cv2.GaussianBlur(plate, (0, 0), 25)
    sets = {view: figures(view) for view in {walk["view"] for walk in WALKS.values()}}
    H, W = plate.shape[:2]
    colour, cover = np.zeros_like(plate), np.zeros((H, W, 1), np.float32)      # the crowd, as colour times cover, and how much of each pixel it covers
    xs = np.arange(W, dtype=np.float32)
    for name, walk in WALKS.items():
        # the floor under the figures: dark, between its two lines, inside the span of the walk
        far, near = lines(walk, xs)
        cols = (xs >= walk["span"][0]) & (xs <= walk["span"][1])
        rows = np.arange(H, dtype=np.float32)[:, None]
        floor = ((rows >= ending(walk, xs)[None]) & (rows <= near[None] + 2) & cols[None]).astype(np.float32)
        floor = cv2.GaussianBlur(floor, (0, 0), 0.8)[..., None]          # no stepped edge
        floor = floor * np.clip((rows - far[None]) / (1.6 * walk["veil"] * (near - far)[None] + 1e-3), 0, 1)[..., None]
        colour = colour * (1 - floor) + air * 0.3 * floor
        cover = cover * (1 - floor) + floor
        # the figures: what each slot of the cell is
        g, ch, slot, turn, lanes = stand(walk, rng)
        figs, kinds, shares, bearers = sets[walk["view"]]
        mean, size = np.array([fig["mean"] for fig in figs], np.float32), np.array([fig["size"] for fig in figs])
        slots = len(ch["f"])                                          # the chains: what a figure is, it is by its chain
        # blocks: lanes that lie BLOCK[1] apart are of one kind, and the share PURE of their figures is of that kind;
        # in a crowd that stands a block is BLOCK[0] long as well
        band = np.unique(np.floor(ch["lane"] * FILE / BLOCK[1]) * 1000 + np.floor(ch["r"] / BLOCK[0]), return_inverse=True)[1]
        kind = rng.choice(len(kinds), band.max() + 1, p=shares)[band]
        mixed = rng.random(slots) > PURE
        kind[mixed] = rng.choice(len(kinds), mixed.sum(), p=shares)
        pick = np.zeros(slots, int)
        for k, members in enumerate(kinds):
            pick[kind == k] = rng.choice(members, (kind == k).sum())
        carries = (rng.random(slots) < BEARERS[0]) & (not walk["pace"])      # a crowd that walks has none: see BEARERS
        pick[carries] = rng.choice(bearers, carries.sum())
        worn, dirt = rng.uniform(*WORN, slots), rng.uniform(*DIRT, slots)
        spread = lambda of: 1 + np.clip(rng.normal(0, PERSON[of][0], slots), -PERSON[of][1], PERSON[of][1])
        height = size[pick] * spread("height")                        # every figure its own height
        girth = np.round(spread("girth") / 0.04) * 0.04
        lean = np.round(rng.uniform(-PERSON["lean"], PERSON["lean"], slots) / 0.035) * 0.035
        mirrored = rng.random(slots) < 0.5
        # light: a slow change of brightness over the floor, and the fires behind the walk
        cells = cv2.GaussianBlur(rng.random((64, 64)).astype(np.float32), (0, 0), 1.2)
        cells = (cells - cells.min()) / (cells.max() - cells.min())
        burning = fires(plate, walk)
        # the first frame of the loop, far to near: this is what the plate shows
        f, r = M.way(ch, slot, turn, 0.0)[:2]
        x, y, tall, depth, ok = M.place(g, f, r)
        sel = np.flatnonzero(ok)[np.argsort(-depth[ok])]
        host = np.stack([x, y, tall, depth, f / g["wide"], r, f], 1)[sel]
        of = slot[sel]                                                # the slot of each figure of that frame
        pick_, worn_, dirt_, girth_, lean_, mirrored_ = pick[of], worn[of], dirt[of], girth[of], lean[of], mirrored[of]
        shade = M.shading(cells, host[:, 6], host[:, 5])
        glows = M.firelight(burning, x[sel], host[:, 3])              # the share of each fire's light on each figure
        lit = shade[:, None] + FIRE * glows.sum(1)[:, None]
        thin = 1.0 - np.exp(-(host[:, 3] / walk["eye"] / HAZE) ** 1.5)  # the share of air in the colour of a figure at its depth
        thin = 1.0 - (1.0 - thin) * np.clip((1.0 - host[:, 4]) / walk["veil"], 0, 1)      # the far rows stand in the smoke: they take its colour, and stay solid
        host[:, 2] *= height[of]
        tiny = host[:, 2] < SMALL
        # far crowd: strokes
        t = host[tiny]
        tx, ty = np.clip(t[:, 0].astype(int), 0, W - 1), t[:, 1].astype(int)
        c = mean[pick_[tiny]] * worn_[tiny, None]
        c = (c * (1 - dirt_[tiny, None]) + (c @ LUM)[:, None] * WARM * dirt_[tiny, None]) * lit[tiny]
        for up in range(SMALL):
            on = (t[:, 2] > up) & (ty - up >= 0) & (ty - up < H)
            yy = ty[on] - up
            colour[yy, tx[on]] = c[on] * (1 - thin[tiny][on, None]) + air[yy, tx[on]] * thin[tiny][on, None]
            cover[yy, tx[on]] = 1
        # near crowd: pictures, far to near
        for k in np.where(~tiny)[0]:
            x, y, tall = host[k, :3]
            h = int(min(round(tall), TALLEST))
            rgb, alpha, foot = sized(figs[pick_[k]], h, girth_[k], lean_[k], mirrored_[k])
            w = rgb.shape[1]
            x0, y0 = int(round(x - foot)), int(round(y)) - h
            cut = (slice(max(-y0, 0), min(h, H - y0)), slice(max(-x0, 0), min(w, W - x0)))      # the part of it on the plate
            if cut[0].start >= cut[0].stop or cut[1].start >= cut[1].stop:
                continue
            rgb, alpha = rgb[cut], alpha[cut]
            x0, y0, h, w = x0 + cut[1].start, y0 + cut[0].start, rgb.shape[0], rgb.shape[1]
            c = rgb * worn_[k]
            c = (c * (1 - dirt_[k]) + (c @ LUM)[..., None] * WARM * dirt_[k]) * lit[k]
            c = c * (1 - thin[k]) + air[int(min(y, H - 1)) - h // 2, int(np.clip(x, 0, W - 1))] * alpha * thin[k]
            colour[y0:y0 + h, x0:x0 + w] = colour[y0:y0 + h, x0:x0 + w] * (1 - alpha) + c
            cover[y0:y0 + h, x0:x0 + w] = cover[y0:y0 + h, x0:x0 + w] * (1 - alpha) + alpha
        print(f"walk {name}: {int((~tiny).sum())} figures as pictures, {int(tiny.sum())} as strokes; the nearest is {host[-1, 2]:.0f} rows tall", flush=True)
        CROWD.append(dict(name=name, g=g, ch=ch, turn=turn, slot=slot, slots=slots, pick=pick, worn=worn, dirt=dirt, height=height, girth=girth, lean=lean,
                          mirrored=mirrored, cells=cells, burning=burning, mean=mean, floor=floor[..., 0], figs=figs,
                          fires=[(W / 2 + fx * FOCAL / fz, fsize) for fx, fz, fsize in burning]))
    seen = np.repeat(1 - front[..., None], 1, 2)                      # the parapet stands before the crowd
    for walk in WALKS.values():                                       # and the crowd ends where its strip is thinner than 8 rows
        far, near = lines(walk, xs)
        inside = (xs >= walk["span"][0]) & (xs <= walk["span"][1])
        seen[:, inside] *= np.clip((near - far)[inside] / 8.0 - 0.5, 0, 1)[None, :, None]
    done = Image.fromarray((np.clip(plate * (1 - cover * seen) + colour * seen, 0, 1) * 255).astype(np.uint8))
    for out in (os.path.join(GEN, "plate_musterP.png"), os.path.join(ROOT, "wip", "preview", "muster-plate.png")):
        done.save(out)
        print("wrote", out)


CROWD = []                                 # what main() set on each walk, for export()


def export():
    """The crowd for the 3D scene (src/muster.py), which sets every figure anew for each frame: the crowd walks.

    - **Walks** - each walk as src/muster.py place() takes it, the depth of its parapet by column, the line where
      its floor meets the parapet, its shade and its fires
    - **Figures** - of every figure that is in the picture at some moment of the loop: its walk, its place across
      chain and its turn in it, and what its chain is: picture, height, width, lean, dirt. The chains themselves
      as src/muster.py way() takes them
    - **Depth** - the plate gives the depth of the parapet along its line; the rule of this file gives the depth of
      a figure in figure heights. The scene sets a figure as deep as the point of that line with the same depth by
      the rule (src/muster.py deep)
    - **Floor** - a dark surface under the figures, as in the plate
    - **Behind** - the part of the plate that lies behind each crowd (`region`) and the depth behind its farthest
      figure by column (`walk_behind`) go into the crowd file. src/muster.py things makes the surfaces of the plate
      from its list of things; this file moves no depth of the plate
    """
    main()
    scene = os.path.join(ROOT, "wip", "scene3d", "muster")
    d = dict(np.load(scene + "_clean.npz"))
    K, H, W = d["intrinsics"], *d["depth"].shape
    plate = np.asarray(Image.open(os.path.join(GEN, "plate_muster_empty.png")).convert("RGB")).astype(np.float32) / 255
    air = cv2.GaussianBlur(plate, (0, 0), 25)
    front = parapet()
    xs = np.arange(W, dtype=np.float32)

    def space(x, y, z):                                               # plate pixel and depth to the camera's space
        return np.stack([((x + 0.5) / W - K[0, 2]) / K[0, 0] * z, z, -((y + 0.5) / H - K[1, 2]) / K[1, 1] * z], -1).astype(np.float32)

    walks = dict(a=[], along=[], across=[], eye=[], span=[], last=[], wide=[], veil=[], line=[], zp=[], cells=[], atlas=[], behind=[], least=[])
    chains = {}
    out = dict(walk=[], turn=[], slot=[], pick=[], worn=[], dirt=[], high=[], wide=[], lean=[], flip=[], floor=[], fcol=[], falpha=[],
               lamp=[], fires=[])
    atlases, first = {}, 0
    region = np.zeros((H, W), np.uint8)                               # the part of the plate that lies behind each crowd: the number of its walk, from 1
    for n, c in enumerate(CROWD):
        walk, g = WALKS[c["name"]], c["g"]
        xa, xb = walk["span"]
        far, near = lines(walk, xs)
        # the depth of the parapet by column: the deepest of its upper 12 rows, smoothed along the walk
        zp = np.full(W, np.nan, np.float32)
        for x in range(xa, min(xb, W - 1) + 1):
            rows = np.flatnonzero(front[:, x] & d["mask"][:, x])
            if len(rows):
                zp[x] = d["depth"][rows[:12], x].max()
        known = np.flatnonzero(np.isfinite(zp))
        zp = np.interp(xs, known, zp[known])
        zp = np.exp(cv2.GaussianBlur(cv2.medianBlur(np.log(zp)[None].astype(np.float32), 5), (0, 0), 20)[0])
        rule = lambda y: FOCAL * walk["eye"] / np.maximum(y - HORIZON, 1.0)      # the depth of a floor row by the rule of this file
        line = M.parapet(zp, (walk["vanish"],) + tuple(walk["near"]), walk["eye"], walk["span"])
        deep = lambda x, y: M.deep(line, rule(y))                     # in the camera's space, as the scene sets the figures
        # behind the crowd: the plate goes back behind the farthest figure of its column
        rows = np.arange(H, dtype=np.float32)[:, None]
        cols = ((xs >= xa) & (xs <= xb))[None]
        part = (rows >= np.interp(xs, [xa, xb], SIDES[c["name"]]["top"])[None]) & (rows <= near[None] + 2) & cols & ~front
        # and what stands on the parapet but was measured as deep as the crowd: a lantern post, which the image model
        # drew down to the rail when it took the crowd out. Every figure that walked past it changed from before it
        # to behind it in one frame. The plate with its painted crowd shows the crowd before such a post
        least = 0.97 * M.deep(line, rule(near) - sum(M.BODY))         # no figure of the column is nearer than this
        part |= front & cols & (rows <= near[None] + 2) & (d["depth"] > least[None])
        top = ending(walk, xs)
        top = np.where(np.isfinite(top), top, far)                    # the far end of the floor in each column
        behind = 1.15 * deep(xs, np.maximum(top, HORIZON + 1.0))
        region[part] = n + 1
        # the floor: a grid of 16 columns by 10 steps from the far edge to the near edge
        gx = np.arange(xa, xb + 1, 16, dtype=np.float32)
        t = np.linspace(0, 1, 11, dtype=np.float32)[:, None]
        edge = np.interp(gx, xs, top)[None]
        gy = edge + (np.interp(gx, xs, near)[None] + 2 - edge) * t
        gxx = np.broadcast_to(gx[None], gy.shape)
        grid = space(gxx, gy, deep(gxx, gy) * 1.01)
        ix, iy = np.clip(gxx.astype(int), 0, W - 1), np.clip(gy.astype(int), 0, H - 1)
        quad = lambda a: np.stack([a[1:, :-1], a[1:, 1:], a[:-1, 1:], a[:-1, :-1]], 2).reshape(-1, 4, *a.shape[2:])
        out["floor"].append(quad(grid)); out["fcol"].append(quad(air[iy, ix] * 0.3)); out["falpha"].append(quad(c["floor"][iy, ix]))
        # the walk and its figures
        view = walk["view"]
        if view not in atlases:
            atlases[view] = atlas(c["figs"], scene + f"_atlas_{view}.png") + (c["mean"],)
        shape = atlases[view][1]
        for key, value in (("a", g["a"]), ("along", g["along"]), ("across", g["across"]), ("eye", g["eye"]), ("span", g["span"]), ("last", g["last"]),
                           ("wide", g["wide"]), ("veil", walk["veil"]),
                           ("line", (walk["vanish"],) + tuple(walk["near"])), ("zp", zp), ("cells", c["cells"]), ("atlas", list(atlases).index(view)),
                           ("behind", behind), ("least", least / 0.97)):
            walks[key].append(np.asarray(value, np.float32))
        of = c["slot"]
        for key, value in c["ch"].items():
            chains.setdefault(key, []).append(value)
        for key, value in (("walk", np.full(len(of), n)), ("turn", c["turn"]), ("slot", first + of), ("pick", c["pick"][of]), ("worn", c["worn"][of]),
                           ("dirt", c["dirt"][of]), ("high", c["height"][of]), ("wide", shape[c["pick"][of]] * c["girth"][of]), ("lean", c["lean"][of]),
                           ("flip", c["mirrored"][of])):
            out[key].append(np.asarray(value, np.float32))
        out["lamp"] += [(n, fx, fz, size) for fx, fz, size in c["burning"]]
        out["fires"] += [(fx, HORIZON, size) for fx, size in c["fires"]]
        first += c["slots"]
        print(f"walk {c['name']}: depth of the parapet {zp[xa]:.1f} to {zp[min(xb, W - 1)]:.1f} m, {len(of)} figures in {c['slots']} slots", flush=True)
    small = cv2.resize(air, (W // 8, H // 8), interpolation=cv2.INTER_AREA)
    np.savez_compressed(scene + "_crowd.npz", views=np.array(list(atlases)), slots=first, air=small.astype(np.float32), region=region,
                        lamp=np.array(out.pop("lamp"), np.float32).reshape(-1, 4), fires=np.array(out.pop("fires"), np.float32).reshape(-1, 3),
                        **{"walk_" + key: np.stack(value) for key, value in walks.items()},
                        **{"chain_" + key: np.concatenate(value) for key, value in chains.items()},
                        **{f"{what}_{view}": np.asarray(a[k], np.float32) for view, a in atlases.items() for k, what in ((0, "rect"), (2, "rows"), (3, "mean"))},
                        **{key: np.concatenate(value).astype(np.float32) for key, value in out.items()})
    # the plate the things are cut from (src/muster.py things): the plate without cloth, with the edge of each painted far side toned
    cv2.imwrite(scene + "_plate.png", seam(cv2.imread(scene + "_clean.png"), front))
    print("wrote", scene + "_crowd.npz, _atlas_<view>.png, _plate.png")


def atlas(figs, path):
    """All figures of one view in one picture, each at LEVELS sizes: 256 rows tall (a bearer 448), then half of that,
    and so on, in rows of at most 4096 columns. With one size only, a figure of 20 rows was drawn from a picture of
    256 rows: the renderer read one texel in thirteen, other texels in every frame, and the crowd flickered.
    Returns the place of each figure at each level as (u0, v0, u1, v1), v upwards; the width over the height of each
    figure; the rows of each figure at its largest size."""
    cells, x, y, row = [], 0, 0, 0
    high = np.array([448 if fig["size"] > 1.3 else 256 for fig in figs])
    for level in range(LEVELS):
        for fig, h in zip(figs, high >> level):
            im = fig["im"].resize((max(round(fig["im"].width * h / fig["im"].height), 1), int(h)), Image.LANCZOS)
            if x + im.width + 4 > 4096:
                x, y, row = 0, y + row + 4, 0
            cells.append((im, x, y))
            x, row = x + im.width + 4, max(row, int(h))
    page = Image.new("RGBA", (4096, y + row), (0, 0, 0, 0))
    for im, x, y in cells:
        page.paste(im, (x, y))
    page.save(path)
    rect = np.array([(x / 4096, 1 - (y + im.height) / page.height, (x + im.width) / 4096, 1 - y / page.height) for im, x, y in cells], np.float32)
    return rect.reshape(LEVELS, len(figs), 4), np.array([im.width / im.height for im, _, _ in cells[:len(figs)]], np.float32), high


def sheet():
    """The sheet for the user: their picture, the prototype plate, the plate with the crowd, and both walks of the
    prototype and of the plate at the same enlargement."""
    from PIL import ImageDraw, ImageFont
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 26)
    wide = SIZE[0]
    user = Image.open(os.path.join(ROOT, "resources", "assets", "scenes", "mechanicum.png")).convert("RGB")
    first = Image.open(os.path.join(GEN, "plate_musterC_3.png")).convert("RGB")
    plate = Image.open(os.path.join(GEN, "plate_musterP.png")).convert("RGB")
    left, right = (0, 440, 760, 690), (1976, 430, 2432, 580)          # the near part of each walk
    parts = [("your picture", user.resize((wide, round(user.height * wide / user.width)), Image.LANCZOS)),
             ("prototype C3: its own figures", first), ("plate with the crowd, figures at half that size", plate)]
    for name, box in (("left walk", left), ("right terrace", right)):
        k = wide / 2 / (box[2] - box[0])
        pair = Image.new("RGB", (wide, round((box[3] - box[1]) * k)))
        for n, picture in enumerate((first, plate)):
            pair.paste(picture.crop(box).resize((wide // 2, pair.height), Image.LANCZOS), (n * wide // 2, 0))
        parts.append((f"{name}, enlarged {k:.1f} times: prototype C3 | plate with the crowd", pair))
    page = Image.new("RGB", (wide, sum(p.height + 40 for _, p in parts)), (24, 22, 22))
    draw, y = ImageDraw.Draw(page), 0
    for name, picture in parts:
        draw.text((10, y + 5), name, fill=(255, 220, 140), font=font)
        page.paste(picture, (0, y + 40))
        y += picture.height + 40
    out = os.path.join(ROOT, "wip", "preview", "muster-plate-sheet.png")
    page.save(out)
    print("wrote", out, page.size)


if __name__ == "__main__":
    {"clear": clear, "tries": tries, "stand": main, "sheet": sheet, "export": export}[sys.argv[1]](*sys.argv[2:])
