import re, sys
p = "src/scenes.py"; s = open(p).read()
head, scale, turn, torso, hd = sys.argv[1:6]
s = re.sub(r"titan=dict\(head=\([^)]*\), scale=[\d.]+, lean=4\.8, turn=[-\d.]+,", f"titan=dict(head=({head}), scale={scale}, lean=4.8, turn={turn},", s)
s = re.sub(r"torso=\([-\d.]+, [-\d.]+\), head=\([-\d.]+, [-\d.]+\),", f"torso=({torso}), head=({hd}),", s)
open(p, "w").write(s)
