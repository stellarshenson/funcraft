"""Orthographic side view of each chassis with a measured grid, so cut planes
can be read off the geometry instead of guessed."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
from mathutils import Euler

name = sys.argv[sys.argv.index("--")+1]
R.clear_scene()
cfg = R.CHASSIS[name]
src = R.normalise(R.import_stl(os.path.join(R.MODELS, cfg["file"])), cfg["height"], cfg["yaw"])
H = cfg["height"]

m = bpy.data.materials.new("m"); m.use_nodes=True
b = m.node_tree.nodes["Principled BSDF"]
b.inputs["Base Color"].default_value=(0.62,0.64,0.68,1); b.inputs["Roughness"].default_value=0.6
src.data.materials.append(m)

SCALE = H*1.25
cd = bpy.data.cameras.new("c"); cd.type="ORTHO"; cd.ortho_scale=SCALE
cam = bpy.data.objects.new("cam", cd); bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (H*6, 0, H*0.5); cam.rotation_euler = Euler((math.radians(90),0,math.radians(90)),"XYZ")

for loc,e,rot in (((18,-14,20),12000,(45,0,40)),((-14,16,12),5000,(60,0,-150))):
    l=bpy.data.lights.new("l","AREA"); l.energy=e; l.size=18
    o=bpy.data.objects.new("l",l); o.location=loc
    o.rotation_euler=Euler(tuple(math.radians(a) for a in rot),"XYZ")
    bpy.context.collection.objects.link(o)
w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.04,0.045,0.06,1)

s=bpy.context.scene
s.render.engine="CYCLES"; s.cycles.device="GPU"; s.cycles.samples=32
pr=bpy.context.preferences.addons["cycles"].preferences
pr.compute_device_type="CUDA"; pr.get_devices()
for d in pr.devices: d.use=(d.type=="CUDA")
s.render.resolution_x=s.render.resolution_y=1000
out=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wip", "preview",f"measure-{name}.png")
s.render.filepath=out
bpy.ops.render.render(write_still=True)
print("ORTHO", out, "scale", SCALE, "camz", H*0.5)
