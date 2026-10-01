"""Render one chassis at several gait phases, side-on, as a strip."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
from mathutils import Euler
name = sys.argv[sys.argv.index("--")+1]
PH = [0.0, 0.2, 0.4, 0.6, 0.8]
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for i,ph in enumerate(PH):
    R.clear_scene()
    parts = R.build(name, R.CHASSIS[name]); R.pose(parts, ph)
    H = parts["H"]
    m=bpy.data.materials.new("m"); m.use_nodes=True
    bd=m.node_tree.nodes["Principled BSDF"]
    bd.inputs["Base Color"].default_value=(0.42,0.45,0.50,1); bd.inputs["Roughness"].default_value=0.45
    bd.inputs["Metallic"].default_value=0.7
    for o in bpy.data.objects:
        if o.type=="MESH": o.data.materials.clear(); o.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=300, location=(0,0,0))
    g=bpy.data.materials.new("g"); g.use_nodes=True
    g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.05,0.055,0.07,1)
    bpy.context.object.data.materials.append(g)
    cd=bpy.data.cameras.new("c"); cd.type="ORTHO"; cd.ortho_scale=H*1.35
    cam=bpy.data.objects.new("cam",cd); bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera=cam
    cam.location=(H*6,0,H*0.52); cam.rotation_euler=Euler((math.radians(90),0,math.radians(90)),"XYZ")
    for loc,e,rot in (((18,-14,22),16000,(45,0,40)),((-16,14,12),6000,(60,0,-150))):
        l=bpy.data.lights.new("l","AREA"); l.energy=e; l.size=20
        o=bpy.data.objects.new("l",l); o.location=loc
        o.rotation_euler=Euler(tuple(math.radians(a) for a in rot),"XYZ")
        bpy.context.collection.objects.link(o)
    w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.03,0.035,0.05,1)
    s=bpy.context.scene
    s.render.engine="CYCLES"; s.cycles.device="GPU"; s.cycles.samples=24
    pr=bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type="CUDA"; pr.get_devices()
    for d in pr.devices: d.use=(d.type=="CUDA")
    s.render.resolution_x=460; s.render.resolution_y=560
    s.render.filepath=os.path.join(root, "wip", "preview",f"strip-{name}-{i}.png")
    bpy.ops.render.render(write_still=True)
print("STRIP_DONE")
