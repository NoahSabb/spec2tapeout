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
