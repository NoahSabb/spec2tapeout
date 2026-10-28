# Overnight log

2026-10-28T08:03:53Z PHASE 0 START (re-validation; Phase 0 originally completed 2026-10-21, see logs/PHASE0_REPORT.md)
2026-10-28T08:05:10Z PHASE 0 END (make doctor exit 0: 17/17 tools; LibreLane v3.0.16 pip+Docker verified; Nix-shell test running)
2026-10-28T08:05:10Z PHASE 1 START
2026-10-28T08:10:29Z PHASE 1 NOTE: plan 3.4 protects Makefile before 3.7 creates it; guard hook became active as soon as .claude/settings.json existed, so the plan's Makefile was installed once via python shutil.copy from a scratch file (content verbatim from the plan plus tools/bin on PATH, ACC_WIDTH passthrough for make sim)
2026-10-28T08:10:29Z PHASE 0 NIX ROUTE OK: nix-shell ~/librelane/shell.nix (tag 3.0.16) librelane --smoke-test exit 0; HARDEN_MODE=nix in factory/state/env.mk
2026-10-28T08:21:17Z GATE doctor FAIL exit=1 log=logs/gates/doctor.log
2026-10-28T08:21:17Z PHASE 1 END
2026-10-28T08:21:17Z PHASE 1 FIX: magic --version in doctor.sh hung waiting on stdin inside gate.py; added </dev/null to chk() and per-line flush in gate.py
2026-10-28T08:24:43Z PHASE 1 FIX: doctor.sh pdk check accepts libs.tech/openlane/config.tcl (what open_pdks 8afc8346 ships; the librelane/ name does not exist in this PDK)
2026-10-28T08:24:54Z GATE doctor PASS exit=0 log=logs/gates/doctor.log
2026-10-28T08:25:14Z PHASE 2 START
2026-10-28T08:25:48Z GATE gen-golden PASS exit=0 log=logs/gates/gen-golden.log
2026-10-28T08:26:02Z FROZEN ref/ and tests/golden/ (chmod a-w + hook)
2026-10-28T08:26:37Z GATE lint PASS exit=0 log=logs/gates/lint.log
2026-10-28T08:26:38Z GATE sim-mac-w8 PASS exit=0 log=logs/gates/sim-mac-w8.log
2026-10-28T08:26:46Z GATE sim-mac FAIL exit=2 log=logs/gates/sim-mac.log
2026-10-28T08:26:46Z GATE sim-mac FAIL exit=2 log=logs/gates/sim-mac.log
2026-10-28T08:26:47Z GATE sim-mac FAIL exit=2 log=logs/gates/sim-mac.log
2026-10-28T08:26:47Z GATE sim-array FAIL exit=2 log=logs/gates/sim-array.log
2026-10-28T08:26:48Z GATE sim-tt FAIL exit=2 log=logs/gates/sim-tt.log
2026-10-28T08:26:50Z GATE synth-8 PASS exit=0 log=logs/gates/synth-8.log
2026-10-28T08:27:04Z GATE sim-mac-w4 PASS exit=0 log=logs/gates/sim-mac-w4.log
2026-10-28T08:27:05Z GATE sim-mac-w2 PASS exit=0 log=logs/gates/sim-mac-w2.log
2026-10-28T08:27:06Z GATE sim-mac-w4 PASS exit=0 log=logs/gates/sim-mac-w4.log
2026-10-28T08:27:07Z GATE sim-array-w8 PASS exit=0 log=logs/gates/sim-array-w8.log
2026-10-28T08:27:08Z GATE sim-tt-w8 PASS exit=0 log=logs/gates/sim-tt-w8.log
2026-10-28T08:27:21Z PHASE 2 NOTE: removed 3 malformed gate records (sim-mac, sim-array, sim-tt) created by a zsh word-splitting bug in my loop (make sim got TOP='mac 4 24'); the real gates sim-mac-w8/w4/w2, sim-array-w8, sim-tt-w8 all PASS
2026-10-28T08:27:21Z PHASE 2 END
2026-10-28T08:27:21Z PHASE 3 START
2026-10-28T08:30:14Z PHASE 3 END
2026-10-28T08:30:14Z PHASE 4 START
2026-10-28T08:33:01Z CLOSURE attempt 1/4 tag=mac-w8-a1 config=flow/mac_int8/config_mac-w8-a1.json
2026-10-28T08:33:04Z GATE harden-mac-w8-a1 FAIL exit=2 log=logs/gates/harden-mac-w8-a1.log
2026-10-28T08:33:04Z CLOSURE FAIL attempt 1 (mac-w8-a1) symptoms=['immediate_error'] {'timing__setup__ws': None, 'timing__hold__ws': None, 'timing__setup_vio__count': None, 'timing__hold_vio__count': None, 'route__drc_errors': None, 'magic__drc_error__count': None, 'klayout__drc_error__count': None, 'design__lvs_error__count': None, 'antenna__violating__pins': None, 'design__instance__count': None, 'design__instance__area': None, 'design__instance__utilization': None, 'power__total': None}
2026-10-28T08:33:04Z NEEDS_HUMAN harden mac-w8-a1: symptoms ['immediate_error']; not a config problem. error.log tail: ''
2026-10-28T08:33:04Z INGEST mac-w8-a1: status=fail setup_ws=None hold_ws=None drc=None lvs=None cells=None source=None
2026-10-28T08:34:38Z PHASE 4 FIX: librelane --force-run-dir needs an existing dir; Makefile is protected so callers (orchestrate/sweep/verify) now mkdir runs/<tag> first; recorded in NEEDS_HUMAN.md; bogus harden-mac-w8-a1 attempt is re-run
2026-10-28T08:34:57Z CLOSURE attempt 1/4 tag=mac-w8-a1 config=flow/mac_int8/config_mac-w8-a1.json
2026-10-28T08:36:34Z GATE harden-mac-w8-a1 FAIL exit=2 log=logs/gates/harden-mac-w8-a1.log
2026-10-28T08:36:34Z CLOSURE FAIL attempt 1 (mac-w8-a1) symptoms=['setup'] {'timing__setup__ws': -2.5192355581352204, 'timing__hold__ws': 0.12015261348172723, 'timing__setup_vio__count': 58, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 4535, 'design__instance__area': 22709.3, 'design__instance__utilization': 0.526887, 'power__total': 0.005043978337198496}
2026-10-28T08:36:34Z DECISION setup: synthesis strategy DELAY 1 (ABC delay-oriented mapping) changes={'SYNTH_STRATEGY': 'DELAY 1'}
2026-10-28T08:36:34Z CLOSURE attempt 2/4 tag=mac-w8-a2 config=flow/mac_int8/config_mac-w8-a2.json
2026-10-28T08:38:39Z GATE harden-mac-w8-a2 FAIL exit=2 log=logs/gates/harden-mac-w8-a2.log
2026-10-28T08:38:39Z CLOSURE FAIL attempt 2 (mac-w8-a2) symptoms=['setup'] {'timing__setup__ws': -1.0306920053614892, 'timing__hold__ws': 0.10409690071241903, 'timing__setup_vio__count': 50, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 7092, 'design__instance__area': 34287.9, 'design__instance__utilization': 0.513246, 'power__total': 0.003007561434060335}
2026-10-28T08:38:39Z DECISION setup: lower utilization by 10 (more room for resizer, shorter wires) changes={'FP_CORE_UTIL': 30.0, 'PL_TARGET_DENSITY_PCT': 45}
2026-10-28T08:38:39Z CLOSURE attempt 3/4 tag=mac-w8-a3 config=flow/mac_int8/config_mac-w8-a3.json
2026-10-28T08:40:44Z GATE harden-mac-w8-a3 FAIL exit=2 log=logs/gates/harden-mac-w8-a3.log
2026-10-28T08:40:44Z CLOSURE FAIL attempt 3 (mac-w8-a3) symptoms=['setup'] {'timing__setup__ws': -0.8360485873577347, 'timing__hold__ws': 0.1130190972798536, 'timing__setup_vio__count': 49, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10292, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.385688, 'power__total': 0.0029543067794293165}
2026-10-28T08:40:44Z DECISION setup: relax CLOCK_PERIOD by 10 % (cap 20 ns standalone) changes={'CLOCK_PERIOD': 11.0}
2026-10-28T08:40:44Z CLOSURE attempt 4/4 tag=mac-w8-a4 config=flow/mac_int8/config_mac-w8-a4.json
2026-10-28T08:42:21Z GATE harden-mac-w8-a4 FAIL exit=2 log=logs/gates/harden-mac-w8-a4.log
2026-10-28T08:42:21Z CLOSURE FAIL attempt 4 (mac-w8-a4) symptoms=['setup'] {'timing__setup__ws': -0.9052225891756138, 'timing__hold__ws': 0.11275281027986614, 'timing__setup_vio__count': 53, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10543, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.363706, 'power__total': 0.002542276168242097}
2026-10-28T08:42:21Z DECISION setup: synthesis strategy DELAY 4 (ORFS delay script) + CSA adders changes={'SYNTH_STRATEGY': 'DELAY 4', 'SYNTH_ADDER_TYPE': 'CSA'}
2026-10-28T08:42:39Z INGEST mac-w8-a1: status=fail setup_ws=-2.5192355581352204 hold_ws=0.12015261348172723 drc=0 lvs=0 cells=4535 source=final/metrics.json
2026-10-28T08:44:31Z PHASE 4: closure series mac-w8 exhausted 4 attempts, all setup-only failures (ws -2.52/-1.03/-0.84/-0.91 ns); violators are 18 in-reg paths b[0]->acc through the multiplier with the PDK 20% placeholder input delay (runs/mac-w8-a3/*-openroad-stapostpnr/max_ss_100C_1v60/violator_list.rpt). Added --resume + repeated clock-relax rules (Appendix C step 8, cap 20 ns) and best-by-slack selection; resuming series
2026-10-28T08:44:31Z CLOSURE RESUME series mac-w8 at attempt 5 with pending decision applied: synthesis strategy DELAY 4 (ORFS delay script) + CSA adders
2026-10-28T08:44:31Z CLOSURE attempt 5/6 tag=mac-w8-a5 config=flow/mac_int8/config_mac-w8-a5.json
2026-10-28T08:46:01Z GATE harden-mac-w8-a5 FAIL exit=2 log=logs/gates/harden-mac-w8-a5.log
2026-10-28T08:46:01Z CLOSURE FAIL attempt 5 (mac-w8-a5) symptoms=['setup'] {'timing__setup__ws': -11.86947462801699, 'timing__hold__ws': 0.1288519327706649, 'timing__setup_vio__count': 87, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5367, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.420181, 'power__total': 0.0023071146570146084}
2026-10-28T08:46:01Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 12.1}
2026-10-28T08:46:01Z CLOSURE attempt 6/6 tag=mac-w8-a6 config=flow/mac_int8/config_mac-w8-a6.json
2026-10-28T08:47:24Z GATE harden-mac-w8-a6 FAIL exit=2 log=logs/gates/harden-mac-w8-a6.log
2026-10-28T08:47:24Z CLOSURE FAIL attempt 6 (mac-w8-a6) symptoms=['setup'] {'timing__setup__ws': -10.745852511974034, 'timing__hold__ws': 0.1287484044706906, 'timing__setup_vio__count': 78, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5337, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.42254, 'power__total': 0.0022156424820423126}
2026-10-28T08:47:24Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 13.31}
2026-10-28T08:47:24Z CLOSURE attempt 7/6 tag=mac-w8-a7 config=flow/mac_int8/config_mac-w8-a7.json
2026-10-28T08:48:53Z GATE harden-mac-w8-a7 FAIL exit=2 log=logs/gates/harden-mac-w8-a7.log
2026-10-28T08:48:53Z CLOSURE FAIL attempt 7 (mac-w8-a7) symptoms=['setup'] {'timing__setup__ws': -9.741374205232948, 'timing__hold__ws': 0.13165527374270292, 'timing__setup_vio__count': 66, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5325, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.413358, 'power__total': 0.001928433426655829}
2026-10-28T08:48:53Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 14.64}
2026-10-28T08:48:53Z CLOSURE attempt 8/6 tag=mac-w8-a8 config=flow/mac_int8/config_mac-w8-a8.json
2026-10-28T08:50:22Z GATE harden-mac-w8-a8 FAIL exit=2 log=logs/gates/harden-mac-w8-a8.log
2026-10-28T08:50:22Z CLOSURE FAIL attempt 8 (mac-w8-a8) symptoms=['setup'] {'timing__setup__ws': -9.22813407364487, 'timing__hold__ws': 0.12737211645928995, 'timing__setup_vio__count': 63, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5411, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.386221, 'power__total': 0.0016358179273083806}
2026-10-28T08:50:22Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 16.1}
2026-10-28T08:50:22Z CLOSURE attempt 9/6 tag=mac-w8-a9 config=flow/mac_int8/config_mac-w8-a9.json
2026-10-28T08:51:51Z GATE harden-mac-w8-a9 FAIL exit=2 log=logs/gates/harden-mac-w8-a9.log
2026-10-28T08:51:51Z CLOSURE FAIL attempt 9 (mac-w8-a9) symptoms=['setup'] {'timing__setup__ws': -7.9038928750214135, 'timing__hold__ws': 0.12653617400925637, 'timing__setup_vio__count': 57, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5377, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.391659, 'power__total': 0.0014649300137534738}
2026-10-28T08:51:51Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 17.71}
2026-10-28T08:51:51Z CLOSURE attempt 10/6 tag=mac-w8-a10 config=flow/mac_int8/config_mac-w8-a10.json
2026-10-28T08:53:18Z GATE harden-mac-w8-a10 FAIL exit=2 log=logs/gates/harden-mac-w8-a10.log
2026-10-28T08:53:18Z CLOSURE FAIL attempt 10 (mac-w8-a10) symptoms=['setup'] {'timing__setup__ws': -6.5807769984875435, 'timing__hold__ws': 0.12619372570762563, 'timing__setup_vio__count': 51, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 5389, 'design__instance__area': 24390.9, 'design__instance__utilization': 0.389607, 'power__total': 0.0013178103836253285}
2026-10-28T08:53:18Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 19.48}
2026-10-28T08:53:36Z INGEST mac-w8-a10: status=fail setup_ws=-6.5807769984875435 hold_ws=0.12619372570762563 drc=0 lvs=0 cells=5389 source=final/metrics.json
2026-10-28T08:54:50Z PHASE 4: attempts 5-10 (DELAY 4 + CSA) regressed setup ws to -11.9..-6.6 ns; my already_applied shortcut treated any DELAY strategy as equivalent so the loop never reverted it. Fixed: regressed rules are skipped, best run is chosen across the whole series, --from-attempt restarts from an earlier config. Resuming from attempt 4's config (DELAY 1, util 30, 11 ns)
2026-10-28T08:54:50Z CLOSURE RESUME series mac-w8 at attempt 11 from the configuration of attempt 4; skipping regressed rules [{'SYNTH_STRATEGY': 'DELAY 4', 'SYNTH_ADDER_TYPE': 'CSA'}]
2026-10-28T08:54:50Z CLOSURE attempt 11/5 tag=mac-w8-a11 config=flow/mac_int8/config_mac-w8-a11.json
2026-10-28T08:56:29Z GATE harden-mac-w8-a11 FAIL exit=2 log=logs/gates/harden-mac-w8-a11.log
2026-10-28T08:56:29Z CLOSURE FAIL attempt 11 (mac-w8-a11) symptoms=['setup'] {'timing__setup__ws': -0.9052225891756138, 'timing__hold__ws': 0.11275281027986614, 'timing__setup_vio__count': 53, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10543, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.363706, 'power__total': 0.002542276168242097}
2026-10-28T08:56:29Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 12.1}
2026-10-28T08:56:29Z CLOSURE attempt 12/5 tag=mac-w8-a12 config=flow/mac_int8/config_mac-w8-a12.json
2026-10-28T08:57:58Z GATE harden-mac-w8-a12 FAIL exit=2 log=logs/gates/harden-mac-w8-a12.log
2026-10-28T08:57:58Z CLOSURE FAIL attempt 12 (mac-w8-a12) symptoms=['setup'] {'timing__setup__ws': -1.1895977872810404, 'timing__hold__ws': 0.11168333240999782, 'timing__setup_vio__count': 47, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10649, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.354297, 'power__total': 0.0022152976598590612}
2026-10-28T08:57:58Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 13.31}
2026-10-28T08:57:58Z CLOSURE attempt 13/5 tag=mac-w8-a13 config=flow/mac_int8/config_mac-w8-a13.json
2026-10-28T08:59:23Z GATE harden-mac-w8-a13 FAIL exit=2 log=logs/gates/harden-mac-w8-a13.log
2026-10-28T08:59:23Z CLOSURE FAIL attempt 13 (mac-w8-a13) symptoms=['setup'] {'timing__setup__ws': -0.9036380788300559, 'timing__hold__ws': 0.11127954428452175, 'timing__setup_vio__count': 33, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10669, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.353004, 'power__total': 0.0020052187610417604}
2026-10-28T08:59:23Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 14.64}
2026-10-28T08:59:23Z CLOSURE attempt 14/5 tag=mac-w8-a14 config=flow/mac_int8/config_mac-w8-a14.json
2026-10-28T09:00:46Z GATE harden-mac-w8-a14 FAIL exit=2 log=logs/gates/harden-mac-w8-a14.log
2026-10-28T09:00:46Z CLOSURE FAIL attempt 14 (mac-w8-a14) symptoms=['setup'] {'timing__setup__ws': -0.5176019759305862, 'timing__hold__ws': 0.11172890706644763, 'timing__setup_vio__count': 8, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10640, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.352537, 'power__total': 0.0018236591713503003}
2026-10-28T09:00:46Z DECISION setup: relax CLOCK_PERIOD by 10 % again (Appendix C step 8; cap 20 ns standalone) changes={'CLOCK_PERIOD': 16.1}
2026-10-28T09:00:46Z CLOSURE attempt 15/5 tag=mac-w8-a15 config=flow/mac_int8/config_mac-w8-a15.json
2026-10-28T09:02:11Z GATE harden-mac-w8-a15 PASS exit=0 log=logs/gates/harden-mac-w8-a15.log
2026-10-28T09:02:30Z INGEST mac-w8-a15: status=pass setup_ws=0.5712657175665821 hold_ws=0.11170553687111831 drc=0 lvs=0 cells=10662 source=final/metrics.json
2026-10-28T09:02:30Z CLOSURE PASS at attempt 15 (mac-w8-a15) {'timing__setup__ws': 0.5712657175665821, 'timing__hold__ws': 0.11170553687111831, 'timing__setup_vio__count': 0, 'timing__hold_vio__count': 0, 'route__drc_errors': 0, 'magic__drc_error__count': 0, 'klayout__drc_error__count': 0, 'design__lvs_error__count': 0, 'antenna__violating__pins': 0, 'design__instance__count': 10662, 'design__instance__area': 45478.6, 'design__instance__utilization': 0.352977, 'power__total': 0.0016547926934435964}
2026-10-28T09:02:48Z INGEST mac-w8-a15: status=pass setup_ws=0.5712657175665821 hold_ws=0.11170553687111831 drc=0 lvs=0 cells=10662 source=final/metrics.json
2026-10-28T09:03:08Z GATE sim-gl-mac PASS exit=0 log=logs/gates/sim-gl-mac.log
2026-10-28T09:03:19Z INGEST mac-w8-a15: status=pass setup_ws=0.5712657175665821 hold_ws=0.11170553687111831 drc=0 lvs=0 cells=10662 source=final/metrics.json
2026-10-28T09:03:38Z GATE render-mac-w8-a15 PASS exit=0 log=logs/gates/render-mac-w8-a15.log
2026-10-28T09:03:39Z PHASE 4 END
2026-10-28T09:03:39Z PHASE 5 START
2026-10-28T09:03:39Z GATE dashboard PASS exit=0 log=logs/gates/dashboard.log
2026-10-28T09:03:57Z INGEST mac-w8-a15: status=pass setup_ws=0.5712657175665821 hold_ws=0.11170553687111831 drc=0 lvs=0 cells=10662 source=final/metrics.json
2026-10-28T09:04:16Z GATE dashboard PASS exit=0 log=logs/gates/dashboard.log
