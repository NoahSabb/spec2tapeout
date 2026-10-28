#!/usr/bin/env python3
"""make verify-factory: re-prove the whole factory from a clean run. Writes factory/state/verify.json."""
import glob, json, os, shutil, subprocess, sys, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); STATE = os.path.join(ROOT, "factory", "state")
sys.path.insert(0, os.path.join(ROOT, "factory")); import orchestrate as O
TAG = "verify-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
results = {}
def check(name, ok, detail=""):
    results[name] = {"ok": bool(ok), "detail": str(detail)[:2000]}; O.log(f"VERIFY {name}: {'PASS' if ok else 'FAIL'} {detail[:200] if detail else ''}")
def make(*args):
    return subprocess.call(["make", *args], cwd=ROOT)

# (a) full pipeline from clean on the MAC
rc = make("doctor"); check("a_doctor", rc == 0, f"exit {rc}")
rc = make("lint"); check("a_lint", rc == 0, f"exit {rc}")
rc = make("sim", "TOP=mac", "WIDTH=8", "ACC_WIDTH=32"); check("a_sim_rtl", rc == 0, f"exit {rc}")
rc = make("synth", "WIDTH=8"); check("a_synth", rc == 0, f"exit {rc}")
make("clean-run", f"TAG={TAG}")
os.makedirs(os.path.join(ROOT, "runs", TAG), exist_ok=True)   # librelane --force-run-dir requires an existing dir
rc = make("harden", f"TAG={TAG}", "DESIGN=mac_int8", "CONFIG=" + (open(os.path.join(STATE, "best_config.txt")).read().strip() if os.path.exists(os.path.join(STATE, "best_config.txt")) else "flow/mac_int8/config.json"))
check("a_harden", rc == 0, f"exit {rc} tag {TAG}")
rc = make("sim-gl", f"TAG={TAG}", "TOP=mac"); check("e_sim_gl_vs_golden", rc == 0, f"exit {rc}")
rc = make("render", f"TAG={TAG}"); check("a_render", rc == 0, f"exit {rc}")

# (b) every gate exit code
gates = O.jload(os.path.join(STATE, "gates.json"), {})
required = ["doctor", "lint", "sim-mac-w8", "synth-8", f"harden-{TAG}", "sim-gl-mac"]
missing = [g for g in required if g not in gates]; failed = [g for g in required if g in gates and gates[g]["exit_code"] != 0]
check("b_gates", not missing and not failed, f"missing={missing} failed={failed}")

# (c) pipeline.json all stations pass
p = O.jload(os.path.join(STATE, "pipeline.json"), {})
bad = [s["id"] for s in p.get("stations", []) if s["status"] not in ("pass", "skipped")]
check("c_pipeline_all_pass", p.get("run_tag") == TAG and not bad and p.get("status") == "pass", f"run_tag={p.get('run_tag')} status={p.get('status')} bad_stations={bad}")

# (d) GDS exists nonzero and SVG renders
gds = glob.glob(os.path.join(ROOT, "runs", TAG, "final", "gds", "*.gds"))
ok_gds = bool(gds) and os.path.getsize(gds[0]) > 0
svg_ok = False; detail = ""
if ok_gds:
    try:
        import gdstk; lib = gdstk.read_gds(gds[0]); top = lib.top_level()[0]; svg = os.path.join(ROOT, "runs", TAG, "final", "gds", "verify.svg")
        top.write_svg(svg, pad="5%"); svg_ok = os.path.getsize(svg) > 0; detail = f"{gds[0]} {os.path.getsize(gds[0])} bytes; svg {os.path.getsize(svg)} bytes; top cell {top.name}"
    except Exception as e: detail = f"gdstk failed: {e}"
check("d_gds_and_svg", ok_gds and svg_ok, detail)

# (f) optional eqy (experimental): LibreLane's Yosys.EQY on the final state; never required
eqy_ok = None; eqy_detail = "skipped"
try:
    steps = O.step_dirs(os.path.join(ROOT, "runs", TAG)); last = [d for _, _, d in steps if os.path.exists(os.path.join(d, "state_out.json"))]
    if last and shutil.which("nix-shell"):
        out = os.path.join(ROOT, "runs", TAG, "eqy"); os.makedirs(out, exist_ok=True)
        cmd = f"cd {ROOT}/runs/{TAG} && python3 -m librelane.steps run --id Yosys.EQY --config resolved.json --state-in {last[-1]}/state_out.json --output {out}"
        r = subprocess.run(["nix-shell", os.path.expanduser("~/librelane/shell.nix"), "--run", cmd], capture_output=True, text=True, timeout=1800)
        txt = r.stdout + r.stderr; eqy_ok = ("DONE (PASS" in txt) or (r.returncode == 0 and "FAIL" not in txt); eqy_detail = f"exit {r.returncode}; " + txt[-600:]
except Exception as e: eqy_detail = f"eqy attempt failed: {e}"
results["f_eqy_experimental"] = {"ok": eqy_ok, "detail": eqy_detail, "required": False}; O.log(f"VERIFY f_eqy_experimental: {eqy_ok} {eqy_detail[:200]}")

# (g) rebuild dashboard
rc = make("dashboard"); check("g_dashboard", rc == 0 and os.path.exists(os.path.join(ROOT, "factory", "dashboard", "site", "index.html")), f"exit {rc}")

results["_tag"] = TAG; results["_time"] = O.now()
json.dump(results, open(os.path.join(STATE, "verify.json"), "w"), indent=2)
req_fail = [k for k, v in results.items() if isinstance(v, dict) and v.get("required", True) and v.get("ok") is False]
print("verify-factory:", "PASS" if not req_fail else f"FAIL {req_fail}")
sys.exit(0 if not req_fail else 1)
