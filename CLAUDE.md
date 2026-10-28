# CLAUDE.md — spec2tapeout factory

You are running an unattended overnight build. The full plan is TAPEOUT_FACTORY_PLAN.md; this file is the short memory that survives compaction. When compacting, always preserve: the current phase number, the list of files modified in this phase, the current run TAG, and the last three gate results.

## Rules (verbatim from the plan; enforced by settings.json deny rules, .claude/hooks/guard.py and chmod)
1. Never edit anything under tests/golden/ or the Python reference models under ref/ once they are written and approved in Phase 2 (make freeze-golden). Fix RTL or testbench drivers instead; if you believe a vector is wrong, write the evidence in NEEDS_HUMAN.md and move on.
2. Never mark a gate as passed unless the gate's command exited 0. factory/gate.py records the real exit code.
3. Every phase ends with a git commit whose message starts with "phase N:".
4. Keep a running log at logs/overnight.md with ISO-8601 timestamps (make log MSG="...").
5. On any failure retry at most 3 times with a changed hypothesis, then record it in NEEDS_HUMAN.md and move on.
6. Never run rm -rf outside runs/. Only the Makefile deletes (make clean, make clean-run TAG=...).
7. Never suggest or use skip-permissions flags.
8. caffeinate is already running but run `caffeinate -dimsu &` anyway at the start.
9. Time budget per phase: P0 60, P1 20, P2 60, P3 20, P4 45, P5 40, P6 90, P7 60, P8 45 minutes (make elapsed).
10. Stop and write the morning report (make report) if total elapsed time exceeds 8 hours (28800 s).
11. Never ask the human anything.
12. Never disable a checker (ERROR_ON_*, RUN_LINTER, RUN_*_DRC, RUN_KLAYOUT_XOR, RUN_LVS), never exclude corners, never set *_ALLOW_SETUP_VIOS, never edit Tiny Tapeout src/config.json below its DO-NOT-EDIT line.
13. Only OpenROAD.STAPostPNR (post-RCX) timing counts; STAMidPNR/STAPrePNR are surrogates.
14. Show evidence: command + exit code in the log; every reported metric names its source file.

## Flow order (gate ladder; run with make, never edit the Makefile targets)
doctor -> lint -> sim -> synth -> harden -> sta-report -> sim-gl -> render -> sweep -> dashboard -> precheck (tt_repo) -> verify-factory -> report

## Commands you cannot guess
- All LibreLane commands run inside Nix: `nix-shell ~/librelane/shell.nix --run "librelane ..."` (Makefile variable NIX_SHELL).
- Python is always `.venv/bin/python` (never conda, never bare python).
- `make harden TAG=<tag>` writes runs/<tag>/ ; `make harden-closure TAG=<tag>` runs the retry loop in factory/orchestrate.py.
- `make sim WIDTH=8`, `make sim-gl TAG=<tag>` (gate-level, uses runs/<tag>/final/pnl/mac_int8.pnl.v).
- Dashboard: `make dashboard` then `make serve` (http://localhost:8787).

## Where things live
- Run outputs: runs/<tag>/NN-<tool>-<step>/ (COMMANDS, config.json, state_in.json, state_out.json, <step>.log) and runs/<tag>/final/{gds,pnl,nl,sdf,spef,lib,def,lef,render,metrics.json,metrics.csv}; runs/<tag>/{flow.log,error.log,warning.log,resolved.json}.
- STA: runs/<tag>/*-openroad-stapostpnr/summary.rpt and <corner>/{max.rpt,min.rpt,checks.rpt,violator_list.rpt,clock.rpt,unpropagated.rpt,power.rpt}.
- DRC: *-magic-drc/reports/drc.klayout.xml, *-klayout-drc/report/drc.lyrdb. LVS: *-netgen-lvs/netgen-lvs.log ("Final result: Circuits match uniquely.").
- Factory state: factory/state/{pipeline.json,gates.json,decisions.json,sweep.csv}. Log: logs/overnight.md. Report: reports/MORNING_REPORT.md. Human queue: NEEDS_HUMAN.md.

## Pass criteria (final/metrics.json unless noted)
design__lint_error__count=0; synthesis__check_error__count=0; design__instance_unmapped__count=0; design__inferred_latch__count=0;
timing__setup__ws>=0 and timing__hold__ws>=0 on all nine corners (max_ss_100C_1v60 binds setup, min_ff_n40C_1v95 binds hold); timing__setup_vio__count=timing__hold_vio__count=0;
route__drc_errors=0; antenna__violating__pins=0 (or explained); magic__drc_error__count=0; klayout__drc_error__count=0; design__xor_difference__count=0; magic__illegal_overlap__count=0; design__lvs_error__count=0; design__critical_disconnected_pin__count=0; timing__unannotated_net_filtered__count=0;
cocotb results.xml has no <failure> or <error>; librelane exit code 0.

## Never edit (after freeze): tests/golden/**, ref/**, .claude/**
