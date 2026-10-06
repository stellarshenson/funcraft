"""Walk strip: one chassis at several points of its gait cycle, side by side,
seen from its left side, in the paint of banner 03. Blender 4.5.

The points are those of PHASES: the left leg, the one nearest to the camera,
stands at the first, swings through the next ones and stands again at the
last. A line marks the ground.

    blender -b -P src/procession/gaitstrip.py -- <chassis>      # wip/preview/procession/gait-<chassis>.png
"""
import bpy, os, sys, math
from mathutils import Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import frame as F

PHASES = (0.5, 0.6, 0.65, 0.7, 0.75, 0.8, 0.85, 0.9, 0.95, 0.0)   # the left leg swings from 0.6 to 1.0
SPACE = 10.0                       # metres between two mechs of the strip
TALL = 15.0                        # metres of height in the picture

if __name__ == "__main__":
    name = sys.argv[sys.argv.index("--") + 1]
    F.mechrig.clear_scene()
    first = F.load_mech(name)
    for k, phase in enumerate(PHASES):
        rig = first[1] if k == 0 else F.twin(*first)
        rig.location = (0.0, -SPACE * k, 0.0)          # the camera's right is -Y: the phase grows to the right
        F.pose(rig, name, phase)
    wide = SPACE * len(PHASES)
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -SPACE * (len(PHASES) - 1) / 2, 0))
    bpy.context.object.scale = (40, wide + 20, 1)
    floor = bpy.data.materials.new("floor")
    floor.diffuse_color = (0.25, 0.25, 0.27, 1)
    bpy.context.object.data.materials.append(floor)
    cd = bpy.data.cameras.new("c")
    cd.type, cd.ortho_scale = "ORTHO", wide
    cam = bpy.data.objects.new("cam", cd)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.location = (-80.0, -SPACE * (len(PHASES) - 1) / 2, TALL / 2 - 0.5)
    cam.rotation_euler = Euler((math.radians(90), 0, math.radians(-90)), "XYZ")
    for lamp, energy, rot in (("key", 4.0, (55, 0, -60)), ("fill", 1.5, (70, 0, -150))):
        o = bpy.data.objects.new(lamp, bpy.data.lights.new(lamp, "SUN"))
        o.data.energy, o.rotation_euler = energy, Euler([math.radians(a) for a in rot], "XYZ")
        bpy.context.collection.objects.link(o)
    w = bpy.data.worlds.new("w")
    bpy.context.scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.58, 0.62, 1)
    F.render_setup(samples=32)
    s = bpy.context.scene
    s.render.resolution_x, s.render.resolution_y = 2400, round(2400 * TALL / wide)
    bpy.context.view_layer.update()
    F.render(os.path.join(F.PREVIEW, f"gait-{name}.png"))
    print("GAITSTRIP", name)
