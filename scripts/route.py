"""Stage 2: simple 2-layer grid maze router (A*), GND via stubs, GND pours, stitching vias."""
import pcbnew, numpy as np, heapq, math, sys, random, time

SRC = "/home/claude/pcb/handset_iface.kicad_pcb"
DST = sys.argv[1] if len(sys.argv) > 1 else SRC
OX, OY = 100.0, 100.0
W, H = 80.0, 60.0
G = 0.2                       # grid pitch (mm)
NX, NY = int(round(W / G)) + 1, int(round(H / G)) + 1
CLR = 0.2                     # copper clearance
INFL = 0.6                    # centre-line keep-out from other-net copper edge (covers 0.5 mm track / 0.6 mm via + grid error)
EDGE_KEEP = 1.0
HOLE_KEEP = 0.75
VIA_D, VIA_DRILL = 0.6, 0.3
POWER = {"+5V": 0.5, "/+5V_FILT": 0.5, "Net-(J4-VBUS)": 0.5}
SIG_W = 0.3
GND_STUB_W = 0.4
VIA_COST = 18.0
BOT_FACTOR = 1.6             # discourage bottom layer (keep GND plane intact)
BEND = 0.4

def mm(v): return pcbnew.FromMM(v)
def tomm(v): return pcbnew.ToMM(v)
def gx(x): return (x) / G
def cell_xy(ix, iy): return ix * G, iy * G

board = pcbnew.LoadBoard(SRC)
netnames = [str(n) for n in board.GetNetsByName().keys() if str(n)]
NETID = {n: i for i, n in enumerate(sorted(netnames))}
GNDID = NETID["GND"]

YY, XX = np.mgrid[0:NY, 0:NX]
XX = XX * G; YY = YY * G

# ---------------------------------------------------------------- obstacle objects
class Obj:  # copper object: kind rect/circle/seg, layers, net
    pass

pads = []   # dicts
for fp in board.GetFootprints():
    for p in fp.Pads():
        c = p.GetPosition()
        cx, cy = tomm(c.x) - OX, tomm(c.y) - OY
        bb = p.GetBoundingBox()
        attr = p.GetAttribute()
        d = dict(ref=fp.GetReference(), num=p.GetNumber(), cx=cx, cy=cy,
                 x0=tomm(bb.GetLeft()) - OX, y0=tomm(bb.GetTop()) - OY,
                 x1=tomm(bb.GetRight()) - OX, y1=tomm(bb.GetBottom()) - OY,
                 circle=(p.GetShape() == pcbnew.PAD_SHAPE_CIRCLE), r=tomm(p.GetSize().x) / 2,
                 net=str(p.GetNetname()), smd=(attr == pcbnew.PAD_ATTRIB_SMD),
                 npth=(attr == pcbnew.PAD_ATTRIB_NPTH), drill=tomm(p.GetDrillSize().x), obj=p)
        pads.append(d)

def dist_rect(x0, y0, x1, y1):
    dx = np.maximum(np.maximum(x0 - XX, XX - x1), 0)
    dy = np.maximum(np.maximum(y0 - YY, YY - y1), 0)
    return np.hypot(dx, dy)

def dist_circle(cx, cy, r):
    return np.hypot(XX - cx, YY - cy) - r

def dist_seg(ax, ay, bx, by, hw):
    vx, vy = bx - ax, by - ay
    L2 = vx * vx + vy * vy
    if L2 == 0:
        return np.hypot(XX - ax, YY - ay) - hw
    t = np.clip(((XX - ax) * vx + (YY - ay) * vy) / L2, 0, 1)
    return np.hypot(XX - (ax + t * vx), YY - (ay + t * vy)) - hw

class Grid:
    def __init__(self):
        self.own = np.full((2, NY, NX), -1, np.int32)
        self.novia = np.zeros((NY, NX), bool)
        # board edge
        edge = (XX < EDGE_KEEP) | (XX > W - EDGE_KEEP) | (YY < EDGE_KEEP) | (YY > H - EDGE_KEEP)
        self.own[:, edge] = -2
        for i, p in enumerate(pads):
            if p["npth"]:
                m = dist_circle(p["cx"], p["cy"], max(p["drill"], p["r"] * 2) / 2) < HOLE_KEEP + INFL - 0.25
                self.own[:, m] = -2
                continue
            if p["circle"]:
                dd = dist_circle(p["cx"], p["cy"], p["r"])
            else:
                dd = dist_rect(p["x0"], p["y0"], p["x1"], p["y1"])
            layers = [0] if p["smd"] else [0, 1]
            nid = NETID[p["net"]] if p["net"] else 1000 + i     # unconnected pad = its own private net
            for L in layers:
                self.mark(L, nid, dd < INFL)
            self.novia |= dd < 0.45
            if not p["smd"]:
                self.novia |= dd < 0.8
        self.block_fp_copper()

    def block_fp_copper(self):
        """copper graphics inside footprints (e.g. solder-jumper bridges) -> keep-out for foreign nets"""
        for fp in board.GetFootprints():
            padnets = {NETID[str(p.GetNetname())] for p in fp.Pads() if str(p.GetNetname())}
            for g in fp.GraphicalItems():
                lay = g.GetLayer()
                if lay not in (pcbnew.F_Cu, pcbnew.B_Cu):
                    continue
                L = 0 if lay == pcbnew.F_Cu else 1
                bb = g.GetBoundingBox()
                dd = dist_rect(tomm(bb.GetLeft()) - OX, tomm(bb.GetTop()) - OY, tomm(bb.GetRight()) - OX, tomm(bb.GetBottom()) - OY)
                m = dd < INFL
                o = self.own[L]
                o[m & ~np.isin(o, list(padnets))] = -2
                self.novia |= dd < 0.8

    def mark(self, L, net, m):
        o = self.own[L]
        free = m & (o == -1)
        clash = m & (o != -1) & (o != net)
        o[free] = net
        o[clash] = -2

    def add_seg(self, L, net, a, b, hw):
        self.mark(L, net, dist_seg(a[0], a[1], b[0], b[1], hw) < INFL)

    def add_via(self, net, c):
        dd = dist_circle(c[0], c[1], VIA_D / 2)
        self.mark(0, net, dd < INFL); self.mark(1, net, dd < INFL)
        self.novia |= dd < VIA_D + CLR

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]
DCOST = [1, 1, 1, 1, math.sqrt(2)] + [math.sqrt(2)] * 3

def terminal_cells(p, net):
    """grid cells inside the pad (shrunk) usable as route endpoints"""
    cells = []
    layers = [0] if p["smd"] else [0, 1]
    shrink = 0.15
    for iy in range(int((p["y0"] + shrink) / G) , int((p["y1"] - shrink) / G) + 2):
        for ix in range(int((p["x0"] + shrink) / G), int((p["x1"] - shrink) / G) + 2):
            x, y = ix * G, iy * G
            if not (p["x0"] + shrink <= x <= p["x1"] - shrink and p["y0"] + shrink <= y <= p["y1"] - shrink):
                continue
            if p["circle"] and math.hypot(x - p["cx"], y - p["cy"]) > p["r"] - shrink:
                continue
            for L in layers:
                cells.append((L, iy, ix))
    if not cells:
        ix, iy = int(round(p["cx"] / G)), int(round(p["cy"] / G))
        cells = [(L, iy, ix) for L in layers]
    return cells

def astar(grid, net, sources, targets, anchors, max_exp=400000):
    own = grid.own
    passL = [((own[L] == -1) | (own[L] == net)) for L in (0, 1)]
    viaok = passL[0] & passL[1] & ~grid.novia
    P0 = passL[0].tolist(); P1 = passL[1].tolist(); VO = viaok.tolist()
    PASS = (P0, P1)
    tset = set(targets)
    anc = anchors
    def h(iy, ix):
        best = 1e9
        for (ay, ax) in anc:
            dx = abs(ax - ix); dy = abs(ay - iy)
            v = max(dx, dy) + 0.4142 * min(dx, dy)
            if v < best: best = v
        return best
    openh = []
    gbest = {}
    parent = {}
    for s in sources:
        L, iy, ix = s
        k = (L, iy, ix, 8)
        gbest[k] = 0.0; parent[k] = None
        heapq.heappush(openh, (h(iy, ix), 0.0, k))
    exp = 0
    while openh:
        f, g, k = heapq.heappop(openh)
        if gbest.get(k, 1e18) < g - 1e-9:
            continue
        L, iy, ix, d = k
        if (L, iy, ix) in tset:
            path = []
            while k is not None:
                path.append(k[:3]); k = parent[k]
            return path[::-1]
        exp += 1
        if exp > max_exp:
            return None
        lf = BOT_FACTOR if L == 1 else 1.0
        PL = PASS[L]
        for di, (dx, dy) in enumerate(DIRS):
            nx, ny = ix + dx, iy + dy
            if nx < 0 or ny < 0 or nx >= NX or ny >= NY or not PL[ny][nx]:
                continue
            if di >= 4 and not (PL[iy][nx] or PL[ny][ix]):
                continue
            ng = g + DCOST[di] * lf
            if d != 8 and d != di:
                ng += BEND
            nk = (L, ny, nx, di)
            if ng < gbest.get(nk, 1e18):
                gbest[nk] = ng; parent[nk] = k
                heapq.heappush(openh, (ng + h(ny, nx), ng, nk))
        # no second via within 4 steps of the previous one (avoids stacked / near-coincident vias)
        recent_via = False
        kk = k
        for _ in range(4):
            pk = parent.get(kk)
            if pk is None: break
            if pk[0] != kk[0]: recent_via = True; break
            kk = pk
        if VO[iy][ix] and not recent_via:
            nk = (1 - L, iy, ix, 8)
            ng = g + VIA_COST
            if ng < gbest.get(nk, 1e18):
                gbest[nk] = ng; parent[nk] = k
                heapq.heappush(openh, (ng + h(iy, ix), ng, nk))
    return None

def path_to_geom(path):
    """-> list of (layer, [(x,y)...]) polylines and via points"""
    runs = []; vias = []
    cur = [path[0]]
    for a, b in zip(path, path[1:]):
        if a[0] != b[0]:
            runs.append(cur); vias.append((a[2] * G, a[1] * G)); cur = [b]
        else:
            cur.append(b)
    runs.append(cur)
    polys = []
    for r in runs:
        pts = [(c[2] * G, c[1] * G) for c in r]
        # compress collinear
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            ax, ay = out[-1]; bx, by = pts[i]; cx, cy = pts[i + 1]
            if (bx - ax) * (cy - by) - (by - ay) * (cx - bx) != 0:
                out.append(pts[i])
        if len(pts) > 1:
            out.append(pts[-1])
        polys.append((r[0][0], out))
    return polys, vias

def net_pads(net):
    return [p for p in pads if p["net"] == net and not p["npth"]]

def route_all(order, grid):
    result = {}
    failed = []
    for net in order:
        nid = NETID[net]
        hw = POWER.get(net, SIG_W) / 2
        plist = net_pads(net)
        # start from pad nearest centroid
        cxm = sum(p["cx"] for p in plist) / len(plist); cym = sum(p["cy"] for p in plist) / len(plist)
        plist.sort(key=lambda p: (p["cx"] - cxm) ** 2 + (p["cy"] - cym) ** 2)
        tree_cells = set(terminal_cells(plist[0], nid))
        anchors = [(int(round(plist[0]["cy"] / G)), int(round(plist[0]["cx"] / G)))]
        remaining = plist[1:]
        geoms = []
        ok = True
        while remaining:
            # pick remaining pad closest to anchors
            def dmin(p):
                return min((p["cy"] / G - a[0]) ** 2 + (p["cx"] / G - a[1]) ** 2 for a in anchors)
            remaining.sort(key=dmin)
            p = remaining.pop(0)
            src = terminal_cells(p, nid)
            path = astar(grid, nid, src, list(tree_cells), anchors)
            if path is None:
                ok = False; break
            polys, vias = path_to_geom(path)
            for L, pts in polys:
                for a, b in zip(pts, pts[1:]):
                    grid.add_seg(L, nid, a, b, hw)
            for v in vias:
                grid.add_via(nid, v)
            geoms.append((polys, vias))
            tree_cells |= set(path)
            tree_cells |= set(terminal_cells(p, nid))
            anchors += [(c[1], c[2]) for c in path[::6]] + [(int(round(p["cy"] / G)), int(round(p["cx"] / G)))]
        result[net] = geoms
        if not ok:
            failed.append(net)
    return result, failed

# ---------------------------------------------------------------- net order
signal_nets = [n for n in netnames if n != "GND" and len(net_pads(n)) >= 2]
def span(n):
    ps = net_pads(n)
    return (max(p["cx"] for p in ps) - min(p["cx"] for p in ps)) + (max(p["cy"] for p in ps) - min(p["cy"] for p in ps))
order = sorted(signal_nets, key=span)

best = None
t0 = time.time()
for attempt in range(12):
    grid = Grid()
    res, failed = route_all(order, grid)
    print(f"pass {attempt}: failed {failed}  ({time.time()-t0:.1f}s)", flush=True)
    if best is None or len(failed) < len(best[1]):
        best = (res, failed, grid)
    if not failed:
        break
    order = failed + [n for n in order if n not in failed]
res, failed, grid = best

# ---------------------------------------------------------------- commit tracks
def add_track(L, a, b, w, net):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(mm(OX + a[0]), mm(OY + a[1])))
    t.SetEnd(pcbnew.VECTOR2I(mm(OX + b[0]), mm(OY + b[1])))
    t.SetWidth(mm(w)); t.SetLayer(pcbnew.F_Cu if L == 0 else pcbnew.B_Cu)
    t.SetNet(board.FindNet(net)); board.Add(t)

def add_via(c, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(mm(OX + c[0]), mm(OY + c[1])))
    v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetNet(board.FindNet(net)); board.Add(v)

ntrk = 0; nvia = 0
for net, geoms in res.items():
    w = POWER.get(net, SIG_W)
    for polys, vias in geoms:
        for L, pts in polys:
            for a, b in zip(pts, pts[1:]):
                add_track(L, a, b, w, net); ntrk += 1
        for v in vias:
            add_via(v, net); nvia += 1

# ---------------------------------------------------------------- GND stubs for SMD GND pads
def gnd_stub(p):
    nid = GNDID
    own = grid.own
    pass0 = (own[0] == -1) | (own[0] == nid)
    viaok = pass0 & ((own[1] == -1) | (own[1] == nid)) & ~grid.novia
    src = terminal_cells(p, nid)
    # Dijkstra/BFS on top layer, max radius 4 mm
    dist = {}; parent = {}
    hq = []
    for s in src:
        dist[s[1:]] = 0.0; parent[s[1:]] = None; heapq.heappush(hq, (0.0, s[1:]))
    while hq:
        d, (iy, ix) = heapq.heappop(hq)
        if d > dist.get((iy, ix), 1e9): continue
        if viaok[iy, ix] and math.hypot(ix * G - p["cx"], iy * G - p["cy"]) > 0.9:
            path = []; k = (iy, ix)
            while k is not None: path.append(k); k = parent[k]
            return path[::-1]
        if d > 4.0 / G: continue
        for di, (dx, dy) in enumerate(DIRS):
            nx, ny = ix + dx, iy + dy
            if 0 <= nx < NX and 0 <= ny < NY and pass0[ny, nx]:
                nd = d + DCOST[di]
                if nd < dist.get((ny, nx), 1e9):
                    dist[(ny, nx)] = nd; parent[(ny, nx)] = (iy, ix); heapq.heappush(hq, (nd, (ny, nx)))
    return None

stub_fail = []
for p in pads:
    if p["net"] == "GND" and p["smd"]:
        path = gnd_stub(p)
        if not path:
            stub_fail.append(f'{p["ref"]}.{p["num"]}'); continue
        pts = [(ix * G, iy * G) for iy, ix in path]
        # compress
        out = [pts[0]]
        for i in range(1, len(pts) - 1):
            ax, ay = out[-1]; bx, by = pts[i]; cx, cy = pts[i + 1]
            if (bx - ax) * (cy - by) - (by - ay) * (cx - bx) != 0: out.append(pts[i])
        if len(pts) > 1: out.append(pts[-1])
        for a, b in zip(out, out[1:]):
            add_track(0, a, b, GND_STUB_W, "GND"); grid.add_seg(0, GNDID, a, b, GND_STUB_W / 2); ntrk += 1
        add_via(out[-1], "GND"); grid.add_via(GNDID, out[-1]); nvia += 1

# ---------------------------------------------------------------- GND zones on both layers
def add_zone(layer):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(board.FindNet("GND"))
    ol = z.Outline(); ol.NewOutline()
    for x, y in [(0, 0), (W, 0), (W, H), (0, H)]:
        ol.Append(mm(OX + x), mm(OY + y))
    z.SetLocalClearance(mm(0.3))
    z.SetMinThickness(mm(0.25))
    z.SetThermalReliefGap(mm(0.3))
    z.SetThermalReliefSpokeWidth(mm(0.4))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)
add_zone(pcbnew.F_Cu); add_zone(pcbnew.B_Cu)
# no pour over the solder-jumper bridges (the unnetted bridge copper would violate zone clearance)
for fp in board.GetFootprints():
    if fp.GetReference().startswith("JP"):
        bb = fp.GetBoundingBox(False, False)
        ra = pcbnew.ZONE(board); ra.SetIsRuleArea(True); ra.SetDoNotAllowCopperPour(True)
        ra.SetDoNotAllowTracks(False); ra.SetDoNotAllowVias(False); ra.SetDoNotAllowPads(False); ra.SetDoNotAllowFootprints(False)
        ra.SetLayer(pcbnew.F_Cu)
        ol = ra.Outline(); ol.NewOutline()
        x0, y0, x1, y1 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
        m = mm(0.2)
        for x, y in [(x0 - m, y0 - m), (x1 + m, y0 - m), (x1 + m, y1 + m), (x0 - m, y1 + m)]:
            ol.Append(x, y)
        board.Add(ra)

# stitching vias every ~5 mm where both layers are free
stitch = 0
free = (grid.own[0] == -1) & (grid.own[1] == -1) & ~grid.novia
step = int(5.0 / G)
for iy in range(int(3 / G), NY - int(3 / G), step):
    for ix in range(int(3 / G), NX - int(3 / G), step):
        # need a comfortably free neighbourhood so the pour actually reaches it
        y0, y1, x0, x1 = iy - 4, iy + 5, ix - 4, ix + 5
        if free[y0:y1, x0:x1].all():
            add_via((ix * G, iy * G), "GND"); grid.add_via(GNDID, (ix * G, iy * G)); stitch += 1

filler = pcbnew.ZONE_FILLER(board)
filler.Fill(board.Zones())
pcbnew.SaveBoard(DST, board)
print(f"tracks {ntrk}, vias {nvia}, stitching vias {stitch}, failed nets {failed}, gnd stub failures {stub_fail}")
