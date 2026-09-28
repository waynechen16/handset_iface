"""Stage 1: create board, load footprints, assign nets, place parts, draw outline."""
import pcbnew, xml.etree.ElementTree as ET, sys, json

FPDIR = "/usr/share/kicad/footprints"
NETXML = "/home/claude/out/net.xml"
OUT = "/home/claude/pcb/handset_iface.kicad_pcb"

W, H = 80.0, 60.0          # board size (mm)
OX, OY = 100.0, 100.0      # board origin on the KiCad canvas

def mm(x): return pcbnew.FromMM(x)
def pt(x, y): return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))

# ------------------------------------------------------------------ placement
# ref: (x, y, rotation_deg)   board-local mm, (0,0) = top-left corner
PLACE = {
    # ---- bottom edge, left -> right: J1, J3, RV1, J4 (all facing +y, out of the board)
    "J1": (15.0, H - 3.3, 0),        # 3.5 mm jack, body front flush with edge
    "J3": (30.0, H - 3.3, 0),        # 3.5 mm jack
    "RV1": (40.0, H - 5.0, 90),      # Alps RK097, body front flush, shaft out of the bottom edge
    "J4": (60.0, H - 15.16, 270),    # USB-B, front flush
    # ---- top edge (opposite side): J2 RJ9 facing -y
    "J2": (30.0, 14.25, 180),
    # ---- PATH B (left): J2 mic -> U2 -> J3
    "U2": (18.0, 30.0, 180),
    "R5": (26.0, 22.0, 90),
    "C8": (24.0, 26.0, 0),
    "R7": (24.0, 29.5, 0),
    "C9": (24.0, 33.5, 0),
    "R8": (29.0, 32.0, 90),
    "RV2": (29.0, 39.0, 0),
    "R9": (22.0, 37.0, 90),
    "C10": (23.0, 41.5, 90),
    "C11": (34.2, 36.0, 90),
    "R10": (34.2, 42.0, 90),
    "R11": (11.0, 26.0, 90),
    "R12": (11.0, 31.0, 90),
    "C12": (7.0, 29.0, 90),
    "C13": (14.0, 35.0, 0),
    # ---- J1 input network (above J1)
    "R2": (10.0, 45.0, 90),
    "R1": (20.0, 45.0, 90),
    "C1": (15.0, 40.5, 0),
    # ---- PATH A (centre-right): RV1 wiper -> U1 -> C5/R3 -> J2 receiver
    "U1": (46.0, 40.0, 0),
    "C2": (52.5, 41.2, 0),
    "C4": (52.5, 37.0, 0),
    "C5": (50.0, 30.0, 180),
    "R3": (40.0, 22.0, 0),
    "R4": (57.0, 30.0, 270),
    "C6": (57.0, 34.5, 270),
    # ---- J2 pinout-select solder jumpers (top edge, right of J2)
    "JP4": (38.0, 12.0, 0),
    "JP3": (44.5, 12.0, 0),
    "JP2": (51.0, 12.0, 0),
    "JP1": (57.5, 12.0, 0),
    "JP5": (64.0, 12.0, 0),
    "JP6": (70.5, 12.0, 0),
    # ---- POWER (right)
    "FB1": (60.0, 40.0, 90),
    "C14": (70.0, 36.0, 0),
    "R6": (66.0, 28.0, 0),
    "C7": (70.0, 21.0, 0),
}
HOLES = [(4.0, 4.0), (W - 4.0, 4.0), (4.0, H - 4.0), (W - 4.0, H - 4.0)]

# ------------------------------------------------------------------ netlist
root = ET.parse(NETXML).getroot()
comps = {c.get("ref"): (c.findtext("value"), c.findtext("footprint")) for c in root.iter("comp")}
tstamp = {c.get("ref"): c.findtext("tstamps") for c in root.iter("comp")}
padnet = {}
netnames = []
for n in root.iter("net"):
    name = n.get("name")
    if name.startswith("unconnected"):
        continue
    netnames.append(name)
    for node in n.findall("node"):
        padnet[(node.get("ref"), node.get("pin"))] = name

brd = pcbnew.BOARD()
brd.SetCopperLayerCount(2)
nets = {}
for name in netnames:
    ni = pcbnew.NETINFO_ITEM(brd, name)
    brd.Add(ni)
    nets[name] = ni

missing = set(comps) - set(PLACE)
assert not missing, f"not placed: {missing}"

def set_text_small(fp):
    r = fp.Reference()
    r.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    r.SetTextThickness(mm(0.12))
    fp.Value().SetVisible(False)

for ref, (val, fpid) in comps.items():
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(f"{FPDIR}/{lib}.pretty", name)
    fp.SetReference(ref)
    fp.SetValue(val)
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    fp.SetPath(pcbnew.KIID_PATH("/" + tstamp[ref]))   # link to schematic symbol
    brd.Add(fp)
    # some library footprints carry their own Edge.Cuts hints -> move them to a user layer
    for g in list(fp.GraphicalItems()):
        if g.GetLayer() == pcbnew.Edge_Cuts:
            g.SetLayer(pcbnew.Cmts_User)
    x, y, rot = PLACE[ref]
    fp.SetPosition(pt(x, y))
    fp.SetOrientationDegrees(rot)
    set_text_small(fp)
    for p in fp.Pads():
        k = (ref, p.GetNumber())
        if k in padnet:
            p.SetNet(nets[padnet[k]])
        elif ref == "J4" and p.GetNumber() == "5":
            p.SetNet(nets["GND"])          # USB shield

for i, (x, y) in enumerate(HOLES, 1):
    fp = pcbnew.FootprintLoad(f"{FPDIR}/MountingHole.pretty", "MountingHole_3.2mm_M3")
    fp.SetReference(f"H{i}")
    fp.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3"))
    brd.Add(fp)
    fp.SetPosition(pt(x, y))
    set_text_small(fp)
    fp.Reference().SetVisible(False)

# ------------------------------------------------------------------ outline (rounded rect, r = 2 mm)
R = 2.0
def seg(a, b):
    s = pcbnew.PCB_SHAPE(brd); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(pt(*a)); s.SetEnd(pt(*b)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); brd.Add(s)
def arc(c, start, angle):
    s = pcbnew.PCB_SHAPE(brd); s.SetShape(pcbnew.SHAPE_T_ARC)
    s.SetCenter(pt(*c)); s.SetStart(pt(*start)); s.SetArcAngleAndEnd(pcbnew.EDA_ANGLE(angle, pcbnew.DEGREES_T), True)
    s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(mm(0.1)); brd.Add(s)
seg((R, 0), (W - R, 0)); seg((W, R), (W, H - R)); seg((W - R, H), (R, H)); seg((0, H - R), (0, R))
arc((W - R, R), (W - R, 0), 90); arc((W - R, H - R), (W, H - R), 90)
arc((R, H - R), (R, H), 90); arc((R, R), (0, R), 90)

# ------------------------------------------------------------------ silkscreen labels
def silk(txt, x, y, size=1.0, rot=0, bold=False):
    t = pcbnew.PCB_TEXT(brd); t.SetText(txt); t.SetPosition(pt(x, y)); t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mm(size), mm(size))); t.SetTextThickness(mm(size * 0.15))
    t.SetTextAngleDegrees(rot); t.SetBold(bold); brd.Add(t)
for r in ("J1", "J2", "J3", "J4", "RV1", "RV2"):
    brd.FindFootprintByReference(r).Reference().SetVisible(False)
silk("J1 LINE OUT", 15.0, 47.2, 0.9)
silk("J3 LINE IN", 30.0, 47.2, 0.9)
silk("RV1 VOL", 42.5, 51.5, 0.9)
silk("J4 USB 5V", 66.0, 42.3, 0.9)
silk("J2 HANDSET", 29.0, 19.5, 0.9)
silk("RV2 GAIN", 29.0, 43.6, 0.9)
silk("RJ9 HANDSET <-> PC AUDIO I/F  Rev B", 57.0, 4.6, 0.9)
silk("2026-09", 57.0, 6.3, 0.8)
silk("PAIR  JP1-JP4", 47.75, 14.7, 0.8)
silk("MIC POL  JP5-JP6", 67.25, 14.7, 0.8)
silk("1-2 = DEFAULT", 57.0, 16.5, 0.8)

pcbnew.SaveBoard(OUT, brd)
print("saved", OUT, "parts:", len(comps), "nets:", len(nets))
