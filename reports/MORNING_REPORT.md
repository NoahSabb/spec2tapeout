# Morning report — spec2tapeout factory

Generated 2026-10-28T02:34:47 after 1.52 h of autonomous work. Git head: `e32155a phase 7: Tiny Tapeout project built, hardened (2x2 tile, Nix), gate-level tested, precheck 15/15 locally; repo creation/push left to human (classifier denial)`.

## Headline (read this first)
- **MAC (`mac_int8`, WIDTH 8 / ACC 32) closed timing on sky130A at CLOCK_PERIOD 16.1 ns** (SYNTH_STRATEGY `DELAY 1`, FP_CORE_UTIL 30.0) in closure run `mac-w8-a15` after 14 recorded decisions; it did **not** close at the 10 ns target (all violators are input-to-register paths through the multiplier with the PDK's 20 % placeholder input delay — see NEEDS HUMAN). Signoff STA, both DRC decks, LVS, XOR and antenna are clean; the gate-level netlist passes the frozen golden vectors.
- **verify-factory: PASS** (fresh run `verify-20261028-023124` from clean; eqy is experimental and failed, informational only).
- **Sweep:** 9 runs with metrics, 4 close timing (WIDTH 2 closes at 10 ns and 20 ns; WIDTH 4 and 8 only at 20 ns).
- **Tiny Tapeout:** local harden `pass` on a **2x2 tile** (1x2 was 115 % utilised), gate-level TT test `pass`, local precheck `pass` (15/15 checks). The GitHub repository was **not created**: the Claude Code permission classifier refused `gh repo create` (public and private); `tt_repo/` holds the ready-to-push commit and NEEDS HUMAN lists the 3 commands to finish. At the template's 20 ns clock the TT design passes the template's nominal-corner check but has -1.67 ns setup slack at the slow corner (decision queued).
- **Toolchain:** the native Nix route works now (the FOSSi cache key was fixed); every LibreLane run tonight ran in `nix-shell ~/librelane/shell.nix` (3.0.16). Docker Desktop's VM crashed twice more during `tt_tool.py --harden` (Phase 0 failure F4), so the TT harden ran with `--no-docker` in the Nix shell.
- **7 items queued for you** in the NEEDS HUMAN section below (repo creation/push, tile count, clock targets, Makefile fixes for the protected Makefile).


## Open the dashboard

    make serve      # then open http://localhost:8787

## What was built
- RTL: `rtl/mac_int8.v` (WIDTH/ACC_WIDTH parameterized signed MAC), `rtl/mac_array_2x2.v` (output-stationary 2x2), `rtl/tt_um_noahsabb_mac.v` (Tiny Tapeout wrapper, byte-serial protocol).
- Verification: frozen reference model `ref/mac_ref.py`, golden vectors `tests/golden/*.json` (6 files), cocotb RTL + gate-level tests.
- Flow: LibreLane Classic on sky130A via Nix (`make harden`), orchestrator with closure rules (`factory/orchestrate.py`), renderer, sweep, dashboard.
- Best MAC run: `verify-20261028-023124` (status **pass**), GDS `runs/verify-20261028-023124/final/gds/mac_int8.gds` (4167262 bytes). Metrics source: `final/metrics.json`.
- Tiny Tapeout project: local clone `tt_repo/` (origin to be set to https://github.com/NoahSabb/tt-um-noahsabb-mac, see NEEDS HUMAN); local harden run `tt_repo/runs/wokwi`, submission bundle `tt_repo/tt_submission/`, render `tt_repo/gds_render.png`.

## Gate ladder results
| gate | status | exit | duration | log |
|---|---|---|---|---|
| gen-golden | pass | 0 | 0.0 s | `logs/gates/gen-golden.log` |
| sim-mac-w2 | pass | 0 | 0.8 s | `logs/gates/sim-mac-w2.log` |
| sim-mac-w4 | pass | 0 | 0.8 s | `logs/gates/sim-mac-w4.log` |
| sim-array-w8 | pass | 0 | 0.7 s | `logs/gates/sim-array-w8.log` |
| sim-tt-w8 | pass | 0 | 0.8 s | `logs/gates/sim-tt-w8.log` |
| harden-mac-w8-a1 | fail | 2 | 96.8 s | `logs/gates/harden-mac-w8-a1.log` |
| harden-mac-w8-a2 | fail | 2 | 124.5 s | `logs/gates/harden-mac-w8-a2.log` |
| harden-mac-w8-a3 | fail | 2 | 125.6 s | `logs/gates/harden-mac-w8-a3.log` |
| harden-mac-w8-a4 | fail | 2 | 96.4 s | `logs/gates/harden-mac-w8-a4.log` |
| harden-mac-w8-a5 | fail | 2 | 90.1 s | `logs/gates/harden-mac-w8-a5.log` |
| harden-mac-w8-a6 | fail | 2 | 82.6 s | `logs/gates/harden-mac-w8-a6.log` |
| harden-mac-w8-a7 | fail | 2 | 88.7 s | `logs/gates/harden-mac-w8-a7.log` |
| harden-mac-w8-a8 | fail | 2 | 89.0 s | `logs/gates/harden-mac-w8-a8.log` |
| harden-mac-w8-a9 | fail | 2 | 89.0 s | `logs/gates/harden-mac-w8-a9.log` |
| harden-mac-w8-a10 | fail | 2 | 86.8 s | `logs/gates/harden-mac-w8-a10.log` |
| harden-mac-w8-a11 | fail | 2 | 98.1 s | `logs/gates/harden-mac-w8-a11.log` |
| harden-mac-w8-a12 | fail | 2 | 89.4 s | `logs/gates/harden-mac-w8-a12.log` |
| harden-mac-w8-a13 | fail | 2 | 85.3 s | `logs/gates/harden-mac-w8-a13.log` |
| harden-mac-w8-a14 | fail | 2 | 82.4 s | `logs/gates/harden-mac-w8-a14.log` |
| harden-mac-w8-a15 | pass | 0 | 85.5 s | `logs/gates/harden-mac-w8-a15.log` |
| render-mac-w8-a15 | pass | 0 | 19.2 s | `logs/gates/render-mac-w8-a15.log` |
| harden-sweep-w2-p5 | fail | 2 | 45.8 s | `logs/gates/harden-sweep-w2-p5.log` |
| harden-sweep-w2-p10 | pass | 0 | 40.5 s | `logs/gates/harden-sweep-w2-p10.log` |
| harden-sweep-w2-p20 | pass | 0 | 40.4 s | `logs/gates/harden-sweep-w2-p20.log` |
| tt-test | pass | 0 | 1.0 s | `logs/gates/tt-test.log` |
| harden-sweep-w4-p5 | fail | 2 | 60.9 s | `logs/gates/harden-sweep-w4-p5.log` |
| harden-sweep-w4-p10 | fail | 2 | 56.7 s | `logs/gates/harden-sweep-w4-p10.log` |
| harden-sweep-w4-p20 | pass | 0 | 48.0 s | `logs/gates/harden-sweep-w4-p20.log` |
| harden-sweep-w8-p5 | fail | 2 | 115.8 s | `logs/gates/harden-sweep-w8-p5.log` |
| harden-sweep-w8-p10 | fail | 2 | 97.7 s | `logs/gates/harden-sweep-w8-p10.log` |
| harden-sweep-w8-p20 | pass | 0 | 60.0 s | `logs/gates/harden-sweep-w8-p20.log` |
| sweep | pass | 0 | 641.3 s | `logs/gates/sweep.log` |
| tt-harden | pass | 0 | 140.2 s | `logs/gates/tt-harden.log` |
| tt-test-gl | pass | 0 | 6.3 s | `logs/gates/tt-test-gl.log` |
| precheck | pass | 0 | 44.9 s | `logs/gates/precheck.log` |
| doctor | pass | 0 | 11.1 s | `logs/gates/doctor.log` |
| lint | pass | 0 | 0.2 s | `logs/gates/lint.log` |
| sim-mac-w8 | pass | 0 | 0.9 s | `logs/gates/sim-mac-w8.log` |
| synth-8 | pass | 0 | 2.1 s | `logs/gates/synth-8.log` |
| harden-verify-20261028-023124 | pass | 0 | 84.0 s | `logs/gates/harden-verify-20261028-023124.log` |
| sim-gl-mac | pass | 0 | 2.2 s | `logs/gates/sim-gl-mac.log` |
| render-verify-20261028-023124 | pass | 0 | 18.7 s | `logs/gates/render-verify-20261028-023124.log` |
| dashboard | pass | 0 | 0.1 s | `logs/gates/dashboard.log` |
| verify-factory | pass | 0 | 144.3 s | `logs/gates/verify-factory.log` |

## Timing (signoff STA, `verify-20261028-023124`)
| corner | setup ws | setup tns | setup vio | hold ws | hold tns | hold vio |
|---|---|---|---|---|---|---|
| max_ff_n40C_1v95 | 8.745356686357212 | 0 | 0 | 0.11623935476500519 | 0 | 0 |
| max_ss_100C_1v60 | 0.5712657175665821 | 0 | 0 | 0.8359888573573205 | 0 | 0 |
| max_tt_025C_1v80 | 6.506345868454777 | 0 | 0 | 0.31657732886772016 | 0 | 0 |
| min_ff_n40C_1v95 | 8.875796349120298 | 0 | 0 | 0.11170553687111831 | 0 | 0 |
| min_ss_100C_1v60 | 1.0187708742751216 | 0 | 0 | 0.8162963869233931 | 0 | 0 |
| min_tt_025C_1v80 | 6.664917695279076 | 0 | 0 | 0.30596037680526433 | 0 | 0 |
| nom_ff_n40C_1v95 | 8.82731424053138 | 0 | 0 | 0.11401480082764909 | 0 | 0 |
| nom_ss_100C_1v60 | 0.8352554440065107 | 0 | 0 | 0.8254822614666335 | 0 | 0 |
| nom_tt_025C_1v80 | 6.587809595413624 | 0 | 0 | 0.31083214659740505 | 0 | 0 |
| overall | 0.5712657175665821 | 0 | 0 | 0.11170553687111831 | 0 | 0 |

Worst skew setup/hold: 0.2735695636345994 / -0.3158978446018568 ns; slew/cap/fanout violations: 9/0/0; unannotated nets (filtered): 0.

## Area / power / physical signoff
| metric | value |
|---|---|
| instances | 10662 |
| instance area (um²) | 45478.6 |
| utilization | 0.352977 |
| die bbox | 0.0 0.0 225.55 236.27 |
| power total / internal / switching / leakage (W) | 0.0016547926934435964 / 0.0007156396168284118 / 0.0009391080238856375 / 4.509456275059165e-08 |
| IR drop worst / avg | 6.81e-05 / 1.06e-05 |
| route DRC / Magic DRC / KLayout DRC | 0 / 0 / 0 |
| XOR diff / illegal overlaps / LVS errors | 0 / 0 / 0 |
| antenna violating pins / nets | 0 / 0 |

## Closure decisions
| time | attempt | symptom | rule | changes | before | after | result |
|---|---|---|---|---|---|---|---|
| 2026-10-28T08:36:34Z | 1 | setup | synthesis strategy DELAY 1 (ABC delay-oriented mapping) | `{"SYNTH_STRATEGY": ["AREA 0", "DELAY 1"]}` | `{"timing__setup__ws": -2.5192355581352204, "timing__hold__ws": 0.12015261348172723, "timing__setup_vio__count": 58, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 4535, "design__instance__area": 22709.3, "design__instance__utilization": 0.526887, "power__total": 0.005043978337198496}` | `{"timing__setup__ws": -1.0306920053614892, "timing__hold__ws": 0.10409690071241903, "timing__setup_vio__count": 50, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 7092, "design__instance__area": 34287.9, "design__instance__utilization": 0.513246, "power__total": 0.003007561434060335}` | fail |
| 2026-10-28T08:38:39Z | 2 | setup | lower utilization by 10 (more room for resizer, shorter wires) | `{"FP_CORE_UTIL": [40, 30.0], "PL_TARGET_DENSITY_PCT": [50, 45]}` | `{"timing__setup__ws": -1.0306920053614892, "timing__hold__ws": 0.10409690071241903, "timing__setup_vio__count": 50, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 7092, "design__instance__area": 34287.9, "design__instance__utilization": 0.513246, "power__total": 0.003007561434060335}` | `{"timing__setup__ws": -0.8360485873577347, "timing__hold__ws": 0.1130190972798536, "timing__setup_vio__count": 49, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10292, "design__instance__area": 45478.6, "design__instance__utilization": 0.385688, "power__total": 0.0029543067794293165}` | fail |
| 2026-10-28T08:40:44Z | 3 | setup | relax CLOCK_PERIOD by 10 % (cap 20 ns standalone) | `{"CLOCK_PERIOD": [10, 11.0]}` | `{"timing__setup__ws": -0.8360485873577347, "timing__hold__ws": 0.1130190972798536, "timing__setup_vio__count": 49, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10292, "design__instance__area": 45478.6, "design__instance__utilization": 0.385688, "power__total": 0.0029543067794293165}` | `{"timing__setup__ws": -0.9052225891756138, "timing__hold__ws": 0.11275281027986614, "timing__setup_vio__count": 53, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10543, "design__instance__area": 45478.6, "design__instance__utilization": 0.363706, "power__total": 0.002542276168242097}` | fail |
| 2026-10-28T08:42:21Z | 4 | setup | synthesis strategy DELAY 4 (ORFS delay script) + CSA adders | `{"SYNTH_STRATEGY": ["DELAY 1", "DELAY 4"], "SYNTH_ADDER_TYPE": [null, "CSA"]}` | `{"timing__setup__ws": -0.9052225891756138, "timing__hold__ws": 0.11275281027986614, "timing__setup_vio__count": 53, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10543, "design__instance__area": 45478.6, "design__instance__utilization": 0.363706, "power__total": 0.002542276168242097}` | `{"timing__setup__ws": -11.86947462801699, "timing__hold__ws": 0.1288519327706649, "timing__setup_vio__count": 87, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5367, "design__instance__area": 24390.9, "design__instance__utilization": 0.420181, "power__total": 0.0023071146570146084}` | fail/abandoned |
| 2026-10-28T08:46:01Z | 5 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [11.0, 12.1]}` | `{"timing__setup__ws": -11.86947462801699, "timing__hold__ws": 0.1288519327706649, "timing__setup_vio__count": 87, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5367, "design__instance__area": 24390.9, "design__instance__utilization": 0.420181, "power__total": 0.0023071146570146084}` | `{"timing__setup__ws": -10.745852511974034, "timing__hold__ws": 0.1287484044706906, "timing__setup_vio__count": 78, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5337, "design__instance__area": 24390.9, "design__instance__utilization": 0.42254, "power__total": 0.0022156424820423126}` | fail/abandoned |
| 2026-10-28T08:47:24Z | 6 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [12.1, 13.31]}` | `{"timing__setup__ws": -10.745852511974034, "timing__hold__ws": 0.1287484044706906, "timing__setup_vio__count": 78, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5337, "design__instance__area": 24390.9, "design__instance__utilization": 0.42254, "power__total": 0.0022156424820423126}` | `{"timing__setup__ws": -9.741374205232948, "timing__hold__ws": 0.13165527374270292, "timing__setup_vio__count": 66, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5325, "design__instance__area": 24390.9, "design__instance__utilization": 0.413358, "power__total": 0.001928433426655829}` | fail/abandoned |
| 2026-10-28T08:48:53Z | 7 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [13.31, 14.64]}` | `{"timing__setup__ws": -9.741374205232948, "timing__hold__ws": 0.13165527374270292, "timing__setup_vio__count": 66, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5325, "design__instance__area": 24390.9, "design__instance__utilization": 0.413358, "power__total": 0.001928433426655829}` | `{"timing__setup__ws": -9.22813407364487, "timing__hold__ws": 0.12737211645928995, "timing__setup_vio__count": 63, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5411, "design__instance__area": 24390.9, "design__instance__utilization": 0.386221, "power__total": 0.0016358179273083806}` | fail/abandoned |
| 2026-10-28T08:50:22Z | 8 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [14.64, 16.1]}` | `{"timing__setup__ws": -9.22813407364487, "timing__hold__ws": 0.12737211645928995, "timing__setup_vio__count": 63, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5411, "design__instance__area": 24390.9, "design__instance__utilization": 0.386221, "power__total": 0.0016358179273083806}` | `{"timing__setup__ws": -7.9038928750214135, "timing__hold__ws": 0.12653617400925637, "timing__setup_vio__count": 57, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5377, "design__instance__area": 24390.9, "design__instance__utilization": 0.391659, "power__total": 0.0014649300137534738}` | fail/abandoned |
| 2026-10-28T08:51:51Z | 9 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [16.1, 17.71]}` | `{"timing__setup__ws": -7.9038928750214135, "timing__hold__ws": 0.12653617400925637, "timing__setup_vio__count": 57, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5377, "design__instance__area": 24390.9, "design__instance__utilization": 0.391659, "power__total": 0.0014649300137534738}` | `{"timing__setup__ws": -6.5807769984875435, "timing__hold__ws": 0.12619372570762563, "timing__setup_vio__count": 51, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5389, "design__instance__area": 24390.9, "design__instance__utilization": 0.389607, "power__total": 0.0013178103836253285}` | fail/abandoned |
| 2026-10-28T08:53:18Z | 10 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [17.71, 19.48]}` | `{"timing__setup__ws": -6.5807769984875435, "timing__hold__ws": 0.12619372570762563, "timing__setup_vio__count": 51, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 5389, "design__instance__area": 24390.9, "design__instance__utilization": 0.389607, "power__total": 0.0013178103836253285}` | `{"timing__setup__ws": -0.9052225891756138, "timing__hold__ws": 0.11275281027986614, "timing__setup_vio__count": 53, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10543, "design__instance__area": 45478.6, "design__instance__utilization": 0.363706, "power__total": 0.002542276168242097}` | fail |
| 2026-10-28T08:56:29Z | 11 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [11.0, 12.1]}` | `{"timing__setup__ws": -0.9052225891756138, "timing__hold__ws": 0.11275281027986614, "timing__setup_vio__count": 53, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10543, "design__instance__area": 45478.6, "design__instance__utilization": 0.363706, "power__total": 0.002542276168242097}` | `{"timing__setup__ws": -1.1895977872810404, "timing__hold__ws": 0.11168333240999782, "timing__setup_vio__count": 47, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10649, "design__instance__area": 45478.6, "design__instance__utilization": 0.354297, "power__total": 0.0022152976598590612}` | fail |
| 2026-10-28T08:57:58Z | 12 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [12.1, 13.31]}` | `{"timing__setup__ws": -1.1895977872810404, "timing__hold__ws": 0.11168333240999782, "timing__setup_vio__count": 47, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10649, "design__instance__area": 45478.6, "design__instance__utilization": 0.354297, "power__total": 0.0022152976598590612}` | `{"timing__setup__ws": -0.9036380788300559, "timing__hold__ws": 0.11127954428452175, "timing__setup_vio__count": 33, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10669, "design__instance__area": 45478.6, "design__instance__utilization": 0.353004, "power__total": 0.0020052187610417604}` | fail |
| 2026-10-28T08:59:23Z | 13 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [13.31, 14.64]}` | `{"timing__setup__ws": -0.9036380788300559, "timing__hold__ws": 0.11127954428452175, "timing__setup_vio__count": 33, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10669, "design__instance__area": 45478.6, "design__instance__utilization": 0.353004, "power__total": 0.0020052187610417604}` | `{"timing__setup__ws": -0.5176019759305862, "timing__hold__ws": 0.11172890706644763, "timing__setup_vio__count": 8, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10640, "design__instance__area": 45478.6, "design__instance__utilization": 0.352537, "power__total": 0.0018236591713503003}` | fail |
| 2026-10-28T09:00:46Z | 14 | setup | relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) | `{"CLOCK_PERIOD": [14.64, 16.1]}` | `{"timing__setup__ws": -0.5176019759305862, "timing__hold__ws": 0.11172890706644763, "timing__setup_vio__count": 8, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10640, "design__instance__area": 45478.6, "design__instance__utilization": 0.352537, "power__total": 0.0018236591713503003}` | `{"timing__setup__ws": 0.5712657175665821, "timing__hold__ws": 0.11170553687111831, "timing__setup_vio__count": 0, "timing__hold_vio__count": 0, "route__drc_errors": 0, "magic__drc_error__count": 0, "klayout__drc_error__count": 0, "design__lvs_error__count": 0, "antenna__violating__pins": 0, "design__instance__count": 10662, "design__instance__area": 45478.6, "design__instance__utilization": 0.352977, "power__total": 0.0016547926934435964}` | pass |

## Sweep (WIDTH × CLOCK_PERIOD)
| tag | width | period ns | status | cells | area um² | setup ws @ss | hold ws @ff | power W | fmax est MHz |
|---|---|---|---|---|---|---|---|---|---|
| sweep-w2-p5 | 2 | 5 | fail | 1965 | 8608.26 | -0.6691238863491303 | 0.11372497709887391 | 0.0008455002098344266 | 176.4 |
| sweep-w2-p10 | 2 | 10 | pass | 2020 | 8608.26 | 1.7204371747532168 | 0.11202122879709886 | 0.00039925076998770237 | 120.8 |
| sweep-w2-p20 | 2 | 20 | pass | 2012 | 8608.26 | 9.723305991129983 | 0.11543735738490955 | 0.0002000924723688513 | 97.3 |
| sweep-w4-p5 | 4 | 5 | fail | 3345 | 15064.4 | -4.300124378288967 | 0.11303658329298598 | 0.0018810279434546828 | 107.5 |
| sweep-w4-p10 | 4 | 10 | fail | 3410 | 15064.4 | -0.45598637267812114 | 0.10388301624067593 | 0.0008481822442263365 | 95.6 |
| sweep-w4-p20 | 4 | 20 | pass | 3522 | 15064.4 | 2.4301770172947217 | 0.1035587200860112 | 0.00038991053588688374 | 56.9 |
| sweep-w8-p5 | 8 | 5 | fail | 7474 | 33344.5 | -6.420037128079439 | 0.1164303131306414 | 0.011386675760149956 | 87.6 |
| sweep-w8-p10 | 8 | 10 | fail | 7560 | 33344.5 | -2.6702782962827847 | 0.11966555862704932 | 0.005256954580545425 | 78.9 |
| sweep-w8-p20 | 8 | 20 | pass | 7854 | 33344.5 | 1.725874603192402 | 0.11187168175145236 | 0.002215150510892272 | 54.7 |

Plots: `factory/state/sweep_area.png`, `sweep_wns.png`, `sweep_power.png` (embedded in the dashboard).

## Tiny Tapeout (`tt_repo/runs/wokwi`, LibreLane 3.0.14, tile per info.yaml)
| metric | value |
|---|---|
| design__instance__count | 13552 |
| design__instance__area | 72564.6 |
| design__instance__utilization | 0.621767 |
| timing__setup__ws | -1.6663364493223698 |
| timing__hold__ws | 0.1180771069896424 |
| timing__setup_vio__count | 36 |
| timing__hold_vio__count | 0 |
| route__drc_errors | 0 |
| magic__drc_error__count | 0 |
| design__lvs_error__count | 0 |
| antenna__violating__pins | 0 |
| power__total | 0.0017533402424305677 |

GitHub Actions:
| workflow | conclusion | url |
|---|---|---|
| (not recorded) | | |

## verify-factory
| check | result | detail |
|---|---|---|
| a_doctor | PASS | exit 0 |
| a_lint | PASS | exit 0 |
| a_sim_rtl | PASS | exit 0 |
| a_synth | PASS | exit 0 |
| a_harden | PASS | exit 0 tag verify-20261028-023124 |
| e_sim_gl_vs_golden | PASS | exit 0 |
| a_render | PASS | exit 0 |
| b_gates | PASS | missing=[] failed=[] |
| c_pipeline_all_pass | PASS | run_tag=verify-20261028-023124 status=pass bad_stations=[] |
| d_gds_and_svg | PASS | /Users/noahsabbavarapu/Documents/GitHub/spec2tapeout/runs/verify-20261028-023124/final/gds/mac_int8.gds 4167262 bytes; svg 6521314 bytes; top cell mac_int8 |
| f_eqy_experimental | FAIL | exit 255;                                     
                    '/Users/noahsabbavarapu/Documents/GitHub/spe                
                    c2tapeout/ru |
| g_dashboard | PASS | exit 0 |

## Failures and hypotheses (from logs/overnight.md)
- 2026-10-28T08:21:17Z GATE doctor FAIL exit=1 log=logs/gates/doctor.log
- 2026-10-28T08:26:46Z GATE sim-mac FAIL exit=2 log=logs/gates/sim-mac.log
- 2026-10-28T08:26:46Z GATE sim-mac FAIL exit=2 log=logs/gates/sim-mac.log
- 2026-10-28T08:26:47Z GATE sim-mac FAIL exit=2 log=logs/gates/sim-mac.log
- 2026-10-28T08:26:47Z GATE sim-array FAIL exit=2 log=logs/gates/sim-array.log
- 2026-10-28T08:26:48Z GATE sim-tt FAIL exit=2 log=logs/gates/sim-tt.log
- 2026-10-28T08:33:04Z GATE harden-mac-w8-a1 FAIL exit=2 log=logs/gates/harden-mac-w8-a1.log
- 2026-10-28T08:33:04Z CLOSURE FAIL attempt 1 (mac-w8-a1) symptoms=['immediate_error'] {'timing__setup__ws': None, 'timing__hold__ws': None, 'timing__setup_vio__count': None, 'timing__hold_vio__count': None, 'route__drc_errors': None, 'magic__drc_error__count': None, 'klayout__drc_error__count': None, 'design__lvs_error__count': None, 'antenna__violating__pins': None, 'design__instance__count': None, 'design__instance__area': None, 'design__instance__utilization': None, 'power__total': None}
- 2026-10-28T08:33:04Z NEEDS_HUMAN harden mac-w8-a1: symptoms ['immediate_error']; not a config problem. error.log tail: ''
- 2026-10-28T08:34:38Z PHASE 4 FIX: librelane --force-run-dir needs an existing dir; Makefile is protected so callers (orchestrate/sweep/verify) now mkdir runs/<tag> first; recorded in NEEDS_HUMAN.md; bogus harden-mac-w8-a1 attempt is re-run
- 2026-10-28T08:36:34Z GATE harden-mac-w8-a1 FAIL exit=2 log=logs/gates/harden-mac-w8-a1.log
- 2026-10-28T08:36:34Z CLOSURE FAIL attempt 1 (mac-w8-a1) symptoms=['setup'] {'timing__setup__ws': -2.5192355581352204, 'timing__hold__ws': 0.12015261348172723, 'timing__setup_vio__count': 58, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 4535, 'design__instance__area': 22709.3, 'design__instance__utilization': 0.526887, 'power__total': 0.005043978337198496}
- 2026-10-28T08:38:39Z GATE harden-mac-w8-a2 FAIL exit=2 log=logs/gates/harden-mac-w8-a2.log
- 2026-10-28T08:38:39Z CLOSURE FAIL attempt 2 (mac-w8-a2) symptoms=['setup'] {'timing__setup__ws': -1.0306920053614892, 'timing__hold__ws': 0.10409690071241903, 'timing__setup_vio__count': 50, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 7092, 'design__instance__area': 34287.9, 'design__instance__utilization': 0.513246, 'power__total': 0.003007561434060335}
- 2026-10-28T08:40:44Z GATE harden-mac-w8-a3 FAIL exit=2 log=logs/gates/harden-mac-w8-a3.log
- 2026-10-28T08:40:44Z CLOSURE FAIL attempt 3 (mac-w8-a3) symptoms=['setup'] {'timing__setup__ws': -0.8360485873577347, 'timing__hold__ws': 0.1130190972798536, 'timing__setup_vio__count': 49, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10292, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.385688, 'power__total': 0.0029543067794293165}
- 2026-10-28T08:42:21Z GATE harden-mac-w8-a4 FAIL exit=2 log=logs/gates/harden-mac-w8-a4.log
- 2026-10-28T08:42:21Z CLOSURE FAIL attempt 4 (mac-w8-a4) symptoms=['setup'] {'timing__setup__ws': -0.9052225891756138, 'timing__hold__ws': 0.11275281027986614, 'timing__setup_vio__count': 53, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10543, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.363706, 'power__total': 0.002542276168242097}
- 2026-10-28T08:46:01Z GATE harden-mac-w8-a5 FAIL exit=2 log=logs/gates/harden-mac-w8-a5.log
- 2026-10-28T08:46:01Z CLOSURE FAIL attempt 5 (mac-w8-a5) symptoms=['setup'] {'timing__setup__ws': -11.86947462801699, 'timing__hold__ws': 0.1288519327706649, 'timing__setup_vio__count': 87, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5367, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.420181, 'power__total': 0.0023071146570146084}
- 2026-10-28T08:47:24Z GATE harden-mac-w8-a6 FAIL exit=2 log=logs/gates/harden-mac-w8-a6.log
- 2026-10-28T08:47:24Z CLOSURE FAIL attempt 6 (mac-w8-a6) symptoms=['setup'] {'timing__setup__ws': -10.745852511974034, 'timing__hold__ws': 0.1287484044706906, 'timing__setup_vio__count': 78, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5337, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.42254, 'power__total': 0.0022156424820423126}
- 2026-10-28T08:48:53Z GATE harden-mac-w8-a7 FAIL exit=2 log=logs/gates/harden-mac-w8-a7.log
- 2026-10-28T08:48:53Z CLOSURE FAIL attempt 7 (mac-w8-a7) symptoms=['setup'] {'timing__setup__ws': -9.741374205232948, 'timing__hold__ws': 0.13165527374270292, 'timing__setup_vio__count': 66, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5325, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.413358, 'power__total': 0.001928433426655829}
- 2026-10-28T08:50:22Z GATE harden-mac-w8-a8 FAIL exit=2 log=logs/gates/harden-mac-w8-a8.log
- 2026-10-28T08:50:22Z CLOSURE FAIL attempt 8 (mac-w8-a8) symptoms=['setup'] {'timing__setup__ws': -9.22813407364487, 'timing__hold__ws': 0.12737211645928995, 'timing__setup_vio__count': 63, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5411, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.386221, 'power__total': 0.0016358179273083806}
- 2026-10-28T08:51:51Z GATE harden-mac-w8-a9 FAIL exit=2 log=logs/gates/harden-mac-w8-a9.log
- 2026-10-28T08:51:51Z CLOSURE FAIL attempt 9 (mac-w8-a9) symptoms=['setup'] {'timing__setup__ws': -7.9038928750214135, 'timing__hold__ws': 0.12653617400925637, 'timing__setup_vio__count': 57, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5377, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.391659, 'power__total': 0.0014649300137534738}
- 2026-10-28T08:53:18Z GATE harden-mac-w8-a10 FAIL exit=2 log=logs/gates/harden-mac-w8-a10.log
- 2026-10-28T08:53:18Z CLOSURE FAIL attempt 10 (mac-w8-a10) symptoms=['setup'] {'timing__setup__ws': -6.5807769984875435, 'timing__hold__ws': 0.12619372570762563, 'timing__setup_vio__count': 51, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5389, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.389607, 'power__total': 0.0013178103836253285}
- 2026-10-28T08:56:29Z GATE harden-mac-w8-a11 FAIL exit=2 log=logs/gates/harden-mac-w8-a11.log
- 2026-10-28T08:56:29Z CLOSURE FAIL attempt 11 (mac-w8-a11) symptoms=['setup'] {'timing__setup__ws': -0.9052225891756138, 'timing__hold__ws': 0.11275281027986614, 'timing__setup_vio__count': 53, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10543, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.363706, 'power__total': 0.002542276168242097}
- 2026-10-28T08:57:58Z GATE harden-mac-w8-a12 FAIL exit=2 log=logs/gates/harden-mac-w8-a12.log
- 2026-10-28T08:57:58Z CLOSURE FAIL attempt 12 (mac-w8-a12) symptoms=['setup'] {'timing__setup__ws': -1.1895977872810404, 'timing__hold__ws': 0.11168333240999782, 'timing__setup_vio__count': 47, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10649, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.354297, 'power__total': 0.0022152976598590612}
- 2026-10-28T08:59:23Z GATE harden-mac-w8-a13 FAIL exit=2 log=logs/gates/harden-mac-w8-a13.log
- 2026-10-28T08:59:23Z CLOSURE FAIL attempt 13 (mac-w8-a13) symptoms=['setup'] {'timing__setup__ws': -0.9036380788300559, 'timing__hold__ws': 0.11127954428452175, 'timing__setup_vio__count': 33, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10669, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.353004, 'power__total': 0.0020052187610417604}
- 2026-10-28T09:00:46Z GATE harden-mac-w8-a14 FAIL exit=2 log=logs/gates/harden-mac-w8-a14.log
- 2026-10-28T09:00:46Z CLOSURE FAIL attempt 14 (mac-w8-a14) symptoms=['setup'] {'timing__setup__ws': -0.5176019759305862, 'timing__hold__ws': 0.11172890706644763, 'timing__setup_vio__count': 8, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10640, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.352537, 'power__total': 0.0018236591713503003}
- 2026-10-28T09:05:48Z GATE harden-sweep-w2-p5 FAIL exit=2 log=logs/gates/harden-sweep-w2-p5.log
- 2026-10-28T09:08:46Z GATE harden-sweep-w4-p5 FAIL exit=2 log=logs/gates/harden-sweep-w4-p5.log
- 2026-10-28T09:09:43Z GATE harden-sweep-w4-p10 FAIL exit=2 log=logs/gates/harden-sweep-w4-p10.log
- 2026-10-28T09:12:46Z GATE harden-sweep-w8-p5 FAIL exit=2 log=logs/gates/harden-sweep-w8-p5.log
- 2026-10-28T09:14:23Z GATE harden-sweep-w8-p10 FAIL exit=2 log=logs/gates/harden-sweep-w8-p10.log
- 2026-10-28T09:16:52Z PHASE 7: make tt-harden recipe would resolve 'python' to .venv (LibreLane 3.0.16); running the same gate via factory/gate.py with .venv-tt (LibreLane 3.0.14, image ghcr.io/librelane/librelane:3.0.14) first on PATH for CI parity (Makefile is protected; fix noted in NEEDS_HUMAN.md)
- 2026-10-28T09:18:13Z GATE tt-harden FAIL exit=1 log=logs/gates/tt-harden.log
- 2026-10-28T09:18:34Z PHASE 7 FAIL tt-harden attempt 1: Docker Desktop VM died at Yosys.Synthesis ('error waiting for container: unexpected EOF', Phase 0 failure F4). Hypothesis 1: docker desktop restart + retry
- 2026-10-28T09:20:22Z GATE tt-harden FAIL exit=1 log=logs/gates/tt-harden.log
- 2026-10-28T09:21:12Z PHASE 7 FAIL tt-harden attempt 2: Docker Desktop VM died again at OpenROAD.Floorplan (unexpected EOF). Floorplan log also showed 'Effective utilization: 1.152' on a 1x2 tile -> tiles set to 2x2 per plan 5.2 decision rule. Hypothesis 2: run tt_tool.py --harden --no-docker inside nix-shell (pip LibreLane 3.0.14 flow logic from .venv-tt driving the Nix tool binaries)
- 2026-10-28T09:21:16Z GATE tt-harden FAIL exit=1 log=logs/gates/tt-harden.log
- 2026-10-28T09:22:13Z PHASE 7 FAIL tt-harden attempt 3: pip LibreLane 3.0.14 needs tkinter (ModuleNotFoundError _tkinter; Homebrew python@3.11 lacks Tk). Hypothesis 3: brew install python-tk@3.11 and retry nix no-docker
- 2026-10-28T09:27:18Z GATE precheck FAIL exit=1 log=logs/gates/precheck.log
- 2026-10-28T09:27:45Z GATE precheck FAIL exit=1 log=logs/gates/precheck.log
- 2026-10-28T09:28:23Z GATE precheck FAIL exit=1 log=logs/gates/precheck.log
- 2026-10-28T09:29:46Z GATE precheck FAIL exit=1 log=logs/gates/precheck.log
- 2026-10-28T09:31:24Z PHASE 7: tt_repo committed locally (not pushed: repo creation denied by the permission classifier, see NEEDS_HUMAN.md); GitHub Actions run cannot be recorded
- 2026-10-28T09:34:11Z PHASE 8: verify-factory PASS (a_doctor a_lint a_sim_rtl a_synth a_harden e_sim_gl_vs_golden a_render b_gates c_pipeline_all_pass d_gds_and_svg g_dashboard all PASS; f_eqy_experimental FAIL exit 255, informational: LibreLane's generic EQY script, see runs/verify-20261028-023124/eqy)


## NEEDS HUMAN
# NEEDS_HUMAN.md — queue for the human

## Pre-populated (known in advance)

- Tiny Tapeout shuttle selection, payment (price only in the calculator at https://app.tinytapeout.com/calculator; the last public anchor was "likely €300 for a devkit and €70 per tile", May 2025) and the final "Submit a new revision" click at https://app.tinytapeout.com/projects/create — there is no API; TTSKY26d closes 2026-11-30.
- Choosing the final tile count (`tiles: "1x2"` vs `"2x2"` in `info.yaml`) and therefore the price; the overnight run records measured utilization for the attempted size(s).
- Accepting the final spec: clock target (50 MHz TT default vs the measured fmax), the byte-serial protocol (§4.3), accumulator width 32, output-stationary 2x2 topology.
- Any GUI-only step: viewing the layout interactively (`--flow OpenInKLayout` / `OpenInOpenROAD` / `OpenInMagic`), the Tiny Tapeout 3D viewer link from the `viewer` job, the KLayout marker browser for DRC markers.
- Enabling GitHub Pages for the `viewer` job if the `gh api ... /pages` call failed (Settings → Pages → Source: GitHub Actions).
- Hardware bring-up after fabrication (chips expected 2027-05-12): flash the SDK v3 UF2 on the RP2350 demo board, `tt.shuttle.tt_um_noahsabb_mac.enable()`, replay `tests/golden/tt_protocol.json` from MicroPython.
- Anything needing `sudo` (e.g. `sudo pkill nix-daemon` after editing `/etc/nix/nix.custom.conf`, Docker Desktop resource changes, Homebrew permission problems).
- Any LVS, DRC, XOR or eqy failure the agent could not explain in one sentence (the entry quotes the log excerpt).
- Any golden-vector disagreement the agent believes is a model/spec error (the entry quotes the vector index and both values).
- Secrets/tokens: nothing in `.env` is read by the agent; GitHub auth was done by the human via `gh auth login`.

## Found overnight

- [2026-10-28T08:38Z] Makefile bug (protected file, plan 3.4 says record it): the `harden` recipe passes `--force-run-dir runs/<tag>` but LibreLane 3.0.16 requires that directory to already exist (`Error: Invalid value for '--force-run-dir': Directory 'runs/mac-w8-a1' does not exist`). Fix to apply by hand: add `mkdir -p $(RUN_DIR)` as the first line of the `harden` recipe. Overnight workaround: factory/orchestrate.py, factory/sweep.py and factory/verify.py create runs/<tag> before calling `make harden`; manual `make harden` needs `mkdir -p runs/<tag>` first.
- [2026-10-28T08:50Z] MAC standalone timing at 10 ns (100 MHz) did not close: all violators are input-to-register paths `b[0] -> acc[*]` through the 8x8 multiplier + 32-bit adder, with the PDK's placeholder 20 % input delay (2.0 ns at 10 ns) added on top (`runs/mac-w8-a3/*-openroad-stapostpnr/max_ss_100C_1v60/violator_list.rpt`: 18 `[setup in-reg]` entries, worst -0.836 ns at max_ss_100C_1v60; reg-to-reg and all hold corners clean). Decision for you: either accept a relaxed standalone clock (the closure loop keeps relaxing in 10 % steps up to the 20 ns cap, i.e. the Tiny Tapeout 50 MHz clock), or provide a custom SDC with realistic input delays for `a`/`b` (`PNR_SDC_FILE`/`SIGNOFF_SDC_FILE`, plan 5.1), or pipeline the RTL between multiply and accumulate (Appendix C step 9). Inside the TT wrapper the operands come from registers, so the in-reg budget there is a real reg-to-reg path at 20 ns.
- [2026-10-28T09:12Z] GitHub repo NOT created: Claude Code's auto-mode permission classifier refused `gh repo create NoahSabb/tt-um-noahsabb-mac --template TinyTapeout/ttsky-verilog-template` both `--public` ("Create Public Surface") and `--private`, and I did not work around it. Everything else of Phase 7 was done in a local clone of the template at `tt_repo/` (the classifier also refused `git remote set-url`, so origin still points at the template). To finish (2 minutes): `gh repo create NoahSabb/tt-um-noahsabb-mac --public --description "2x2 int8 MAC array for Tiny Tapeout TTSKY26d"` (plain, not from template — tt_repo/ already contains the template files and history), then `cd tt_repo && git remote set-url origin https://github.com/NoahSabb/tt-um-noahsabb-mac && git push -u origin main`, then `gh run list --repo NoahSabb/tt-um-noahsabb-mac --json name,conclusion,url,databaseId > ../factory/state/tt_actions.json` after the `gds` workflow finishes (~15 min), and `make report` again to pull the Actions table into the morning report. Also enable GitHub Pages (Settings → Pages → Source: GitHub Actions) for the `viewer` job.
- [2026-10-28T09:25Z] Tile decision (sets the price): with `tiles: "1x2"` LibreLane's floorplan reported `Effective utilization: 1.152` (the 3330-cell wrapper needs ~25,165 um² of standard cells; a 1x2 core is ~22,000 um²), so the overnight run switched `info.yaml` to `tiles: "2x2"` (plan 5.2 rule: utilization > 65 % -> 2x2). Measured 2x2 utilization is in `factory/state/tt_sta_report.txt` / the morning report once the local harden finishes. A 1x2 tile is only possible with a smaller design (e.g. a single MAC or 16-bit accumulators).
- [2026-10-28T09:25Z] Docker Desktop 4.73 / macOS 26.5 virtiofs crash (Phase 0 F4) reproduced twice tonight during `tt_tool.py --harden` (`error waiting for container: unexpected EOF`, VM dies at Yosys.Synthesis / OpenROAD.Floorplan; `docker desktop restart` recovers it). The local TT harden therefore ran with `--no-docker` inside `nix-shell ~/librelane/shell.nix` (pip LibreLane 3.0.14 flow + Nix tool binaries from the 3.0.16 shell), so it is NOT bit-identical to the CI action; the GitHub Actions `gds` job is authoritative. Consider Docker Desktop → Settings → Resources → File sharing implementation: virtiofs → gRPC FUSE.
- [2026-10-28T09:45Z] Makefile (protected) fixes for the two Tiny Tapeout targets, applied by hand tonight via factory/gate.py: `tt-harden` must put `$(CURDIR)/.venv-tt/bin` first on PATH (otherwise `python -m librelane` inside tt_tool.py resolves to .venv's LibreLane 3.0.16) and, while Docker Desktop keeps crashing, use `--harden --no-docker` inside `$(NIX_SHELL)`; `precheck` must export `PDK_ROOT`, put `.venv-tt/bin` (yowasp-yosys) and `tools/bin` (klayout wrapper; the precheck nix-shell has no klayout binary on macOS) on PATH, and pass an absolute `--gds` path (YOWASP_MOUNT rejects relative paths). The gate records `tt-harden` and `precheck` in factory/state/gates.json come from those corrected commands (see logs/gates/tt-harden.log, logs/gates/precheck.log).
- [2026-10-28T09:35Z] Tiny Tapeout timing at the template's 20 ns (50 MHz) clock: the local harden exits 0 because the TT template only checks the `*tt*` corners (LibreLane PDK default `TIMING_VIOLATION_CORNERS`), but the signoff STA at `max_ss_100C_1v60` shows setup ws = -1.666 ns with 36 violating endpoints (`tt_repo/runs/wokwi/*-openroad-stapostpnr/summary.rpt`, copied to `factory/state/tt_sta_report.txt`); nominal tt corner has +8.99 ns and all hold corners are positive (worst +0.118 ns at min_ff). Decision for you: keep 50 MHz (works at nominal, may fail on a slow/hot/low-voltage die), or raise `CLOCK_PERIOD` in `tt_repo/src/config.json` (it is above the DO-NOT-EDIT line) to ~24 ns and set `clock_hz: 40000000` in info.yaml, then `make tt-harden` again (~3 min via Nix).


## Suggested first things to try this morning
1. `make serve` and click through the factory line; open the Signoff STA station and read `max.rpt` at `max_ss_100C_1v60` for the worst path.
2. Open the GDS: `nix-shell ~/librelane/shell.nix --run "librelane --flow OpenInKLayout --run-tag verify-20261028-023124 --force-run-dir runs/verify-20261028-023124 flow/mac_int8/config.json"` (or `--flow OpenInOpenROAD`).
3. Check the GitHub Actions links above; if `gds`/`precheck`/`gl_test` are green, go to https://app.tinytapeout.com/projects/create, paste the repo URL, choose TTSKY26d, pay or enter a coupon, and press "Submit a new revision" before 2026-11-30.
4. Decide the tile count (see NEEDS HUMAN) and whether 50 MHz is the final clock; re-run `make tt-harden` after any change.
5. Re-run the sweep at finer clock periods near the WNS zero crossing: `.venv/bin/python factory/sweep.py --widths 8 --periods 6,7,8`.
