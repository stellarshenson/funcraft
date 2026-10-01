import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
from mathutils import Euler

R.clear_scene()
name = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "madcat"
parts = R.build(name, R.CHASSIS[name])
R.pose(parts, 0.22)

COLS = {"torso": (0.55,0.57,0.62), "pelvis": (0.90,0.75,0.20),
        "outer": (0.75,0.25,0.80), "leg": (0.88,0.38,0.16), "foot": (0.28,0.75,0.35)}
def mat(n,c):
    m=bpy.data.materials.new(n); m.use_nodes=True
    b=m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(*c,1); b.inputs["Roughness"].default_value=0.5
    return m
for o in bpy.data.objects:
    if o.type!="MESH": continue
    k=next((k for k in COLS if o.name.endswith(k)),"torso")
    o.data.materials.clear(); o.data.materials.append(mat(o.name,COLS[k]))

H=parts["H"]
bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,0))
gm=mat("ground",(0.06,0.065,0.08)); bpy.context.object.data.materials.append(gm)

cd=bpy.data.cameras.new("c"); cam=bpy.data.objects.new("cam",cd)
bpy.context.collection.objects.link(cam); bpy.context.scene.camera=cam
cd.lens=85
cam.location=(H*3.1, 0, H*0.50)
cam.rotation_euler=Euler((math.radians(88),0,math.radians(90)),"XYZ")

for loc,e,rot in (((14,-18,22),9000,(50,0,35)), ((-16,10,14),3000,(60,0,-140))):
    l=bpy.data.lights.new("l","AREA"); l.energy=e; l.size=14
    o=bpy.data.objects.new("l",l); o.location=loc
    o.rotation_euler=Euler(tuple(math.radians(a) for a in rot),"XYZ")
    bpy.context.collection.objects.link(o)
w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True
w.node_tree.nodes["Background"].inputs[0].default_value=(0.025,0.03,0.045,1)

s=bpy.context.scene
s.render.engine="CYCLES"; s.cycles.device="GPU"; s.cycles.samples=48
pr=bpy.context.preferences.addons["cycles"].preferences
pr.compute_device_type="CUDA"; pr.get_devices()
for d in pr.devices: d.use = (d.type=="CUDA")
s.render.resolution_x, s.render.resolution_y = 900, 900
s.render.filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "wip", "preview",f"cut-{name}.png")
bpy.ops.render.render(write_still=True)
print("RENDERED", s.render.filepath)
