import pcbnew, sys, itertools
OX, OY = 100.0, 100.0
W, H = 80.0, 60.0
b = pcbnew.LoadBoard(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/pcb/handset_iface.kicad_pcb")
def mm(v): return pcbnew.ToMM(v)
boxes = {}
for fp in b.GetFootprints():
    xs = []; ys = []
    for g in fp.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            bb = g.GetBoundingBox()
            xs += [mm(bb.GetLeft()) - OX, mm(bb.GetRight()) - OX]
            ys += [mm(bb.GetTop()) - OY, mm(bb.GetBottom()) - OY]
    if xs:
        boxes[fp.GetReference()] = (min(xs), min(ys), max(xs), max(ys))
bad = 0
for (a, A), (c, C) in itertools.combinations(boxes.items(), 2):
    if A[0] < C[2] and C[0] < A[2] and A[1] < C[3] and C[1] < A[3]:
        print(f"OVERLAP {a} {c}"); bad += 1
# pads must lie inside the board with 0.5 mm margin
for fp in b.GetFootprints():
    for p in fp.Pads():
        x = mm(p.GetPosition().x) - OX; y = mm(p.GetPosition().y) - OY
        if not (0.5 < x < W - 0.5 and 0.5 < y < H - 0.5):
            print(f"PAD OUTSIDE {fp.GetReference()}.{p.GetNumber()} ({x:.2f},{y:.2f})"); bad += 1
for r in ("J1", "J2", "J3", "J4", "RV1"):
    print(r, "crtyd", tuple(round(v, 2) for v in boxes[r]))
print("issues:", bad)
