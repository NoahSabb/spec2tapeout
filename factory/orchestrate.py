#!/usr/bin/env python3
"""spec2tapeout orchestrator.
  ingest  --run-dir runs/<tag> --design mac_int8          -> factory/state/pipeline.json (+ renders)
  closure --config flow/mac_int8/config.json --design mac_int8 --tag <tag> --max-attempts 4
"""
import argparse, copy, datetime, glob, json, os, re, shutil, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "factory", "state")
os.makedirs(STATE, exist_ok=True)

def now(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def ts(path): return datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
def log(msg):
    with open(os.path.join(ROOT, "logs", "overnight.md"), "a") as f: f.write(f"{now()} {msg}\n")
    print(msg)
def jload(p, default=None):
    try: return json.load(open(p))
    except Exception: return default

# ---- stations (mirror of plan section 5.3) ---------------------------------------------------
STATIONS = [
  ("lint", "Lint", "Verilator", ["verilator-lint", "checker-lint"],
   "Verilator parses the RTL and flags latches, multiply-driven nets, width mismatches and timing constructs before any synthesis happens.",
   ["RTL (.v)"], ["lint log, metrics"]),
  ("synth", "Synthesis", "Yosys 0.62 + ABC", ["yosys-jsonheader", "yosys-synthesis", "checker-yosys", "checker-netlistassign"],
   "Yosys turns the RTL into generic logic, flattens, optimizes, maps flip-flops to sky130 cells (dfflibmap) and lets ABC map the combinational logic against the liberty timing with the chosen SYNTH_STRATEGY.",
   ["RTL (.v)", "liberty (.lib)"], ["gate netlist (.nl.v)", "stat.rpt / stat.json"]),
  ("sta_pre", "Pre-PnR STA", "OpenSTA", ["openroad-checksdcfiles", "openroad-staprepnr"],
   "OpenSTA times the mapped netlist with ideal clocks and no wires: a first, optimistic look at whether the clock period is plausible.",
   ["netlist", "SDC"], ["summary.rpt, per-corner reports"]),
  ("floorplan", "Floorplan", "OpenROAD ifp", ["openroad-floorplan", "openroad-dumprcvalues", "odb-setpowerconnections", "odb-checkmacroantenna", "odb-manualmacroplacement", "openroad-cutrows"],
   "The die and core outlines are created (relative sizing from FP_CORE_UTIL, or absolute from DIE_AREA) and standard-cell rows are laid down on the unithd site grid.",
   ["netlist"], ["ODB, DEF"]),
  ("tap", "Tap/endcap", "OpenROAD tap", ["openroad-tapendcapinsertion"],
   "Well-tap cells are inserted every 13 um to tie wells to the rails (latch-up prevention) and end-cap cells close every row.",
   ["ODB"], ["ODB"]),
  ("pdn", "PDN", "OpenROAD pdngen", ["odb-addpdnobstructions", "openroad-generatepdn", "odb-removepdnobstructions"],
   "The power distribution network is built: met1 rails that follow the cell rows plus met4 straps every PDN_VPITCH um, connected by via stacks.",
   ["ODB"], ["ODB, DEF"]),
  ("io", "I/O placement", "OpenROAD ppl", ["odb-addroutingobstructions", "openroad-globalplacementskipio", "openroad-ioplacement", "odb-customioplacement", "odb-applydeftemplate"],
   "Top-level pins are placed on the die edge (met2 vertical / met3 horizontal), or copied from a template DEF on Tiny Tapeout.",
   ["ODB"], ["DEF"]),
  ("gpl", "Global placement", "OpenROAD gpl (RePlAce)", ["openroad-globalplacement", "odb-writeverilogheader", "checker-powergridviolations", "openroad-stamidpnr-1"],
   "Cells are spread across the core by an electrostatic analogy (cells repel where density is high, wires pull them together) until overflow is below 10 percent.",
   ["ODB"], ["ODB, .vh"]),
  ("repair", "Repair design", "OpenROAD rsz", ["openroad-repairdesignpostgpl", "odb-manualglobalplacement"],
   "The resizer buffers input/output ports and fixes max-slew, max-capacitance and max-fanout violations with a 20 percent margin, sizing gates as needed.",
   ["ODB"], ["ODB"]),
  ("dpl", "Detailed placement", "OpenROAD dpl", ["openroad-detailedplacement"],
   "Every cell is snapped to a legal row site with minimum displacement; check_placement must return 0.",
   ["ODB"], ["ODB"]),
  ("cts", "CTS", "TritonCTS", ["openroad-cts", "openroad-stamidpnr-2"],
   "A clock tree of clkbuf cells is synthesized from the clock pin to every flop; from here on the clock is 'propagated' and real skew exists, which is why hold violations first appear now.",
   ["ODB"], ["ODB, cts.rpt"]),
  ("rsz_cts", "Post-CTS timing repair", "OpenROAD rsz", ["openroad-resizertimingpostcts", "openroad-stamidpnr-3"],
   "Setup is repaired first (sizing, buffering, cloning), then hold is repaired with delay buffers that are refused if they would break setup; margins 0.05 ns setup / 0.1 ns hold.",
   ["ODB"], ["ODB"]),
  ("grt", "Global routing", "OpenROAD grt (FastRoute)", ["openroad-globalrouting", "openroad-checkantennas-1", "openroad-repairdesignpostgrt", "odb-diodesonports", "odb-heuristicdiodeinsertion"],
   "Nets are assigned to coarse routing cells and layers with capacity derated by GRT_ADJUSTMENT; any remaining overflow means congestion.",
   ["ODB"], ["route guides, antenna report"]),
  ("antenna", "Antenna repair", "OpenROAD repair_antennas", ["openroad-repairantennas", "openroad-resizertimingpostgrt", "openroad-stamidpnr-4"],
   "Long wires attached to gates can collect charge during plasma etch and damage the gate oxide; antenna diodes (diode_2) are inserted on violating nets.",
   ["ODB"], ["ODB"]),
  ("drt", "Detailed routing", "TritonRoute", ["openroad-detailedrouting", "odb-removeroutingobstructions", "openroad-checkantennas-2", "checker-trdrc"],
   "Real wires and vias are drawn on the tracks with a built-in DRC engine; violations should fall to zero well before the 64th iteration.",
   ["route guides"], ["routed DEF/ODB, route__drc_errors"]),
  ("postroute", "Post-route checks", "OpenDB", ["odb-reportdisconnectedpins", "checker-disconnectedpins", "odb-reportwirelength", "checker-wirelength"],
   "Every pin must be connected and no wire may exceed the PDK's length threshold.",
   ["ODB"], ["reports"]),
  ("fill", "Fill", "OpenROAD filler_placement", ["openroad-fillinsertion", "odb-cellfrequencytables"],
   "Gaps between cells are filled with fill and decap cells so power rails and wells are continuous and metal density rules are met.",
   ["ODB"], ["ODB, DEF"]),
  ("rcx", "RCX", "OpenRCX", ["openroad-rcx"],
   "Parasitic resistance and capacitance of every routed wire are extracted for the nominal, minimum and maximum interconnect corners into SPEF files.",
   ["DEF"], ["SPEF x3"]),
  ("sta_post", "Signoff STA", "OpenSTA", ["openroad-stapostpnr"],
   "The only timing that counts: nine corners (3 interconnect x 3 PVT) with real parasitics; setup is judged at max_ss_100C_1v60, hold at min_ff_n40C_1v95.",
   ["netlist, SPEF, SDC"], ["summary.rpt, max/min/checks/violator_list/clock reports, SDF, LIB"]),
  ("ir", "IR drop", "OpenROAD psm", ["openroad-irdropreport"],
   "A static solve of the power grid resistance with per-cell currents gives the worst voltage droop; rule of thumb is a few percent of 1.8 V.",
   ["ODB, SPEF"], ["irdrop report"]),
  ("gds", "Stream-out + XOR", "Magic + KLayout", ["magic-streamout", "klayout-streamout", "klayout-render", "magic-writelef", "odb-checkdesignantennaproperties", "klayout-xor", "checker-xor"],
   "Two independent tools write the GDS from the same DEF and the two results are XOR-compared; any difference is a tool disagreement to investigate.",
   ["DEF, cell GDS"], ["final GDS, LEF, PNG render"]),
  ("signoff", "DRC + LVS + signoff", "Magic, KLayout, Netgen", ["magic-drc", "klayout-drc", "checker-magicdrc", "checker-klayoutdrc", "magic-spiceextraction", "checker-illegaloverlap", "netgen-lvs", "checker-lvs", "yosys-eqy", "checker-setupviolations", "checker-holdviolations", "checker-maxslewviolations", "checker-maxcapviolations", "misc-reportmanufacturability"],
   "Two DRC decks check the manufacturing rules, Magic extracts a transistor netlist from the layout and Netgen proves it matches the gate netlist (LVS); then every deferred checker reports.",
   ["GDS, powered netlist"], ["drc reports, netgen-lvs.log"]),
]
RENDER_STATIONS = ["floorplan", "pdn", "gpl", "dpl", "cts", "drt", "fill", "gds"]

KEY_METRICS = ["timing__setup__ws", "timing__setup__wns", "timing__setup__tns", "timing__setup_vio__count",
  "timing__hold__ws", "timing__hold__wns", "timing__hold__tns", "timing__hold_vio__count",
  "design__max_slew_violation__count", "design__max_cap_violation__count", "design__max_fanout_violation__count",
  "clock__skew__worst_setup", "clock__skew__worst_hold", "timing__unannotated_net_filtered__count",
  "design__instance__count", "design__instance__area", "design__instance__utilization", "design__die__bbox", "design__core__bbox",
  "route__drc_errors", "route__wirelength__max", "route__antenna_violation__count", "antenna__violating__pins", "antenna__violating__nets",
  "magic__drc_error__count", "klayout__drc_error__count", "magic__illegal_overlap__count", "design__xor_difference__count",
  "design__lvs_error__count", "design__lvs_unmatched_net__count", "design__lvs_unmatched_device__count",
  "design__power_grid_violation__count", "design__critical_disconnected_pin__count",
  "design__lint_error__count", "design__inferred_latch__count", "synthesis__check_error__count", "design__instance_unmapped__count",
  "power__total", "power__internal__total", "power__switching__total", "power__leakage__total",
  "ir__drop__avg", "ir__drop__worst", "ir__voltage__worst"]

def step_dirs(run_dir):
    out = []
    for d in sorted(glob.glob(os.path.join(run_dir, "[0-9]*-*"))):
        m = re.match(r"(\d+)-(.+)$", os.path.basename(d))
        if m and os.path.isdir(d): out.append((int(m.group(1)), m.group(2), d))
    return out

def station_for(slug, seen):
    """Match a step-dir slug to a station; repeated steps (stamidpnr, checkantennas) are disambiguated by occurrence order."""
    base = re.sub(r"-\d+$", "", slug)
    seen[base] = seen.get(base, 0) + 1
    for sid, _, _, prefixes, *_ in STATIONS:
        for p in prefixes:
            pm = re.match(r"(.+?)-(\d+)$", p)
            if pm and base == pm.group(1):
                if seen[base] == int(pm.group(2)): return sid
            elif base.startswith(p): return sid
    return None

def final_metrics(run_dir):
    m = jload(os.path.join(run_dir, "final", "metrics.json"))
    if m: return m, "final/metrics.json"
    last = None
    for _, _, d in step_dirs(run_dir):
        so = os.path.join(d, "state_out.json")
        if os.path.exists(so): last = so
    if last:
        s = jload(last, {}); return s.get("metrics", {}), os.path.relpath(last, run_dir)
    return {}, None

def corner_table(metrics):
    corners = {}
    for k, v in metrics.items():
        if "__corner:" in k:
            name, corner = k.split("__corner:")
            corners.setdefault(corner, {})[name] = v
    return corners

def ingest(run_dir, design, render=True):
    run_dir = os.path.abspath(run_dir); tag = os.path.basename(run_dir)
    metrics, src = final_metrics(run_dir)
    err = open(os.path.join(run_dir, "error.log")).read() if os.path.exists(os.path.join(run_dir, "error.log")) else ""
    stations = {sid: {"id": sid, "name": name, "tool": tool, "status": "pending", "steps": [], "started": None, "ended": None,
                      "duration_s": 0.0, "log": None, "dir": None, "metrics": {}, "image": None, "explain": expl, "inputs": ins, "outputs": outs}
                for sid, name, tool, _, expl, ins, outs in STATIONS}
    seen = {}; prev_metrics = {}; flow_failed_at = None
    for n, slug, d in step_dirs(run_dir):
        sid = station_for(slug, seen)
        if not sid: continue
        st = stations[sid]
        si, so = os.path.join(d, "state_in.json"), os.path.join(d, "state_out.json")
        logs = glob.glob(os.path.join(d, "*.log"))
        entry = {"n": n, "slug": slug, "dir": os.path.relpath(d, ROOT), "log": os.path.relpath(logs[0], ROOT) if logs else None,
                 "started": ts(si) if os.path.exists(si) else None, "ended": ts(so) if os.path.exists(so) else None,
                 "ok": os.path.exists(so) or not os.path.exists(si)}   # a dir with neither file is a skipped (RUN_*=false) step
        if os.path.exists(so):
            mo = jload(so, {}).get("metrics", {})
            delta = {k: v for k, v in mo.items() if prev_metrics.get(k) != v and "__corner:" not in k}
            entry["metrics_delta"] = delta; prev_metrics = mo
            st["metrics"].update({k: v for k, v in delta.items() if k in KEY_METRICS})
        elif os.path.exists(si):
            flow_failed_at = flow_failed_at or sid
        st["steps"].append(entry); st["dir"] = st["dir"] or entry["dir"]; st["log"] = entry["log"] or st["log"]
        st["started"] = st["started"] or entry["started"]; st["ended"] = entry["ended"] or st["ended"]
        if entry["started"] and entry["ended"]:
            st["duration_s"] += (datetime.datetime.fromisoformat(entry["ended"].replace("Z", "+00:00")) - datetime.datetime.fromisoformat(entry["started"].replace("Z", "+00:00"))).total_seconds()
    for sid, st in stations.items():
        if st["steps"]:
            st["status"] = "pass" if all(e["ok"] for e in st["steps"]) else "fail"
    gates = jload(os.path.join(STATE, "gates.json"), {})
    harden_gate = gates.get(f"harden-{tag}")
    run_ok = bool(harden_gate and harden_gate["exit_code"] == 0)
    # deferred checker failures: the step dir exists with state_out but the run exited nonzero -> mark the responsible station fail
    def bad(k, thr=0):
        v = metrics.get(k); return v is not None and float(v) > thr
    if not run_ok:
        if bad("timing__setup_vio__count") or bad("timing__hold_vio__count") or (metrics.get("timing__setup__ws") is not None and float(metrics["timing__setup__ws"]) < 0) or (metrics.get("timing__hold__ws") is not None and float(metrics["timing__hold__ws"]) < 0):
            stations["sta_post"]["status"] = "fail"
        if bad("route__drc_errors"): stations["drt"]["status"] = "fail"
        if bad("magic__drc_error__count") or bad("klayout__drc_error__count") or bad("design__lvs_error__count") or bad("magic__illegal_overlap__count"): stations["signoff"]["status"] = "fail"
        if bad("design__xor_difference__count"): stations["gds"]["status"] = "fail"
        if bad("design__power_grid_violation__count"): stations["gpl"]["status"] = "fail"
        if bad("antenna__violating__pins"): stations["antenna"]["status"] = "warn" if stations["antenna"]["status"] == "pass" else stations["antenna"]["status"]
    if render:
        try:
            sys.path.insert(0, os.path.join(ROOT, "factory")); import render as R
            imgs = R.render_run(run_dir, design, stations)
            for sid, p in imgs.items(): stations[sid]["image"] = p
        except Exception as e:
            log(f"RENDER failed for {tag}: {e}")
    pipeline = {"run_tag": tag, "design": design, "generated_at": now(), "status": "pass" if run_ok else ("fail" if harden_gate else "unknown"),
                "run_dir": os.path.relpath(run_dir, ROOT), "metrics_source": src, "metrics": {k: metrics.get(k) for k in KEY_METRICS if k in metrics},
                "corners": corner_table(metrics), "stations": [stations[s[0]] for s in STATIONS], "flow_failed_at": flow_failed_at,
                "error_log_tail": err[-4000:], "gates": gates, "decisions": jload(os.path.join(STATE, "decisions.json"), []),
                "sweep": jload(os.path.join(STATE, "sweep.json"), None), "needs_human": read_needs_human(),
                "gds": first(os.path.join(run_dir, "final", "gds", "*.gds")), "gds_bytes": size(first(os.path.join(run_dir, "final", "gds", "*.gds")))}
    json.dump(pipeline, open(os.path.join(STATE, "pipeline.json"), "w"), indent=2)
    open(os.path.join(STATE, "latest_run.txt"), "w").write(tag)
    log(f"INGEST {tag}: status={pipeline['status']} setup_ws={metrics.get('timing__setup__ws')} hold_ws={metrics.get('timing__hold__ws')} drc={metrics.get('route__drc_errors')} lvs={metrics.get('design__lvs_error__count')} cells={metrics.get('design__instance__count')} source={src}")
    return pipeline

def first(pattern):
    g = sorted(glob.glob(pattern)); return os.path.relpath(g[0], ROOT) if g else None
def size(p):
    return os.path.getsize(os.path.join(ROOT, p)) if p and os.path.exists(os.path.join(ROOT, p)) else 0
def read_needs_human():
    p = os.path.join(ROOT, "NEEDS_HUMAN.md")
    if not os.path.exists(p): return []
    return [l.strip("- ").strip() for l in open(p) if l.startswith("- ")]

# ---- closure loop ---------------------------------------------------------------------------
def classify(metrics, run_ok, err):
    s = []
    if run_ok: return s
    f = lambda k: float(metrics.get(k, 0) or 0)
    if not metrics or "design__instance__count" not in metrics or f("design__lint_error__count") > 0 or f("design__instance_unmapped__count") > 0 or f("synthesis__check_error__count") > 0:
        s.append("immediate_error")   # lint/synthesis StepError: an RTL problem, not a config knob
    if f("design__lvs_error__count") > 0: s.append("lvs")
    if f("design__power_grid_violation__count") > 0: s.append("pdn")
    if f("route__drc_errors") > 0 or re.search(r"GRT-0\d+.*overflow|congestion", err, re.I): s.append("congestion")
    if f("magic__drc_error__count") > 0 or f("klayout__drc_error__count") > 0: s.append("drc")
    if f("design__xor_difference__count") > 0: s.append("xor")
    if (metrics.get("timing__setup__ws") is not None and float(metrics["timing__setup__ws"]) < 0) or f("timing__setup_vio__count") > 0: s.append("setup")
    if (metrics.get("timing__hold__ws") is not None and float(metrics["timing__hold__ws"]) < 0) or f("timing__hold_vio__count") > 0: s.append("hold")
    if f("antenna__violating__pins") > 0: s.append("antenna")
    if re.search(r"GPL-0302", err): s.append("gpl_density")
    if not s: s.append("unknown")
    return s

PRIORITY = ["immediate_error", "lvs", "pdn", "gpl_density", "congestion", "drc", "xor", "setup", "hold", "antenna", "unknown"]

def rules(symptom, k, cfg):
    """Return (description, changes dict) for the k-th attempt at a symptom, or None when out of rules."""
    cp = float(cfg.get("CLOCK_PERIOD", 10)); util = float(cfg.get("FP_CORE_UTIL", 40)); dens = float(cfg.get("PL_TARGET_DENSITY_PCT", util + 10))
    R = {
      "setup": [
        ("synthesis strategy DELAY 1 (ABC delay-oriented mapping)", {"SYNTH_STRATEGY": "DELAY 1"}),
        ("lower utilization by 10 (more room for resizer, shorter wires)", {"FP_CORE_UTIL": max(25, util - 10), "PL_TARGET_DENSITY_PCT": max(35, util - 10) + 10}),
        ("relax CLOCK_PERIOD by 10 % (cap 20 ns standalone)", {"CLOCK_PERIOD": round(min(20.0, cp * 1.1), 2)}),
        ("synthesis strategy DELAY 4 (ORFS delay script) + CSA adders", {"SYNTH_STRATEGY": "DELAY 4", "SYNTH_ADDER_TYPE": "CSA"}),
      ] + [("relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone)", {"CLOCK_PERIOD": round(min(20.0, cp * 1.1), 2)})] * 6,
      "congestion": [
        ("lower PL_TARGET_DENSITY_PCT by 10", {"PL_TARGET_DENSITY_PCT": max(35, dens - 10)}),
        ("raise GRT_ADJUSTMENT by 0.1 (more global-routing headroom)", {"GRT_ADJUSTMENT": min(0.6, float(cfg.get("GRT_ADJUSTMENT", 0.3)) + 0.1)}),
        ("lower FP_CORE_UTIL by 10", {"FP_CORE_UTIL": max(25, util - 10), "PL_TARGET_DENSITY_PCT": max(35, util - 10) + 10}),
      ],
      "gpl_density": [
        ("raise PL_TARGET_DENSITY_PCT by 10 (GPL-0302: target density too low for the cell area)", {"PL_TARGET_DENSITY_PCT": min(80, dens + 10)}),
        ("switch to absolute floorplan 200x200 um", {"FP_SIZING": "absolute", "DIE_AREA": "0 0 200 200"}),
      ],
      "hold": [
        ("raise resizer hold margins (over-fix hold)", {"PL_RESIZER_HOLD_SLACK_MARGIN": float(cfg.get("PL_RESIZER_HOLD_SLACK_MARGIN", 0.1)) + 0.1, "GRT_RESIZER_HOLD_SLACK_MARGIN": float(cfg.get("GRT_RESIZER_HOLD_SLACK_MARGIN", 0.05)) + 0.05}),
        ("tighter CTS clustering (less skew)", {"CTS_SINK_CLUSTERING_MAX_DIAMETER": 30, "CTS_SINK_CLUSTERING_SIZE": 16}),
      ],
      "antenna": [
        ("more antenna repair iterations and margin", {"GRT_ANTENNA_REPAIR_ITERS": 6, "GRT_ANTENNA_REPAIR_MARGIN": 20, "DRT_ANTENNA_REPAIR_ITERS": 6}),
        ("heuristic diode insertion on long nets", {"RUN_HEURISTIC_DIODE_INSERTION": True}),
        ("diodes on input ports", {"DIODE_ON_PORTS": "in"}),
      ],
      "pdn": [
        ("denser PDN straps", {"PDN_VPITCH": 25.0}),
        ("absolute floorplan floor so straps fit", {"FP_SIZING": "absolute", "DIE_AREA": "0 0 150 150"}),
      ],
      "drc": [
        ("lower placement density by 10 (DRC usually from congestion)", {"PL_TARGET_DENSITY_PCT": max(35, dens - 10)}),
      ],
    }
    lst = R.get(symptom, [])
    return lst[k] if k < len(lst) else None

def already_applied(changes, cfg):
    """True when every change is already in effect."""
    return all(cfg.get(k) == v for k, v in changes.items())

def regressed(d):
    """A decision whose 'after' setup slack is clearly worse than 'before' (the rule hurt; never retry it in this series)."""
    try: return float(d["after"]["timing__setup__ws"]) < float(d["before"]["timing__setup__ws"]) - 0.5
    except Exception: return False

def closure(config_path, design, tag, max_attempts, resume=False, from_attempt=None):
    base = jload(config_path); cfg = copy.deepcopy(base); counts = {}
    decisions = jload(os.path.join(STATE, "decisions.json"), [])
    best = None; best_ws = None; first = 1; skip = []
    gates = jload(os.path.join(STATE, "gates.json"), {})
    def consider(atag, rc, metrics):
        nonlocal best, best_ws
        ws = metrics.get("timing__setup__ws")
        if rc == 0: best = atag
        elif best is None or (ws is not None and (best_ws is None or float(ws) > best_ws)): best, best_ws = atag, (float(ws) if ws is not None else best_ws)
    if resume:
        mine = [d for d in decisions if d.get("series") == tag]
        skip = [{k: v[1] for k, v in d["changes"].items()} for d in mine if regressed(d)]
        for d in mine:   # the best run so far across the whole series (passing run, else least negative setup slack)
            t = d["tag_before"]; g = gates.get(f"harden-{t}")
            if g: consider(t, g["exit_code"], final_metrics(os.path.join(ROOT, "runs", t))[0])
        if mine:
            last = mine[-1]; first = last["attempt"] + 1
            if from_attempt:
                # restart from an earlier attempt's configuration; later decisions are kept in the ledger but marked abandoned
                cfg = jload(os.path.join(os.path.dirname(config_path), f"config_{tag}-a{from_attempt}.json"), cfg)
                for d in mine:
                    if d["attempt"] >= from_attempt and d.get("result") != "abandoned": d["result"] = (d.get("result") or "pending") + "/abandoned"
                counts = {}
                for d in mine:
                    if d["attempt"] < from_attempt: counts[d["symptom"]] = counts.get(d["symptom"], 0) + 1
                log(f"CLOSURE RESUME series {tag} at attempt {first} from the configuration of attempt {from_attempt}; skipping regressed rules {skip}")
            elif last.get("tag_after") is None:
                cfg = jload(os.path.join(os.path.dirname(config_path), f"config_{last['tag_before']}.json"), cfg)
                cfg.update({k: v[1] for k, v in last["changes"].items()})
                for d in mine: counts[d["symptom"]] = counts.get(d["symptom"], 0) + 1
                log(f"CLOSURE RESUME series {tag} at attempt {first} with pending decision applied: {last['rule']}")
    for attempt in range(first, first + max_attempts):
        atag = f"{tag}-a{attempt}"
        acfg = os.path.join(os.path.dirname(config_path), f"config_{atag}.json")
        json.dump(cfg, open(acfg, "w"), indent=2)
        log(f"CLOSURE attempt {attempt}/{max_attempts} tag={atag} config={os.path.relpath(acfg, ROOT)}")
        t0 = time.time()
        os.makedirs(os.path.join(ROOT, "runs", atag), exist_ok=True)   # librelane --force-run-dir requires an existing dir (Makefile fix queued in NEEDS_HUMAN.md)
        rc = subprocess.call(["make", "harden", f"TAG={atag}", f"CONFIG={os.path.relpath(acfg, ROOT)}", f"DESIGN={design}"], cwd=ROOT)
        run_dir = os.path.join(ROOT, "runs", atag)
        metrics, _ = final_metrics(run_dir)
        err = open(os.path.join(run_dir, "error.log")).read() if os.path.exists(os.path.join(run_dir, "error.log")) else ""
        symptoms = classify(metrics, rc == 0, err)
        snap = {k: metrics.get(k) for k in ("timing__setup__ws", "timing__hold__ws", "timing__setup_vio__count", "timing__hold_vio__count", "route__drc_errors",
                                           "magic__drc_error__count", "klayout__drc_error__count", "design__lvs_error__count", "antenna__violating__pins",
                                           "design__instance__count", "design__instance__area", "design__instance__utilization", "power__total")}
        if decisions and decisions[-1].get("tag_after") is None and decisions[-1].get("series") == tag:
            decisions[-1]["after"] = snap; decisions[-1]["tag_after"] = atag; decisions[-1]["result"] = "pass" if rc == 0 else "fail"
        consider(atag, rc, metrics)
        if decisions and decisions[-1].get("series") == tag and regressed(decisions[-1]):
            skip.append({k: v[1] for k, v in decisions[-1]["changes"].items()}); log(f"CLOSURE rule regressed setup slack, will not retry: {decisions[-1]['rule']}")
        if rc == 0:
            log(f"CLOSURE PASS at attempt {attempt} ({atag}) {snap}"); break
        log(f"CLOSURE FAIL attempt {attempt} ({atag}) symptoms={symptoms} {snap}")
        if "immediate_error" in symptoms or "lvs" in symptoms or "xor" in symptoms or "unknown" in symptoms:
            needs_human(f"harden {atag}: symptoms {symptoms}; not a config problem. error.log tail: {err[-800:]!r}")
            break
        applied = None
        for sym in PRIORITY:
            if sym in symptoms:
                k = counts.get(sym, 0); r = rules(sym, k, cfg)
                while r is not None and (already_applied(r[1], cfg) or r[1] in skip):
                    k += 1; r = rules(sym, k, cfg)
                if r is None: continue
                counts[sym] = k + 1; applied = (sym, r); break
        if not applied:
            needs_human(f"harden {atag}: rule table exhausted for symptoms {symptoms}. Last metrics: {snap}")
            break
        sym, (desc, changes) = applied
        before = {k: cfg.get(k) for k in changes}
        cfg.update(changes)
        decisions.append({"time": now(), "series": tag, "attempt": attempt, "tag_before": atag, "tag_after": None, "symptom": sym,
                          "rule": desc, "changes": {k: [before[k], changes[k]] for k in changes}, "before": snap, "after": None, "result": None})
        json.dump(decisions, open(os.path.join(STATE, "decisions.json"), "w"), indent=2)
        log(f"DECISION {sym}: {desc} changes={changes}")
    json.dump(decisions, open(os.path.join(STATE, "decisions.json"), "w"), indent=2)
    if best:
        ingest(os.path.join(ROOT, "runs", best), design)
        open(os.path.join(STATE, "best_run.txt"), "w").write(best)
        open(os.path.join(STATE, "best_config.txt"), "w").write(os.path.relpath(os.path.join(os.path.dirname(config_path), f"config_{best}.json"), ROOT))
    return 0 if best and jload(os.path.join(STATE, "gates.json"), {}).get(f"harden-{best}", {}).get("exit_code") == 0 else 1

def needs_human(text):
    with open(os.path.join(ROOT, "NEEDS_HUMAN.md"), "a") as f: f.write(f"- [{now()}] {text}\n")
    log(f"NEEDS_HUMAN {text[:200]}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ingest"); a.add_argument("--run-dir", required=True); a.add_argument("--design", default="mac_int8"); a.add_argument("--no-render", action="store_true")
    c = sub.add_parser("closure"); c.add_argument("--config", required=True); c.add_argument("--design", default="mac_int8"); c.add_argument("--tag", required=True); c.add_argument("--max-attempts", type=int, default=4); c.add_argument("--resume", action="store_true"); c.add_argument("--from-attempt", type=int, default=None)
    args = ap.parse_args()
    if args.cmd == "ingest": ingest(args.run_dir, args.design, render=not args.no_render); sys.exit(0)
    sys.exit(closure(args.config, args.design, args.tag, args.max_attempts, resume=args.resume, from_attempt=args.from_attempt))
