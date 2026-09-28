"""Render PCB layers to PNG via kicad-cli svg + cairosvg."""
import subprocess, sys, cairosvg, os
pcb = sys.argv[1]; out = sys.argv[2]; layers = sys.argv[3] if len(sys.argv) > 3 else "F.Cu,B.Cu,F.SilkS,Edge.Cuts,F.CrtYd"
scale = float(sys.argv[4]) if len(sys.argv) > 4 else 12
svg = out.replace(".png", ".svg")
subprocess.run(["kicad-cli", "pcb", "export", "svg", "--exclude-drawing-sheet", "--page-size-mode", "2",
                "-l", layers, "-o", svg, pcb], check=True, capture_output=True)
cairosvg.svg2png(url=svg, write_to=out, scale=scale, background_color="white")
os.remove(svg)
print(out)
