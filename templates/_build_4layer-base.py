"""Build the 4layer-base KiCad template from the twinspora project.

- .kicad_pro: keep all settings; replace project-name and sheet references with template values.
- .kicad_pcb: keep header + setup block (stackup, design rules, pre-defined sizes, plot params),
              strip all footprints/traces/vias/zones/graphics/nets/groups, close with embedded_fonts.
- .kicad_sch: keep header (paper, title_block cleared), empty lib_symbols, sheet_instances, close.
"""
import json
import re
import uuid
from pathlib import Path

SRC_DIR = Path(r"D:\gh\twinspora\twinspora")
DST_DIR = Path(r"D:\gh\library\templates\4layer-base")
NAME = "4layer-base"

# Fresh UUID for the template's root schematic. Must be consistent across
# .kicad_pro (top_level_sheets, sheets) and .kicad_sch (uuid).
ROOT_UUID = str(uuid.uuid4())

# ---------- .kicad_pro ----------
pro = json.loads((SRC_DIR / "twinspora.kicad_pro").read_text(encoding="utf-8"))

pro["meta"]["filename"] = f"{NAME}.kicad_pro"
pro["schematic"]["top_level_sheets"] = [
    {"filename": f"{NAME}.kicad_sch", "name": NAME, "uuid": ROOT_UUID}
]
pro["schematic"]["used_designators"] = ""
pro["sheets"] = [[ROOT_UUID, NAME]]
pro["boards"] = []

(DST_DIR / f"{NAME}.kicad_pro").write_text(
    json.dumps(pro, indent=2), encoding="utf-8"
)

# ---------- .kicad_pcb ----------
# Keep everything from the start through the closing `)` of the (setup ...) block.
# In the twinspora file that ends at line 153 (1-indexed). We detect it robustly by
# tracking paren depth from the line where `(setup` starts.
pcb_lines = (SRC_DIR / "twinspora.kicad_pcb").read_text(encoding="utf-8").splitlines()

setup_start = next(i for i, ln in enumerate(pcb_lines) if ln.strip().startswith("(setup"))
depth = 0
setup_end = None
for i in range(setup_start, len(pcb_lines)):
    for ch in pcb_lines[i]:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                setup_end = i
                break
    if setup_end is not None:
        break

header = "\n".join(pcb_lines[: setup_end + 1])
tail = "\n\t(embedded_fonts no)\n)\n"
(DST_DIR / f"{NAME}.kicad_pcb").write_text(header + tail, encoding="utf-8")

# ---------- .kicad_sch ----------
# Read the source schematic's generator/version lines so the template matches the
# installed KiCad version. Then emit a minimal, empty schematic that references
# ROOT_UUID and has a cleared title_block.
src_sch = (SRC_DIR / "twinspora.kicad_sch").read_text(encoding="utf-8").splitlines()
version_line = next(ln for ln in src_sch if ln.strip().startswith("(version"))
gen_line = next(ln for ln in src_sch if ln.strip().startswith("(generator "))
gen_ver_line = next(ln for ln in src_sch if ln.strip().startswith("(generator_version"))
paper_line = next(ln for ln in src_sch if ln.strip().startswith("(paper"))

sch = "\n".join([
    "(kicad_sch",
    f"\t{version_line.strip()}",
    f"\t{gen_line.strip()}",
    f"\t{gen_ver_line.strip()}",
    f'\t(uuid "{ROOT_UUID}")',
    f"\t{paper_line.strip()}",
    "\t(title_block",
    '\t\t(title "")',
    '\t\t(date "")',
    '\t\t(rev "")',
    "\t)",
    "\t(lib_symbols)",
    "\t(sheet_instances",
    '\t\t(path "/"',
    '\t\t\t(page "1")',
    "\t\t)",
    "\t)",
    "\t(embedded_fonts no)",
    ")",
    "",
])
(DST_DIR / f"{NAME}.kicad_sch").write_text(sch, encoding="utf-8")

# ---------- meta/info.html ----------
info = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>4-Layer Base</title></head>
<body>
<h1>4-Layer Base</h1>
<p>4-layer JLCPCB-compatible stackup (NP-155F, 1.6mm finished thickness)
with design rules, net classes, pre-defined track/via sizes, and default
graphical text styles inherited from the Twinspora project.</p>
<ul>
<li>Layers: F.Cu / In1.Cu / In2.Cu / B.Cu (signal)</li>
<li>Dielectric: Nan Ya Plastics NP-155F (er 4.4 / 4.43)</li>
<li>Solder mask: JLCPCB 0.01524mm, er 3.8</li>
<li>Default net classes: 3V3, 5V, ADC, CAN, GND, H_PWR, SPI1-4, TIM1-2, USB</li>
<li>BOM preset: CSV (Reference, Quantity, Value, DNP, etc.)</li>
</ul>
</body>
</html>
"""
(DST_DIR / "meta" / "info.html").write_text(info, encoding="utf-8")

print(f"Built template at {DST_DIR}")
print(f"Root schematic UUID: {ROOT_UUID}")
