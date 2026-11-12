#!/usr/bin/env python3
"""Build factory/dashboard/site/index.html from factory/state/*.json."""
import base64, csv, json, os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STATE = os.path.join(ROOT, "factory", "state"); HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.join(HERE, "site"); IMG = os.path.join(SITE, "img"); os.makedirs(IMG, exist_ok=True)
def jload(p, d=None):
    try: return json.load(open(p))
    except Exception: return d
data = jload(os.path.join(STATE, "pipeline.json"), {"stations": [], "metrics": {}, "corners": {}, "status": "unknown", "run_tag": "(no run yet)"})
data["gates"] = jload(os.path.join(STATE, "gates.json"), {})
data["decisions"] = jload(os.path.join(STATE, "decisions.json"), [])
data["needs_human"] = []
nh = os.path.join(ROOT, "NEEDS_HUMAN.md")
if os.path.exists(nh): data["needs_human"] = [l.rstrip("\n") for l in open(nh) if l.startswith("- ")]
sweep_csv = os.path.join(STATE, "sweep.csv"); data["sweep"] = []
if os.path.exists(sweep_csv): data["sweep"] = list(csv.DictReader(open(sweep_csv)))
data["sweep_plots"] = {}
for name in ("area", "wns", "power"):
    p = os.path.join(STATE, f"sweep_{name}.png")
    if os.path.exists(p): data["sweep_plots"][name] = "data:image/png;base64," + base64.b64encode(open(p, "rb").read()).decode()
for st in data.get("stations", []):
    img = st.get("image")
    if img and os.path.exists(os.path.join(ROOT, img)):
        dst = f"{st['id']}.png"; shutil.copy(os.path.join(ROOT, img), os.path.join(IMG, dst)); st["image_url"] = f"img/{dst}"
    for e in st.get("steps", []):
        lp = e.get("log")
        if lp and os.path.exists(os.path.join(ROOT, lp)):
            os.makedirs(os.path.join(SITE, "logs"), exist_ok=True)
            dst = os.path.join(SITE, "logs", os.path.basename(e["dir"]) + ".log")
            with open(os.path.join(ROOT, lp), errors="replace") as f, open(dst, "w") as g: g.write(f.read()[-200000:])
            e["log_url"] = f"logs/{os.path.basename(e['dir'])}.log"
try:
    start = float(open(os.path.join(STATE, "start_time")).read().strip()); import time; data["elapsed_s"] = int(time.time() - start)
except Exception: data["elapsed_s"] = None
tpl = open(os.path.join(HERE, "template.html")).read()
# Browsers' JSON.parse rejects the bare NaN/Infinity tokens that json.dumps emits for non-finite floats
# (e.g. timing__setup_r2r__ws = inf when a corner has no reg-to-reg path), so stringify them for the page.
def finite(o):
    if isinstance(o, float) and o != o: return "nan"
    if isinstance(o, float) and o in (float("inf"), float("-inf")): return "inf" if o > 0 else "-inf"
    if isinstance(o, dict): return {k: finite(v) for k, v in o.items()}
    if isinstance(o, list): return [finite(v) for v in o]
    return o
data = finite(data)
payload = json.dumps(data, allow_nan=False)
html = tpl.replace("__DATA_JSON__", payload.replace("</", "<\\/"))
open(os.path.join(SITE, "index.html"), "w").write(html)
open(os.path.join(SITE, "pipeline.json"), "w").write(payload)
print("wrote", os.path.join(SITE, "index.html"), "stations:", len(data.get("stations", [])), "gates:", len(data["gates"]), "decisions:", len(data["decisions"]))
