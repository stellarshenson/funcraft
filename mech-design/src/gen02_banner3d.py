#!/usr/bin/env python3
"""Three BattleMechs walking, built as 3D geometry and rendered with mech3d."""

import math
import numpy as np
from PIL import Image
import mech3d as M

# ------------------------------------------------------------------ look ----
STEEL      = np.array([0.205, 0.235, 0.292])
STEEL_DARK = np.array([0.120, 0.140, 0.180])
STEEL_WARM = np.array([0.245, 0.238, 0.230])
GLOW       = np.array([1.55, 1.05, 0.42])
GLOW_COOL  = np.array([0.55, 1.25, 1.50])

LIGHT = {"dir": M.normalise(np.array([-0.55, 0.62, 0.56])),
         "col": np.array([0.86, 0.79, 0.68]),
         "rim": np.array([0.46, 0.33, 0.16])}
FILL  = {"dir": M.normalise(np.array([0.35, 0.90, -0.25])),
         "col": np.array([0.17, 0.24, 0.40])}
AMBIENT = np.array([0.055, 0.068, 0.095])
FOG = {"start": 62.0, "end": 330.0, "col": np.array([0.062, 0.078, 0.112])}


# ----------------------------------------------------------------- rigs -----
class Chassis:
    def __init__(self, kind, pos, yaw, sc, phase_off):
        self.kind, self.pos, self.yaw, self.sc, self.off = kind, pos, yaw, sc, phase_off
        if kind == "timberwolf":
            self.hip_h, self.l1, self.l2 = 5.6, 2.9, 3.0
            self.stride, self.lift, self.bend = 4.6, 1.5, +1     # reverse knee
            self.leg_dz, self.leg_w = 1.45, 1.15
        elif kind == "battlemaster":
            self.hip_h, self.l1, self.l2 = 6.0, 3.1, 3.1
            self.stride, self.lift, self.bend = 4.2, 1.3, -1
            self.leg_dz, self.leg_w = 1.40, 1.15
        else:
            self.hip_h, self.l1, self.l2 = 5.4, 2.8, 2.9
            self.stride, self.lift, self.bend = 3.8, 1.1, -1
            self.leg_dz, self.leg_w = 1.75, 1.50

    def root(self, phase):
        p = (phase + self.off) % 1.0
        bob = -0.16 * math.cos(4 * math.pi * p)
        roll = 0.035 * math.sin(2 * math.pi * p)
        m = (M.translate(*self.pos) @ M.rot_y(self.yaw)
             @ M.translate(0, bob, 0) @ M.rot_z(roll) @ M.scale(self.sc))
        return p, m

    # -- legs ---------------------------------------------------------------
    def legs(self, s, R, p):
        for side, off in ((+1, 0.0), (-1, 0.5)):
            fx, fy = M.foot_track(p + off, self.stride, self.lift)
            hip2 = (0.0, self.hip_h)
            foot2 = (fx, fy)
            kx, ky = M.knee_point(hip2, foot2, self.l1, self.l2, self.bend)
            dz = self.leg_dz * side
            hip = np.array([0.0, self.hip_h, dz])
            knee = np.array([kx, ky, dz])
            foot = np.array([fx, fy, dz])

            w = self.leg_w
            s.segment(hip, knee, w * 1.05, w * 1.15, STEEL, 0)          # thigh
            s.segment(knee, foot + np.array([0, 0.30, 0]), w * 0.82, w * 0.95,
                      STEEL_DARK, 0)                                     # shin
            # knee actuator block
            s.box(M.translate(*knee) @ M.scale(w * 1.15, w * 0.9, w * 1.25), STEEL_WARM)
            # hydraulic ram from the hip down to mid-shin
            mid = knee + (foot - knee) * 0.45
            back = np.array([-0.55 * self.bend, 0.0, 0.0])
            s.segment(hip + back * 0.7, mid + back * 0.5, w * 0.30, w * 0.30, STEEL_WARM)
            # hip ball joint
            s.box(M.translate(*hip) @ M.scale(w * 1.3, w * 1.1, w * 1.35), STEEL_DARK)
            # foot
            s.box(M.translate(fx + 0.35, fy + 0.28, dz)
                  @ M.scale(w * 2.3, 0.55, w * 1.5), STEEL_DARK)
            s.box(M.translate(fx + 1.25, fy + 0.22, dz)
                  @ M.scale(w * 0.9, 0.42, w * 1.35), STEEL_DARK)

    # -- arms ---------------------------------------------------------------
    def arms(self, s, p):
        sw = math.sin(2 * math.pi * p)
        if self.kind == "timberwolf":
            for side, ph in ((+1, 0.0), (-1, 0.5)):
                a = sw * (1 if ph == 0 else -1)
                z = 2.55 * side
                s.box(M.translate(1.0 + a * 0.25, 6.9, z) @ M.rot_z(-0.10)
                      @ M.scale(3.4, 1.5, 1.6), STEEL)
                s.box(M.translate(2.9 + a * 0.25, 6.85, z)
                      @ M.scale(1.5, 0.95, 1.05), STEEL_DARK)
                s.box(M.translate(3.75 + a * 0.25, 6.85, z)
                      @ M.scale(0.5, 0.42, 0.42), GLOW * 0.45, emissive=True)
        elif self.kind == "battlemaster":
            for side, ph in ((+1, 0.0), (-1, 0.5)):
                a = sw * (1 if ph == 0 else -1)
                z = 2.75 * side
                sh = np.array([0.0, 8.5, z])
                el = np.array([a * 0.8, 6.3, z * 1.04])
                s.segment(sh, el, 1.35, 1.45, STEEL)
                if side > 0:                                  # PPC
                    s.box(M.translate(el[0] + 1.9, el[1] - 0.35, z)
                          @ M.rot_z(-0.06) @ M.scale(4.2, 1.15, 1.2), STEEL_DARK)
                    s.box(M.translate(el[0] + 4.1, el[1] - 0.45, z)
                          @ M.scale(0.6, 1.0, 1.05), GLOW_COOL * 0.55, emissive=True)
                else:
                    s.segment(el, el + np.array([0.5, -2.0, 0]), 1.15, 1.0, STEEL_DARK)
        else:                                                  # atlas
            for side, ph in ((+1, 0.0), (-1, 0.5)):
                a = sw * (1 if ph == 0 else -1)
                z = 3.35 * side
                sh = np.array([0.0, 8.2, z])
                el = np.array([a * 0.7, 6.0, z * 1.03])
                s.segment(sh, el, 1.85, 1.95, STEEL)
                if side > 0:                                   # AC/20
                    s.box(M.translate(el[0] + 2.0, el[1] - 0.4, z) @ M.rot_z(-0.05)
                          @ M.scale(4.4, 1.9, 1.95), STEEL_DARK)
                    s.box(M.translate(el[0] + 4.4, el[1] - 0.5, z)
                          @ M.scale(0.7, 1.35, 1.4), STEEL_WARM)
                else:
                    s.segment(el, el + np.array([0.4, -2.2, 0]), 1.6, 1.45, STEEL_DARK)

    # -- torsos -------------------------------------------------------------
    def body(self, s, p):
        k = self.kind
        if k == "timberwolf":
            s.box(M.translate(0, 5.85, 0) @ M.scale(3.2, 1.6, 3.8), STEEL_DARK)
            s.box(M.translate(0.20, 7.35, 0) @ M.rot_z(-0.20)
                  @ M.scale(4.6, 3.0, 4.2), STEEL, taper=(0.70, 0.82))
            s.box(M.translate(1.70, 6.55, 0) @ M.rot_z(-0.30)
                  @ M.scale(2.6, 1.5, 3.6), STEEL_WARM)          # chest glacis
            for side in (+1, -1):                                # LRM racks
                z = 3.05 * side
                s.box(M.translate(-1.55, 9.15, z) @ M.rot_z(-0.13)
                      @ M.scale(4.0, 2.6, 2.5), STEEL_DARK)
                for r in range(3):
                    for c in range(3):
                        s.box(M.translate(0.42, 8.55 + r * 0.72, z - 0.78 + c * 0.78)
                              @ M.rot_z(-0.13) @ M.scale(0.30, 0.46, 0.46),
                              np.array([0.055, 0.065, 0.085]))
                s.box(M.translate(-1.2, 10.5, z) @ M.scale(0.9, 0.55, 0.55), STEEL_WARM)
                s.box(M.translate(-0.8, 10.5, z) @ M.scale(0.28, 0.3, 0.3),
                      GLOW * 0.5, emissive=True)
            # low forward cockpit between the racks
            s.box(M.translate(2.55, 8.05, 0) @ M.rot_z(-0.18)
                  @ M.scale(2.3, 1.5, 2.4), STEEL_WARM, taper=(0.8, 0.85))
            s.box(M.translate(3.62, 7.90, 0) @ M.rot_z(-0.18)
                  @ M.scale(0.26, 0.58, 1.7), GLOW, emissive=True)
        elif k == "battlemaster":
            s.box(M.translate(0, 6.3, 0) @ M.scale(3.2, 1.6, 3.8), STEEL_DARK)
            s.box(M.translate(0, 8.4, 0) @ M.scale(4.2, 3.6, 4.6), STEEL)
            for i in range(4):                                  # heat sinks
                s.box(M.translate(2.12, 7.4 + i * 0.75, 0) @ M.scale(0.18, 0.34, 3.4),
                      np.array([0.08, 0.09, 0.11]))
            for side in (+1, -1):
                z = 3.05 * side
                s.box(M.translate(-0.1, 9.75, z) @ M.rot_z(0.06)
                      @ M.scale(3.6, 2.3, 2.2), STEEL_DARK, taper=(0.82, 0.88))
                s.segment(np.array([-1.1, 9.0, z * 0.75]),
                          np.array([-0.3, 10.7, z * 0.95]), 0.34, 0.34, STEEL_WARM)
            s.box(M.translate(0.25, 11.35, 0) @ M.scale(2.1, 1.8, 2.4), STEEL_WARM)
            s.box(M.translate(0.25, 12.35, 0) @ M.scale(1.5, 0.35, 1.9), STEEL_DARK)
            s.box(M.translate(1.38, 11.42, 0) @ M.scale(0.22, 0.52, 1.7),
                  GLOW, emissive=True)
        else:                                                   # atlas
            s.box(M.translate(0, 5.8, 0) @ M.scale(3.6, 1.7, 4.4), STEEL_DARK)
            s.box(M.translate(-0.15, 8.1, 0) @ M.rot_z(0.05)
                  @ M.scale(4.8, 4.0, 5.4), STEEL)
            for side in (+1, -1):                               # slab pauldrons
                s.box(M.translate(-0.3, 9.5, 3.9 * side) @ M.rot_z(0.04)
                      @ M.scale(4.4, 3.2, 2.9), STEEL_DARK)
            s.box(M.translate(-0.9, 11.9, 3.5) @ M.scale(3.2, 1.9, 2.6), STEEL_DARK)
            for r in range(2):
                for c in range(2):
                    s.box(M.translate(0.62, 11.45 + r * 0.78, 2.9 + c * 0.95)
                          @ M.scale(0.22, 0.46, 0.5), np.array([0.07, 0.08, 0.10]))
            # chest glacis
            s.box(M.translate(2.05, 8.6, 0) @ M.rot_z(-0.22)
                  @ M.scale(1.6, 3.0, 4.4), STEEL_WARM)
            # death's-head cockpit, standing clear of the pauldrons
            s.box(M.translate(0.55, 12.55, 0) @ M.scale(2.5, 2.3, 2.7),
                  STEEL_WARM, taper=(0.86, 0.9))
            s.box(M.translate(1.05, 13.72, 0) @ M.scale(2.0, 0.45, 2.3), STEEL_DARK)
            s.box(M.translate(1.30, 11.50, 0) @ M.scale(1.5, 1.05, 2.1), STEEL_WARM)
            for z in (-0.68, 0.68):                             # eye sockets
                s.box(M.translate(1.72, 12.85, z) @ M.scale(0.34, 0.60, 0.84),
                      GLOW, emissive=True)
            for i in range(4):                                  # teeth
                s.box(M.translate(1.98, 11.48, -0.95 + i * 0.63)
                      @ M.scale(0.24, 0.84, 0.30), np.array([0.055, 0.065, 0.085]))

    def build(self, scene, phase):
        p, R = self.root(phase)
        local = M.Scene()
        self.legs(local, R, p)
        self.arms(local, p)
        self.body(local, p)
        v, c, e = local.arrays()
        if len(v):
            flat = v.reshape(-1, 3)
            hom = np.concatenate([flat, np.ones((len(flat), 1))], 1) @ R.T
            v = hom[:, :3].reshape(-1, 3, 3)
            scene.v.extend(list(v))
            scene.c.extend(list(c))
            scene.emissive.extend(list(e))


# ------------------------------------------------------------------ city ----
def skyline(scene):
    rng = np.random.default_rng(12)
    for i in range(70):
        x = rng.uniform(-420, 420)
        z = rng.uniform(-360, -140)
        w = rng.uniform(10, 30)
        h = rng.uniform(14, 78)
        d = rng.uniform(10, 26)
        shade = np.array([0.055, 0.068, 0.092]) * rng.uniform(0.7, 1.25)
        scene.box(M.translate(x, h / 2, z) @ M.scale(w, h, d), shade)
    for i in range(12):                       # pylons well behind the walkway
        x = -200 + i * 38
        scene.box(M.translate(x, 8, -58) @ M.scale(0.55, 16, 0.55),
                  np.array([0.048, 0.058, 0.078]))
        scene.box(M.translate(x, 15.2, -58) @ M.scale(2.6, 0.45, 0.5),
                  np.array([0.048, 0.058, 0.078]))


# ------------------------------------------------------------------ main ----
def main(out):
    aspect = W_ = 1140 / 360
    cam_pos = np.array([1.5, 12.2, 62.0])
    view = M.look_at(cam_pos, np.array([1.0, 8.2, 0.0]))
    proj = M.perspective(20.0, aspect, 0.4, 600.0)

    mechs = [
        Chassis("battlemaster", (-20.0, 0, -6.0), math.radians(-14), 1.02, 0.34),
        Chassis("timberwolf",   (  0.5, 0, 1.0),  math.radians(-20), 1.06, 0.00),
        Chassis("atlas",        ( 19.0, 0, -2.0), math.radians(-16), 1.16, 0.67),
    ]

    STRIDE_WORLD = 9.0            # ground travel per gait cycle; 9 == one seam period

    frames = []
    for i in range(M.FRAMES):
        phase = i / M.FRAMES
        scene = M.Scene()
        skyline(scene)
        for m in mechs:
            m.build(scene, phase)

        shift = phase * STRIDE_WORLD

        def sky_fn(_s=shift):
            c, d = M.make_background(cam_pos, view, proj, M.RW, M.RH, _s, FOG)
            return c, d

        colour, _ = M.render(scene, view, proj, cam_pos, LIGHT, FILL, AMBIENT,
                             FOG, sky_fn, M.RW, M.RH)
        img = np.clip(colour, 0, 1)
        img = img ** (1 / 2.2)                         # to display gamma
        frame = Image.fromarray((img * 255).astype(np.uint8)).resize(
            (1140, 360), Image.LANCZOS)
        frames.append(frame)
        print(f"  frame {i + 1}/{M.FRAMES}", flush=True)

    pal = frames[0].quantize(colors=200, method=Image.MEDIANCUT)
    out_frames = [f.quantize(palette=pal, dither=Image.FLOYDSTEINBERG) for f in frames]
    out_frames[0].save(out, save_all=True, append_images=out_frames[1:],
                       duration=50, loop=0, optimize=True, disposal=1)
    print("wrote", out)


if __name__ == "__main__":
    import sys
    main(sys.argv[1] if len(sys.argv) > 1 else "mech3d.gif")
