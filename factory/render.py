#!/usr/bin/env python3
"""Render layout PNGs for the dashboard. render_run(run_dir, design, stations) -> {station_id: relpath_png}"""
import glob, json, os, shutil, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIBRELANE_DIR = os.environ.get("LIBRELANE_DIR", os.path.expanduser("~/librelane"))
NIX = ["nix-shell", os.path.join(LIBRELANE_DIR, "shell.nix"), "--run"]
RENDER_STATIONS = ["floorplan", "pdn", "gpl", "dpl", "cts", "drt", "fill", "gds"]

def sh(cmd, timeout=600):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

def render_state(run_dir, step_dir, out_dir):
    """Method 1: re-run KLayout.Render on a step's state_out.json inside the Nix shell."""
    os.makedirs(out_dir, exist_ok=True)
    cfg = os.path.join(run_dir, "resolved.json")
    cmd = f"cd {run_dir} && python3 -m librelane.steps run --id KLayout.Render --config {cfg} --state-in {step_dir}/state_out.json --output {out_dir}"
    r = sh(NIX + [cmd], timeout=900)
    pngs = glob.glob(os.path.join(out_dir, "**", "*.png"), recursive=True)
    if r.returncode == 0 and pngs: return pngs[0]
    open(os.path.join(out_dir, "render.err"), "w").write(r.stdout[-3000:] + r.stderr[-3000:])
    return None

def render_gds(gds, png):
    """Method 3: gdstk -> SVG -> PNG."""
    try:
        import gdstk
        lib = gdstk.read_gds(gds); tops = lib.top_level()
        if not tops: return None
        svg = png.replace(".png", ".svg"); tops[0].write_svg(svg, pad="5%")
        if shutil.which("rsvg-convert"):
            r = sh(["rsvg-convert", "--unlimited", "-w", "1200", svg, "-o", png])
            if r.returncode == 0: return png
        import cairosvg; cairosvg.svg2png(url=svg, write_to=png, output_width=1200); return png
    except Exception as e:
        sys.stderr.write(f"gdstk render failed: {e}\n"); return None

def render_run(run_dir, design, stations):
    out = {}; rdir = os.path.join(run_dir, "renders"); os.makedirs(rdir, exist_ok=True)
    for sid in RENDER_STATIONS:
        st = stations.get(sid) if isinstance(stations, dict) else None
        if not st or not st["steps"]: continue
        last = [e for e in st["steps"] if e["ok"]]
        if not last: continue
        step_dir = os.path.join(ROOT, last[-1]["dir"])
        png = render_state(run_dir, step_dir, os.path.join(rdir, sid))
        if not png and sid == "gds":
            flow_png = glob.glob(os.path.join(run_dir, "final", "render", "*.png"))
            if flow_png: png = flow_png[0]
            else:
                g = glob.glob(os.path.join(run_dir, "final", "gds", "*.gds"))
                if g: png = render_gds(g[0], os.path.join(rdir, "gds", f"{design}.png"))
        if png: out[sid] = os.path.relpath(png, ROOT)
    # always try to have at least the final image
    if "gds" not in out:
        g = glob.glob(os.path.join(run_dir, "final", "gds", "*.gds"))
        if g:
            os.makedirs(os.path.join(rdir, "gds"), exist_ok=True)
            png = render_gds(g[0], os.path.join(rdir, "gds", f"{design}.png"))
            if png: out["gds"] = os.path.relpath(png, ROOT)
    json.dump(out, open(os.path.join(rdir, "index.json"), "w"), indent=2)
    return out

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument("--run-dir", required=True); ap.add_argument("--design", default="mac_int8"); a = ap.parse_args()
    sys.path.insert(0, os.path.join(ROOT, "factory")); import orchestrate as O
    p = O.ingest(os.path.abspath(a.run_dir), a.design, render=False)
    st = {s["id"]: s for s in p["stations"]}
    imgs = render_run(os.path.abspath(a.run_dir), a.design, st)
    print(json.dumps(imgs, indent=2)); sys.exit(0 if imgs else 1)
