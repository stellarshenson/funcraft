"""The muster scene: a crowd of Mechanicum personnel on two rampart walks under banners, after the user's picture
resources/assets/scenes/mechanicum.png.

    python3 src/muster.py map        # wip/preview/motion-muster.png: every element that moves, and how
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/muster.py cloth
                                     # wip/scene3d/muster_cloth.png: the cloth of every banner, wip/preview/muster-cloth.png
    ... src/muster.py clean          # wip/scene3d/muster_clean.png: the plate without the cloth of its banners
    ... src/img2geometry.py wip/scene3d/muster_clean.png      # its depth (MoGe-2)
    python3 wip/muster/host.py export                         # the crowd in the camera's space, wip/scene3d/muster_crowd.npz
    python3 src/muster.py posts                               # wip/scene3d/muster_posts.npz: the post of every banner, measured; wip/preview/posts-muster.png
    python3 src/muster.py banners                             # wip/scene3d/muster_banners.npz and .png: the cloths as meshes
    blender -b -P src/muster.py -- wind                       # wip/scene3d/muster_wind.npz: every cloth through the loop
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv-moge/bin/python src/muster.py sky
                                     # wip/scene3d/muster_sky.png: the air behind the painted smoke, wip/preview/muster-sky.png
    python3 src/muster.py things                              # wip/scene3d/muster_back.*, muster_things.npz, muster_thing_<id>.png; wip/preview/things-muster.png
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/fire.py muster      # wip/sim/muster/: every fire and the smoke column, simulated
    CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 .venv-moge/bin/python src/dust.py muster      # wip/sim/muster/dust<n>.npz: the dust of each walk
    python3 src/muster.py flames                              # wip/scene3d/muster_still.png, muster_flames.npz, wip/preview/muster-flames.png
    python3 src/muster.py assemble wip/frames-muster out/16-muster.avif
    CUDA_VISIBLE_DEVICES=1 blender -b -P src/muster.py -- preview [frame]      # one still, wip/preview/scene-muster.png
    CUDA_VISIBLE_DEVICES=1 blender -b -P src/muster.py -- frames 0 30    # those frames, wip/frames-muster/f000.png ...
    CUDA_VISIBLE_DEVICES=1 blender -b -P src/muster.py -- frames         # all frames and seam-check.png

The plate is designed in wip/muster/ (drafts.py, banners.py, figures.py, host.py; DESIGN.md section 5.11). This file
holds what moves in it. The owner reviews the motion map before anything is built (DESIGN.md section 5.1).

- **Banners** - the user: "banners are made out of cloth and must be animated such with the help of physics model,
  where gusts of wind make the movement believable". A banner is a cloth simulated in Blender, held at its crossbar,
  in a wind that comes in gusts. The far, small banners stay painted
  - **Mesh** - one vertex per GRID plate pixels where SAM 2.1 found cloth, flat at the depth of the cloth; the row
    under the crossbar is held (`banners`). Rags are strips of their own and move alone
  - **Frame** - the post of each banner is measured in the source picture and built as a round rod (`posts`,
    src/rods.py); the crossbar stands on it, and the cloth hangs just before the two. The pikes on the far wall of
    the left terrace are rods too (PIKES), at the depth of the wall they stand on: the fires burn behind them
  - **Wind** - each cloth has a wind of its own direction WIND_TO: the same course of strength through the loop
    (GUSTS, and the gusts of GUST, which pass all banners from left to right), later for a banner further right. It
    has no steady share (STEADY): after a gust the air flows back, and the cloth swings about hanging straight. The course
    repeats every loop, so the cloth settles into a motion that repeats. Three loops are simulated, the third is
    kept, and its last CLOSE frames are led over into its first frame. The simulated loop is CALM times shorter
    than the loop and is shown over the whole of it
  - **Same answer from every cloth** - Blender gives every vertex one weight, and a wind pushes a face by its
    area: a cloth with more vertices per square metre is heavier and answered six times less. The wind of each
    cloth is therefore multiplied by its number of vertices per square metre
  - **Size** - the figures are half as tall as those the plate was drawn for, so a banner is twice as large as
    the scene's own measure says; gravity acts with half its strength, which gives the cloth the pace of that size
  - **Light** - the plate's cloth has its light painted in. A fold of the simulated cloth is shown by its slope:
    a face turned to the light LAMP is brighter by FOLD times the change of its slope
- **Flames** - the user on flames that were the plate's own pixels carried upward: "the flames don't look real,
  they move too fast and they seem to be animated, not simulated", "the fire is far away, there is no way convection
  will move the fire so fast". Every fire is simulated as a gas in metres and seconds (src/fire.py), at its real
  width: its width on the plate over `scale`, the plate pixels per metre at its place. Its pace follows its size
  on the plate (FAR). `flames` takes the painted flames out of the plate, gives the simulated ones the colours of
  the painted ones and sets each as a picture at the place of its bed. The glow round a fire and the light of a
  fire on the crowd follow the light of the simulated flame
- **Smoke column** - simulated as the fires are: a fire that burns out of sight behind the far wall, in a higher
  box of air, of which only the soot is shown (src/fire.py, `column`). The two plumes of the plate are taken out
  (THINGS). The user on a first version, in which the plate's own pixels were carried along inside a box: "smoke
  must not be animated as pixels, must be animated as smoke using physiscs"; that box also moved the tops of two
  banner posts
- **No sparks** - small lights that rose from every fire were built first; the user: "elliminate sparks please"
- **Dust** - the user: "let the crowd be also a little interwoven with dust and dirtiness". HAZE curtains per walk
  stand across it between the ranks, from the floor up; each shows the dust of a strip of air, simulated (src/dust.py)
- **Sigils** - the user: on the left banners the Mechanicum sigil, on the right banners the Stellars Tech sigil,
  "well crafted so it fits the colours". Each lies on its cloth, is as worn as its cloth and moves with it
- **Crowd** - every figure is an element of its own: a card with its picture. The user on a crowd that stepped
  and swayed at its place: "the crowd seems to not be mooving forward in the gallery (towads image depth), instead
  they just animate as moving in place". The crowd of the left walk walks away from the camera. A crowd on the
  right terrace that walked towards the camera got: "please, no, let that crowd behave on this side like last
  time"; it stands
  - **Loop** - the loop closes only if the figure that arrives at a place equals the one that left it. A figure is
    one of a chain: its copies follow it on the same way, each one loop behind the one before it (`way`). A crowd
    that went 5.4 m in a loop of 4 s got: "crowd moves too fast; it must move slowly and irregularly", "the same
    person occurs every few centimeters". A slow pace and a distance between the copies need a long loop: 12 s
  - **Uneven** - each lane has CHAINS chains and its own pace, so no group of figures stands a second time; each
    chain has a pace that changes (UNEVEN); height, brightness and dirt of a figure change slowly along its way
    (DRIFT), so its next copy differs from it
  - **Place and person** - what a place gives stays there: size, depth, the light of the fires, the shade, the
    haze. What a figure is walks with it: its picture, its girth, its step. `place` gives, for each frame, where
    a figure stands on the plate; the pose sets every card from that
  - **Solid** - the user: sprites "were appearing and disappearing - very poor". No figure covers less than its
    picture does; a figure comes in and goes out beside the picture or where it is a pixel tall; a card shows two
    sizes of its picture, mixed; a figure under SMALL rows is a stroke, and at SMALL rows the two look alike
  - **Passing** - the user: "clipping still happens, because there is no hysteresis, and clipping is done to the
    entire object, doesn't work progressively". Two flat cards that overlap changed their order in one frame. The
    card of a walking figure has the depth of a body (BODY, ROUND), so the line between two figures moves across
    what they share while one passes the other. Moving passing figures apart was built and removed: "do not
    disperse the crowd, simply allow for more gradual transitions"
  - **Step** - a walking figure steps by the way it has gone (STEP) and less while it slows; a standing one shifts
    its weight STEPS times per loop. It rises by RISE of its height and sways by SWAY; the light of every fire on
    it changes with that fire
- **Loop** - 360 frames at 30 frames per second, 12 s, written as an animated AVIF. The user: "when planning video
  render - use high 2h res and 30fps". The frames are rendered at the plate's own size, 2432 x 768: one pixel of the
  render per pixel of the plate, which is all the detail the plate has
"""
import os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENE = os.path.join(ROOT, "wip", "scene3d", "muster")
FRAMES, RATE = 360, 30
RES, SAMPLES = (2432, 768), int(os.environ.get("MUSTER_SAMPLES", 64))      # the plate's own size
LOOP = FRAMES / RATE                       # seconds
# a figure that walks: the length of its step in figure heights, between these two. A figure that stands shifts its
# weight STEPS times per loop and sways SWAYS times, one of each. How far a step lifts a figure and how far its head
# goes to each side, as shares of its height: for one that walks, for one that stands
STEP, STEPS, SWAYS = (0.26, 0.34), (9, 10, 11, 12), (3, 4, 5, 6)
RISE, SWAY = (0.03, 0.06), (0.02, 0.045)
LEAST = 0.6                                # no figure rises or sways by less than this many plate pixels
# the rule that sets the crowd on the plate (wip/muster/host.py): the size of the plate, the row of its horizon, its
# focal length in pixels; no figure stands nearer than NEAREST figure heights; a figure under SMALL rows is a stroke
PLATE, HORIZON, FOCAL, NEAREST, SMALL = (2432, 768), 448, 2000.0, 10.0, 3
# a lane of a walking crowd holds one of these numbers of different figures, RANK figure heights apart on average: it
# walks that far in a loop, and then the next figure of each chain stands where the one before it stood
CHAINS, RANK = (5, 6, 7), 0.5
# the pace of a walking figure changes by these shares of its mean pace, each over a period between these seconds: it
# slows almost to a stand and goes on. It goes to each side of its lane by up to this many figure heights, over a
# period between these seconds
UNEVEN, ASIDE = ((0.4, 0.3, 0.2), (2.5, 6.0)), (0.08, (5.0, 12.0))
# along its way the height, the brightness and the dirt of a walking figure change slowly by these shares, over a
# period between these numbers of loops: the next figure of its chain is then not its copy
DRIFT = ((2.3, 4.7), 0.03, 0.08, 0.08)
DEEPER = 1.06                              # the nearest figures stand this many times as deep as the parapet
# the middle of a figure that walks stands BODY[0] figure heights nearer than its two sides, and its head up to BODY[1]
# nearer than its feet, another share of it for every chain. A figure that is ROUND[0] plate rows tall at a moment of
# the loop has a card of ROUND[1] strips across with that depth
BODY, ROUND = (0.30, 0.10), (8, 8)
MURK, REACH = 90.0, 6.0                    # the depth at which a figure has 63 % of the air's colour, over the camera's height; the reach of a fire's light in its sizes
SHADOW = (0.65, 1.25)                      # the brightness of the crowd in the darkest and in the brightest place
SHADE = 0.6                                # the brightness of a figure's feet against its head, as wip/muster/host.py has it
FIRE = (1.5, 0.7, 0.25)                    # the light of a fire on a figure beside it, as wip/muster/host.py has it
WARM = (1.276, 0.944, 0.740)               # the colour of dirt, as wip/muster/host.py has it
GRID = 36                                  # a cloth is this many vertices wide, and at least 3 plate pixels between them
WIND_TO = (0.72, 0.69, 0.0)                # where the wind blows to (x right, y into the picture, z up)
BLOW = float(os.environ.get("MUSTER_BLOW", 55.0))     # its mean strength on a cloth of 100 vertices per square metre
# the steady share of the wind at the banners. With a share of 1 the wind never turned and held the lower part of
# every cloth 0.2 to 0.5 m deeper than at rest: the right banners leaned 12 to 21 plate pixels to the left. With this
# share and the gusts the wind comes to nothing over a loop: a gust blows into the picture, the air flows back after
# it, and a cloth swings about hanging straight, as the source picture shows it
STEADY = -0.1
GUSTS = ((1, 0.15), (3, 0.22), (5, 0.20), (8, 0.14))      # the course of the wind: cycles per loop and share
# the gusts: the moment in the loop and the strength of each; the length of a gust and its travel over the plate, in loops; the frames led over
GUST, CLOSE = (((0.12, 1.1), (0.47, 0.8), (0.80, 1.0)), 0.023, 0.1), 60
# the cloth is simulated for a loop this many times shorter and shown over the whole loop: every motion of it takes
# that much longer, as that of a cloth CALM squared times as large. The owner on banners at the pace of the simulation:
# "considering their size, the gravity + wind wouldn't be able to move them such quickly, and because of this the scene
# feels small", "slightly slow them down"
CALM = 1.3
LAMP, FOLD = (-0.45, -0.60, 0.66), 0.5     # the light on the cloth comes from here; how much a fold changes the brightness
GLOW = 0.5                                 # the glow round a fire changes by this share of the change of the fire's light
EMBERS = 748                               # from this row down the fire in the gorge stays as painted: its bed of wreckage
# the pace of a fire: every fire moves as a fire that is this many metres wide per plate pixel of its bed, as if all
# fires stood at one distance. Each fire first moved at the pace of its own width, and the gas of none rose faster
# than 8 m/s: a brazier 4 m wide then flickered 20 times as fast, against its size on the plate, as the fire in the
# gorge. The owner: "main flame at the center is too slow, while flames on the sides are too fast"
FAR = 2.5
# a unit of soot per width of a fire covers this much; its colour against the air behind it; over the bed it thins out
# between these two heights, in widths of the fire: without that the soot of a wide fire stood as a dark box of smoke
SOOT = (2.5, 0.42, 1.0, 2.8)
# the smoke between a fire and the camera spreads its light: a blur in plate pixels and the share of the light that goes
# into a wide halo, each as (at the camera, more per 100 m); and the width of the halo in plate pixels
SCATTER = ((0.6, 0.45), (0.10, 0.05), 9.0)
BEYOND = 100.0                             # the column of smoke rises before what the plate shows farther than this many metres: the crane, the far city
THICK = 2.3                                # a column of smoke: the soot that the densest tenth of its picture has or exceeds covers 90 % of what is behind it
# dust among the crowd (src/dust.py): per walk the wind along its sheets, 2 m over the floor, in m/s, and how much dust
# its crowd raises: one that walks raises more than one that stands. Curtains of dust per walk, each across the walk at
# one rank, and how much of what is behind it a curtain covers per unit of dust when the next curtain is 20 m away
DUST = ((1.2, 1.0), (1.0, 0.4))
HAZE, THIN = 9, 1.4
OVER = (0.9, 1.9)                          # the bodies of a crowd hide the dust between them: a curtain shows none under the first height, in metres, and all of it from the second
BAR = 0.05                                 # the share of a banner's box, from its top, that is crossbar and stays in the plate
WIND = "from the left"
# every element: id, kind, box on the plate (x0, y0, x1, y1), and for a crowd the corners of its floor
# a fire: `scale`, the plate pixels per metre at its place. The figures are 1.8 m tall, and the perspective that sets
# their size says how far a place is: at the far end of the left walk a figure is 3.5 pixels tall. The measured depth
# of the plate (MoGe-2) puts that end 3.4 times nearer, and scales taken from it made the far fires 4 times too small;
# the owner: "the size of that fire is likey in 100s of meters". F3 burns behind the far end of the left walk, F6 on
# the far bridge, F7 in the gorge before it: about 200 m wide in all; `wind`, the mean wind there in m/s. A wind leans
# a flame by its speed against the speed of the fire's gas, which grows with the root of the fire's width: the wind of
# the gorge is set so that its wide fires lean as the narrow ones do
# there in m/s (the gorge is sheltered); `beds`, each bed of fire as the column of its middle, the row of its foot
# and its width on the plate; `painted`, the box of the painted flames of each bed where it is not the fire's box;
# `fine`, how many times smaller the cells of its simulation are; `smoke`, the share of its soot that is shown;
# `lumps`, the heaps of fuel of a bed; `deep`, the depth of a bed in widths; `tall`, how many times longer its fuel
# burns
ELEMENTS = [
    dict(id="B1", kind="banner", sigil="Mechanicum", box=(255, 55, 400, 428)),
    dict(id="B2", kind="banner", sigil="Mechanicum", box=(560, 172, 656, 430)),
    dict(id="B3", kind="banner", sigil="Mechanicum", box=(696, 232, 768, 412)),
    dict(id="B4", kind="banner", sigil="Mechanicum", box=(797, 272, 853, 410)),
    dict(id="B5", kind="banner", sigil="Mechanicum", box=(884, 302, 933, 412)),
    dict(id="B6", kind="banner", sigil="Mechanicum", box=(933, 327, 972, 414)),
    dict(id="B7", kind="painted", box=(975, 335, 1140, 425)),
    dict(id="B8", kind="painted", box=(1640, 308, 1790, 408)),
    dict(id="B9", kind="banner", sigil="Stellars Tech", box=(1833, 250, 1899, 407)),
    dict(id="B10", kind="banner", sigil="Stellars Tech", box=(1979, 227, 2053, 393)),
    dict(id="B11", kind="banner", sigil="Stellars Tech", box=(2079, 193, 2166, 407)),
    dict(id="B12", kind="banner", sigil="Stellars Tech", box=(2169, 160, 2269, 417), on=[(2178, 177)]),      # its dark hem at the upper left corner, which the cut left out: the corner hung loose
    dict(id="B13", kind="banner", sigil="Stellars Tech", box=(2326, 100, 2432, 420)),
    dict(id="F1", kind="fire", box=(387, 405, 455, 455), scale=5.9, wind=3.5, tall=0.7, beds=[(424, 460, 82)]),
    dict(id="F2", kind="fire", box=(763, 405, 822, 448), scale=5.5, wind=3.0, tall=0.85, beds=[(798, 460, 70)]),
    dict(id="F3", kind="fire", box=(933, 392, 1100, 435), scale=2.0, wind=2.5, lumps=4,
         beds=[(945, 443, 36), (985, 443, 34), (1017, 443, 36), (1062, 440, 24), (1096, 436, 14)],
         painted=[(928, 412, 964, 438), (966, 420, 1002, 438), (1000, 398, 1036, 438), (1048, 410, 1078, 436), (1086, 412, 1104, 432)]),
    dict(id="F4", kind="fire", box=(1838, 392, 1882, 436), scale=8.0, wind=2.5, lumps=10, deep=0.9, tall=1.6, beds=[(1862, 438, 38)]),
    dict(id="F5", kind="fire", box=(1996, 395, 2048, 440), scale=11.0, wind=2.5, lumps=10, deep=0.9, tall=1.6, beds=[(2017, 439, 42)],
         thing="V5", stand=(2022, 442, 534, 6)),      # it burns in the bowl V5 (THINGS). The bowl stood on a rod too thin to see: the column of a stand, its rows from the bowl to the railing, its width
    dict(id="F6", kind="fire", box=(1570, 408, 1598, 432), scale=1.0, wind=2.5, lumps=4, beds=[(1586, 432, 22)]),
    dict(id="F7", kind="pit", box=(1262, 630, 1440, 768), scale=0.9, wind=6.0, lumps=6, deep=0.7, tall=1.6, smoke=0.25,
         beds=[(1298, 754, 48), (1332, 748, 64), (1372, 742, 72), (1408, 732, 56)]),
    # the column of smoke over the fires behind the far wall: a fire of its own behind that wall, of which only the soot
    # is seen (src/fire.py, `column`). Its scale and its wind are those of the fires F3 under it. With half that wind
    # it rose straight, did not leave its box of air and filled it: the box showed as a grey rectangle. `high`, `wide`:
    # its box of air is that many times higher and wider; `lasts`: its soot stays in sight that long, in units of the
    # fire's time. With soot that lasted 10 units in a box of single width, the soot reached the downwind wall and the
    # top of the box at 80 % cover and showed two straight edges in the sky. Under the top of its box the soot spreads
    # as a level layer: the box is so high that its top and that layer lie above the picture
    # A column 20 m wide in the wind of the fires rose nearly straight, as a narrow dark stroke. The user: the one plume
    # must be "slightly more dispersed". It is 30 m wide, and its wind is that of the air 100 m and more over the
    # walls, twice that at the fires: it leans to the right and spreads
    dict(id="S1", kind="smoke", box=(900, 0, 1420, 330), scale=2.0, wind=5.0, high=1.6, wide=2.0, lasts=4.0, beds=[(1010, 400, 60)]),
    dict(id="K1", kind="hook", box=(1166, 228, 1190, 262)),
    dict(id="C1", kind="crowd", view="walks away from the camera, to the bridge", floor=[(0, 505), (1100, 452), (1100, 458), (0, 660)]),
    dict(id="C2", kind="crowd", view="stands, seen from the front", floor=[(2030, 505), (2432, 505), (2432, 566), (2030, 522)]),
]
# the pikes that stand on the far wall of the left terrace: thin dark uprights, 1 to 3 pixels wide. The plate measures
# a thin thing with what lies behind it: they had the depth of the sky (56 to 67 m), the wall they stand on is 27 to
# 45 m deep and the fire behind it burns at 47 m, so its flames were drawn before them (the user: "posts are
# missing"). Each is built as a rod at the depth of the wall under it (thing U1). As (column of its foot, row of its
# tip, row of its foot in the wall, radius at the wall, columns it leans to the right per row down), measured by
# wip/muster/pikes.py at the columns read from the enlarged picture. The radius is that of a straight taper that
# covers as much of each row as the picture shows: most pikes are thinner than a pixel. With radii of 0.7 to 1.6 px,
# taken from the width of their dark trace, they stood as black wedges, heavier than in the picture
PIKES = [(613.3, 443, 452, 0.8, -0.09), (638.2, 446, 452, 0.6, 0.0), (665.9, 444, 452, 0.81, -0.11), (700.1, 442, 453, 0.5, -0.06), (708.7, 446, 452, 0.6, 0.0),
         (720.3, 440, 452, 0.35, 0.02), (825.1, 439, 452, 0.87, -0.11), (834.5, 447, 452, 0.6, 0.0), (842.1, 438, 452, 0.53, 0.08), (855.8, 437, 452, 0.4, 0.12),
         (861.0, 448, 452, 0.6, 0.0), (865.0, 438, 452, 0.73, 0.1), (874.5, 435, 453, 1.08, -0.01), (884.0, 437, 453, 1.22, 0.06), (895.2, 440, 453, 1.24, -0.03),
         (904.1, 444, 453, 0.9, 0.25)]
# the things of the plate (src/things.py, DESIGN.md section 5.13), from the nearest to the farthest. What covers what
# in this scene follows from this list. A fault of the picture is corrected here: a thing is named, is given its
# support, or is taken out
THINGS = [
    dict(id="P1", name="railing of the left walk", mask="railing left", surface="railing left depth", on="frame", before=["C1"]),
    dict(id="P2", name="railing of the right terrace", mask="railing right", surface="railing right depth", on="frame", before=["C2"]),
    dict(id="V5", name="bowl of the brazier", boxes=[(2003, 426, 2044, 444)], limit=0.07, without="flame", mirror=True, on="S5", before=["C2"],
         holds=["fire F5"]),                          # the painted flame hid the right of its rim: the bowl is whole and its rim level
    dict(id="S5", name="stand of the brazier", at=(2019, 442, 2026, 534), on="P2", behind=["P2"], before=["C2"]),      # the user: "it must be behind the railing"
    # a banner is its post, its crossbar with its finial, and its cloth. The source picture shows one post per banner,
    # at the right end of its crossbar. The post is built as a round rod (POSTS; the user: "you must build them as 3d
    # objects"): its pixels are taken out of the plate, and the crossbar stands on it, at its depth: the depth measured
    # for the cloth, the wide surface. The cloth hangs from the crossbar, ends at the post when it hangs straight, and
    # moves in a room just before the two (`swing`, HUNG); the cloth of B13 hangs over its post and hides it. On the walk
    # and on the terrace a banner stands on the floor behind the railing, which hides its foot: the user on a post
    # drawn before the railing: "it must be behind the railing". The banners of the walk stand in one row, 2.4 to 4.2 m
    # from its railing by the depth of their cloths. B1 stands near, and the railing hides its foot. B2 to B6 stand on
    # the floor among the crowd (`among`): the figures before a post hide its foot, the figures behind it pass behind it
    dict(id="M1", name="crossbar and finial of banner B1", dark=True, boxes=[(228, 40, 430, 76), (312, 0, 350, 48)], on="T1", feet=[388]),
    dict(id="T1", name="post of banner B1", mask="post B1", built=True, on="floor", behind=["P1"], holds=["cloth B1"],
         beyond="right"),                             # the source shows the tower right of it along its whole length: the tower goes on behind it
    dict(id="M12", name="crossbar and finial of banner B12", dark=True, boxes=[(2143, 150, 2290, 172), (2203, 116, 2220, 154)], on="T12", feet=[2262]),
    dict(id="T12", name="post of banner B12", mask="post B12", built=True, on="floor", behind=["P2"], holds=["cloth B12"]),
    dict(id="M13", name="crossbar and finial of banner B13", dark=True, boxes=[(2300, 94, 2432, 116), (2368, 40, 2398, 98)], on="T13", feet=[2387]),
    dict(id="T13", name="post of banner B13", mask="post B13", built=True, on="floor", behind=["P2"], holds=["cloth B13"]),      # the plate shows it under the cloth only
    dict(id="M11", name="crossbar and finial of banner B11", dark=True, boxes=[(2056, 186, 2172, 204), (2112, 148, 2133, 188)], on="T11", feet=[2162]),
    dict(id="T11", name="post of banner B11", mask="post B11", built=True, on="floor", behind=["P2"], holds=["cloth B11"]),
    dict(id="M10", name="crossbar and finial of banner B10", dark=True, boxes=[(1966, 218, 2066, 236), (2007, 190, 2022, 222)], on="T10", feet=[2050]),
    dict(id="T10", name="post of banner B10", mask="post B10", built=True, on="floor", behind=["P2"], holds=["cloth B10"]),      # under row 404 two black posts stood before it; they are taken out (R2, R3)
    dict(id="M9", name="crossbar and finial of banner B9", dark=True, boxes=[(1818, 242, 1916, 260), (1856, 219, 1873, 246)], on="T9", feet=[1896]),
    dict(id="T9", name="post of banner B9", mask="post B9", built=True, on="floor", behind=["P2"], holds=["cloth B9"]),
    dict(id="M2", name="crossbar and finial of banner B2", dark=True, boxes=[(541, 163, 682, 186), (598, 124, 624, 168)], on="T2", feet=[652]),
    dict(id="T2", name="post of banner B2", mask="post B2", built=True, on="floor", among="C1", holds=["cloth B2"]),
    dict(id="M3", name="crossbar and finial of banner B3", dark=True, boxes=[(680, 226, 786, 242), (721, 194, 742, 230)], on="T3", feet=[761]),
    dict(id="T3", name="post of banner B3", mask="post B3", built=True, on="floor", among="C1", holds=["cloth B3"]),
    dict(id="M4", name="crossbar and finial of banner B4", dark=True, boxes=[(782, 263, 866, 279), (815, 239, 833, 267)], on="T4", feet=[849]),
    dict(id="T4", name="post of banner B4", mask="post B4", built=True, on="floor", among="C1", holds=["cloth B4"]),
    # the crossbars and finials of B5 and B6 stood before the black base of the painted smoke: they are built as rods
    # too (POSTS, `bar`, `finials`)
    dict(id="M5", name="crossbar and finial of banner B5", mask="frame B5", built=True, on="T5", feet=[929]),
    dict(id="T5", name="post of banner B5", mask="post B5", built=True, on="floor", among="C1", holds=["cloth B5"]),
    dict(id="M6", name="crossbar and finial of banner B6, finials of the far banners beside it", mask="frame B6", built=True, on="T6", feet=[970]),
    dict(id="T6", name="post of banner B6", mask="post B6", built=True, on="floor", among="C1", holds=["cloth B6"]),
    # the masts that the image model painted where the cloths were: they stay, by the user's choice. Each is joined to
    # its crossbar and stands behind the room in which the cloth moves. It stands on its crossbar and lies in the
    # crossbar's picture: as a second picture at the same depth it made the crossbar flicker (src/things.py, `planes`)
    dict(id="N11", name="mast painted under the cloth of B11", dark=True, boxes=[(2112, 204, 2133, 394), (2100, 240, 2145, 256)], on="M11", behind=["swing B11"]),
    dict(id="N10", name="mast painted under the cloth of B10", dark=True, boxes=[(1979, 234, 1994, 334)], on="M10", behind=["swing B10"]),
    dict(id="N9", name="mast painted under the cloth of B9", dark=True, boxes=[(1834, 258, 1848, 404)], rods=[(1834, 258, 1848, 402)], on="M9", behind=["swing B9"]),
    dict(id="N2", name="mast painted under the cloth of B2", dark=True, boxes=[(564, 184, 584, 408)], on="M2", behind=["swing B2"]),
    dict(id="N3", name="mast painted under the cloth of B3", dark=True, boxes=[(700, 240, 716, 414)], on="M3", behind=["swing B3"]),
    dict(id="N4", name="mast painted under the cloth of B4", dark=True, boxes=[(798, 277, 813, 404)], on="M4", behind=["swing B4"]),
    dict(id="R1", name="dark object with a rod and a ball", boxes=[(1936, 358, 1986, 429)], limit=0.07, keep=False, note="stood on nothing"),
    dict(id="R2", name="black post, left", boxes=[(2038, 408, 2054, 428), (2036, 428, 2054, 529)], limit=0, keep=False, note="the owner's choice"),
    dict(id="R3", name="black post, right", boxes=[(2054, 414, 2069, 529)], limit=0.07, keep=False, note="the owner's choice"),
    dict(id="R4", name="orange rod and dark shade under the bowl", boxes=[(2004, 444, 2036, 458), (2022, 458, 2036, 529)], limit=0.07, keep=False,
         note="the stand S5 takes its place"),
    dict(id="R5", name="three remainders of painted cloth", boxes=[(2083, 388, 2118, 428), (2142, 395, 2154, 414), (2169, 408, 2183, 427)], limit=0.07,
         keep=False, note="the cloth of the scene replaces them"),
    dict(id="Q1", name="wreck behind banner B12", boxes=[(2172, 318, 2258, 418)], keep=False, note="painted by the image model behind the cloth; stood on nothing"),
    dict(id="Q2", name="platform on the mast of banner B13", boxes=[(2338, 300, 2432, 368), (2364, 366, 2432, 424)], keep=False,
         note="painted by the image model behind the cloth"),
    dict(id="Q3", name="pole with a crossarm", boxes=[(2322, 240, 2368, 412)], keep=False, note="painted by the image model behind the cloth; stood on nothing"),
    dict(id="Q4", name="three dark shapes in the air", boxes=[(255, 350, 300, 385), (238, 383, 268, 400), (250, 405, 282, 432)], keep=False,
         note="stood on nothing"),
    dict(id="S1", name="smoke of the plate: the dark plume and the pale one behind it", mask="smoke", keep=False,
         note="one column is simulated in their place (ELEMENTS, src/fire.py)"),
    dict(id="U1", name="pikes on the far wall of the left terrace", mask="built U1", built=True, on="W1", feet=[round(p[0]) for p in PIKES]),      # before W1 in the list: their feet stand in the wall
    dict(id="W1", name="the picture behind the left crowd", mask="behind left", surface="behind left depth", on="far", behind=["C1"], region=True),
    dict(id="W2", name="the picture behind the right crowd", mask="behind right", surface="behind right depth", on="far", behind=["C2"], region=True),
]
# the post of each banner. The source picture shows one post per banner, at the right end of its crossbar, from the
# crossbar to the ground. It is measured there and built as a round rod (src/rods.py, `posts`); the user: "you must
# build them as 3d objects". `post`: two places on its axis in the source picture, between which the picture shows it
# (x, y, x, y); `top`, `foot`: the rows at which it begins and ends where the picture does not show that: behind its
# cloth, behind the railing it stands behind, under the two black posts that were taken out; `thick`: its radius in
# plate pixels, for a post too thick for the common search; `plain`: rows between which it has no joint, where the
# picture shows a thing beside it: the rough iron of the nearest post, a figure painted behind a post. No post has a
# joint within PLAIN rows of its ends as given: there its crossbar crosses it, or the wall it stands behind begins;
# `covered`: the cloth hangs over the post, which the picture then shows under the cloth only: its cut does not end at the post;
# `bar`, `finials`: a crossbar (x, y, x, y, radius) and finials (x, top row, lower row, greatest radius) that stood
# before the black base of the painted smoke and went with it: they are built as rods too, in the colour of the post.
# The further finials of B6 are those of the far banners beside it, which are painted
# `joints`: a ball on it that the measure does not find, half in light and half before a cloth, as the row of its
# middle and its radius; `near`: its own NEAR, where the cut of the cloth left out a band beside the post in a part of
# its rows (B1: the grey band of 5 pixels from row 200 to row 358 was cloth down to row 262 and no cloth below).
# B2 to B6: the picture shows each post down to the upper edge of the far wall, where post and wall are equally dark
# and the measure ends. The post stands on the floor of the walk at the depth of its cloth: `foot` is the row at
# which it meets that floor (wip/muster/feet.py). With the posts of B2 to B4 set behind the whole crowd, so that the
# crowd hid their open ends, they stood at the far wall, 6.5 to 7.1 m from the railing and not in the row of B1; the
# user: "banner posts on the left are not put in the ground where they should"
POSTS = {
    "B1": dict(post=(385.5, 48, 372, 586), foot=625, plain=[(48, 586)], joints=[(376, 7.5)], near=9), "B2": dict(post=(650.5, 172, 650.5, 451), foot=534),
    "B3": dict(post=(761.5, 233, 761.5, 448), foot=501), "B4": dict(post=(849, 271, 849, 446), foot=488),
    "B5": dict(post=(929, 302, 929, 443), foot=479, bar=(875, 303.5, 941, 300.3, 1.0), finials=[(908, 278.5, 302, 4.0)]),
    "B6": dict(post=(970.5, 322, 970.5, 440), foot=475, bar=(935, 324.8, 979.5, 323.3, 0.9),
               finials=[(954, 306, 324, 3.0), (988.5, 314, 334, 2.5), (1017, 331, 344, 2.0), (1040.7, 338, 352, 2.0), (1052, 345, 357, 1.8)]),
    "B9": dict(post=(1898, 250, 1898, 510), foot=550),
    "B10": dict(post=(2053, 228, 2053, 400), foot=565), "B11": dict(post=(2165.5, 193, 2165.5, 536), foot=575, plain=[(470, 536)]),
    "B12": dict(post=(2264.5, 163, 2264.5, 541), foot=585), "B13": dict(post=(2387, 374, 2387, 561), top=106, foot=600, thick=6.0, covered=True),
}
PLAIN = 12
# the radius along a crossbar and along a finial from its tip down, as shares of its length and of its radius
ALONG = dict(bar=((0, 0.2), (0.08, 1), (0.92, 1), (1, 0.2)), finial=((0, 0.1), (0.2, 0.35), (0.45, 1), (0.62, 0.55), (0.75, 0.3), (1, 0.3)),
             pike=((0, 0.25), (1, 1)))
# the painted smoke of the plate: the dark plume, the grey cloud behind it and the black base over the far banners lie
# inside this outline. Smoke is what is darker there than the second number, and what lies within the third number of
# pixels of that: the pale rim of the plume, which a mask of the dark pixels alone left in the sky as wisps. The clear
# sky of the plate has a brightness of 0.59 to 0.69, the grey cloud 0.38, the dark plume 0.28. With the whole outline
# painted anew, the image model painted one even colour, and the outline showed against the sky beside it. Its lower
# side follows the crossbars of the far banners, which stay: with a level lower side over their finials, the simulated
# column ended in a straight line over a pale strip
SMOKY = ([(600, 0), (1030, 0), (1030, 150), (1060, 270), (1060, 349), (1038, 348), (1036, 341), (1010, 340), (1008, 332), (975, 331), (965, 328),
          (880, 328), (860, 300), (760, 262), (600, 242)], 0.52, 25)
# what `sky` paints: the part of the plate that the image model sees, its seed, and what it is asked for
AIR = ((576, 0, 1088, 352), 3,
       "Hazy evening sky, soft clouds of warm orange-brown dust haze, pale backlight, only sky and haze, a frame from a war "
       "film, muted colours, grain")
# the painted air goes over into the plate along the edge of the smoke over this many pixels, and at the left side of
# the smoke, where the haze of the plate begins, between these two columns
SEAM = (8.0, (600, 760))
# a cloth hangs before its crossbar and its post: its deepest place in the loop, as a share of the depth of the post
HUNG = 0.985
NEAR = 6                                   # a cloth that ends within this many pixels of its post reaches the post
# what each fire burns in or behind: the fire is shown only over the upper outline of that thing
BURNS = ["F5 burns in V5, the bowl of the brazier: shown over the rim of the bowl, at the depth of the bowl",
         "F1, F2, F3 burn behind the far wall of the left walk (in W1): shown over the top of that wall",
         "F4 burns on the far wall of the right side: shown over the top of that wall",
         "F6 burns on the far bridge, F7 in the gorge: shown over the wreckage they burn on"]
# what `clean` paints: the part of the plate the image model sees for each group of banners, and its seed
BEHIND = [((200, 30, 1016, 454), 2), ((1616, 30, 2432, 454), 2)]
EMPTY = ("Thick brown and orange dust haze and smoke over a forge city at dusk, faint grey silhouettes of distant gothic "
         "spires and smokestacks, tall thin iron masts with bare crossbars, nothing hangs on them, empty air behind, a "
         "frame from a war film, muted colours, grain. No banner, no flag, no cloth, no drapery")
COLOURS = dict(banner=(0, 214, 255), painted=(150, 150, 150), fire=(255, 229, 0), pit=(255, 121, 41), smoke=(249, 0, 213),
               hook=(3, 255, 118), crowd=(120, 255, 120))
LEGEND = [
    ("banner", "B1 to B6, B9 to B13 - banner: a cloth held at its crossbar, simulated with a physics model. The wind blows "
               f"{WIND} and changes in gusts; a large banner answers slowly, a small one fast. Rags and holes move with the cloth"),
    ("banner", "Sigils: Mechanicum sigil on B1 to B6, Stellars Tech sigil on B9 to B13, as gold thread in the banner's own "
               "cloth; each lies on its cloth and moves with it"),
    ("painted", "B7, B8 - far banners: stay as painted, they are 20 to 90 pixels tall"),
    ("fire", "F1 to F6 - fire: simulated as a gas. Its pace follows its size on the plate: every fire moves as a fire "
             f"{FAR} m wide per plate pixel of its bed, so two flames of one size on the plate move alike. The light of each fire "
             "on the crowd near it and its glow follow the simulated flame"),
    ("pit", "F7 - fire in the gorge: four fires on the wreckage, simulated at the same pace rule; the wreckage stays as painted"),
    ("smoke", "S1 - smoke column: simulated as a gas, the soot of a fire that burns out of sight behind the far wall; one "
              "column, at the pace rule of the fires. Dust, "
              "simulated, hangs low over both walks, between the ranks of the crowd, and drifts with the wind"),
    ("hook", "K1 - hook of the crane: stands still; a swing of 1 degree is under one pixel"),
    ("crowd", "C1 - crowd on the left walk, about 150,000 figures: walks away from the camera, to the bridge, slowly: "
              f"{np.mean(CHAINS) * RANK * 1.8 / LOOP:.2f} m/s on average. Every figure has a pace of its own that changes: it slows almost to "
              "a stand and goes on. One loop of way further along its lane stands the next figure of its chain, a little changed in "
              "height, brightness and dirt; the lanes have different paces, so no group of figures stands a second time"),
    ("crowd", "C2 - crowd on the right terrace, about 700 figures: stands. Every figure is a person of its own, shifts its "
              "weight and sways at its place"),
    (None, "Not marked: the camera, which moves on a closed path "
           "of 0.8 % of the nearest depth; the figures on the far bridge, which stay as painted"),
    (None, f"Loop: {FRAMES} frames at {RATE} frames per second, {FRAMES / RATE:.0f} s; every motion closes at the last frame"),
]


def smoke(colour):
    """The painted smoke of a picture of the plate (0 to 1): what is dark inside the outline SMOKY, with its pale rim,
    as one solid shape. A banner top that stands before it lies inside this shape: the list names it before the smoke,
    or the scene builds it."""
    import cv2
    outline, dark, rim = SMOKY
    inside = np.zeros(colour.shape[:2], np.uint8)
    cv2.fillPoly(inside, [np.array(outline, np.int32)], 1)
    found = ((inside > 0) & (colour @ np.array([0.2126, 0.7152, 0.0722], np.float32) < dark)).astype(np.uint8)
    found = cv2.morphologyEx(cv2.morphologyEx(found, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)), cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))
    return (cv2.dilate(found, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * rim + 1, 2 * rim + 1))) > 0) & (inside > 0)


def listed():
    """The list of things of the plate, built (src/things.py): the plate, its measured depth, the crowd, the cloths
    as meshes and through the loop, the banners, the extent of the wide things, what the scene gives to the list, and
    the list as built.

    - **Plate** - the one without the cloth of its banners, as the crowd builder leaves it (muster_plate.png)
    - **From the crowd** - the part of the plate behind each crowd and the nearest and the farthest figure by column
      (muster_crowd.npz). A railing is the parapet without what lies behind a crowd, with the pixels it encloses,
      at the measured depth of its own pixels by column
    - **Posts** - where the plate shows each post and each crossbar that the scene builds as rods (muster_posts.npz)
    - **Smoke** - the painted smoke of the plate (`smoke`)
    - **Cloths** - the room in which each cloth moves, from the depth of its post
    """
    import cv2
    from PIL import Image
    import things as T
    plate = np.asarray(Image.open(SCENE + "_plate.png").convert("RGB"))
    d, c, b, blown = np.load(SCENE + "_clean.npz"), np.load(SCENE + "_crowd.npz"), np.load(SCENE + "_banners.npz"), np.load(SCENE + "_wind.npz")
    H, W = plate.shape[:2]
    cloths = [el for el in ELEMENTS if el["kind"] == "banner"]
    front = np.asarray(Image.open(os.path.join(ROOT, "wip", "muster", "parapet.png"))) > 127
    left = np.arange(W)[None] < W // 2
    crowd = lambda w: (c["walk_least"][w], c["walk_behind"][w] / 1.15)      # the nearest and the farthest figure by column
    whole = {"P1": front & left & (c["region"] == 0), "P2": front & ~left & (c["region"] == 0), "W1": c["region"] == 1, "W2": c["region"] == 2}
    # a railing is whole: the pixels that the railings and the parts behind the crowds enclose are a railing's where
    # they touch one, and else belong to the part behind the crowd round them. The masks leave them out: gaps of the
    # lattice, the upper edge of a railing
    shut = np.pad(np.any(list(whole.values()), 0), 1).astype(np.uint8)
    cv2.floodFill(shut, None, (0, 0), 2)
    count, holes = cv2.connectedComponents((shut[1:-1, 1:-1] == 0).astype(np.uint8), connectivity=8)
    for name in ("P1", "P2", "W1", "W2"):                               # the railings first
        near = cv2.dilate(whole[name].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
        mine = np.isin(holes, np.setdiff1d(np.unique(holes[near]), [0]))
        whole[name], holes = whole[name] | mine, np.where(mine, 0, holes)
    def wall(mask):
        """The depth of a railing for each column: the measured depth of its own pixels there, evened along the
        railing. A railing is wide and near, and its measured depth differs by 3 % in a column. The depth
        of the parapet line from the crowd builder is not its surface: that line is made to lie behind every post,
        for the figures, and is up to 2.5 times as deep as the railing."""
        rows = np.where(mask & d["mask"], d["depth"], np.nan)
        cols = np.flatnonzero(np.isfinite(rows).sum(0) >= 12)             # a column with a few pixels of it only shows its far end
        by = np.interp(np.arange(W), cols, np.nanpercentile(rows[:, cols], 25, 0))      # the lower quarter: at its far end a column holds a far piece too
        return cv2.GaussianBlur(by[None].astype(np.float32), (0, 0), 4)[0]

    given = {"railing left": whole["P1"], "railing right": whole["P2"], "railing left depth": wall(whole["P1"]), "railing right depth": wall(whole["P2"]),
             "behind left": whole["W1"], "behind right": whole["W2"], "behind left depth": c["walk_behind"][0],
             "behind right depth": c["walk_behind"][1], "C1": crowd(0), "C2": crowd(1)}
    given.update({f"cloth {el['id']}": float(np.median(b[f"v{k}"][:, 1])) for k, el in enumerate(cloths, 1)})      # the depth of each cloth, measured on its whole width
    colour = plate.astype(np.float32) / 255
    given["flame"] = (colour[..., 0] > 0.59) & (colour[..., 0] - colour[..., 2] > 0.27)      # bright and orange: the colours of a painted flame
    import rods as R
    measured = np.load(SCENE + "_posts.npz")                              # the posts, which the scene builds: where the plate shows each
    for name in (str(v) for v in measured["names"]):
        given[f"post {name}"] = R.outline((H, W), {key: measured[f"{name}_{key}"] for key in ("at", "r")})
        given[f"frame {name}"] = np.any([R.outline((H, W), {key: measured[f"{part}_{key}"] for key in ("at", "r")})
                                         for part in (str(v) for v in measured["parts"]) if part.split("_")[0] == name] or [np.zeros((H, W), bool)], 0)
    for name in {str(v).split("_")[0] for v in measured["parts"]} - {str(v) for v in measured["names"]}:      # rods that belong to no banner: the pikes of a wall
        given[f"built {name}"] = np.any([R.outline((H, W), {key: measured[f"{part}_{key}"] for key in ("at", "r")})
                                         for part in (str(v) for v in measured["parts"]) if part.split("_")[0] == name], 0)
    given["smoke"] = smoke(colour)
    # the room in which each cloth moves, as its nearest and its deepest place by column: it follows from the depth of
    # its post, which the list gives. The list is built once for the posts and once more with these rooms, for what
    # stands behind a cloth
    swing = lambda near, far, box: tuple(np.where((np.arange(W) >= box[0]) & (np.arange(W) < box[2]), v, np.nan) for v in (near, far))
    given.update({f"swing {el['id']}": swing(np.nan, np.nan, el["box"]) for el in cloths})
    first = {t["id"]: t["depth"] for t in T.build(plate, d["depth"], d["mask"], THINGS, given)["things"] if t.get("depth") is not None}
    for k, el in enumerate(cloths, 1):
        at, moves = float(np.nanmedian(first["T" + el["id"][1:]])), blown[f"p{k}"][..., 1]
        given[f"swing {el['id']}"] = swing(HUNG * at * moves.min() / moves.max(), HUNG * at, el["box"])
    made = T.build(plate, d["depth"], d["mask"], THINGS, given)
    return plate, d, c, b, blown, cloths, whole, given, made


def things():
    """The things of the plate (THINGS) with their masks and depths, the surfaces the scene is built from, and the
    map of the things for the owner's review (wip/preview/things-muster.png).

    - **List** - built by `listed`
    - **Ground** - the far side, the railings and the plate behind each crowd as one surface without every other
      thing: muster_back.png, muster_back.npz and the fill behind its breaks, muster_back_bg.png. Where the plate
      had its painted smoke, the ground shows the air that the image model painted there (`sky`, muster_sky.png)
    - **Planes** - every other thing that stays, as a picture of its own with its depth: muster_thing_<id>.png and
      muster_things.npz
    - **Check** - no thing that stays and no cloth has ground before it; a fault stops the build
    - **Cloths** - the row at which each cloth begins under its crossbar, by column (muster_things.npz, hang_<id>),
      and the picture of the cloths with the rows from there to their cut (muster_hung.png)
    """
    import cv2
    from PIL import Image
    import things as T
    plate, d, c, b, blown, cloths, whole, given, made = listed()
    H, W = plate.shape[:2]
    for text in made["faults"]:
        print("FAULT", text)
    for text in made["notes"]:
        print("note ", text)
    print(f"{len(made['things'])} things, {int((made['label'] > 0).mean() * 100)} % of the plate; the far side is the rest; {len(made['faults'])} faults")
    out = os.path.join(ROOT, "wip", "preview", "things-muster.png")
    print("wrote", out, T.chart(plate, made, out, BURNS, zoom=[(1800, 80, 2432, 580), (200, 30, 900, 620)]))
    if made["faults"] or any(t.get("keep", True) is None for t in made["things"]):
        sys.exit("the list has a fault or a thing the owner has not decided: no surface is written")
    # the ground, in the form src/backdrop.py takes: a point for every pixel, the depth behind every break, the fill there
    # the painted smoke is no surface: where it was, the ground shows the air that the image model painted behind it
    # (sky), and has no measured depth, as the rest of the sky
    gone = made["label"] == [t["id"] for t in made["things"]].index("S1") + 1
    if not os.path.exists(SCENE + "_sky.png"):
        sys.exit("the air behind the painted smoke is not painted yet: run `sky` first")
    aired = np.asarray(Image.open(SCENE + "_sky.png").convert("RGB"))      # the plate with that air, gone over into it softly
    picture, deep, known = T.ground(aired, d["depth"], d["mask"] & ~gone, dict(made, label=np.where(gone, 0, made["label"])), whole)
    held = [(f"cloth {el['id']}", el["box"], given[f"swing {el['id']}"][1]) for el in cloths]      # the deepest place of every cloth in the loop
    hidden = T.covered(made, deep, whole, held)
    for text in hidden:
        print("FAULT", text)
    if hidden:
        sys.exit("the ground lies before a thing: no surface is written")
    K = d["intrinsics"]
    ray = np.stack(np.broadcast_arrays(((np.arange(W) + 0.5) / W - K[0, 2])[None] / K[0, 0], ((np.arange(H) + 0.5) / H - K[1, 2])[:, None] / K[1, 1],
                                       np.ones((H, W))), -1)
    deepest = cv2.dilate(np.where(known, deep, 0).astype(np.float32), np.ones((25, 25), np.uint8))
    edge = cv2.dilate(((deep < 0.92 * deepest) & known).astype(np.uint8) * 255, np.ones((5, 5), np.uint8))
    Image.fromarray(picture).save(SCENE + "_back.png")
    Image.fromarray(cv2.inpaint(picture, edge, 9, cv2.INPAINT_TELEA)).save(SCENE + "_back_bg.png")
    np.savez_compressed(SCENE + "_back.npz", points=(ray * deep[..., None]).astype(np.float32), depth=deep, mask=known, intrinsics=K,
                        bg_depth=deepest)
    flat = T.planes(plate, made, whole)
    for name, (rgba, box, by) in flat.items():
        Image.fromarray(rgba, "RGBA").save(SCENE + f"_thing_{name}.png")
    # a cloth hangs from the crossbar of its mast: it begins at the last row of the crossbar's picture, column by
    # column. It was cut at a level row, BAR under the top of its box, and the rows over that cut were painted out
    sewn, woven, hang = np.asarray(Image.open(SCENE + "_banners.png")).copy(), trimmed(), {}
    number = {t["id"]: n for n, t in enumerate(made["things"], 1)}
    for k, el in enumerate(cloths, 1):
        x0, y0, x1, y1 = el["box"]
        cut, top = int(y0 + BAR * (y1 - y0)), max(y0 - 40, 0)
        if "M" + el["id"][1:] not in number:                              # a banner whose mast the list does not name stays as it is
            continue
        bar = made["label"][top:cut + 1, x0:x1] == number["M" + el["id"][1:]]
        cols = np.flatnonzero(bar.any(0))
        if not len(cols):
            continue
        last = top + bar.shape[0] - 1 - np.argmax(bar[::-1], 0)           # the last row of the crossbar in each column
        # the first row of the cloth: the crossbar's last row, and no lower than the rows that `clean` painted out
        # with the cloth, 4 rows over the cut. The cloth lies before the crossbar and shows the same picture there
        first = np.minimum(np.interp(np.arange(x1 - x0), cols, last[cols]), cut - 4) - 1
        hang[el["id"]] = (first - 0.5).astype(np.float32)                 # the upper edge of that row
        hem = np.zeros(woven.shape, np.float32)
        for x in np.flatnonzero((woven[cut:cut + 4, x0:x1] == k).any(0)):      # over the columns where the cloth begins under the crossbar
            hem[int(first[x]):cut + 4, x0 + x] = 1
        sewn[..., 3] = np.maximum(sewn[..., 3], (cv2.GaussianBlur(hem, (0, 0), 0.7) * 255).astype(np.uint8))
    Image.fromarray(sewn, "RGBA").save(SCENE + "_hung.png")
    np.savez_compressed(SCENE + "_things.npz", label=made["label"], ids=np.array([t["id"] for t in made["things"]]),
                        depth=np.stack([t["depth"] if t.get("depth") is not None else np.full(W, np.nan, np.float32) for t in made["things"]]),
                        planes=np.array(list(flat)), **{f"box_{name}": np.array(box) for name, (_, box, _) in flat.items()},
                        **{f"depth_{name}": by for name, (_, _, by) in flat.items()}, **{f"hang_{name}": by for name, by in hang.items()})
    print(f"wrote {SCENE}_back.png, _back.npz, _back_bg.png, _things.npz and {len(flat)} planes: {', '.join(flat)}")


def posts():
    """Measures the post of every banner in the source picture (POSTS, src/rods.py): wip/scene3d/muster_posts.npz,
    and for the owner's review wip/preview/posts-muster.png: every post straightened, its top at the left, as the
    source picture shows it and with the measured outline drawn over it."""
    import cv2
    from PIL import Image, ImageDraw
    import rods as R
    source = np.asarray(Image.open(SCENE + ".png").convert("RGB")).astype(np.float32) / 255
    out, sheet, zoom, parts = {}, [], 4, []
    for name, given in POSTS.items():
        x0, y0, x1, y1 = given["post"]
        rod = R.measure(source, (x0, y0), (x1, y1), given.get("top"), given.get("foot"), given.get("thick"),
                        given.get("plain", []) + [(y0, y0 + PLAIN)] * ("top" not in given) + [(y1 - PLAIN, y1)], given.get("joints", []))
        out.update({f"{name}_{key}": np.asarray(rod[key]) for key in ("at", "r", "colour", "seen", "span", "lean")})
        iron, more = np.median(rod["colour"][rod["span"][0]:rod["span"][0] + 2 * PLAIN], 0), {}      # the colour of the post at its crossbar
        if "bar" in given:
            bx0, by0, bx1, by1, r = given["bar"]
            more["bar"] = R.shaped((bx0, by0), (bx1, by1), [(t, v * r) for t, v in ALONG["bar"]], iron)
        for n, (x, top, low, r) in enumerate(given.get("finials", [])):
            more[f"finial{n}"] = R.shaped((x, top), (x, low), [(t, v * r) for t, v in ALONG["finial"]], iron)
        for part, shape in more.items():
            parts.append(f"{name}_{part}")
            out.update({f"{name}_{part}_{key}": np.asarray(shape[key]) for key in ("at", "r", "colour", "lean")})
        wide = int(max(3 * rod["r"].max(), 10))
        strip, u = R.straight(source, rod["at"][0], rod["at"][-1], wide, 1)
        strip = strip[:len(rod["r"])]
        both = np.concatenate([strip, strip], 1).transpose(1, 0, 2)[::-1]      # across the page: along the rod; its right side up
        page = Image.fromarray((cv2.resize(both, None, fx=zoom, fy=zoom, interpolation=cv2.INTER_NEAREST) * 255).astype(np.uint8))
        draw, high = ImageDraw.Draw(page), len(u) * zoom
        for k in range(len(rod["r"]) - 1):                                # the lower strip: the outline, yellow where the picture shows the post, red where it goes on unseen
            for sign in (-1, 1):
                y0, y1 = (high + (wide - sign * rod["r"][j] + 0.5) * zoom for j in (k, k + 1))
                draw.line([((k + 0.5) * zoom, y0), ((k + 1.5) * zoom, y1)], fill=(255, 235, 0) if rod["seen"][k] else (255, 60, 40))
        full = Image.new("RGB", (page.width + 70, page.height + 18), (20, 20, 20))
        full.paste(page, (70, 0))
        draw = ImageDraw.Draw(full)
        draw.text((4, 4), f"{name}  r {rod['base']:.2f}", fill=(255, 230, 120))
        for row in range(int(rod["at"][0, 1]) // 50 * 50 + 50, int(rod["at"][-1, 1]), 50):
            k = np.argmin(np.abs(rod["at"][:, 1] - row))
            draw.text((70 + k * zoom - 8, page.height + 3), str(row), fill=(200, 200, 200))
        sheet.append(full)
        print(f"{name}: axis ({rod['a'][0]:.1f}, {rod['a'][1]:.0f}) to ({rod['b'][0]:.1f}, {rod['b'][1]:.0f}), radius {rod['base']:.2f} px, {rod['r'].min():.2f} to "
              f"{rod['r'].max():.2f}; right half {rod['lean']:+.0%} against left; shown at {int(rod['seen'].sum())} of {len(rod['r'])} stations", flush=True)
    dark = source @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    for n, (x, tip, foot, r, lean) in enumerate(PIKES):                   # the pikes of the far wall: each in the colour of the wall under it, the darkest third of it
        under = source[foot:foot + 5, int(round(x)) - 3:int(round(x)) + 4].reshape(-1, 3)
        under = under[np.argsort(dark[foot:foot + 5, int(round(x)) - 3:int(round(x)) + 4].ravel())[:len(under) // 3]]
        shape = R.shaped((x - (foot - tip) * lean, tip), (x, foot), [(t, v * r) for t, v in ALONG["pike"]], np.median(under, 0))
        parts.append(f"U1_pike{n}")
        out.update({f"U1_pike{n}_{key}": np.asarray(shape[key]) for key in ("at", "r", "colour", "lean")})
    np.savez_compressed(SCENE + "_posts.npz", names=np.array(list(POSTS)), parts=np.array(parts), **out)
    page = Image.new("RGB", (max(p.width for p in sheet), sum(p.height for p in sheet)), (20, 20, 20))
    at = 0
    for p in sheet:
        page.paste(p, (0, at))
        at += p.height
    path = os.path.join(ROOT, "wip", "preview", "posts-muster.png")
    page.save(path)
    print("wrote", SCENE + "_posts.npz", "and", path, page.size)


def sky():
    """The air where the plate has its painted smoke: wip/scene3d/muster_sky.png, the plate with the pixels of the
    thing S1 (THINGS: the dark plume, the grey cloud behind it, its black base) painted by the image model as hazy
    sky. The scene shows one simulated column of smoke before that air. A fill from the colours round the smoke gave
    a flat pale patch: the smoke is a quarter of the sky of the left half, and a sky has structure."""
    import cv2, torch
    from PIL import Image
    from diffusers import ZImageInpaintPipeline
    plate, d, c, b, blown, cloths, whole, given, made = listed()
    plate = plate.copy()
    hole = (made["label"] == [t["id"] for t in made["things"]].index("S1") + 1).astype(np.uint8)
    (x0, y0, x1, y1), seed, words = AIR
    if hole[:y0].any() or hole[y1:].any() or hole[:, :x0].any() or hole[:, x1:].any():
        sys.exit("the painted smoke reaches beyond the part of the plate that the image model sees (AIR)")
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    crop, part = plate[y0:y1, x0:x1], hole[y0:y1, x0:x1]
    big = (2 * (x1 - x0), 2 * (y1 - y0))
    gen = pipe(prompt=words, image=Image.fromarray(cv2.resize(crop, big, interpolation=cv2.INTER_CUBIC)),
               mask_image=Image.fromarray(cv2.resize(part, big, interpolation=cv2.INTER_NEAREST) * 255), strength=1.0,
               height=big[1], width=big[0], num_inference_steps=9, guidance_scale=0.0,
               generator=torch.Generator("cuda").manual_seed(int(os.environ.get("MUSTER_SKY_SEED", seed)))).images[0]
    gen = cv2.resize(np.asarray(gen), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
    a = cv2.GaussianBlur(part.astype(np.float32), (0, 0), SEAM[0]) * np.clip((np.arange(x0, x1) - SEAM[1][0]) / (SEAM[1][1] - SEAM[1][0]), 0, 1)[None]
    plate[y0:y1, x0:x1] = (crop * (1 - a[..., None]) + gen * a[..., None]).astype(np.uint8)
    Image.fromarray(plate).save(SCENE + "_sky.png")
    shown = np.concatenate([np.asarray(Image.open(SCENE + "_plate.png").convert("RGB"))[y0:y1, x0:x1], plate[y0:y1, x0:x1]], 1)
    Image.fromarray(shown).save(os.path.join(ROOT, "wip", "preview", f"muster-sky{os.environ.get('MUSTER_SKY_SEED', '')}.png"))
    print(f"wrote {SCENE}_sky.png: {int(part.sum())} px of smoke painted as air; wip/preview/muster-sky.png shows the plate and the result")


def cloth():
    """The cloth of every banner, cut by SAM 2.1 from the plate without the crowd: one picture whose pixel value is
    the number of the banner (1 for the first banner of ELEMENTS), 0 elsewhere. Holes and gaps between rags are not
    cloth. The crossbar, the top BAR of the box, stays in the plate; the cloth hangs from its lower edge."""
    import torch
    from PIL import Image
    from transformers import Sam2Processor, Sam2Model
    plate = np.asarray(Image.open(SCENE + ".png").convert("RGB"))
    rid = "facebook/sam2.1-hiera-large"
    proc, model = Sam2Processor.from_pretrained(rid), Sam2Model.from_pretrained(rid).to("cuda").eval()
    label = np.zeros(plate.shape[:2], np.uint8)
    for k, el in enumerate([el for el in ELEMENTS if el["kind"] == "banner"], 1):
        x0, y0, x1, y1 = el["box"]
        m = 30
        cx0, cy0, cx1, cy1 = max(x0 - m, 0), max(y0 - m, 0), min(x1 + m, plate.shape[1]), min(y1 + m, plate.shape[0])
        xc, h = (x0 + x1) / 2, y1 - y0
        on = [[xc - cx0, y0 + f * h - cy0] for f in (0.2, 0.38, 0.6)] + [[x - cx0, y - cy0] for x, y in el.get("on", [])]      # `on`: further places of the plate that are cloth
        inputs = proc(images=Image.fromarray(plate[cy0:cy1, cx0:cx1]), input_boxes=[[[x0 - cx0, y0 - cy0, x1 - cx0, y1 - cy0]]],
                      input_points=[[on]], input_labels=[[[1] * len(on)]], return_tensors="pt").to("cuda")
        with torch.no_grad():
            out = model(**inputs, multimask_output=False)
        cut = np.zeros(plate.shape[:2], bool)
        cut[cy0:cy1, cx0:cx1] = proc.post_process_masks(out.pred_masks.cpu(), inputs["original_sizes"])[0][0, 0].numpy() > 0
        cut[:int(y0 + BAR * h)], cut[y1:], cut[:, :x0], cut[:, x1:] = False, False, False, False
        label[cut & (label == 0)] = k
        print(f"{el['id']}: {int(cut.sum())} px of cloth, iou {float(out.iou_scores.max()):.2f}", flush=True)
    Image.fromarray(label).save(SCENE + "_cloth.png")
    shown = plate.astype(np.float32)
    shown[label > 0] = shown[label > 0] * 0.45 + np.array([0, 214, 255]) * 0.55
    Image.fromarray(shown.astype(np.uint8)).save(os.path.join(ROOT, "wip", "preview", "muster-cloth.png"))
    print("wrote", SCENE + "_cloth.png", "and wip/preview/muster-cloth.png")


def clean():
    """The plate without the cloth of its banners: what a moving cloth uncovers. The image model paints the air, the
    masts and the far city behind each group of banners; the crossbars and masts of the plate stay."""
    import cv2, torch
    from PIL import Image
    from diffusers import ZImageInpaintPipeline
    plate = np.asarray(Image.open(SCENE + ".png").convert("RGB")).copy()
    hole = cv2.dilate((np.asarray(Image.open(SCENE + "_cloth.png")) > 0).astype(np.uint8), np.ones((9, 9), np.uint8))
    pipe = ZImageInpaintPipeline.from_pretrained("Tongyi-MAI/Z-Image-Turbo", torch_dtype=torch.bfloat16).to("cuda")
    for (x0, y0, x1, y1), seed in BEHIND:
        crop, part = plate[y0:y1, x0:x1], hole[y0:y1, x0:x1]
        big = (2 * (x1 - x0), 2 * (y1 - y0))
        gen = pipe(prompt=EMPTY, image=Image.fromarray(cv2.resize(crop, big, interpolation=cv2.INTER_CUBIC)),
                   mask_image=Image.fromarray(cv2.resize(part, big, interpolation=cv2.INTER_NEAREST) * 255), strength=1.0,
                   height=big[1], width=big[0], num_inference_steps=9, guidance_scale=0.0,
                   generator=torch.Generator("cuda").manual_seed(seed)).images[0]
        gen = cv2.resize(np.asarray(gen), (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA)
        a = cv2.GaussianBlur(part.astype(np.float32), (0, 0), 2)[..., None]
        plate[y0:y1, x0:x1] = (crop * (1 - a) + gen * a).astype(np.uint8)
        print(f"behind the banners of columns {x0} to {x1}: {int(part.sum())} px painted with seed {seed}", flush=True)
    Image.fromarray(plate).save(SCENE + "_clean.png")
    print("wrote", SCENE + "_clean.png")


def trimmed():
    """The cloth of every banner as SAM 2.1 cut it (muster_cloth.png), ending at the left side of its post. The
    source picture shows post and cloth side by side. The cut took a few pixels of the post and beyond it for cloth,
    and in other rows it ended up to NEAR pixels before the post, where the source has the dark edge of the cloth: a
    pale line of the plate showed between cloth and post. The cloth of a banner that hangs over its post (POSTS,
    `covered`) stays as cut."""
    from PIL import Image
    label, measured = np.asarray(Image.open(SCENE + "_cloth.png")).copy(), np.load(SCENE + "_posts.npz")
    cols = np.arange(label.shape[1])[None]
    for k, el in enumerate([el for el in ELEMENTS if el["kind"] == "banner"], 1):
        if not POSTS[el["id"]].get("covered"):
            at, r = measured[f"{el['id']}_at"], float(np.median(measured[f"{el['id']}_r"]))
            side = (np.polyval(np.polyfit(at[:, 1], at[:, 0], 1), np.arange(label.shape[0])) - r + 0.5)[:, None]      # just inside the left side of the post, in each row
            own = label == k
            last = np.where(own.any(1), label.shape[1] - 1 - np.argmax(own[:, ::-1], 1), -9999)[:, None]      # the last column of the cloth in each row
            label[own & (cols >= side)] = 0
            label[(label == 0) & (cols > last) & (cols < side) & (side - last <= POSTS[el["id"]].get("near", NEAR))] = k
    return label


def banners():
    """Every cloth as a mesh in the camera's space, and the picture of all cloths with their shape as alpha.

    A cloth is held along its crossbar only. The source picture shows post and cloth side by side, and a cloth that
    swings into the picture is seen at an angle: under a wind that never turned, the cloth of the left banners
    showed up to 48 pixels beyond its post (B1) and hid it. The user on a post drawn before that cloth: "wait posts
    obscure the cloth in front of it???", and chose that the cloth stops at its post. A wall at the post, as an
    obstacle in the simulation, stopped the cloth sideways and did not change what the camera sees of its swing into
    the picture. The edge beside the post was then fastened to the post: that edge stayed upright while the free
    side leaned, and the cloth hardly moved. The user: "skewed to the left", "weirdly flared out at the bottom", "the
    wind doesnt seem to work on it", "the right side of the cloth is almost perpendicular to the ground, and because
    of this it looks not rectangular". Both sides are free again, and the wind has no steady share (STEADY)."""
    import cv2
    from PIL import Image
    d, b = np.load(SCENE + "_back.npz"), np.load(SCENE + ".npz")
    K, (H, W) = d["intrinsics"], d["depth"].shape
    label = trimmed()
    print(f"{int(((np.asarray(Image.open(SCENE + '_cloth.png')) > 0) & (label == 0)).sum())} px of the cut cloths lie at or beyond their posts and are no cloth")
    front = np.asarray(Image.open(os.path.join(ROOT, "wip", "muster", "parapet.png"))) > 127
    both = front & d["mask"] & b["mask"]
    scale = float(np.median(d["depth"][both]) / np.median(b["depth"][both]))      # the two plates were measured apart
    out = {}
    for k, el in enumerate([el for el in ELEMENTS if el["kind"] == "banner"], 1):
        x0, y0, x1, y1 = el["box"]
        y0 = int(y0 + BAR * (y1 - y0))
        cloth = label == k
        z = 0.98 * scale * float(np.median(b["depth"][cloth & b["mask"]]))
        g = max((x1 - x0) / GRID, 3.0)
        gx, gy = np.arange(x0, x1 + g, g), np.arange(y0, y1 + g, g)
        part = cv2.resize(cloth[y0:y1, x0:x1].astype(np.float32), (len(gx) - 1, len(gy) - 1), interpolation=cv2.INTER_AREA) > 0.4
        part[0] |= part[1]                                            # the row under the crossbar is whole where the next one is cloth
        joined = cv2.connectedComponents(part.astype(np.uint8), connectivity=4)[1]
        part &= np.isin(joined, np.unique(joined[0][part[0]]))        # a piece that hangs on nothing would fall: it stays painted out
        idx = np.arange(len(gy) * len(gx)).reshape(len(gy), len(gx))
        quads = np.stack([idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:], idx[:-1, :-1]], -1)[part]
        used = np.unique(quads)
        xx, yy = np.meshgrid(gx, gy)
        px = np.stack([xx.ravel()[used], yy.ravel()[used]], 1)
        out[f"v{k}"] = np.stack([((px[:, 0] + 0.5) / W - K[0, 2]) / K[0, 0] * z, np.full(len(px), z),
                                 -((px[:, 1] + 0.5) / H - K[1, 2]) / K[1, 1] * z], 1).astype(np.float32)
        out[f"uv{k}"] = np.stack([(px[:, 0] + 0.5) / W, 1 - (px[:, 1] + 0.5) / H], 1).astype(np.float32)
        out[f"f{k}"] = np.searchsorted(used, quads).astype(np.int32)
        out[f"pin{k}"] = px[:, 1] < y0 + 0.5 * g
        out[f"x{k}"] = np.float32((x0 + x1) / 2 / W)
        print(f"{el['id']}: {len(px)} vertices, {len(quads)} faces, {int(out[f'pin{k}'].sum())} of them held, {z:.1f} m deep, "
              f"{(x1 - x0) * z / (K[0, 0] * W):.2f} x {(y1 - y0) * z / (K[1, 1] * H):.2f} m", flush=True)
    np.savez_compressed(SCENE + "_banners.npz", **out)
    sigils = np.asarray(Image.open(SCENE + "_sigils.png").convert("RGBA"))      # its alpha: the holes that go through a sigil
    rgba = np.dstack([sigils[..., :3], (cv2.GaussianBlur((label > 0).astype(np.float32), (0, 0), 0.7) * sigils[..., 3]).astype(np.uint8)])
    Image.fromarray(rgba, "RGBA").save(SCENE + "_banners.png")
    print("wrote", SCENE + "_banners.npz and .png")


def wind():
    """Simulates every cloth in its wind for three loops and keeps the third, closed: wip/scene3d/muster_wind.npz."""
    import bpy, math
    b = np.load(SCENE + "_banners.npz")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.fps = RATE
    span = round(FRAMES / CALM)                                       # the frames of one simulated loop
    s.frame_start, s.frame_end = 1, 3 * span
    cloths, rng = [], np.random.default_rng(11)

    def field(kind, into):                                            # a force field in the collection `into` only
        bpy.ops.object.effector_add(type=kind)
        ob = bpy.context.object
        for coll in list(ob.users_collection):
            coll.objects.unlink(ob)
        into.objects.link(ob)
        return ob

    k = 1
    while f"v{k}" in b:
        me = bpy.data.meshes.new(f"cloth{k}")
        me.from_pydata(b[f"v{k}"].tolist(), [], b[f"f{k}"].tolist())
        me.update(calc_edges=True)
        ob = bpy.data.objects.new(f"cloth{k}", me)
        own = bpy.data.collections.new(f"wind{k}")                    # the cloth feels the wind of this collection only
        s.collection.children.link(own)
        own.objects.link(ob)
        ob.vertex_groups.new(name="pin").add(np.flatnonzero(b[f"pin{k}"]).tolist(), 1.0, "REPLACE")
        mod = ob.modifiers.new("cloth", "CLOTH")
        c = mod.settings
        area = sum(face.area for face in me.polygons)
        c.quality, c.mass, c.air_damping = 10, 0.3, 1.0
        dense = len(me.vertices) / area / 100                         # vertices per square metre, in hundreds
        c.tension_stiffness, c.compression_stiffness, c.shear_stiffness, c.bending_stiffness = 40, 40, 20, 1.5
        c.tension_damping, c.compression_damping, c.shear_damping, c.bending_damping = 12, 12, 6, 0.5
        c.vertex_group_mass = "pin"
        c.effector_weights.gravity = 0.5
        c.effector_weights.collection = own
        mod.point_cache.frame_start, mod.point_cache.frame_end = 1, 3 * span
        blow = field("WIND", own)
        blow.field.flow = 0.0
        to = np.array(WIND_TO) / np.linalg.norm(WIND_TO)
        blow.rotation_euler = (math.atan2(math.hypot(to[0], to[1]), to[2]), 0, math.atan2(to[0], -to[1]))      # its z axis along WIND_TO
        eddy = field("TURBULENCE", own)
        eddy.field.size, eddy.field.strength, eddy.field.seed = 0.8, 0.5 * BLOW * dense, k
        eddy.location = b[f"v{k}"].mean(0)
        cloths.append((ob, blow, float(b[f"x{k}"]), rng.random(len(GUSTS)), dense))
        k += 1

    def course(t, x, moment):                                         # the strength of the wind at loop time t for a banner at x
        late = t - GUST[2] * x
        gust = sum(strong * math.exp(-((late - moment + 0.5) % 1 - 0.5) ** 2 / GUST[1] ** 2) for moment, strong in GUST[0])
        return BLOW * (STEADY + sum(share * math.sin(2 * math.pi * (cycles * late + moment[j])) for j, (cycles, share) in enumerate(GUSTS)) + gust)

    kept = [np.zeros((3 * span, len(c[0].data.vertices), 3), np.float32) for c in cloths]
    for f in range(1, 3 * span + 1):
        for ob, blow, x, moment, dense in cloths:
            blow.field.strength = course((f - 1) / span, x, moment) * dense
        s.frame_set(f)
        deps = bpy.context.evaluated_depsgraph_get()
        for n, c in enumerate(cloths):
            c[0].evaluated_get(deps).data.vertices.foreach_get("co", kept[n][f - 1].ravel())
    out = {}
    for n in range(1, len(cloths) + 1):
        p, rest = kept[n - 1], b[f"v{n}"]
        tall = np.ptp(rest[:, 2])
        loop, before = p[2 * span:].copy(), p[span:2 * span]
        gap = np.abs(p[3 * span - 1] - p[2 * span - 1]).max() / tall           # how far the third loop ends from where it began
        w = np.clip((np.arange(span) - (span - CLOSE)) / CLOSE, 0, 1)[:, None, None]
        loop = loop * (1 - w) + before * w                            # its last frames go over into the end of the second loop
        at = np.arange(FRAMES) * span / FRAMES                        # shown over the whole loop: each frame between two simulated ones
        lo, part = at.astype(int), (at - at.astype(int))[:, None, None]
        loop = loop[lo] * (1 - part) + loop[(lo + 1) % span] * part
        moved = np.linalg.norm(loop - rest[None], axis=2)
        print(f"cloth {n}: moves {moved.mean() / tall:.3f} of its height on average, {moved.max() / tall:.3f} at most; "
              f"into the picture {np.abs(loop[..., 1] - rest[None, :, 1]).max() / tall:.3f}; the third loop ends {gap:.3f} from its start", flush=True)
        out[f"p{n}"] = loop.astype(np.float32)
    np.savez_compressed(SCENE + "_wind.npz", **out)
    print("wrote", SCENE + "_wind.npz")


def place(g, f, r):
    """A figure of a walk at the place f across and r along it, in figure heights: the column and the row of its
    feet on the plate, its height by the rule (a figure whose feet are y rows below the horizon is y / eye rows
    tall), its depth in figure heights, and whether it is in the picture. g is the walk: the place of its near corner,
    its directions along and across, the height of the camera over its floor, its columns on the plate, and its last
    rank, where its floor ends."""
    side = g["a"][0] + r * g["along"][0] + f * g["across"][0]
    depth = g["a"][1] + r * g["along"][1] + f * g["across"][1]
    ok = depth > NEAREST
    d = np.where(ok, depth, NEAREST)
    x = PLATE[0] / 2 + FOCAL * side / d
    y = HORIZON + FOCAL * g["eye"] / d
    tall = (y - HORIZON) / g["eye"]
    beside = np.maximum(25, 0.6 * tall)                               # a figure comes in and goes out beside the picture, with its whole width
    ok = ok & (x > g["span"][0] - beside) & (x < g["span"][1] + beside) & (tall >= 1.0) & (y < PLATE[1] + 40) & (r <= g["last"])
    return x, y, tall, depth, ok


def parapet(zp, line, eye, span):
    """The line where the floor of a walk meets its parapet, as the depth by the rule of points of it, rising, and
    the depth of each in the camera's space, rising as well. zp: the measured depth of the parapet by column; line:
    the column of the walk's vanishing point and a point of the line. The measured depth does not rise all along
    the line: a post stands nearer than the rail behind it. Only the points that are deeper than every point before
    them are kept; between two of them `deep` goes up evenly. With the rest held level instead, all figures of a
    stretch of the walk stood at one depth and covered each other by chance."""
    cols = np.arange(int(span[0]), min(int(span[1]), PLATE[0] - 1) + 1)
    edge = HORIZON + (line[2] - HORIZON) * (cols - line[0]) / (line[1] - line[0])
    rule = FOCAL * float(eye) / np.maximum(edge - HORIZON, 1.0)
    order = np.argsort(rule)
    rule, zp = rule[order], np.asarray(zp)[cols][order]
    more = np.concatenate([[True], zp[1:] > np.maximum.accumulate(zp)[:-1]])      # the points where the parapet is deeper than anywhere before
    return rule[more], zp[more]


def deep(line, depth):
    """The depth in the camera's space of a place `depth` figure heights deep by the rule: that of the point of the
    parapet line (`parapet`) that is as deep by the rule. So a figure nearer by the rule always stands before one
    that is farther, and every figure stands behind the parapet of its column.

    A first depth was that of the parapet in the figure's own column times how much deeper than the parapet the
    figure stands. Where the measured depth of the parapet changes fast from column to column, that put a near
    figure behind a far one, and it changed by a step when a figure passed from one column to the next: figures
    covered each other in one frame and not in the next."""
    rule, zp = line
    return DEEPER * np.interp(depth, rule, zp) * np.clip(depth / rule[-1], 1, None) * np.clip(depth / rule[0], None, 1)


def way(ch, of, turn, t):
    """The figures at the moment t of the loop, 0 to 1. ch: the chains; of: the chain of each figure; turn: how many
    loops the figure is ahead of the first one of its chain. A figure of a walking chain has gone on for
    t + turn + late loops, at the chain's mean pace `go` and faster and slower by `part`. At t = 1 it stands where
    the next figure of its chain stood at t = 0, in the same step: the loop closes. A chain with `go` 0 stands.
    Returns its place across and along the walk and how far it has gone, in figure heights; its pace against its
    mean pace; the loops it has gone on for."""
    loops = (t + turn) + ch["late"][of]
    life = loops * LOOP
    swing = 2 * np.pi * life[:, None] / ch["every"][of] + ch["start"][of]
    gone = ch["go"][of] / LOOP * (life + (ch["part"][of] * ch["every"][of] / (2 * np.pi) * np.sin(swing)).sum(1))
    aside = ch["side"][of, 0] * np.sin(2 * np.pi * life / ch["side"][of, 1] + ch["side"][of, 2])
    return ch["f"][of] + aside, ch["r"][of] + gone, gone, 1 + (ch["part"][of] * np.cos(swing)).sum(1), loops


def shading(cells, f, r):
    """The brightness of the floor at a place, between the two values of SHADOW: the picture `cells`, looked up
    between its cells, 6 figure heights apart along the walk and 2 across."""
    u, v = (r / 6) % 64, (f / 2) % 64
    i, j = np.floor(u).astype(int), np.floor(v).astype(int)
    a, b = u - i, v - j
    at = lambda di, dj: cells[(i + di) % 64, (j + dj) % 64]
    return SHADOW[0] + (SHADOW[1] - SHADOW[0]) * ((1 - a) * ((1 - b) * at(0, 0) + b * at(0, 1)) + a * ((1 - b) * at(1, 0) + b * at(1, 1)))


def firelight(fires, x, depth):
    """The share of each fire's light on a figure whose feet stand in column x at that depth. fires: place across,
    depth and size of each, in figure heights."""
    side = (x - PLATE[0] / 2) * depth / FOCAL
    return np.stack([1 / (1 + ((side - fx) ** 2 + (depth - fz) ** 2) / (REACH * size) ** 2) for fx, fz, size in fires]
                    or [np.zeros_like(depth)], 1)


def beds():
    """Every bed of fire of ELEMENTS as (name, values): its width in metres, its place on the plate, the box of its
    painted flames, and what src/fire.py needs. The source of a column of smoke is such a bed, of kind "smoke"."""
    out = []
    for el in ELEMENTS:
        for n, (x, foot, px) in enumerate(el.get("beds", [])):
            out.append((el["id"] + "abcdefgh"[n] * (len(el["beds"]) > 1),
                        dict({key: el[key] for key in ("scale", "wind", "fine", "smoke", "lumps", "deep", "tall", "thing", "high", "wide", "lasts") if key in el},
                             kind=el["kind"], x=x, foot=foot, px=px, width=px / el["scale"], like=px * FAR,
                             box=el.get("painted", [el["box"]] * len(el["beds"]))[n])))
    return out


def flames():
    """The simulated fires (src/fire.py) as pictures for the scene, and the plate without its painted flames.

    - **Plate** - the pixels of flame in the box of each bed are taken out and the colours round them carried in
      (heraldry.fill), with the grain of the plate: muster_still.png. The smoke that a fire lights is not flame
      and stays, as does the glow the image model painted round a fire. Below the row EMBERS the fire in the gorge
      stays as painted
    - **Colours** - a simulated flame gets the colours of the painted flames: the painted flame pixels in the order
      of their brightness are the scale, and a pixel of the simulation takes the colour at the rank of its glow
      among all glowing pixels of its loop. Faint glow covers little. Soot is dark against the air behind it
    - **Place** - a picture is as large on the plate as its box of air at the fire's scale, with the bed at its foot
    - **Smoke before the fire** - the user: the flames must be "little blurred as there is distance and smoke that
      disperses light". Each picture is blurred, more for a fire farther away, and a share of its light lies in a
      wide halo round it (SCATTER)
    - **Light** - per fire and frame the light of the flame against its mean, and where its glow lies on the plate
    - **Behind the fire** - where a painted flame stood, the plate is air now. By its measured depth a part of it
      stood before the simulated flame and covered its base as a dark flat shape (23 % of fire F2). `was` marks
      those pixels, and the scene sets them behind the fire
    """
    import cv2
    from PIL import Image
    from heraldry import fill
    luma = np.array([0.2126, 0.7152, 0.0722], np.float32)
    plate = np.asarray(Image.open(SCENE + "_back.png").convert("RGB")).astype(np.float32) / 255
    back = np.load(SCENE + "_back.npz")
    depth = back["depth"]
    H, W = plate.shape[:2]
    focal = back["intrinsics"][0, 0] * W                              # in plate pixels
    # a flame pixel is bright and far from grey; the smoke that a fire lights is as red, and less far from grey
    hot = ((plate[..., 0] > 0.85) & (plate[..., 0] - plate[..., 2] > 0.58)) | ((plate[..., 0] > 0.9) & (plate[..., 1] > 0.55))
    gone, parts = np.zeros((H, W), bool), {}
    fires = [(name, bed) for name, bed in beds() if bed["kind"] != "smoke"]
    for name, bed in fires:
        x0, y0, x1, y1 = bed["box"]
        y1 = min(y1, EMBERS)
        parts[name] = np.zeros((H, W), bool)
        parts[name][y0:y1, x0:x1] = hot[y0:y1, x0:x1]
        gone |= parts[name]
    # the colours of the painted flames, darkest first: the flame pixels and the dimmer flame colours at their edges
    wide = cv2.dilate(gone.astype(np.uint8), np.ones((7, 7), np.uint8)) > 0
    pixels = plate[wide & (plate[..., 0] > 0.5) & (plate[..., 0] - plate[..., 2] > 0.3) & (plate[..., 1] < 0.92 * plate[..., 0])]
    pixels = pixels[np.argsort(pixels @ luma)]
    ramp = np.stack([np.median(part, 0) for part in np.array_split(pixels, 64)])
    ramp = cv2.resize(ramp[None], (256, 1), interpolation=cv2.INTER_LINEAR)[0]
    # the plate without them: the colours round each flame carried in, with the grain of the plate
    high = (plate - cv2.GaussianBlur(plate, (0, 0), 1.2)) @ luma
    ring = ~wide & (cv2.dilate(wide.astype(np.uint8), np.ones((41, 41), np.uint8)) > 0)
    rng = np.random.default_rng(3)
    noise = cv2.GaussianBlur(rng.normal(0, 1, (H, W)).astype(np.float32), (0, 0), 0.6)
    noise *= 1.48 * np.median(np.abs(high[ring])) / noise.std()       # by the middle of the grain, which the edges of things do not raise
    soft = cv2.GaussianBlur(wide.astype(np.float32), (0, 0), 1.5)[..., None]
    still = plate * (1 - soft) + fill(plate, ~wide) * (1 + noise[..., None] / 0.4) * soft
    Image.fromarray((still.clip(0, 1) * 255).astype(np.uint8)).save(SCENE + "_still.png")
    air = cv2.GaussianBlur(still, (0, 0), 25)
    out, shown = {}, still.copy()
    things = np.load(SCENE + "_things.npz")
    ids = [str(v) for v in things["ids"]]
    for name, bed in fires:
        sim = np.load(os.path.join(ROOT, "wip", "sim", "muster", name + ".npz"))
        glow, soot = sim["glow"].astype(np.float32), sim["soot"].astype(np.float32)
        lit = glow[glow > 0.02 * np.quantile(glow, 0.9995)]
        steps = np.quantile(lit, np.linspace(0, 1, 256))               # the glow at each rank
        rank = np.interp(glow, steps, np.linspace(0, 1, 256), left=0.0)
        cover = 1 - np.exp(-glow / np.quantile(lit, 0.3))              # the faint outer glow covers little
        over = (glow.shape[1] - 1 - np.arange(glow.shape[1]) - float(sim["bed"][1])) * float(sim["cell"]) / bed["width"]      # widths over the bed
        thins = 1 - np.clip((over - SOOT[2]) / (SOOT[3] - SOOT[2]), 0, 1) ** 2      # the smoke of a fire goes into the smoke of the air
        dark = (1 - np.exp(-SOOT[0] * bed.get("smoke", 1.0) * soot)) * thins[None, :, None]
        colour = ramp[(rank * 255).astype(int)] * cover[..., None]
        smoke = SOOT[1] * air[min(bed["foot"], H - 1) - 40, bed["x"]]
        alpha = 1 - (1 - cover) * (1 - dark)
        rgba = np.concatenate([colour + smoke * (dark * (1 - cover))[..., None], alpha[..., None]], -1)      # colour times cover
        # on the plate: the box of air at the fire's scale
        each = float(sim["cell"]) * bed["scale"]                       # plate pixels per cell
        size = (max(round(glow.shape[2] * each), 1), max(round(glow.shape[1] * each), 1))
        x0 = round(bed["x"] - float(sim["bed"][0]) * each)
        y1 = round(bed["foot"] + float(sim["bed"][1]) * each)
        y0 = y1 - size[1]
        how = cv2.INTER_AREA if each < 1 else cv2.INTER_CUBIC
        far = min(float(focal) / bed["scale"] / 100, 4.0)             # the distance of the fire in hundreds of metres; no more blur beyond 400 m
        near, halo = SCATTER[0][0] + SCATTER[0][1] * far, SCATTER[1][0] + SCATTER[1][1] * far
        spread = lambda f: (1 - halo) * cv2.GaussianBlur(f, (0, 0), near) + halo * cv2.GaussianBlur(f, (0, 0), SCATTER[2])
        foot = np.arange(size[1])[:, None, None] <= size[1] - float(sim["bed"][1]) * each      # nothing shows under the bed: a wall or a bowl stands there
        big = np.stack([spread(cv2.resize(f, size, interpolation=how) * foot) for f in rgba]).clip(0, 1)
        seen = big[..., 3].max(0) > 0.01
        rows, cols = np.flatnonzero(seen.any(1)), np.flatnonzero(seen.any(0))
        ra, rb = max(rows[0], -y0), min(rows[-1] + 1, H - y0)          # what shows, and lies on the plate
        ca, cb = max(cols[0], -x0), min(cols[-1] + 1, W - x0)
        big = big[:, ra:rb, ca:cb]
        box = (x0 + ca, y0 + ra, x0 + cb, y0 + rb)
        big[..., :3] /= np.maximum(big[..., 3:], 1e-4)                 # the colour itself
        if "thing" in bed:
            # a fire that burns in a thing (a bowl) is the flame and not what lies at or under the upper outline of that
            # thing. Beside the thing that line rises by one row per column: a flame leaves a bowl through its mouth
            own = things["label"] == ids.index(bed["thing"]) + 1
            cols = np.flatnonzero(own.any(0))
            rim = cv2.medianBlur(own.argmax(0)[cols].astype(np.float32)[None], 5)[0]
            xs = np.arange(W, dtype=np.float32)
            line = np.interp(xs, cols, rim) - np.maximum(cols[0] - xs, 0) - np.maximum(xs - cols[-1], 0)
            over = cv2.GaussianBlur((np.arange(H, dtype=np.float32)[:, None] < line[None]).astype(np.float32), (0, 0), 0.8)
            big[..., 3] *= over[box[1]:box[3], box[0]:box[2]]
            out[name + "_at"] = np.float32(1.02 * things["depth"][ids.index(bed["thing"])][bed["x"]])      # just behind the wall of the thing that faces the camera
        where = parts[name] if parts[name].any() else gone
        lit_round = cv2.GaussianBlur(parts[name].astype(np.float32), (0, 0), 30)
        lit_round = cv2.resize(lit_round / max(lit_round.max(), 1e-6), (W // 8, H // 8), interpolation=cv2.INTER_AREA)
        light = sim["light"] / sim["light"].mean()
        out.update({name + "_rgba": (big.clip(0, 1) * 255).astype(np.uint8), name + "_box": np.array(box), name + "_light": light.astype(np.float32),
                    name + "_depth": float(np.median(depth[where & (depth > 0)])), name + "_halo": lit_round.astype(np.float16)})
        f = big[0]
        part = shown[box[1]:box[3], box[0]:box[2]]
        behind = (depth[box[1]:box[3], box[0]:box[2]] > 0.97 * out[name + "_depth"])[..., None]      # what stands before the fire hides it
        shown[box[1]:box[3], box[0]:box[2]] = part * (1 - f[..., 3:] * behind) + f[..., :3] * f[..., 3:] * behind
        print(f"{name}: {bed['width']:.1f} m wide, {bed['scale']} px per m, picture {box[2] - box[0]} x {box[3] - box[1]} px at {box[:2]}, "
              f"depth {out[name + '_depth']:.1f}, light changes by {light.std():.0%}", flush=True)
    was = np.zeros((H, W), np.uint8)                                  # where the painted flame of each bed stood: the number of the bed, from 1
    for k, (name, _) in enumerate(fires, 1):
        was[cv2.dilate(parts[name].astype(np.uint8), np.ones((3, 3), np.uint8)) > 0] = k
    # a column of smoke (src/fire.py, `column`): the soot of a fire that burns out of sight, as pictures at its place.
    # It rises behind the far wall and the banners on it. Its colours are those of the painted smoke it replaces (the
    # thing of its name in THINGS), the darkest where the soot is thickest
    # the sky, where the painted smoke stood (its base had a measured depth), and what the plate shows farther than
    # BEYOND: the crane and the city behind the far wall. The banners on the far wall are nearer and hide the column
    sky = ~np.load(SCENE + "_clean.npz")["mask"] | (things["label"] == ids.index("S1") + 1) | (back["mask"] & (depth > BEYOND))
    sky = cv2.GaussianBlur(sky.astype(np.float32), (0, 0), 1.0)
    first = np.asarray(Image.open(SCENE + "_plate.png").convert("RGB")).astype(np.float32) / 255
    smokes = [(name, bed) for name, bed in beds() if bed["kind"] == "smoke"]
    for name, bed in smokes:
        sim = np.load(os.path.join(ROOT, "wip", "sim", "muster", name + ".npz"))
        soot = sim["soot"].astype(np.float32)
        pixels = first[things["label"] == ids.index(name) + 1]
        pixels = pixels[np.argsort(-(pixels @ luma))]                  # the lightest first: the thinnest smoke
        ramp = cv2.resize(np.stack([np.median(part, 0) for part in np.array_split(pixels, 64)])[None], (256, 1), interpolation=cv2.INTER_LINEAR)[0]
        seen = soot[soot > 0.02]
        rank = np.interp(soot, np.quantile(seen, np.linspace(0, 1, 256)), np.linspace(0, 1, 256), left=0.0)
        cover = 1 - np.exp(-THICK * soot / np.quantile(seen, 0.9))
        rgba = np.concatenate([ramp[(rank * 255).astype(int)] * cover[..., None], cover[..., None]], -1)      # colour times cover
        each = float(sim["cell"]) * bed["scale"]                       # plate pixels per cell
        size = (max(round(soot.shape[2] * each), 1), max(round(soot.shape[1] * each), 1))
        x0, y1 = round(bed["x"] - float(sim["bed"][0]) * each), round(bed["foot"] + float(sim["bed"][1]) * each)
        y0 = y1 - size[1]
        far = min(float(focal) / bed["scale"] / 100, 4.0)             # the air before it blurs it as it blurs a fire at that distance
        big = np.stack([cv2.GaussianBlur(cv2.resize(f, size, interpolation=cv2.INTER_CUBIC), (0, 0), SCATTER[0][0] + SCATTER[0][1] * far) for f in rgba]).clip(0, 1)
        ra, rb, ca, cb = max(0, -y0), min(size[1], H - y0), max(0, -x0), min(size[0], W - x0)      # what lies on the plate
        big = big[:, ra:rb, ca:cb] * sky[y0 + ra:y0 + rb, x0 + ca:x0 + cb][None, ..., None]
        rows, cols = np.flatnonzero((big[..., 3].max(0) > 0.01).any(1)), np.flatnonzero((big[..., 3].max(0) > 0.01).any(0))
        big = big[:, rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
        box = (x0 + ca + cols[0], y0 + ra + rows[0], x0 + ca + cols[-1] + 1, y0 + ra + rows[-1] + 1)
        big[..., :3] /= np.maximum(big[..., 3:], 1e-4)                 # the colour itself
        here = depth[box[1]:box[3], box[0]:box[2]][sky[box[1]:box[3], box[0]:box[2]] > 0.5]
        out.update({name + "_rgba": (big.clip(0, 1) * 255).astype(np.uint8), name + "_box": np.array(box),
                    name + "_at": np.float32(0.97 * np.percentile(here, 2))})      # before the sky behind it
        f = big[0]
        part = shown[box[1]:box[3], box[0]:box[2]]
        shown[box[1]:box[3], box[0]:box[2]] = part * (1 - f[..., 3:]) + f[..., :3] * f[..., 3:]
        print(f"{name}: column of smoke, source {bed['width']:.1f} m wide, {bed['scale']} px per m, picture {box[2] - box[0]} x {box[3] - box[1]} px at {box[:2]}, "
              f"depth {float(out[name + '_at']):.1f}, colours from {len(pixels)} painted pixels", flush=True)
    # the stand of a brazier (ELEMENTS, `stand`): its column, rows and width, the depth of the bowl it carries (the
    # thing of the fire) and the colour of the bowl's dark parts
    stands = []
    for el in ELEMENTS:
        if "stand" in el:
            x, top, foot, wide = el["stand"]
            bowl = np.asarray(Image.open(SCENE + f"_thing_{el['thing']}.png").convert("RGBA"), np.float32) / 255
            dark = (bowl[..., 3] > 0.5) & (bowl[..., :3] @ luma < 0.22)
            stands.append([x, top, foot, wide, things["depth"][ids.index(el["thing"])][x], *np.median(bowl[..., :3][dark], 0)])
            print(f"stand of {el['id']}: column {x}, rows {top} to {foot}, depth {stands[-1][4]:.1f}, colour {np.round(np.array(stands[-1][5:]) * 255)}")
    np.savez_compressed(SCENE + "_flames.npz", names=np.array([name for name, _ in fires]), smokes=np.array([name for name, _ in smokes]), was=was,
                        stands=np.array(stands, np.float32).reshape(-1, 8), **out)
    page = np.concatenate([plate, still, shown], 0)
    Image.fromarray((page.clip(0, 1) * 255).astype(np.uint8)).save(os.path.join(ROOT, "wip", "preview", "muster-flames.png"))
    print("wrote", SCENE + "_still.png, _flames.npz and wip/preview/muster-flames.png (the plate, without its flames, with frame 0 of the simulated ones)")


def assemble(frames, out, width=0):
    """The frames f000.png ... as an animated AVIF at RATE frames per second, `width` pixels wide or as rendered."""
    import glob
    from PIL import Image
    files = sorted(glob.glob(os.path.join(frames, "f[0-9]*.png")))
    pages = [Image.open(f).convert("RGB") for f in files]
    if int(width):
        pages = [im.resize((int(width), round(im.height * int(width) / im.width)), Image.LANCZOS) for im in pages]
    ends = [round(1000 * (k + 1) / RATE) for k in range(len(pages))]   # a frame lasts whole milliseconds: 33 or 34
    pages[0].save(out, save_all=True, append_images=pages[1:], duration=[b - a for a, b in zip([0] + ends, ends)], quality=88, speed=4,
                  subsampling="4:4:4")
    print("wrote", out, len(files), "frames", round(os.path.getsize(out) / 1e6, 2), "MB")


def lit(m, picture, gain):
    """The plate's material: its picture, which emits, with its brightness multiplied by the picture `gain`, the
    glow of the fires in this frame."""
    N, L = m.node_tree.nodes, m.node_tree.links
    for node in list(N):
        if node.type != "OUTPUT_MATERIAL":
            N.remove(node)
    uv = N.new("ShaderNodeUVMap").outputs["UV"]
    tex, glow, both, em = N.new("ShaderNodeTexImage"), N.new("ShaderNodeTexImage"), N.new("ShaderNodeVectorMath"), N.new("ShaderNodeEmission")
    tex.image, tex.interpolation, glow.image, both.operation = picture, "Cubic", gain, "MULTIPLY"
    L.new(uv, tex.inputs["Vector"]); L.new(uv, glow.inputs["Vector"])
    L.new(tex.outputs["Color"], both.inputs[0]); L.new(glow.outputs["Color"], both.inputs[1])
    L.new(both.outputs[0], em.inputs["Color"])
    L.new(em.outputs[0], N["Material Output"].inputs["Surface"])


def plane(name, picture, gain):
    """The material of a thing of the plate that is a surface of its own: its picture, which emits as the plate
    does, shown by its cover, with its brightness multiplied by `gain` at its place on the plate (the second set of
    places, "plate")."""
    import bpy
    m = bpy.data.materials.new("thing " + name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for node in list(N):
        if node.type != "OUTPUT_MATERIAL":
            N.remove(node)
    tex, glow, at = N.new("ShaderNodeTexImage"), N.new("ShaderNodeTexImage"), N.new("ShaderNodeUVMap")
    tex.image = bpy.data.images.load(picture)
    tex.image.alpha_mode = "STRAIGHT"
    tex.interpolation = "Cubic"
    tex.extension = "CLIP"
    glow.image, at.uv_map = gain, "plate"
    L.new(at.outputs["UV"], glow.inputs["Vector"])
    lit = N.new("ShaderNodeVectorMath")
    lit.operation = "MULTIPLY"
    L.new(tex.outputs["Color"], lit.inputs[0]); L.new(glow.outputs["Color"], lit.inputs[1])
    emit, clear, both = N.new("ShaderNodeEmission"), N.new("ShaderNodeBsdfTransparent"), N.new("ShaderNodeMixShader")
    L.new(lit.outputs[0], emit.inputs["Color"])
    L.new(tex.outputs["Alpha"], both.inputs["Fac"]); L.new(clear.outputs[0], both.inputs[1]); L.new(emit.outputs[0], both.inputs[2])
    L.new(both.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def mesh(name, quads, material, uv=None, **colours):
    """An object of four-cornered faces. quads: (n, 4, 3), corners counter-clockwise seen from the camera. colours:
    one colour per corner, (n, 4, 3 or 4), kept under its name for the material."""
    import bpy
    n = len(quads)
    me = bpy.data.meshes.new(name)
    me.vertices.add(4 * n)
    me.vertices.foreach_set("co", quads.astype(np.float32).ravel())
    me.loops.add(4 * n)
    me.loops.foreach_set("vertex_index", np.arange(4 * n))
    me.polygons.add(n)
    me.polygons.foreach_set("loop_start", np.arange(0, 4 * n, 4))
    me.polygons.foreach_set("loop_total", np.full(n, 4))
    if uv is not None:
        me.uv_layers.new(name="uv").data.foreach_set("uv", uv.astype(np.float32).ravel())
    for key, value in colours.items():
        paint(me, key, value, new=True)
    me.update()
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    return ob


def paint(me, key, value, new=False):
    """Sets the corner colours `key` of a mesh; a value without a fourth number gets 1."""
    if value.shape[-1] == 3:
        value = np.concatenate([value, np.ones(value.shape[:-1] + (1,), np.float32)], -1)
    layer = me.color_attributes.new(key, "FLOAT_COLOR", "CORNER") if new else me.color_attributes[key]
    layer.data.foreach_set("color", value.astype(np.float32).ravel())


def shader(name, atlas=None, cloth=None, soft=False):
    """A surface that only emits. Its colour is worked out in the plate's own number space and turned into light at
    the end. With `atlas`: the picture at the places `uv` and `uv2`, two sizes of it, mixed by `misc` blue; moved
    towards the colour of dirt by `misc` red, times `tint`, moved towards `air` by `misc` green, shown by its alpha. With `cloth`: that picture (a file, or a
    picture of the scene) times `tint`, shown by its alpha. Without both: the colour `tint`, shown by its fourth number.
    The renderer shows a half-covering surface by chance, sample by sample; `soft` is for a picture with wide soft
    cover, a flame: there it showed as a pattern of dots."""
    import bpy
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    for node in list(N):
        if node.type != "OUTPUT_MATERIAL":
            N.remove(node)
    def attribute(key):
        node = N.new("ShaderNodeAttribute")
        node.attribute_name = key
        return node
    def mix(a, b, factor, kind="RGBA"):
        node = N.new("ShaderNodeMix")
        node.data_type = kind
        L.new(factor, node.inputs["Factor"]); L.new(a, node.inputs["A"]); L.new(b, node.inputs["B"])
        return node.outputs["Result"]
    def times(a, b, kind="ShaderNodeMath"):
        node = N.new(kind)
        node.operation = "MULTIPLY"
        L.new(a, node.inputs[0]); L.new(b, node.inputs[1])
        return node.outputs[0]
    tint = attribute("tint")
    if cloth:
        tex = N.new("ShaderNodeTexImage")
        tex.image = bpy.data.images.load(cloth) if isinstance(cloth, str) else cloth
        tex.image.colorspace_settings.name = "Non-Color"
        tex.image.alpha_mode = "STRAIGHT"
        colour, alpha = times(tex.outputs["Color"], tint.outputs["Color"], "ShaderNodeVectorMath"), tex.outputs["Alpha"]
    elif atlas:
        tex, next_ = N.new("ShaderNodeTexImage"), N.new("ShaderNodeTexImage")
        tex.image = next_.image = bpy.data.images.load(atlas)
        tex.image.colorspace_settings.name = "Non-Color"
        tex.image.alpha_mode = "STRAIGHT"
        second = N.new("ShaderNodeUVMap")
        second.uv_map = "uv2"
        L.new(second.outputs["UV"], next_.inputs["Vector"])
        misc = N.new("ShaderNodeSeparateColor")
        L.new(attribute("misc").outputs["Color"], misc.inputs["Color"])
        picture = mix(tex.outputs["Color"], next_.outputs["Color"], misc.outputs["Blue"])      # the two sizes of the picture next to the size of the card
        grey = N.new("ShaderNodeVectorMath")
        grey.operation = "DOT_PRODUCT"
        L.new(picture, grey.inputs[0])
        grey.inputs[1].default_value = (0.2126, 0.7152, 0.0722)
        dirt = N.new("ShaderNodeVectorMath")
        dirt.operation = "SCALE"
        dirt.inputs[0].default_value = WARM
        L.new(grey.outputs["Value"], dirt.inputs["Scale"])
        colour = times(mix(picture, dirt.outputs["Vector"], misc.outputs["Red"]), tint.outputs["Color"], "ShaderNodeVectorMath")
        colour = mix(colour, attribute("air").outputs["Color"], misc.outputs["Green"])
        alpha = mix(tex.outputs["Alpha"], next_.outputs["Alpha"], misc.outputs["Blue"], "FLOAT")
    else:
        colour, alpha = tint.outputs["Color"], tint.outputs["Alpha"]
    light = N.new("ShaderNodeGamma")
    light.inputs["Gamma"].default_value = 2.2
    L.new(colour, light.inputs["Color"])
    emit, clear = N.new("ShaderNodeEmission"), N.new("ShaderNodeBsdfTransparent")
    L.new(light.outputs["Color"], emit.inputs["Color"])
    if soft:                                                          # what is behind, less the cover, plus the light times the cover: no chance in it
        both, rest = N.new("ShaderNodeAddShader"), N.new("ShaderNodeMath")
        rest.operation = "SUBTRACT"
        rest.inputs[0].default_value = 1.0
        L.new(alpha, rest.inputs[1])
        L.new(rest.outputs[0], clear.inputs["Color"])
        L.new(alpha, emit.inputs["Strength"])
        L.new(clear.outputs[0], both.inputs[0]); L.new(emit.outputs[0], both.inputs[1])
    else:
        both = N.new("ShaderNodeMixShader")
        L.new(alpha, both.inputs["Fac"]); L.new(clear.outputs[0], both.inputs[1]); L.new(emit.outputs[0], both.inputs[2])
    L.new(both.outputs[0], N["Material Output"].inputs["Surface"])
    return m


def scene():
    """Builds the scene and returns the function that sets it to a frame of the loop."""
    import bpy, math
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import backdrop as B
    bpy.ops.wm.read_factory_settings(use_empty=True)
    back, fov = B.backdrop(SCENE + "_back")
    cam = B.camera(fov, RES)
    d = np.load(SCENE + "_back.npz")
    K, near = d["intrinsics"], float(np.percentile(d["depth"][d["mask"]], 1))
    cam.data.shift_x, cam.data.shift_y = 0.5 - float(K[0, 2]), (float(K[1, 2]) - 0.5) * RES[1] / RES[0]
    cam.data.clip_end = 10000
    H, W = d["depth"].shape
    space = lambda x, y, z: np.stack([((x + 0.5) / W - K[0, 2]) / K[0, 0] * z, z * np.ones_like(x), -((y + 0.5) / H - K[1, 2]) / K[1, 1] * z], -1)

    def picture(name, w, h):                                          # a picture whose pixels the pose sets
        im = bpy.data.images.new(name, w, h, alpha=True, float_buffer=True)
        im.colorspace_settings.name = "Non-Color"
        im.alpha_mode = "STRAIGHT"
        return im

    # the fires: the plate without its painted flames, the glow of the simulated ones, and each as a picture at its place
    fl = np.load(SCENE + "_flames.npz")
    names = [str(name) for name in fl["names"]]
    lights = np.stack([fl[name + "_light"] for name in names])        # the light of each fire through the loop, against its mean
    halos = np.stack([fl[name + "_halo"] for name in names]).astype(np.float32)
    gain = picture("gain", halos.shape[2], halos.shape[1])
    co = np.zeros(len(back.data.vertices) * 3, np.float32)            # the plate where a painted flame stood goes behind the fire that burns there
    back.data.vertices.foreach_get("co", co)
    co, was = co.reshape(-1, 3), fl["was"][::2, ::2].ravel()            # the backdrop has one vertex per two pixels
    for k, name in enumerate(names, 1):
        far = float(fl[name + "_depth"])
        move = (was == k) & (co[:, 1] < far)
        co[move] *= (far / co[move, 1])[:, None]
    back.data.vertices.foreach_set("co", co.ravel())
    back.data.update()
    lit(back.material_slots[0].material, bpy.data.images.load(SCENE + "_still.png"), gain)
    burning = []
    for k, name in enumerate(names):
        x0, y0, x1, y1 = (np.float32(v) - 0.5 for v in fl[name + "_box"])
        z = float(fl[name + "_depth"]) * (0.97 - 0.002 * k)           # a little before what it burns on, and no two fires at one depth
        if name + "_at" in fl:
            z = float(fl[name + "_at"])                               # a fire that burns in a thing: at the depth flames() gives
        im = picture(name, int(x1 - x0), int(y1 - y0))
        mesh(name, np.stack([space(x0, y1, z), space(x1, y1, z), space(x1, y0, z), space(x0, y0, z)])[None], shader(name, cloth=im, soft=True),
             uv=np.array([[(0, 0), (1, 0), (1, 1), (0, 1)]], np.float32), tint=np.ones((1, 4, 3), np.float32))
        burning.append((im, fl[name + "_rgba"]))
    for name in (str(v) for v in fl["smokes"]):                       # a column of smoke: its picture in the sky, at the depth flames() gives
        x0, y0, x1, y1 = (np.float32(v) - 0.5 for v in fl[name + "_box"])
        z, im = float(fl[name + "_at"]), picture(name, int(x1 - x0), int(y1 - y0))
        mesh(name, np.stack([space(x0, y1, z), space(x1, y1, z), space(x1, y0, z), space(x0, y0, z)])[None], shader(name, cloth=im, soft=True),
             uv=np.array([[(0, 0), (1, 0), (1, 1), (0, 1)]], np.float32), tint=np.ones((1, 4, 3), np.float32))
        burning.append((im, fl[name + "_rgba"]))
    import rods as R
    iron = shader("iron")
    # the stand of a brazier (flames): a round rod at the depth of the bowl. Under the bowl it is twice as wide and
    # lighter, where it carries the bowl and the fire lights it
    for x, top, foot, wide, z, *colour in fl["stands"]:
        rows = np.arange(top, foot + 1.0)
        under = np.clip(1 - (rows - top) / (2 * wide), 0, 1)[:, None]      # 1 under the bowl, 0 from two widths down
        rod = dict(at=np.stack([np.full(len(rows), x), rows], 1), r=0.5 * wide * (1 + under[:, 0]), colour=np.array(colour)[None] * (1 + 0.6 * under), lean=0.0)
        mesh("stand", *R.lathe(rod, space, 0.995 * z)[:1], iron, tint=R.lathe(rod, space, 0.995 * z)[1])
    # the things of the plate that are no part of the ground (things): each a surface of its own with its picture as
    # cover, in strips of 8 columns at its depth by column. The glow of the fires lies on it as on the ground
    T = np.load(SCENE + "_things.npz")
    for name in (str(v) for v in T["planes"]):
        x0, y0, x1, y1 = (float(v) for v in T["box_" + name])
        xs = np.unique(np.r_[np.arange(x0, x1, 8), x1])
        zs = np.interp(xs, np.arange(x0, x1) + 0.5, T["depth_" + name])
        at = lambda i, y: space(np.float32(xs[i] - 0.5), np.float32(y - 0.5), zs[i])
        strips = range(len(xs) - 1)
        ob = mesh("thing " + name, np.array([[at(i, y1), at(i + 1, y1), at(i + 1, y0), at(i, y0)] for i in strips]), plane(name, SCENE + f"_thing_{name}.png", gain),
                  uv=np.array([[((xs[j] - x0) / (x1 - x0), v) for j, v in ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))] for i in strips], np.float32))
        ob.data.uv_layers.new(name="plate").data.foreach_set(
            "uv", np.array([[(xs[j] / W, 1 - y / H) for j, y in ((i, y1), (i + 1, y1), (i + 1, y0), (i, y0))] for i in strips], np.float32).ravel())
    # the posts of the banners (posts): each a round rod at the depth of its banner, with the radius and the colours
    # that the source picture shows along it. A post is an object: it is whole from its crossbar to its foot, and it
    # moves against what is behind it as its banner does
    measured, ids = np.load(SCENE + "_posts.npz"), [str(v) for v in T["ids"]]
    for name in [str(v) for v in measured["names"]] + [str(v) for v in measured["parts"]]:      # the posts, then the crossbars, finials and pikes that are built
        rod = {key: measured[f"{name}_{key}"] for key in ("at", "r", "colour", "lean")}
        own = name.split("_")[0]
        if own in ids:                                                    # a pike: just before the wall it stands on, at the depth of the wall in its own column
            z = 0.99 * float(T["depth"][ids.index(own)][int(round(rod["at"][-1, 0]))])
        else:
            z = float(np.nanmedian(T["depth"][ids.index("T" + own[1:])]))
        quads, tint = R.lathe(rod, space, z)
        mesh("rod " + name, quads, iron, tint=tint)
    # the crowd: every figure as a card with its picture and as a stroke of one colour; a frame shows one of the two
    c = dict(np.load(SCENE + "_crowd.npz"))                           # read whole: a file that is written again while a render reads it ends the render
    n = len(c["slot"])
    mesh("floor", c["floor"], shader("floor"), tint=np.concatenate([c["fcol"], c["falpha"][..., None]], -1))
    views = [str(view) for view in c["views"]]
    walk, of, pick, flip = c["walk"].astype(int), c["slot"].astype(int), c["pick"].astype(int), c["flip"] > 0
    ch = {key[6:]: c[key] for key in c if key.startswith("chain_")}      # what a figure is, it is by its chain
    turn, walking = c["turn"].astype(np.float64), ch["go"][of] > 0
    walks = [{key[5:]: c[key][w] for key in c if key.startswith("walk_")} for w in range(len(c["walk_eye"]))]
    atlas = np.array([int(g["atlas"]) for g in walks])[walk]          # the view of each figure
    rects = [c["rect_" + view] for view in views]                     # the place of each picture at each size in its atlas
    levels = rects[0].shape[0]
    rows = np.zeros(n, np.float32)                                    # the rows of each figure's picture at its largest size, and its mean colour
    mean = np.zeros((n, 3), np.float32)
    for a, view in enumerate(views):
        rows[atlas == a], mean[atlas == a] = c["rows_" + view][pick[atlas == a]], c["mean_" + view][pick[atlas == a]]
    luma, warm = np.array([0.2126, 0.7152, 0.0722], np.float32), np.array(WARM, np.float32)

    lines = [parapet(g["zp"], g["line"], g["eye"], g["span"]) for g in walks]      # for the depth of each figure in the camera's space

    def standing(w, t):
        """The figures of walk w at the moment t of the loop: the walk, which figures they are, their places across
        and along it, column and row of their feet, height by the rule, depth, how far under the floor, whether
        in the picture, their own height, and their depth in the camera's space. Then how far each has gone, its pace
        against its mean pace, and where its height, its brightness and its dirt are in their slow change."""
        g = walks[w]
        k = np.flatnonzero(walk == w)
        f, r, gone, pace, loops = way(ch, of[k], turn[k], t)
        drift = walking[k][:, None] * np.sin(2 * np.pi * loops[:, None] / ch["drift"][of[k], :1] + ch["drift"][of[k], 1:])
        x, y, rule, depth, ok = place(g, f, r)
        return g, k, f, r, x, y, rule, depth, ok, rule * c["high"][k] * (1 + DRIFT[1] * drift[:, 0]), deep(lines[w], depth), gone, pace, drift

    # the cards. A figure that walks passes others. As a flat card at one depth it changes places with the card it
    # passes in one frame, over all the two share on the plate, and back again when its pace changes. With the depth
    # of a body, the line between the two goes across what they share, over as long as the passing takes. Two cards
    # in one column of the plate have no such line: there the head stands nearer than the feet, by another amount
    # for every chain, and the line goes up or down the card
    bent = np.zeros(n, bool)
    for w in range(len(walks)):
        for t in (0.0, 1 - 1 / FRAMES):
            k, ok, tall = (standing(w, t)[j] for j in (1, 8, 9))
            bent[k] |= walking[k] & ok & (tall >= ROUND[0])
    row = np.cumsum(bent) - 1                                         # the place of each of them among them
    nod = BODY[1] * ((of * 0.6180339887) % 1.0)                       # how much nearer the head of each figure stands: the same for all figures of a chain
    specks = mesh("far crowd", np.zeros((n, 4, 3), np.float32), shader("far crowd"), tint=np.zeros((n, 4, 4), np.float32)).data
    ramp = np.array([SHADE, SHADE, 1, 1], np.float32)[None, :, None]
    crowds = []
    for a, view in enumerate(views):
        look = shader(f"crowd {view}", SCENE + f"_atlas_{view}.png")
        for strips, k in ((1, np.flatnonzero(atlas == a)), (ROUND[1], row[(atlas == a) & bent])):
            m = len(k) * strips
            if m:
                ob = mesh(f"crowd {view} {strips}", np.zeros((m, 4, 3), np.float32), look, uv=np.zeros((m, 4, 2), np.float32),
                          tint=np.ones((m, 4, 3), np.float32), misc=np.zeros((m, 4, 3), np.float32), air=np.zeros((m, 4, 3), np.float32))
                ob.data.uv_layers.new(name="uv2")
                crowds.append((ob.data, k, strips))
    print(f"crowd: {n} figures, {int(bent.sum())} of them with a card of {ROUND[1]} strips", flush=True)
    # the banners: each cloth with its places through the loop
    b, blown = np.load(SCENE + "_banners.npz"), np.load(SCENE + "_wind.npz")
    banner_ids = [el["id"] for el in ELEMENTS if el["kind"] == "banner"]
    banner_left = {el["id"]: el["box"][0] for el in ELEMENTS if el["kind"] == "banner"}
    mast_depth = {str(v): T["depth"][n] for n, v in enumerate(T["ids"])}      # by column; a cloth is scaled about the camera, which keeps its picture
    weave, lamp, cloths = shader("cloth", cloth=SCENE + "_hung.png"), np.array(LAMP) / np.linalg.norm(LAMP), []

    def hemmed(k, banner):
        """The places in the picture and the places through the loop of cloth k. Its upper edge is raised to the row
        at which the cloth begins under its crossbar (things, `hang`), at its own depth: the cloth hangs from the
        crossbar."""
        uv, places = b[f"uv{k}"], blown[f"p{k}"]
        if "hang_" + banner in T.files:
            pin, by = b[f"pin{k}"], T["hang_" + banner]              # the held row under the crossbar
            px = uv[pin, 0] * W - 0.5
            row = np.interp(px - banner_left[banner], np.arange(len(by)), by)
            uv, places = uv.copy(), places.copy()
            uv[pin, 1], places[:, pin] = 1 - (row + 0.5) / H, space(px, row, places[0, pin, 1])
        return uv, places

    k = 1
    while f"v{k}" in b:
        faces = b[f"f{k}"]
        cloth_uv, places = hemmed(k, banner_ids[k - 1])
        me = bpy.data.meshes.new(f"cloth{k}")
        me.from_pydata(b[f"v{k}"].tolist(), [], faces.tolist())
        me.uv_layers.new(name="uv").data.foreach_set("uv", cloth_uv[faces.ravel()].ravel())
        paint(me, "tint", np.ones((len(faces), 4, 3), np.float32), new=True)
        me.materials.append(weave)
        bpy.context.collection.objects.link(bpy.data.objects.new(f"cloth{k}", me))
        hung = "T" + banner_ids[k - 1][1:]                              # the post of this banner in THINGS; a banner without one keeps its own depth
        if hung in mast_depth:
            # the cloth hangs before its crossbar and its post at every moment (things, `swing`): the wind carries it 2 to
            # 10 % deeper than it hangs at rest
            places = places * (HUNG * float(np.nanmedian(mast_depth[hung])) / places[..., 1].max())
        cloths.append((me, faces, places.astype(np.float32)))
        k += 1

    def fold(p, faces):
        """The brightness of every corner of a cloth at the places p: by how much its slope has turned to the lamp."""
        q = p[faces]
        normal = np.cross(q[:, 2] - q[:, 0], q[:, 3] - q[:, 1])       # of each face, by its two diagonals
        normal *= np.sign(-normal[:, 1:2] + 1e-9)                     # towards the camera
        at = np.zeros_like(p)
        for corner in range(4):
            np.add.at(at, faces[:, corner], normal)
        at /= np.linalg.norm(at, axis=1, keepdims=True) + 1e-9
        bright = np.clip(1 + FOLD * (at @ lamp + lamp[1]), 0.5, 1.5)   # a cloth that hangs flat faces the camera: no change
        return np.repeat(bright[faces][..., None], 3, 2)

    # dust: HAZE curtains per walk. A curtain stands across the walk at one rank, from the floor up, and shows the dust
    # of a strip of air (src/dust.py) in the colour of the air there; each takes its dust from another place and
    # moment of the strip. A curtain stands for the dust between it and the next one: the farther apart, the thicker,
    # between 12 and 40 m
    dusts = []
    for w, g in enumerate(walks):
        sim = np.load(os.path.join(ROOT, "wip", "sim", "muster", f"dust{w}.npz"))
        dust, cell = sim["dust"].astype(np.float32), float(sim["cell"])
        ok, tall = standing(w, 0.0)[8:10]
        sizes = np.geomspace(np.quantile(tall[ok], 0.999), max(np.quantile(tall[ok], 0.02), 4.0), HAZE)      # the rows of a figure at each curtain
        ranks = (FOCAL / sizes - g["a"][1] - 0.5 * float(g["wide"]) * g["across"][1]) / g["along"][1]
        apart = np.abs(np.gradient(ranks)) * 1.8                      # metres from one curtain to the next
        cells = round(float(g["wide"]) * 1.8 / cell)                  # cells of the strip across the walk
        ends = np.clip(np.minimum(np.arange(cells), cells - 1 - np.arange(cells)) * cell / 1.0, 0, 1)[None]      # no dust beyond the walk
        ends = ends * np.clip(((np.arange(dust.shape[1]) + 0.5) * cell - OVER[0]) / (OVER[1] - OVER[0]), 0, 1)[:, None] ** 2      # and none between the bodies
        for nth, r in enumerate(ranks):
            f = np.linspace(0, float(g["wide"]), 13)
            x, y, rule, depth = place(g, f, r + 0 * f)[:4]
            z = deep(lines[w], depth)
            low, high = space(x, y, z), space(x, y - dust.shape[1] * cell / 1.8 * rule, z)
            u = np.linspace(1, 0, 13) if x[-1] < x[0] else np.linspace(0, 1, 13)      # the wind carries the dust to the right on the plate
            im = picture(f"dust {w} {nth}", cells, dust.shape[1])
            mesh(f"dust {w} {nth}", np.stack([low[:-1], low[1:], high[1:], high[:-1]], 1), shader(f"dust {w} {nth}", cloth=im, soft=True),
                 uv=np.stack([np.stack([u[:-1], 0 * u[:-1]], 1), np.stack([u[1:], 0 * u[1:]], 1), np.stack([u[1:], 1 + 0 * u[1:]], 1), np.stack([u[:-1], 1 + 0 * u[:-1]], 1)], 1),
                 tint=np.ones((12, 4, 3), np.float32))
            at = np.interp(np.linspace(0, 1, cells), u[::-1] if u[0] > u[-1] else u, np.arange(13)[::-1] if u[0] > u[-1] else np.arange(13))
            hue = c["air"][np.clip((np.interp(at, np.arange(13), y) / 8).astype(int) - 2, 0, c["air"].shape[0] - 1),
                           np.clip((np.interp(at, np.arange(13), x) / 8).astype(int), 0, c["air"].shape[1] - 1)] * 1.05
            hue = np.concatenate([np.tile(hue[None], (dust.shape[1], 1, 1)), np.zeros((dust.shape[1], cells, 1), np.float32)], -1)
            dusts.append((im, dust, hue, (np.arange(cells) + 251 * nth) % dust.shape[2], THIN * np.clip(apart[nth], 12.0, 40.0) / 20.0, ends, nth * FRAMES // HAZE))
    bed = dict(beds())
    nearest = [min(range(len(names)), key=lambda k: abs(bed[names[k]]["x"] - x)) for x in c["fires"][:, 0]]        # the fire that lights each part of the crowd
    fire = np.array(FIRE, np.float32)

    def pose(i):
        t = (i % FRAMES) / FRAMES
        frame = i % FRAMES
        Q = np.zeros((n, 4, 3), np.float32)                           # the strokes; a figure out of the picture is a point
        Q[..., 1] = -1.0                                              # behind the camera
        dot = np.zeros((n, 4, 4), np.float32)
        cards = {}                                                    # by the strips of a card: corners, the place in its picture at two sizes, tint, misc, air
        for strips, m in ((1, n), (ROUND[1], int(bent.sum()))):
            cards[strips] = [np.zeros((m, strips, 4, size), np.float32) for size in (3, 2, 2, 3, 3, 3)]
            cards[strips][0][..., 1] = -1.0
            cards[strips][3][:] = 1.0
        for w in range(len(walks)):
            g, k, f, r, x, y, rule, depth, ok, tall, z, gone, pace, drift = standing(w, t)
            # its step: one that walks steps by the way it has gone, and less while it slows; one that stands shifts its weight
            own, goes = of[k], walking[k]
            count = np.where(goes, gone / ch["step"][own], ch["steps"][own] * t) + ch["at"][own]
            lively = np.where(goes, np.clip(pace, 0, 1), 1.0)
            rise = lively * np.maximum(np.where(goes, *RISE) * tall, LEAST) * 0.5 * (1 - np.cos(2 * np.pi * count))      # plate pixels
            lean = c["lean"][k] + lively * np.maximum(np.where(goes, *SWAY), LEAST / tall) * np.sin(
                2 * np.pi * (np.where(goes, count / 2, ch["sways"][own] * t) + ch["to"][own]))
            worn, dirt = c["worn"][k] * (1 + DRIFT[2] * drift[:, 1]), np.clip(c["dirt"][k] + DRIFT[3] * drift[:, 2], 0, 1)
            big = ok & (tall >= SMALL)
            small = ok & ~big
            # light and air at its place
            lamps = c["lamp"][c["lamp"][:, 0] == w][:, 1:]
            burn = lights[[nearest[j] for j in np.flatnonzero(c["lamp"][:, 0] == w)], frame] if len(lamps) else np.zeros(1)
            lit = shading(g["cells"], f, r)[:, None] + (firelight(lamps, x, depth) * burn[None]).sum(1)[:, None] * fire[None]
            thin = 1 - np.exp(-(depth / float(g["eye"]) / MURK) ** 1.5)
            thin = 1 - (1 - thin) * np.clip((1 - f / float(g["wide"])) / float(g["veil"]), 0, 1)      # the far rows stand in the smoke: they take its colour
            here = c["air"][np.clip(((y - tall / 2) / 8).astype(int), 0, c["air"].shape[0] - 1), np.clip((x / 8).astype(int), 0, c["air"].shape[1] - 1)]
            # the card: its corners in strips across, the picture of the size that fits, its colours
            for strips, cut, places in ((1, big & ~bent[k], k), (ROUND[1], big & bent[k], row[k])):
                P, uv, uv2, tint, misc, air = cards[strips]
                b, to = k[cut], places[cut]
                s = np.linspace(-1, 1, strips + 1)                    # across the card, from one side to the other
                foot, head = y[cut] - rise[cut], lean[cut] * tall[cut]
                across = x[cut][:, None] + s * (0.5 * tall[cut] * c["wide"][b])[:, None]
                body = depth[cut][:, None] - (strips > 1) * BODY[0] * (1 - s ** 2)      # the two sides at the figure's place, the middle nearer
                low = space(across, foot[:, None], deep(lines[w], body))
                top = space(across + head[:, None], (foot - tall[cut])[:, None], deep(lines[w], body - (strips > 1) * nod[b][:, None]))
                P[to] = np.stack([low[:, :-1], low[:, 1:], top[:, 1:], top[:, :-1]], 2)
                size = np.clip(np.log2(rows[b] / np.maximum(tall[cut], 1.0)), 0, levels - 1)      # between two sizes of its picture: both are shown, mixed
                level = np.minimum(np.floor(size).astype(int), levels - 2)
                for a in set(atlas[b].tolist()):
                    m = atlas[b] == a
                    for into, at in ((uv, level[m]), (uv2, level[m] + 1)):
                        rect = rects[a][at, pick[b[m]]]
                        u0, u1 = np.where(flip[b[m]], rect[:, 2], rect[:, 0]), np.where(flip[b[m]], rect[:, 0], rect[:, 2])
                        u = u0[:, None] + (u1 - u0)[:, None] * (s + 1) / 2
                        v0, v1 = np.broadcast_to(rect[:, 1:2], u.shape), np.broadcast_to(rect[:, 3:4], u.shape)
                        into[to[m]] = np.stack([np.stack([u[:, :-1], v0[:, :-1]], -1), np.stack([u[:, 1:], v0[:, 1:]], -1),
                                                np.stack([u[:, 1:], v1[:, 1:]], -1), np.stack([u[:, :-1], v1[:, :-1]], -1)], 2)
                tint[to] = (worn[cut][:, None] * lit[cut])[:, None, None] * ramp
                misc[to] = np.stack([dirt[cut], thin[cut], size - level], 1)[:, None, None]
                air[to] = here[cut][:, None, None]
            # the stroke: 1.2 plate pixels wide, in the mean colour of the picture
            b = k[small]
            high, up = np.minimum(tall[small], SMALL), rise[small]
            Q[b] = np.stack([space(x[small] + dx * 0.6, y[small] - dy * high - up, z[small]) for dx, dy in ((-1, 0), (1, 0), (1, 1), (-1, 1))], 1)
            col = mean[b] * worn[small][:, None]
            col = (col * (1 - dirt[small][:, None]) + (col @ luma)[:, None] * warm * dirt[small][:, None]) * lit[small]
            col = col * (1 - thin[small][:, None]) + here[small] * thin[small][:, None]
            dot[b] = np.concatenate([col, np.ones((len(b), 1), np.float32)], 1)[:, None]
        specks.vertices.foreach_set("co", Q.ravel())
        paint(specks, "tint", dot)
        specks.update()
        for me, k, strips in crowds:
            P, uv, uv2, tint, misc, air = cards[strips]
            me.vertices.foreach_set("co", P[k].ravel())
            me.uv_layers["uv"].data.foreach_set("uv", uv[k].ravel())
            me.uv_layers["uv2"].data.foreach_set("uv", uv2[k].ravel())
            paint(me, "tint", tint[k])
            paint(me, "misc", misc[k])
            paint(me, "air", air[k])
            me.update()
        for me, faces, places in cloths:
            p = places[i % FRAMES]
            me.vertices.foreach_set("co", p.ravel())
            paint(me, "tint", fold(p, faces))
            me.update()
        now = 1 + GLOW * np.tensordot(lights[:, i % FRAMES] - 1, halos, 1)
        gain.pixels.foreach_set(np.repeat(now[::-1, :, None], 4, 2).astype(np.float32).ravel())
        gain.update()
        for im, rgba in burning:
            im.pixels.foreach_set((rgba[i % FRAMES, ::-1].astype(np.float32) / 255).ravel())
            im.update()
        for im, dust, hue, cols, thick, ends, late in dusts:
            hue[..., 3] = (1 - np.exp(-thick * dust[(frame + late) % FRAMES][:, cols])) * ends
            im.pixels.foreach_set(hue.ravel())
            im.update()
        amp, swing = 0.008 * near, 2 * math.pi * round(LOOP / 4) * t     # the camera: a closed path every 4 s, parallax without tearing
        cam.location = (amp * math.sin(swing), amp * 0.6 * (1 - math.cos(swing)), amp * 0.3 * math.sin(2 * swing))
        bpy.context.view_layer.update()

    s = bpy.context.scene
    s.world = bpy.data.worlds.new("world")
    s.world.color = (0, 0, 0)
    s.render.engine = "CYCLES"
    s.cycles.device = "GPU"
    s.cycles.samples = SAMPLES
    s.cycles.use_denoising = False
    s.cycles.transparent_max_bounces = 96                             # a ray crosses the clear parts of many cards
    pr = bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type = "CUDA"
    pr.get_devices()
    for dv in pr.devices:
        dv.use = dv.type == "CUDA"
    s.view_settings.view_transform = "Standard"                       # the plate is already graded
    s.render.image_settings.file_format = "PNG"
    return pose


def render(*argv):
    import bpy
    pose = scene()
    s = bpy.context.scene
    draft = "draft" in argv                                           # half the size and a quarter of the samples: to see the motion
    if draft:
        s.render.resolution_x, s.render.resolution_y, s.cycles.samples = RES[0] // 2, RES[1] // 2, 16
    if argv[0] == "preview":
        s.cycles.samples = 24
        pose(int(argv[1]) if len(argv) > 1 else 0)
        s.render.filepath = os.path.join(ROOT, "wip", "preview", "scene-muster.png")
        bpy.ops.render.render(write_still=True)
        return
    outdir = os.path.join(ROOT, "wip", "frames-muster" + "-draft" * draft)
    os.makedirs(outdir, exist_ok=True)
    for i in ([int(a) for a in argv[1:] if a.isdigit()] or range(FRAMES + 1)):
        pose(i)
        s.render.filepath = os.path.join(outdir, f"f{i:03d}.png" if i < FRAMES else "seam-check.png")
        bpy.ops.render.render(write_still=True)
        print(f"FRAME {i + 1}/{FRAMES}", flush=True)
    print("RENDER_DONE", outdir)


def motion_map():
    """The plate with every moving element marked, and a legend that states each motion in plain words."""
    from PIL import Image, ImageDraw, ImageFont
    plate = Image.open(os.path.join(ROOT, "wip", "gen", "plate_musterP.png")).convert("RGB")
    font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 22)
    text = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 22)
    over = Image.new("RGBA", plate.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(over)
    for el in sorted(ELEMENTS, key=lambda el: el["kind"] != "smoke"):     # smoke first: its large boxes lie under the others
        c = COLOURS[el["kind"]]
        if el["kind"] == "crowd":
            draw.polygon(el["floor"], fill=c + (60,), outline=c + (255,))
            at = (el["floor"][0][0] + 30, el["floor"][0][1] + 40)
        else:
            draw.rectangle(el["box"], fill=c + (36,), outline=c + (255,), width=2)
            at = (el["box"][0] + 3, el["box"][1] + 2)
        draw.rectangle((at[0] - 2, at[1] - 1, at[0] + draw.textlength(el["id"], font=font) + 3, at[1] + 24), fill=(0, 0, 0, 190))
        draw.text(at, el["id"], fill=c + (255,), font=font)
    draw.line([(60, 40), (200, 40), (180, 28), (200, 40), (180, 52)], fill=(255, 255, 255, 255), width=4)
    draw.text((60, 54), "wind", fill=(255, 255, 255, 255), font=font)
    marked = Image.alpha_composite(plate.convert("RGBA"), over).convert("RGB")
    # legend: lines of at most the plate's width
    lines = []
    for kind, words in LEGEND:
        line = ""
        for word in words.split():
            if ImageDraw.Draw(marked).textlength(line + " " + word, font=text) > plate.width - 80:
                lines.append((kind, line))
                line, kind = "", "more"
            line = (line + " " + word).strip()
        lines.append((kind, line))
    page = Image.new("RGB", (plate.width, plate.height + 30 * len(lines) + 30), (24, 22, 22))
    page.paste(marked, (0, 0))
    draw = ImageDraw.Draw(page)
    for k, (kind, line) in enumerate(lines):
        y = plate.height + 16 + 30 * k
        if kind in COLOURS:
            draw.rectangle((20, y + 4, 44, y + 22), fill=COLOURS[kind])
        draw.text((60, y), line, fill=(235, 225, 205), font=text)
    out = os.path.join(ROOT, "wip", "preview", "motion-muster.png")
    page.save(out)
    print("wrote", out, page.size)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    {"map": motion_map, "things": things, "posts": posts, "sky": sky, "cloth": cloth, "clean": clean, "banners": banners, "wind": wind, "flames": flames, "assemble": assemble, "preview": render,
     "frames": render}[argv[0]](*(argv if argv[0] in ("preview", "frames") else argv[1:]))
