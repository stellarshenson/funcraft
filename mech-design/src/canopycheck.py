"""Close-up of each head with the isolated canopy faces flagged, so the
selection can be judged instead of guessed at."""
import bpy, sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mechrig as R
from mathutils import Euler, Vector
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for name in ("madcat","atlas","battlemaster"):
    R.clear_scene()
    cfg=R.CHASSIS[name]
    p=R.build(name,cfg)
    hull=bpy.data.materials.new("hull"); hull.use_nodes=True
    b=hull.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value=(0.30,0.32,0.36,1)
    b.inputs["Roughness"].default_value=0.5; b.inputs["Metallic"].default_value=0.3
    for o in bpy.data.objects:
        if o.type=="MESH" and not o.data.materials: o.data.materials.append(hull)
    R.redden_canopy(p,name)
    # recolour the canopy slot to vivid green so the selection is unmistakable
    t=p["torso"]
    if len(t.data.materials)>1:
        m=t.data.materials[-1]; nt=m.node_tree
        for n in nt.nodes:
            if n.type=="EMISSION":
                n.inputs[0].default_value=(0.05,1.0,0.15,1); n.inputs[1].default_value=3.0
    H=p["H"]
    if "canopy_box" in cfg:
        zc=(cfg["canopy_box"][4]+cfg["canopy_box"][5])/2
    else:
        zlo,zhi=(h*H for h in cfg["canopy_z"]); zc=(zlo+zhi)/2
    cd=bpy.data.cameras.new("c"); cd.lens=110
    cam=bpy.data.objects.new("cam",cd); bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera=cam
    cam.location=(0, H*1.5, zc+H*0.05)
    d=Vector((0,0,zc))-cam.location
    cam.rotation_euler=d.to_track_quat("-Z","Y").to_euler()
    for loc,e in (((-8,16,zc+7),4000),((9,13,zc+3),1800)):
        l=bpy.data.lights.new("l","AREA"); l.energy=e; l.size=9
        o=bpy.data.objects.new("l",l); o.location=loc
        dd=Vector((0,0,zc))-o.location; o.rotation_euler=dd.to_track_quat("-Z","Y").to_euler()
        bpy.context.collection.objects.link(o)
    w=bpy.data.worlds.new("w"); bpy.context.scene.world=w; w.use_nodes=True
    w.node_tree.nodes["Background"].inputs[0].default_value=(0.05,0.06,0.08,1)
    s=bpy.context.scene
    s.render.engine="CYCLES"; s.cycles.device="GPU"; s.cycles.samples=32
    pr=bpy.context.preferences.addons["cycles"].preferences
    pr.compute_device_type="CUDA"; pr.get_devices()
    for dv in pr.devices: dv.use=(dv.type=="CUDA")
    s.render.resolution_x=520; s.render.resolution_y=520
    s.view_settings.view_transform="AgX"
    s.render.filepath=os.path.join(ROOT, "wip", "preview",f"canopy-{name}.png")
    bpy.ops.render.render(write_still=True)
print("CANOPY_CHECK_DONE")
