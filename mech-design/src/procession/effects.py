"""What moves in the air of the procession scene: embers over the deck and
smoke over the chimneys of the backdrop. Blender 4.5.

Embers. Glowing specks that leave the deck, rise and go out. The air stands
still over the moving ground, so an ember moves away with the ground while
it rises. Each lives for one loop and is born again where it was born: the
loop closes with every ember in another place of its own, and nothing
repeats along the way.

Chimney smoke. The plumes of src/procession/chimneys.py, one over each
chimney of the plate. A plume leaves its source as a narrow jet and rolls
only higher up, so it stands a little behind its chimney and SINK of its
height below the mouth: the chimney hides the jet, and the rolling smoke
begins at the mouth. Thin smoke at a plume's edge shows
SMOKE_EDGE and thick smoke SMOKE_CORE, as sky light on rolling smoke does. One OpenVDB file per loop frame; the scene's
frame number picks the file. The smoke emits and absorbs and does not
scatter: a scattering volume needs light sampling, and the denoiser turns
its noise into flicker.
"""
import bpy, os, math
import numpy as np
import frame as F

EMBERS = 160
EMBER_FIELD = ((-60.0, 60.0), (-140.0, 56.0))    # x and y between which they are born
EMBER_COLOUR, EMBER_LIGHT = (1.0, 0.35, 0.05), 14.0
PLUMES = os.path.join(F.WIP, "chimneys")
# per plate, each chimney: plate pixel of its mouth, pixel on its body (for the depth), plate pixels the plume
# stands tall over the mouth, which plume, and what share of a loop later it is read (two chimneys with one plume differ so)
CHIMNEYS = {"terra_forgeto51c": [((1320, 100), (1320, 130), 210, 0, 0.0), ((1450, 103), (1450, 135), 210, 1, 0.0),
                                 ((1655, 90), (1655, 125), 210, 2, 0.0), ((2000, 95), (2000, 130), 210, 1, 0.5),
                                 ((2305, 88), (2330, 200), 190, 0, 0.5), ((1840, 225), (1840, 240), 80, 2, 0.5)]}
SMOKE_EDGE, SMOKE_CORE = (0.050, 0.047, 0.050), (0.012, 0.012, 0.014)    # the light and the dark of the smoke the plate had painted
SMOKE_THICK = 0.05                               # density from which smoke shows SMOKE_CORE
SMOKE_DARK = 1400.0                              # absorption per unit of density and metre of the simulated plume
SMOKE_BEHIND = 1.03                              # the plume stands at this multiple of the chimney's distance
SINK = 0.30                                      # share of the plume's height that stands below the mouth


def chimneys(sc, plate):
    """The smoke of the chimneys of `plate`; a plate without a list has none."""
    import openvdb as vdb
    data = {}
    for mouth, body, tall, k, late in CHIMNEYS.get(plate, []):
        if k not in data:
            d = np.load(os.path.join(PLUMES, f"{k}.npz"))
            seq = os.path.join(PLUMES, str(k))
            first = os.path.join(seq, "s_0001.vdb")
            if not os.path.exists(first) or os.path.getmtime(first) < os.path.getmtime(os.path.join(PLUMES, f"{k}.npz")):
                os.makedirs(seq, exist_ok=True)
                dens = d["density"].astype(np.float32)
                for f in range(F.FRAMES):
                    g = vdb.FloatGrid()
                    g.copyFromArray(dens[f], tolerance=2e-3)
                    g.name = "density"
                    g.transform = vdb.createLinearTransform(voxelSize=float(d["cell"]))
                    vdb.write(os.path.join(seq, f"s_{f + 1:04d}.vdb"), grids=[g])
            assert len(d["density"]) == F.FRAMES, "the smoke record has another number of frames: run src/procession/chimneys.py"
            data[k] = d["origin"], d["density"].shape[3] * float(d["cell"]), first
        origin, height, first = data[k]
        top, metres = sc.spot(*mouth, body)
        eye = np.array(sc.cam.location)
        top = eye + (top - eye) * SMOKE_BEHIND
        scale = tall * metres / (height * (1 - SINK))
        vol = bpy.data.volumes.new(f"chimney_{mouth[0]}")
        vol.filepath = first
        # the sequence starts the share `late` of a loop before the loop: Blender repeats it from its start, but not past an offset
        vol.is_sequence, vol.frame_duration, vol.frame_start, vol.sequence_mode = True, F.FRAMES, 1 - round(late * F.FRAMES), "REPEAT"
        m = bpy.data.materials.new(vol.name)
        m.use_nodes = True
        N, L = m.node_tree.nodes, m.node_tree.links
        N.remove(N["Principled BSDF"])
        dark = N.new("ShaderNodeMath")
        dark.operation = "MULTIPLY"
        dark.inputs[1].default_value = SMOKE_DARK               # Blender counts a volume's density in the object's own space: the same darkness at any size
        dens = N.new("ShaderNodeVolumeInfo").outputs["Density"]
        L.new(dens, dark.inputs[0])
        thick = N.new("ShaderNodeMapRange")
        thick.inputs["From Max"].default_value = SMOKE_THICK
        L.new(dens, thick.inputs["Value"])
        tone = N.new("ShaderNodeMix")
        tone.data_type = "RGBA"
        L.new(thick.outputs["Result"], tone.inputs["Factor"])
        tone.inputs["A"].default_value, tone.inputs["B"].default_value = (*SMOKE_EDGE, 1), (*SMOKE_CORE, 1)
        em = N.new("ShaderNodeEmission")
        L.new(tone.outputs["Result"], em.inputs["Color"])
        L.new(dark.outputs[0], em.inputs["Strength"])
        ab = N.new("ShaderNodeVolumeAbsorption")
        ab.inputs["Color"].default_value = (0, 0, 0, 1)
        L.new(dark.outputs[0], ab.inputs["Density"])
        add = N.new("ShaderNodeAddShader")
        L.new(em.outputs[0], add.inputs[0])
        L.new(ab.outputs[0], add.inputs[1])
        L.new(add.outputs[0], N["Material Output"].inputs["Volume"])
        m.cycles.emission_sampling = "NONE"
        vol.materials.append(m)
        ob = bpy.data.objects.new(vol.name, vol)
        ob.scale = (scale, scale, scale)
        ob.location = top + origin * scale - np.array([0.0, 0.0, SINK * height * scale])
        ob.visible_shadow = False
        bpy.context.collection.objects.link(ob)
        print(f"CHIMNEY at plate x {mouth[0]}: {np.linalg.norm(top - np.array(sc.cam.location)):.0f} m away, plume {scale * height:.0f} m tall", flush=True)
    if data:
        sc.movers.append(lambda i: bpy.context.scene.frame_set(i % F.FRAMES + 1))     # the smoke's file


def embers(sc):
    rng = np.random.default_rng(7)
    n = EMBERS
    base = np.stack([rng.uniform(*EMBER_FIELD[0], n), rng.uniform(*EMBER_FIELD[1], n), np.full(n, 0.1)], 1)
    born, rise, size = rng.uniform(0, 1, n), rng.uniform(4.0, 10.0, n), rng.uniform(0.025, 0.05, n)
    sway, turns, at = rng.uniform(0.3, 1.2, (n, 2)), rng.integers(1, 4, (n, 2)), rng.uniform(0, math.tau, (n, 2))
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=1.0)
    one = bpy.context.object
    shape = np.array([v.co for v in one.data.vertices])
    faces = np.array([p.vertices[:] for p in one.data.polygons])
    bpy.data.objects.remove(one)
    mesh = bpy.data.meshes.new("embers")
    mesh.from_pydata(np.zeros((n * len(shape), 3)), [], (faces[None] + (np.arange(n) * len(shape))[:, None, None]).reshape(-1, 3))
    ob = bpy.data.objects.new("embers", mesh)
    ob.visible_shadow = False
    bpy.context.collection.objects.link(ob)
    m = bpy.data.materials.new("embers")
    m.use_nodes = True
    N, L = m.node_tree.nodes, m.node_tree.links
    N.remove(N["Principled BSDF"])
    em = N.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*EMBER_COLOUR, 1)
    em.inputs["Strength"].default_value = EMBER_LIGHT
    L.new(em.outputs[0], N["Material Output"].inputs["Surface"])
    mesh.materials.append(m)

    def move(i):
        age = (i / F.FRAMES + born) % 1                # 0 as it leaves the deck, 1 as it goes out
        p = base.copy()
        p[:, :2] += sway * np.sin(math.tau * turns * age[:, None] + at) * age[:, None]
        p[:, 1] -= F.TRAVEL * age
        p[:, 2] += rise * age ** 0.8
        s = size * np.minimum(age / 0.08, 1) * (1 - age) ** 0.7
        mesh.vertices.foreach_set("co", (p[:, None] + s[:, None, None] * shape[None]).ravel())
        mesh.update()

    sc.movers.append(move)
