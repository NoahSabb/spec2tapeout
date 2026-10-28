#!/usr/bin/env python3
import argparse, json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDK_ROOT = os.environ.get("PDK_ROOT", os.path.expanduser("~/.ciel"))
LIB = f"{PDK_ROOT}/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
TOPS = {
    "mac_int8": ["rtl/mac_int8.v"],
    "mac_array_2x2": ["rtl/mac_int8.v", "rtl/mac_array_2x2.v"],
    "tt_um_noahsabb_mac": ["rtl/mac_int8.v", "rtl/mac_array_2x2.v", "rtl/tt_um_noahsabb_mac.v"],
}
def run(top, files, width, acc, out, period_ns=10):
    os.makedirs(out, exist_ok=True)
    chparam = f"chparam -set WIDTH {width} -set ACC_WIDTH {acc} {top}\n" if top != "tt_um_noahsabb_mac" else ""
    ys = f"""
read_liberty -lib -ignore_miss_dir -setattr blackbox {LIB}
{''.join(f'read_verilog -sv -noautowire {ROOT}/{f}' + chr(10) for f in files)}
{chparam}hierarchy -check -top {top}
proc
tee -o {out}/{top}.latch.rpt select -count t:$dlatch t:$adlatch t:$dlatchsr
tee -o {out}/{top}.mem.rpt select -count t:$mem t:$mem_v2
synth -top {top} -flatten
dfflibmap -liberty {LIB}
abc -D {period_ns*1000} -liberty {LIB}
setundef -zero
hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
splitnets
opt_clean -purge
tee -o {out}/{top}.chk.rpt check -mapped
tee -o {out}/{top}.stat.json stat -json -liberty {LIB}
write_verilog -noattr -noexpr -nohex -nodec {out}/{top}.nl.v
"""
    open(f"{out}/{top}.ys", "w").write(ys)
    r = subprocess.run(["yosys", "-q", "-l", f"{out}/{top}.log", "-s", f"{out}/{top}.ys"], capture_output=True, text=True)
    sys.stdout.write(r.stdout[-2000:]); sys.stderr.write(r.stderr[-2000:])
    if r.returncode != 0: print(f"FAIL {top}: yosys exit {r.returncode}"); return False
    txt = open(f"{out}/{top}.stat.json").read()
    j = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
    d = j["design"] if "design" in j else list(j["modules"].values())[0]
    cells = d.get("num_cells", 0); area = d.get("area", 0.0)
    unmapped = {k: v for k, v in d.get("num_cells_by_type", {}).items() if k.startswith("$")}
    latches = int(re.search(r"(\d+)", open(f"{out}/{top}.latch.rpt").read() or "0").group(1) or 0)
    mems = int(re.search(r"(\d+)", open(f"{out}/{top}.mem.rpt").read() or "0").group(1) or 0)
    chk = open(f"{out}/{top}.chk.rpt").read(); problems = len(re.findall(r"^Warning:", chk, re.M))
    ok = not unmapped and latches == 0 and mems == 0 and problems == 0 and cells >= 20
    print(f"{'PASS' if ok else 'FAIL'} {top}: cells={cells} area={area:.1f}um2 unmapped={unmapped} latches={latches} mems={mems} check_warnings={problems}")
    json.dump({"top": top, "cells": cells, "area": area, "unmapped": unmapped, "latches": latches, "mems": mems, "check_warnings": problems},
              open(f"{out}/{top}.summary.json", "w"), indent=2)
    return ok
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--width", type=int, default=8); ap.add_argument("--acc", type=int, default=0)
    ap.add_argument("--out", default=f"{ROOT}/runs/synth"); a = ap.parse_args()
    acc = a.acc or (2 * a.width + 16)
    ok = all(run(t, f, a.width, acc, a.out) for t, f in TOPS.items())
    sys.exit(0 if ok else 1)
