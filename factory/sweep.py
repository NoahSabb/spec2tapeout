#!/usr/bin/env python3
"""WIDTH x CLOCK_PERIOD sweep of mac_int8 -> factory/state/sweep.csv, sweep.json, sweep_{area,wns,power}.png"""
import argparse, copy, csv, json, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "factory", "state"); sys.path.insert(0, os.path.join(ROOT, "factory"))
import orchestrate as O
DIE = {2: "0 0 110 110", 4: "0 0 140 140", 8: "0 0 200 200"}   # um; always >= one PDN strap pitch + offset
COLS = ["tag", "width", "acc_width", "clock_period_ns", "status", "exit_code", "runtime_s", "instance_count", "instance_area_um2", "utilization",
        "setup_ws_overall", "setup_ws_ss", "setup_ws_tt", "hold_ws_overall", "hold_ws_ff", "setup_vio", "hold_vio",
        "route_drc", "magic_drc", "klayout_drc", "lvs_errors", "antenna_pins", "power_total_W", "fmax_est_MHz"]

def run_one(base, width, period):
    tag = f"sweep-w{width}-p{period}"; acc = 2 * width + 16
    cfg = copy.deepcopy(base)
    cfg.update({"SYNTH_PARAMETERS": [f"WIDTH={width}", f"ACC_WIDTH={acc}"], "CLOCK_PERIOD": period,
                "FP_SIZING": "absolute", "DIE_AREA": DIE[width]})
    cfg.pop("FP_CORE_UTIL", None)
    d = os.path.join(ROOT, "flow", "sweep", tag); os.makedirs(os.path.join(d, "src"), exist_ok=True)
    subprocess.call(f"cp {ROOT}/rtl/*.v {d}/src/", shell=True)
    cpath = os.path.join(d, "config.json"); json.dump(cfg, open(cpath, "w"), indent=2)
    t0 = time.time()
    os.makedirs(os.path.join(ROOT, "runs", tag), exist_ok=True)   # librelane --force-run-dir requires an existing dir
    rc = subprocess.call(["make", "harden", f"TAG={tag}", f"CONFIG={os.path.relpath(cpath, ROOT)}", "DESIGN=mac_int8"], cwd=ROOT)
    run_dir = os.path.join(ROOT, "runs", tag); m, _ = O.final_metrics(run_dir)
    g = lambda k: m.get(k)
    ss, tt_, ff = g("timing__setup__ws__corner:max_ss_100C_1v60"), g("timing__setup__ws__corner:nom_tt_025C_1v80"), g("timing__hold__ws__corner:min_ff_n40C_1v95")
    fmax = None
    try:
        if ss is not None: fmax = round(1000.0 / (period - float(ss)), 1)
    except Exception: pass
    row = dict(zip(COLS, [tag, width, acc, period, "pass" if rc == 0 else ("fail" if m else "crash"), rc, round(time.time() - t0, 1),
                          g("design__instance__count"), g("design__instance__area"), g("design__instance__utilization"),
                          g("timing__setup__ws"), ss, tt_, g("timing__hold__ws"), ff, g("timing__setup_vio__count"), g("timing__hold_vio__count"),
                          g("route__drc_errors"), g("magic__drc_error__count"), g("klayout__drc_error__count"), g("design__lvs_error__count"),
                          g("antenna__violating__pins"), g("power__total"), fmax]))
    O.log(f"SWEEP {tag}: {row}")
    return row

def plot(rows):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    periods = sorted({r["clock_period_ns"] for r in rows}); widths = sorted({r["width"] for r in rows})
    def series(key):
        return {p: [(r["width"], r[key]) for r in rows if r["clock_period_ns"] == p and r[key] is not None] for p in periods}
    for key, fname, ylabel in [("instance_area_um2", "sweep_area.png", "instance area (um^2)"), ("setup_ws_ss", "sweep_wns.png", "setup worst slack @ max_ss_100C_1v60 (ns)"), ("power_total_W", "sweep_power.png", "total power (W)")]:
        fig, ax = plt.subplots(figsize=(6, 4)); s = series(key)
        for p, pts in s.items():
            if pts: ax.plot([x for x, _ in pts], [y for _, y in pts], marker="o", label=f"CLOCK_PERIOD={p} ns")
        if key == "setup_ws_ss": ax.axhline(0, color="k", lw=0.8, ls="--")
        ax.set_xlabel("WIDTH (bits)"); ax.set_ylabel(ylabel); ax.set_xticks(widths); ax.grid(alpha=0.3); ax.legend(fontsize=8); fig.tight_layout()
        fig.savefig(os.path.join(STATE, fname), dpi=120); plt.close(fig)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--widths", default="2,4,8"); ap.add_argument("--periods", default="5,10,20")
    ap.add_argument("--base", default=os.path.join(ROOT, "flow", "mac_int8", "config.json")); a = ap.parse_args()
    base = json.load(open(a.base)); rows = []
    csv_path = os.path.join(STATE, "sweep.csv")
    if os.path.exists(csv_path):
        rows = [r for r in csv.DictReader(open(csv_path))]
        for r in rows:
            for k in ("width", "acc_width", "exit_code"): r[k] = int(r[k])
            for k in ("clock_period_ns",): r[k] = float(r[k])
            for k in ("instance_count", "instance_area_um2", "utilization", "setup_ws_overall", "setup_ws_ss", "setup_ws_tt", "hold_ws_overall", "hold_ws_ff",
                      "setup_vio", "hold_vio", "route_drc", "magic_drc", "klayout_drc", "lvs_errors", "antenna_pins", "power_total_W", "fmax_est_MHz", "runtime_s"):
                try: r[k] = float(r[k]) if r[k] not in ("", "None", None) else None
                except Exception: r[k] = None
    done = {r["tag"] for r in rows}
    for w in [int(x) for x in a.widths.split(",")]:
        for p in [float(x) for x in a.periods.split(",")]:
            if f"sweep-w{w}-p{p:g}" in done: continue
            rows.append(run_one(base, w, p if p != int(p) else int(p)))
            with open(csv_path, "w", newline="") as f:
                wr = csv.DictWriter(f, fieldnames=COLS); wr.writeheader(); wr.writerows(rows)
    json.dump(rows, open(os.path.join(STATE, "sweep.json"), "w"), indent=2)
    try: plot(rows)
    except Exception as e: O.log(f"SWEEP plot failed: {e}")
    ok = sum(1 for r in rows if r["status"] != "crash")
    print(f"sweep rows={len(rows)} with_metrics={ok}")
    sys.exit(0 if ok >= 6 else 1)
