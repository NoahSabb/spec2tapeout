#!/usr/bin/env python3
import csv, glob, json, os, subprocess, datetime, time
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); STATE = os.path.join(ROOT, "factory", "state")
def jload(p, d=None):
    try: return json.load(open(p))
    except Exception: return d
def sh(cmd):
    try: return subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=ROOT, timeout=60).stdout.strip()
    except Exception as e: return f"({e})"
gates = jload(os.path.join(STATE, "gates.json"), {}); p = jload(os.path.join(STATE, "pipeline.json"), {}); dec = jload(os.path.join(STATE, "decisions.json"), [])
ver = jload(os.path.join(STATE, "verify.json"), {}); tt = jload(os.path.join(STATE, "tt_metrics.json"), {}); acts = jload(os.path.join(STATE, "tt_actions.json"), [])
sweep = list(csv.DictReader(open(os.path.join(STATE, "sweep.csv")))) if os.path.exists(os.path.join(STATE, "sweep.csv")) else []
m = p.get("metrics", {}); C = p.get("corners", {})
try: elapsed = time.time() - float(open(os.path.join(STATE, "start_time")).read())
except Exception: elapsed = 0
nh = open(os.path.join(ROOT, "NEEDS_HUMAN.md")).read() if os.path.exists(os.path.join(ROOT, "NEEDS_HUMAN.md")) else "(none)"
failures = [l for l in open(os.path.join(ROOT, "logs", "overnight.md")) if " FAIL" in l or "NEEDS_HUMAN" in l or "OVERRUN" in l or "STOPPED" in l] if os.path.exists(os.path.join(ROOT, "logs", "overnight.md")) else []
f = lambda k, d=m: d.get(k, "—")
corner_rows = "\n".join(f"| {c} | {C[c].get('timing__setup__ws','—')} | {C[c].get('timing__setup__tns','—')} | {C[c].get('timing__setup_vio__count','—')} | {C[c].get('timing__hold__ws','—')} | {C[c].get('timing__hold__tns','—')} | {C[c].get('timing__hold_vio__count','—')} |" for c in sorted(C))
gate_rows = "\n".join(f"| {k} | {v['status']} | {v['exit_code']} | {v['duration_s']} s | `{v['log']}` |" for k, v in sorted(gates.items(), key=lambda kv: kv[1].get('ended', '')))
dec_rows = "\n".join(f"| {d['time']} | {d['attempt']} | {d['symptom']} | {d['rule']} | `{json.dumps(d['changes'])}` | `{json.dumps(d['before'])}` | `{json.dumps(d['after'])}` | {d['result']} |" for d in dec)
sweep_rows = "\n".join("| " + " | ".join(str(r.get(c, '')) for c in ("tag", "width", "clock_period_ns", "status", "instance_count", "instance_area_um2", "setup_ws_ss", "hold_ws_ff", "power_total_W", "fmax_est_MHz")) + " |" for r in sweep)
ver_rows = "\n".join(f"| {k} | {'PASS' if v.get('ok') else ('n/a' if v.get('ok') is None else 'FAIL')} | {v.get('detail','')[:160]} |" for k, v in ver.items() if isinstance(v, dict))
act_rows = "\n".join(f"| {a.get('name')} | {a.get('conclusion')} | {a.get('url')} |" for a in acts) if isinstance(acts, list) else ""
tt_rows = "\n".join(f"| {k} | {tt.get(k, '—')} |" for k in ("design__instance__count", "design__instance__area", "design__instance__utilization", "timing__setup__ws", "timing__hold__ws", "timing__setup_vio__count", "timing__hold_vio__count", "route__drc_errors", "magic__drc_error__count", "design__lvs_error__count", "antenna__violating__pins", "power__total"))
report = f"""# Morning report — spec2tapeout factory

Generated {datetime.datetime.now().isoformat(timespec='seconds')} after {elapsed/3600:.2f} h of autonomous work. Git head: `{sh('git log --oneline -1')}`.

## Open the dashboard

    make serve      # then open http://localhost:8787

## What was built
- RTL: `rtl/mac_int8.v` (WIDTH/ACC_WIDTH parameterized signed MAC), `rtl/mac_array_2x2.v` (output-stationary 2x2), `rtl/tt_um_noahsabb_mac.v` (Tiny Tapeout wrapper, byte-serial protocol).
- Verification: frozen reference model `ref/mac_ref.py`, golden vectors `tests/golden/*.json` ({len(glob.glob(os.path.join(ROOT,'tests','golden','*.json')))} files), cocotb RTL + gate-level tests.
- Flow: LibreLane Classic on sky130A via Nix (`make harden`), orchestrator with closure rules (`factory/orchestrate.py`), renderer, sweep, dashboard.
- Best MAC run: `{p.get('run_tag')}` (status **{p.get('status')}**), GDS `{p.get('gds')}` ({p.get('gds_bytes')} bytes). Metrics source: `{p.get('metrics_source')}`.
- Tiny Tapeout repo: https://github.com/NoahSabb/tt-um-noahsabb-mac

## Gate ladder results
| gate | status | exit | duration | log |
|---|---|---|---|---|
{gate_rows}

## Timing (signoff STA, `{p.get('run_tag')}`)
| corner | setup ws | setup tns | setup vio | hold ws | hold tns | hold vio |
|---|---|---|---|---|---|---|
{corner_rows}
| overall | {f('timing__setup__ws')} | {f('timing__setup__tns')} | {f('timing__setup_vio__count')} | {f('timing__hold__ws')} | {f('timing__hold__tns')} | {f('timing__hold_vio__count')} |

Worst skew setup/hold: {f('clock__skew__worst_setup')} / {f('clock__skew__worst_hold')} ns; slew/cap/fanout violations: {f('design__max_slew_violation__count')}/{f('design__max_cap_violation__count')}/{f('design__max_fanout_violation__count')}; unannotated nets (filtered): {f('timing__unannotated_net_filtered__count')}.

## Area / power / physical signoff
| metric | value |
|---|---|
| instances | {f('design__instance__count')} |
| instance area (um²) | {f('design__instance__area')} |
| utilization | {f('design__instance__utilization')} |
| die bbox | {f('design__die__bbox')} |
| power total / internal / switching / leakage (W) | {f('power__total')} / {f('power__internal__total')} / {f('power__switching__total')} / {f('power__leakage__total')} |
| IR drop worst / avg | {f('ir__drop__worst')} / {f('ir__drop__avg')} |
| route DRC / Magic DRC / KLayout DRC | {f('route__drc_errors')} / {f('magic__drc_error__count')} / {f('klayout__drc_error__count')} |
| XOR diff / illegal overlaps / LVS errors | {f('design__xor_difference__count')} / {f('magic__illegal_overlap__count')} / {f('design__lvs_error__count')} |
| antenna violating pins / nets | {f('antenna__violating__pins')} / {f('antenna__violating__nets')} |

## Closure decisions
| time | attempt | symptom | rule | changes | before | after | result |
|---|---|---|---|---|---|---|---|
{dec_rows or '| — | — | — | no decisions needed | | | | |'}

## Sweep (WIDTH × CLOCK_PERIOD)
| tag | width | period ns | status | cells | area um² | setup ws @ss | hold ws @ff | power W | fmax est MHz |
|---|---|---|---|---|---|---|---|---|---|
{sweep_rows or '| (no sweep) |'}

Plots: `factory/state/sweep_area.png`, `sweep_wns.png`, `sweep_power.png` (embedded in the dashboard).

## Tiny Tapeout (`tt_repo/runs/wokwi`, LibreLane 3.0.14, tile per info.yaml)
| metric | value |
|---|---|
{tt_rows}

GitHub Actions:
| workflow | conclusion | url |
|---|---|---|
{act_rows or '| (not recorded) | | |'}

## verify-factory
| check | result | detail |
|---|---|---|
{ver_rows or '| (not run) | | |'}

## Failures and hypotheses (from logs/overnight.md)
{''.join('- ' + l for l in failures) or '- none recorded'}

## NEEDS HUMAN
{nh}

## Suggested first things to try this morning
1. `make serve` and click through the factory line; open the Signoff STA station and read `max.rpt` at `max_ss_100C_1v60` for the worst path.
2. Open the GDS: `nix-shell ~/librelane/shell.nix --run "librelane --flow OpenInKLayout --run-tag {p.get('run_tag')} --force-run-dir runs/{p.get('run_tag')} flow/mac_int8/config.json"` (or `--flow OpenInOpenROAD`).
3. Check the GitHub Actions links above; if `gds`/`precheck`/`gl_test` are green, go to https://app.tinytapeout.com/projects/create, paste the repo URL, choose TTSKY26d, pay or enter a coupon, and press "Submit a new revision" before 2026-11-30.
4. Decide the tile count (see NEEDS HUMAN) and whether 50 MHz is the final clock; re-run `make tt-harden` after any change.
5. Re-run the sweep at finer clock periods near the WNS zero crossing: `.venv/bin/python factory/sweep.py --widths 8 --periods 6,7,8`.
"""
os.makedirs(os.path.join(ROOT, "reports"), exist_ok=True)
open(os.path.join(ROOT, "reports", "MORNING_REPORT.md"), "w").write(report)
print(report[:1500])
