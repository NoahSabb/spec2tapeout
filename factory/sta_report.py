#!/usr/bin/env python3
import glob, json, os, sys
run = sys.argv[1]
summ = sorted(glob.glob(os.path.join(run, "*-openroad-stapostpnr", "summary.rpt")))
if summ: print(open(summ[-1]).read())
else: print("no STAPostPNR summary.rpt in", run)
m = {}
try: m = json.load(open(os.path.join(run, "final", "metrics.json")))
except Exception: print("no final/metrics.json")
keys = ["timing__setup__ws", "timing__setup__tns", "timing__setup_vio__count", "timing__hold__ws", "timing__hold__tns", "timing__hold_vio__count",
        "design__max_slew_violation__count", "design__max_cap_violation__count", "design__max_fanout_violation__count", "clock__skew__worst_setup", "clock__skew__worst_hold",
        "timing__unannotated_net_filtered__count", "design__instance__count", "design__instance__area", "design__instance__utilization",
        "route__drc_errors", "antenna__violating__pins", "magic__drc_error__count", "klayout__drc_error__count", "design__xor_difference__count",
        "design__lvs_error__count", "power__total", "ir__drop__worst"]
for k in keys: print(f"{k:48s} {m.get(k)}")
print("\nper-corner setup/hold worst slack:")
for corner in ("max_ss_100C_1v60", "nom_tt_025C_1v80", "min_ff_n40C_1v95"):
    print(f"  {corner:20s} setup_ws={m.get('timing__setup__ws__corner:'+corner)}  hold_ws={m.get('timing__hold__ws__corner:'+corner)}")
