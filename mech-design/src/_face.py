import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
from mathutils import Euler
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for tag, yaw in (("yawPI", math.pi), ("yaw0", 0.0)):
    R.clear_scene()
    cfg = dict(R.CHASSIS["madcat"]); cfg["yaw"] = yaw
    p = R.build("madcat", cfg); R.pose(p, 0.25)
    m=bpy.data.materials.new("m"); m.use_nodes=True
    b=m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(0.16,0.175,0.20,1)
    b.inputs["Roughness"].default_value=0.38; b.inputs["Metallic"].default_value=0.8
    for o in bpy.data.objects:
        if o.type=="MESH": o.data.materials.clear(); o.data.materials.append(m)
    bpy.ops.mesh.primitive_plane_add(size=400)
    g=bpy.data.materials.new("g"); g.use_nodes=True
    g.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value=(0.03,0.034,0.042,1)
    bpy.context.object.data.materials.append(g)
    # the banner camera: sits at +Y looking back along -Y
    cd=bpy.data.cameras.new("c"); cd.lens=42
    cam=bpy.data.objects.new("cam",cd); bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera=cam
    cam.location=(0,34,7.0); cam.rotation_euler=Euler((math.radians(88.2),0,math.radians(180)),"XYZ")
    for loc,e,rot in (((-30,26,34),300000,(52,0,-140)),((30,20,20),120000,(64,0,130))):
        l=bpy.data.lights.new("l","AREA"); l.energy=e; l.size=30
        o=bpy.data.objects.new("l",l); o.location=loc
        o.rotation_euler=Euler(tuple(math.radians(a) for a in rot),"XYZ")
        bpy.context.collection.objects.link(o)
    w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.04,0.05,0.07,1)
    s=bpy.context.scene
    s.render.engine="CYCLES"; s.cycles.device="GPU"; s.cycles.samples=40
    pr=bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type="CUDA"; pr.get_devices()
    for d in pr.devices: d.use=(d.type=="CUDA")
    s.render.resolution_x=560; s.render.resolution_y=620
    s.view_settings.view_transform="AgX"
    s.render.filepath=os.path.join(ROOT, "wip", "preview",f"face-{tag}.png")
    bpy.ops.render.render(write_still=True)
print("FACE_DONE")
