import sys; sys.path.insert(0, "/home/claude")
from kicadgen import Sch

u = 1.27
OFF = [0, 0]
def P(x, y): return ((x + OFF[0]) * u, (y + OFF[1]) * u)

s = Sch("RJ9 Handset <-> PC Line In / Line Out Interface", "A3", "handset_iface")

FP_R = "Resistor_SMD:R_0805_2012Metric"
FP_C = "Capacitor_SMD:C_0805_2012Metric"
FP_C1206 = "Capacitor_SMD:C_1206_3216Metric"
FP_CP = "Capacitor_SMD:CP_Elec_6.3x5.4"
FP_CP_BIG = "Capacitor_SMD:CP_Elec_6.3x7.7"
FP_DIP8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
FP_POT = "Potentiometer_SMD:Potentiometer_Bourns_3314J_Vertical"
FP_JACK = "Connector_Audio:Jack_3.5mm_CUI_SJ1-3523N_Horizontal"
FP_RJ9 = "Connector_RJ:RJ9_Evercom_5301-440xxx_Horizontal"
FP_USB = "Connector_USB:USB_B_Lumberg_2411_02_Horizontal"
FP_FB = "Inductor_SMD:L_0805_2012Metric"

# label placement presets (dx/dy in mm relative to symbol origin)
H_ABOVE = {"Reference": {"dx": 0, "dy": -2.8}, "Value": {"dx": 0, "dy": 2.8}}          # horizontal R/C: ref above, value below
V_RIGHT = {"Reference": {"dx": 3.6, "dy": -1.3}, "Value": {"dx": 3.6, "dy": 1.5}}      # vertical R/C: text on right
V_LEFT = {"Reference": {"dx": -3.6, "dy": -1.3}, "Value": {"dx": -3.6, "dy": 1.5}}     # vertical R/C: text on left
def jl(d, ref_left=False):
    return {"Reference": {**d["Reference"], "justify": "right" if ref_left else "left"},
            "Value": {**d["Value"], "justify": "right" if ref_left else "left"}}

def R(ref, val, x, y, rot=0, fp=FP_R, props=None):  return s.place("Device", "R", ref, val, *P(x, y), rot, footprint=fp, props=props)
def C(ref, val, x, y, rot=0, fp=FP_C, props=None):  return s.place("Device", "C", ref, val, *P(x, y), rot, footprint=fp, props=props)
def CP(ref, val, x, y, rot=0, fp=FP_CP, props=None): return s.place("Device", "C_Polarized", ref, val, *P(x, y), rot, footprint=fp, props=props)
def W(*pts): s.wire(*[P(*p) for p in pts])
def GND(x, y, rot=0): return s.power("GND", *P(x, y), rot)
def V5(x, y): return s.power("+5V", *P(x, y))
def LBL(name, x, y, rot=0): s.label(name, *P(x, y), rot)
def TXT(t, x, y, size=1.27, bold=False, justify="left bottom"): s.text(t, *P(x, y), size, bold, justify=justify)
def BOX(x1, y1, x2, y2, title):
    s.rect(*P(x1, y1), *P(x2, y2)); TXT(title, x1 + 1, y1 - 1, 2.0, True)

# =====================================================================
# PATH A : PC LINE OUT -> LM386 -> handset receiver
# =====================================================================
OFF[:] = [0, 0]
BOX(14, 22, 132, 68, "PATH A :  PC LINE OUT  ->  LM386 (Av=20)  ->  Handset receiver      路徑 A：電腦 line out → 聽筒")

J1 = s.place("Connector_Audio", "AudioJack3", "J1", "LINE OUT (from PC)", *P(24, 40), footprint=FP_JACK,
             props={"Reference": {"dx": 0, "dy": -8.5}, "Value": {"dx": -2, "dy": 8.5}})
W((28, 38), (32, 38), (32, 34)); GND(32, 34, 180)
R2 = R("R2", "10k", 36, 40, 90, props={"Reference": {"dx": -2.2, "dy": -2.8}, "Value": {"dx": 2.4, "dy": -2.8}})
R1 = R("R1", "10k", 36, 42, 90, props={"Reference": {"dx": -2.2, "dy": 2.8}, "Value": {"dx": 2.4, "dy": 2.8}})
W((28, 40), (33, 40)); W((28, 42), (33, 42))
W((39, 40), (42, 40), (42, 42)); W((39, 42), (43, 42))
C1 = C("C1", "10uF", 46, 42, 90, fp=FP_C1206, props={"Reference": {"dx": 0, "dy": -3.0}, "Value": {"dx": 0, "dy": 3.0}})
RV1 = s.place("Device", "R_Potentiometer", "RV1", "10k VOL", *P(54, 46), footprint="Potentiometer_THT:Potentiometer_Alps_RK097_Single_Horizontal",
              props=jl({"Reference": {"dx": -2.5, "dy": -1.5}, "Value": {"dx": -2.5, "dy": 1.5}}, True))
W((49, 42), (54, 42), (54, 43))
W((54, 49), (54, 52)); GND(54, 52)
U1 = s.place("Amplifier_Audio", "LM386", "U1", "LM386M (SOIC-8)", *P(76, 46), footprint=FP_DIP8,
             props={"Reference": {"dx": 0, "dy": -11.5}, "Value": {"dx": 0, "dy": 11.5}})
W((57, 46), (62, 46), (62, 44), (70, 44))                 # wiper -> pin 3 (+)
W((70, 48), (66, 48), (66, 54)); GND(66, 54)               # pin 2 (-) -> GND
W((74, 52), (74, 56)); GND(74, 56)                         # pin 4
s.no_connect(P(76, 52)); s.no_connect(P(78, 52))           # pins 1/8 open -> Av = 20
W((74, 40), (74, 28)); V5(74, 28)                          # pin 6 V+
W((74, 30), (68, 30))
C2 = C("C2", "100nF", 68, 33, props=jl(V_LEFT, True))
W((68, 36), (68, 37)); GND(68, 37)
W((76, 40), (76, 36), (81, 36))                            # pin 7 BYPASS
C4 = C("C4", "10uF", 84, 36, 90, fp=FP_C1206, props={"Reference": {"dx": 0, "dy": -3.0}, "Value": {"dx": 0, "dy": 3.0}})
W((87, 36), (90, 36), (90, 32)); GND(90, 32, 180)
W((82, 46), (85, 46))                                      # pin 5 out
C5 = CP("C5", "220uF", 88, 46, 90, fp=FP_CP_BIG, props={"Reference": {"dx": 0, "dy": -3.0}, "Value": {"dx": 0, "dy": 3.0}})
W((91, 46), (93, 46))
R3 = R("R3", "47R", 96, 46, 90, props=H_ABOVE)
W((84, 46), (84, 50))                                      # Zobel
R4 = R("R4", "10R", 84, 53, props=jl(V_RIGHT))
C6 = C("C6", "47nF", 84, 59, props=jl(V_RIGHT))
W((84, 62), (84, 63)); GND(84, 63)
W((99, 46), (106, 46)); LBL("EAR+", 100, 46)
TXT("EAR+ -> J2 via JP1/JP2 (see PINOUT SELECT)", 98, 59, 1.2, justify="left top")
TXT("R1/R2: L+R mix to mono\nC1: DC block", 30, 55, 1.2, justify="left top")
TXT("R4+C6: Zobel network\nReceiver 150R: R3=47R\nReceiver 8~32R : R3=10R", 90, 53, 1.2, justify="left top")

# =====================================================================
# PATH B : Electret MIC -> MCP6022 preamp -> PC LINE IN
# =====================================================================
OFF[:] = [0, 8]
BOX(14, 70, 132, 152, "PATH B :  MIC -> MCP6022 preamp (Av 5.5~51) -> PC LINE IN     路徑 B：麥克風 → line in")
OFF[:] = [0, 12]

V5(21, 74); W((21, 74), (21, 76))
R6 = R("R6", "100R", 24, 76, 90, props=H_ABOVE)
W((27, 76), (46, 76))
C7 = CP("C7", "100uF", 31, 79, fp=FP_CP, props=jl(V_RIGHT))
W((31, 82), (31, 83)); GND(31, 83)
LBL("+5V_FILT", 34, 76)
R5 = R("R5", "2.2k", 46, 79, props=jl(V_LEFT, True))            # electret bias
W((46, 82), (46, 87), (42, 87)); LBL("MIC+", 42, 87)
TXT("R5: bias for electret mic", 38, 90, 1.2, justify="left top")
W((46, 82), (48, 82))
C8 = C("C8", "1uF", 51, 82, 90, props={"Reference": {"dx": 0, "dy": -3.0}, "Value": {"dx": 0, "dy": 3.0}})
W((54, 82), (56, 82))
R7 = R("R7", "100k", 55, 79, props=jl(V_RIGHT))
W((55, 76), (55, 73)); LBL("VREF", 55, 73)
U2A = s.place("Amplifier_Operational", "MCP6022", "U2", "MCP6022-E/SN", *P(62, 84), unit=1, footprint=FP_DIP8,
              props={"Reference": {"dx": 2.5, "dy": -8.5}, "Value": {"dx": 0, "dy": 8.5}})
W((68, 84), (88, 84))                                      # OUT node
W((72, 84), (72, 92))                                      # feedback R8 + RV2 (rheostat)
R8 = R("R8", "10k", 72, 95, props=jl(V_RIGHT))
RV2 = s.place("Device", "R_Potentiometer", "RV2", "100k GAIN", *P(72, 101), footprint=FP_POT,
              props=jl({"Reference": {"dx": -2.5, "dy": -1.5}, "Value": {"dx": -2.5, "dy": 1.5}}, True))
W((75, 101), (75, 104), (72, 104))
W((72, 104), (72, 106), (54, 106), (54, 86), (56, 86))     # FB -> pin 2 (-)
W((80, 84), (80, 95))                                      # C9 across feedback
C9 = C("C9", "47pF", 80, 98, props=jl(V_RIGHT))
W((80, 101), (80, 106), (72, 106))
R9 = R("R9", "2.2k", 64, 109, props=jl(V_RIGHT))          # Rg
C10 = C("C10", "22uF", 64, 115, fp=FP_C1206, props=jl(V_RIGHT))
W((64, 118), (64, 120), (68, 120)); LBL("VREF", 65, 120)
C11 = C("C11", "10uF", 91, 84, 90, fp=FP_C1206, props={"Reference": {"dx": 0, "dy": -3.0}, "Value": {"dx": 0, "dy": 3.0}})
W((94, 84), (95, 84))
R10 = R("R10", "100R", 98, 84, 90, props=H_ABOVE)
W((101, 84), (108, 84))
W((105, 84), (105, 86), (108, 86))
W((108, 82), (105, 82), (105, 78)); GND(105, 78, 180)
J3 = s.place("Connector_Audio", "AudioJack3", "J3", "LINE IN (to PC)", *P(112, 84), mirror="y", footprint=FP_JACK,
             props={"Reference": {"dx": 0, "dy": -8.5}, "Value": {"dx": 2, "dy": 8.5}})
TXT("same signal to L and R", 92, 94, 1.2)
TXT("Gain: R8 = 10k fixed + RV2 (0~100k)\n=> Av = 1 + (10k~110k)/2.2k = 5.5 ~ 51  (15~34 dB)\nC9 limits HF / RF pickup\nC10 sets LF corner: 1/(2*pi*2.2k*22u) = 3.3 Hz", 84, 114, 1.2)

# VREF buffer (U2B) : 2.5 V virtual ground
LBL("+5V_FILT", 48, 113); W((48, 113), (48, 117))
R11 = R("R11", "10k", 48, 120, props=jl(V_RIGHT))
W((48, 123), (48, 129))
R12 = R("R12", "10k", 48, 132, props=jl(V_LEFT, True))
W((48, 135), (48, 136)); GND(48, 136)
W((40, 126), (48, 126)); W((48, 126), (56, 126))
C12 = C("C12", "10uF", 40, 129, fp=FP_C1206, props=jl(V_LEFT, True))
W((40, 132), (40, 133)); GND(40, 133)
U2B = s.place("Amplifier_Operational", "MCP6022", "U2", "MCP6022-E/SN", *P(62, 128), unit=2, footprint=FP_DIP8,
              props={"Reference": {"dx": 0, "dy": -8.5}, "Value": {"dx": 0, "dy": 8.5}})
W((68, 128), (72, 128), (72, 139), (53, 139), (53, 130), (56, 130))
W((72, 128), (78, 128)); LBL("VREF", 74, 128)
TXT("U2B: VREF = 2.5 V buffered virtual ground", 40, 143, 1.2)
U2C = s.place("Amplifier_Operational", "MCP6022", "U2", "MCP6022-E/SN", *P(92, 128), unit=3, footprint=FP_DIP8,
              props={"Reference": {"dx": -4.5, "dy": -2.5, "justify": "right"}, "Value": {"dx": -4.5, "dy": 2.5, "justify": "right"}})
W((90, 122), (90, 118)); LBL("+5V_FILT", 90, 118)
W((90, 120), (98, 120))
C13 = C("C13", "100nF", 98, 123, props=jl(V_RIGHT))
W((98, 126), (98, 127)); GND(98, 127)
W((90, 134), (90, 138)); GND(90, 138)

# =====================================================================
# POWER : USB 5 V from the same PC (single ground, no ground loop)
# =====================================================================
OFF[:] = [12, 0]
BOX(132, 22, 208, 68, "POWER :  5 V from PC USB (shares PC ground -> no ground loop)      電源與接地")
J4 = s.place("Connector", "USB_B", "J4", "USB-B (5V only)", *P(140, 40), footprint=FP_USB,
             props={"Reference": {"dx": -6, "dy": -10.5}, "Value": {"dx": 4, "dy": 26}})
W((146, 36), (150, 36))
FB1 = s.place("Device", "FerriteBead", "FB1", "600R@100MHz", *P(153, 36), 90, footprint=FP_FB,
              props={"Reference": {"dx": 0, "dy": -3.0}, "Value": {"dx": 0, "dy": 3.2}})
W((156, 36), (170, 36))
W((160, 36), (160, 32)); V5(160, 32)
C14 = CP("C14", "100uF", 164, 39, fp=FP_CP, props=jl(V_RIGHT))
W((164, 42), (164, 43)); GND(164, 43)
s.power("PWR_FLAG", *P(170, 36))
s.no_connect(P(146, 40)); s.no_connect(P(146, 42))
W((140, 48), (140, 52)); W((138, 48), (138, 52), (140, 52))
W((140, 52), (148, 52)); GND(140, 54); W((140, 52), (140, 54))
s.power("PWR_FLAG", *P(148, 52))
TXT("D+ / D- unused: power only.\nFB1 + C14: HF filter on USB 5 V.", 152, 66, 1.2)

# =====================================================================
# NOTES
# =====================================================================
BOX(132, 78, 208, 152, "NOTES      設計說明")
TXT(
"1. RJ9 (4P4C) pinout is NOT standardized. Measure first:\n"
"   - receiver pair: 30~300 ohm DC; electret mic pair: diode-like (asymmetric).\n"
"   - set JP1-JP4 (pair) and JP5-JP6 (mic polarity) to match the handset.\n"
"2. Path A: LM386 has low output impedance, so the receiver no longer\n"
"   loads the PC line out -> no volume drop. RV1 sets the level.\n"
"   Gain fixed at 20 (pins 1/8 open). C5 blocks the 2.5 V DC offset.\n"
"   R3 limits current into the receiver (telephone receiver ~1 mW rated).\n"
"3. Path B: electret needs 2~5 V bias via R5. Mic level ~10 mV -> line\n"
"   level ~300 mV needs ~30 dB; set with RV2. Output impedance ~100 ohm\n"
"   drives the 10 kohm line in without loss.\n"
"   Dynamic mic instead of electret: remove R5, raise gain (2 stages).\n"
"4. Ground: everything is powered from the same PC USB port -> single\n"
"   ground reference. Star ground on PCB; keep U2 away from U1 output.\n"
"   R6/C7 filter USB switching noise for the mic preamp (+5V_FILT).\n"
"5. Optional sidetone: 47k~100k from U2A output to RV1 pin 1.\n"
"6. Optional LDO (e.g. 4.5 V) in place of R6 if USB noise is still audible.\n"
"7. SMT: R/C 0805; 10uF/22uF = 1206 X5R 10V ceramic; 47pF = C0G;\n"
"   U1/U2 = SOIC-8; RV2 = Bourns 3314J SMT trimmer; FB1 = 0805 bead.\n"
"   THT (connectors + panel pot): J1/J3 = CUI SJ1-3523N 3.5 mm jack,\n"
"   J2 = Evercom 5301-440 RJ9, J4 = Lumberg 2411 02 USB-B,\n"
"   RV1 = Alps RK097 single 9 mm right-angle shaft pot.\n"
"8. C5/C7/C14 = SMD V-chip electrolytic 6.3 mm, >= 6.3 V rating.",
 134, 80, 1.2, justify="left top")

# =====================================================================
# J2 HANDSET CONNECTOR + PINOUT SELECT (solder jumpers)
# =====================================================================
OFF[:] = [0, 0]
BOX(14, 166, 132, 224, "J2 HANDSET PINOUT SELECT (solder jumpers, default = 1-2 bridged)      話筒腳位選擇跳線")
FP_SJ3 = "Jumper:SolderJumper-3_P1.3mm_Bridged12_RoundedPad1.0x1.5mm_NumberLabels"
def SJ(ref, x, y, val):
    return s.place("Jumper", "SolderJumper_3_Bridged12", ref, val, *P(x, y), 90, footprint=FP_SJ3,
                   props={"Reference": {"dx": 5.6, "dy": -0.9, "justify": "left", "_angle": 0},
                          "Value": {"dx": 5.6, "dy": 1.9, "justify": "left", "_angle": 0}})
def endlabel(name, x, y, side=-1):
    """wire from a pin at (x,y) 4 units to the left and put a label (or GND) there"""
    W((x, y), (x + 4 * side, y))
    if name == "GND":
        GND(x + 4 * side, y)
    else:
        LBL(name, x + 4 * side, y, 0)

J2 = s.place("Connector", "RJ9", "J2", "RJ9 HANDSET", *P(126, 196), mirror="y", footprint=FP_RJ9,
             props={"Reference": {"dx": 0, "dy": -12}, "Value": {"dx": 0, "dy": 11}})
# pair-swap jumpers: common -> J2 pin ; A (pad1, default) below, B (pad3) above
# (ref, centre y, J2 pin, pin y, jog x, net A, net B)
for ref, yc, pin, py, xk, na, nb in [
        ("JP4", 172, 4, 192, 117, "GND", "MB"),
        ("JP3", 185, 3, 194, 115, "MB", "GND"),
        ("JP2", 202, 2, 196, 111, "MA", "EAR+"),
        ("JP1", 216, 1, 198, 113, "EAR+", "MA")]:
    SJ(ref, 100, yc, "PAIR")
    W((103, yc), (xk, yc), (xk, py), (118, py))
    endlabel(na, 100, yc + 4)
    endlabel(nb, 100, yc - 4)
# mic polarity jumpers: common = MA / MB
for ref, yc, com, na, nb in [("JP5", 190, "MA", "MIC+", "GND"), ("JP6", 210, "MB", "GND", "MIC+")]:
    SJ(ref, 70, yc, "MIC POL")
    W((73, yc), (80, yc)); LBL(com, 76, yc)
    endlabel(na, 70, yc + 4)
    endlabel(nb, 70, yc - 4)

TXT("JP1-JP4 = PAIR select (always set all four the same way)\n"
    "   1-2 (default): J2.1 = EAR+, J2.4 = EAR-/GND, J2.2 = MA, J2.3 = MB\n"
    "   2-3          : J2.2 = EAR+, J2.3 = EAR-/GND, J2.1 = MA, J2.4 = MB\n"
    "JP5-JP6 = MIC polarity (always set both the same way)\n"
    "   1-2 (default): MA = MIC+ (hot), MB = GND\n"
    "   2-3          : MA = GND, MB = MIC+ (hot)\n"
    "To change: cut the 1-2 trace on the jumper, then bridge 2-3 with solder.", 18, 168, 1.2, justify="left top")

s.dump("/home/claude/out/handset_iface.kicad_sch")
open("/home/claude/out/handset_iface.kicad_pro", "w").write(
'{\n  "board": {"design_settings": {}, "layer_presets": [], "viewports": []},\n'
'  "meta": {"filename": "handset_iface.kicad_pro", "version": 1},\n'
'  "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},\n'
'  "sheets": [["%s", ""]],\n  "text_variables": {}\n}\n' % s.root)
print("ok")
