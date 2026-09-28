"""Minimal KiCad 7 schematic generator (s-expression text)."""
import re, uuid, math

LIBDIR = "/usr/share/kicad/symbols"
_libcache = {}

def _lib(libname):
    if libname not in _libcache:
        _libcache[libname] = open(f"{LIBDIR}/{libname}.kicad_sym").read()
    return _libcache[libname]

def _block(txt, start):
    d = 0; j = start
    while True:
        c = txt[j]
        if c == '(': d += 1
        elif c == ')':
            d -= 1
            if d == 0: return txt[start:j+1]
        j += 1

def _raw_symbol(libname, name):
    txt = _lib(libname)
    i = txt.find(f'(symbol "{name}"')
    if i < 0: raise KeyError(f"{libname}:{name}")
    return _block(txt, i)

def _props(blk):
    return re.findall(r'\(property "([^"]+)" "([^"]*)"', blk)

def flat_symbol(libname, name):
    """Return flattened symbol block renamed to Lib:Name."""
    blk = _raw_symbol(libname, name)
    m = re.search(r'\(extends "([^"]+)"\)', blk)
    if m:
        base = _raw_symbol(libname, m.group(1))
        basename = m.group(1)
        # override properties present in derived
        out = base
        for k, v in _props(blk):
            out = re.sub(r'\(property "%s" "[^"]*"' % re.escape(k),
                         '(property "%s" "%s"' % (k, v.replace('\\', '\\\\')), out, count=1)
        out = out.replace(f'(symbol "{basename}"', f'(symbol "{name}"', 1)
        out = out.replace(f'(symbol "{basename}_', f'(symbol "{name}_')
        blk = out
    blk = blk.replace(f'(symbol "{name}"', f'(symbol "{libname}:{name}"', 1)
    return blk

def pins(libname, name):
    """dict number -> (x, y, angle, length, pinname, unit)"""
    blk = _raw_symbol(libname, name)
    m = re.search(r'\(extends "([^"]+)"\)', blk)
    if m: blk = _raw_symbol(libname, m.group(1))
    res = {}
    for um in re.finditer(r'\(symbol "[^"]+_(\d+)_(\d+)"', blk):
        unit = int(um.group(1))
        ub = _block(blk, um.start())
        for pm in re.finditer(r'\(pin (\w+) \w+ \(at ([-\d.]+) ([-\d.]+) (\d+)\) \(length ([\d.]+)\)[^\n]*\n\s*\(name "([^"]*)"[^\n]*\n\s*\(number "([^"]*)"', ub):
            res[pm.group(7)] = (float(pm.group(2)), float(pm.group(3)), int(pm.group(4)),
                                float(pm.group(5)), pm.group(6), unit)
    return res

def U(): return str(uuid.uuid4())

def f(v):
    s = f"{v:.4f}".rstrip('0').rstrip('.')
    return "0" if s in ("-0", "") else s

class Sch:
    def __init__(self, title="", paper="A3", project="handset_iface"):
        self.title = title; self.paper = paper; self.project = project
        self.root = U()
        self.libs = {}
        self.items = []      # raw s-expr strings
        self.wires = []      # list of (x1,y1,x2,y2)
        self.pinpts = []     # pin endpoints
        self.refcount = {}
        self.symbols = []

    def place(self, lib, name, ref, value, x, y, rot=0, mirror=None, unit=1,
              footprint="", fields=None, hide_value=False, props=None):
        key = f"{lib}:{name}"
        if key not in self.libs:
            self.libs[key] = flat_symbol(lib, name)
        s = Sym(self, lib, name, ref, value, x, y, rot, mirror, unit, footprint, fields, hide_value, props)
        self.symbols.append(s)
        return s

    def wire(self, *pts):
        pts = [tuple(p) for p in pts]
        for a, b in zip(pts, pts[1:]):
            if a != b:
                self.wires.append((a[0], a[1], b[0], b[1]))

    def route(self, a, b, mode="hv", mid=None):
        """L-shaped route: 'hv' = horizontal first, 'vh' = vertical first.
        mid: x (for 'hvh') or y (for 'vhv') of the middle segment."""
        a = tuple(a); b = tuple(b)
        if mode == "hv":
            self.wire(a, (b[0], a[1]), b)
        elif mode == "vh":
            self.wire(a, (a[0], b[1]), b)
        elif mode == "hvh":
            self.wire(a, (mid, a[1]), (mid, b[1]), b)
        elif mode == "vhv":
            self.wire(a, (a[0], mid), (b[0], mid), b)

    def label(self, name, x, y, rot=0, justify="left bottom"):
        self.items.append(f'  (label "{name}" (at {f(x)} {f(y)} {rot}) (fields_autoplaced)\n'
                          f'    (effects (font (size 1.27 1.27)) (justify {justify}))\n    (uuid {U()})\n  )')

    def text(self, s, x, y, size=1.27, bold=False, rot=0, justify="left bottom"):
        s = s.replace('"', '\\"').replace("\n", "\\n")
        b = " bold" if bold else ""
        self.items.append(f'  (text "{s}" (at {f(x)} {f(y)} {rot})\n'
                          f'    (effects (font (size {size} {size}){b}) (justify {justify}))\n    (uuid {U()})\n  )')

    def rect(self, x1, y1, x2, y2):
        self.items.append(f'  (rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)})\n'
                          f'    (stroke (width 0.2) (type dash)) (fill (type none))\n    (uuid {U()})\n  )')

    def no_connect(self, p):
        self.items.append(f'  (no_connect (at {f(p[0])} {f(p[1])}) (uuid {U()}))')

    def power(self, name, x, y, rot=0, ref=None):
        """power symbol (+5V / GND / PWR_FLAG); its single pin is at origin"""
        self.refcount["#PWR"] = self.refcount.get("#PWR", 0) + 1
        r = ref or f"#PWR{self.refcount['#PWR']:02d}"
        if name == "PWR_FLAG":
            self.refcount["#FLG"] = self.refcount.get("#FLG", 0) + 1
            r = f"#FLG{self.refcount['#FLG']:02d}"
        up = (name != "GND") ^ (rot == 180)
        dy = -5.5 if up else 5.5
        pr = {"Reference": {"hide": True}, "Value": {"dx": 0, "dy": dy, "justify": "center"}}
        return self.place("power", name, r, name, x, y, rot, props=pr)

    def _split_wires(self):
        """Split wire segments wherever another wire endpoint or a pin touches their interior
        (KiCad's connectivity expects segments to end at every junction)."""
        eps = 0.01
        pts = set()
        for (x1, y1, x2, y2) in self.wires:
            pts.add((round(x1, 3), round(y1, 3))); pts.add((round(x2, 3), round(y2, 3)))
        for p in self.pinpts:
            pts.add((round(p[0], 3), round(p[1], 3)))
        out = []
        for (x1, y1, x2, y2) in self.wires:
            inner = []
            for p in pts:
                if abs(x1-x2) < eps and abs(p[0]-x1) < eps and min(y1, y2)+eps < p[1] < max(y1, y2)-eps:
                    inner.append(p)
                elif abs(y1-y2) < eps and abs(p[1]-y1) < eps and min(x1, x2)+eps < p[0] < max(x1, x2)-eps:
                    inner.append(p)
            chain = [(x1, y1)] + sorted(inner, key=lambda p: (p[0]-x1)**2 + (p[1]-y1)**2) + [(x2, y2)]
            for a, b in zip(chain, chain[1:]):
                out.append((a[0], a[1], b[0], b[1]))
        self.wires = out

    # ---- junction computation
    def _junctions(self):
        eps = 0.01
        endpoints = set()
        for (x1, y1, x2, y2) in self.wires:
            endpoints.add((round(x1, 3), round(y1, 3))); endpoints.add((round(x2, 3), round(y2, 3)))
        for p in self.pinpts:
            endpoints.add((round(p[0], 3), round(p[1], 3)))
        junc = []
        for p in endpoints:
            n_end = 0; n_mid = 0
            for (x1, y1, x2, y2) in self.wires:
                if (abs(p[0]-x1) < eps and abs(p[1]-y1) < eps) or (abs(p[0]-x2) < eps and abs(p[1]-y2) < eps):
                    n_end += 1
                else:
                    # on segment interior?
                    if abs(x1-x2) < eps and abs(p[0]-x1) < eps and min(y1, y2) < p[1] < max(y1, y2): n_mid += 1
                    elif abs(y1-y2) < eps and abs(p[1]-y1) < eps and min(x1, x2) < p[0] < max(x1, x2): n_mid += 1
            n_pin = sum(1 for q in self.pinpts if abs(q[0]-p[0]) < eps and abs(q[1]-p[1]) < eps)
            if n_mid >= 1 or (n_end + n_pin) >= 3:
                junc.append(p)
        return junc

    def dump(self, path):
        self._split_wires()
        out = [f'(kicad_sch (version 20230121) (generator eeschema)\n\n  (uuid {self.root})\n\n  (paper "{self.paper}")\n']
        out.append(f'  (title_block\n    (title "{self.title}")\n    (date "2026-09-28")\n    (rev "A")\n  )\n')
        out.append('  (lib_symbols\n' + "\n".join("    " + b.replace("\n", "\n    ") for b in self.libs.values()) + '\n  )\n')
        for p in self._junctions():
            out.append(f'  (junction (at {f(p[0])} {f(p[1])}) (diameter 0) (color 0 0 0 0)\n    (uuid {U()})\n  )')
        for (x1, y1, x2, y2) in self.wires:
            out.append(f'  (wire (pts (xy {f(x1)} {f(y1)}) (xy {f(x2)} {f(y2)}))\n    (stroke (width 0) (type default))\n    (uuid {U()})\n  )')
        out += self.items
        out += [s.sexpr() for s in self.symbols]
        out.append('  (sheet_instances\n    (path "/" (page "1"))\n  )\n)\n')
        open(path, "w").write("\n".join(out))


class Sym:
    def __init__(self, sch, lib, name, ref, value, x, y, rot, mirror, unit, footprint, fields, hide_value, props=None):
        self.props = props or {}
        self.sch = sch; self.lib = lib; self.name = name; self.ref = ref; self.value = value
        self.x = x; self.y = y; self.rot = rot; self.mirror = mirror; self.unit = unit
        self.footprint = footprint; self.fields = fields or {}; self.hide_value = hide_value
        self.uuid = U()
        self._pins = pins(lib, name)
        for num, (px, py, ang, ln, pn, un) in self._pins.items():
            if un in (0, unit):
                sch.pinpts.append(self.pin(num))

    def _xf(self, px, py):
        # library coords are y-up; schematic y-down.
        # KiCad: transform applied to lib coords then y flipped.
        r = self.rot
        if r == 0:   qx, qy = px, py
        elif r == 90:  qx, qy = -py, px      # verified empirically below
        elif r == 180: qx, qy = -px, -py
        elif r == 270: qx, qy = py, -px
        if self.mirror == "x": qy = -qy
        if self.mirror == "y": qx = -qx
        return (self.x + qx, self.y - qy)

    def pin(self, num):
        px, py, ang, ln, pn, un = self._pins[str(num)]
        return self._xf(px, py)

    def sexpr(self):
        mir = f" (mirror {self.mirror})" if self.mirror else ""
        props = [("Reference", self.ref, 0, -2.54, False),
                 ("Value", self.value, 0, 2.54, self.hide_value),
                 ("Footprint", self.footprint, 0, 0, True),
                 ("Datasheet", "", 0, 0, True)]
        for k, v in self.fields.items():
            props.append((k, v, 0, 0, True))
        ps = ""
        for k, v, dx, dy, hide in props:
            just = "left"; px = self.x + 2.54 + dx; py = self.y + dy
            ov = self.props.get(k)
            if ov:
                px = self.x + ov.get("dx", 0); py = self.y + ov.get("dy", 0)
                hide = ov.get("hide", hide); just = ov.get("justify", "center")
            h = " hide" if hide else ""
            j = "" if just == "center" else f" (justify {just})"
            ang = self.props.get("_angle", 90 if self.rot in (90, 270) else 0)
            ps += (f'    (property "{k}" "{v}" (at {f(px)} {f(py)} {ang})\n'
                   f'      (effects (font (size 1.27 1.27)){j}{h})\n    )\n')
        pinlist = "".join(f'    (pin "{n}" (uuid {U()}))\n' for n in self._pins)
        return (f'  (symbol (lib_id "{self.lib}:{self.name}") (at {f(self.x)} {f(self.y)} {self.rot}){mir} (unit {self.unit})\n'
                f'    (in_bom yes) (on_board yes) (dnp no)\n    (uuid {self.uuid})\n{ps}{pinlist}'
                f'    (instances\n      (project "{self.sch.project}"\n        (path "/{self.sch.root}"\n          (reference "{self.ref}") (unit {self.unit})\n        )\n      )\n    )\n  )')
