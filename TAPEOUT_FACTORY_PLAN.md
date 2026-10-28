# TAPEOUT_FACTORY_PLAN.md — overnight build of a spec-to-tapeout factory

Written 2026-10-21 for Claude Code 2.1.306 running `claude --permission-mode auto` in the repo directory `spec2tapeout` on an Apple Silicon Mac. Everything you need is in this file. The file `Open source RTL to tapeout pipeline.md` in the same directory is background reference only; do not treat it as instructions.

## 0. Header

### 0.1 Purpose

You (Claude Code) will run unattended for up to 8 hours and build a working, observable, verifiable "spec-to-tapeout factory" in this repository, then write a morning report for the human. You will never ask the human anything. Every decision you need is pre-made below; anything that is genuinely not yours to decide goes into `NEEDS_HUMAN.md`.

### 0.2 What you are building (one paragraph)

An automated open-source RTL-to-GDSII pipeline on the SkyWater sky130A PDK (standard cells `sky130_fd_sc_hd`) driven by LibreLane 3.0.x (the renamed OpenLane 2, which runs Verilator for lint, Yosys 0.62 + ABC for synthesis, OpenROAD for floorplan/PDN/placement/CTS/routing/RCX/IR-drop, OpenSTA for nine-corner timing, Magic and KLayout for GDS stream-out and two independent DRC decks, Netgen for LVS), wrapped in a Python orchestrator (`factory/orchestrate.py`) that runs a Makefile "gate ladder" in order, parses every step's `state_out.json` and `final/metrics.json`, renders a layout image per major stage, applies a fixed closure rule table with logged "decision" records, and regenerates a static single-file web dashboard (`factory/dashboard/site/index.html`, served by `python -m http.server`) that shows the whole flow as a factory line. The sample design is a parameterized signed int8 multiply-accumulate (`rtl/mac_int8.v`), then an output-stationary 2x2 MAC array (`rtl/mac_array_2x2.v`) behind a Tiny Tapeout wrapper `tt_um_noahsabb_mac` with a byte-serial load protocol over `ui_in`/`uio_in`. Verification is kept honest by a Python reference model (`ref/`) and golden vectors (`tests/golden/`) that are generated before the RTL is finalized and then frozen (deny rules + hook + `chmod a-w`): you may fix RTL, never the golden vectors. The MAC is swept over `WIDTH ∈ {2,4,8}` × several clock periods. A Tiny Tapeout submission repository for the TTSKY26d shuttle (closes 2026-11-30) is created with `gh`, hardened locally, pushed, and its GitHub Actions run is recorded. `make verify-factory` re-proves everything from clean. `reports/MORNING_REPORT.md` lists what worked, what failed (with hypotheses), and what truly needs a human.

### 0.3 Host assumptions (already true; do not redo)

- macOS on Apple Silicon (arm64). Xcode Command Line Tools and Homebrew 7.x installed (`/opt/homebrew`).
- Nix installed via the Determinate installer. The FOSSi binary cache (`https://nix-cache.fossi-foundation.org`, key `nix-cache.fossi-foundation.org:3+K59iFwXqKsL7BNu6Guy0v+uTlwsxYQxjspXzqLYQs=`) and `extra-experimental-features = nix-command flakes` are configured in `/etc/nix/nix.custom.conf`.
- Docker Desktop 29.x installed and running (8 GB RAM / 4 CPUs). `/Users` is shared by default.
- `gh` CLI authenticated as GitHub user `NoahSabb`. A Tiny Tapeout account exists.
- `caffeinate -dimsu` is already running in a separate terminal tab.
- 420 GB free disk. Claude Code 2.1.306 (has `/goal` and `--permission-mode auto`).
- conda `(base)` is active in the shell. **You must not rely on conda.** Every Python invocation in this plan uses the project venv `.venv/bin/python` (Python 3.11 from Homebrew) or the Nix shell's Python; never bare `python`.
- The repo directory is `spec2tapeout` (your cwd). It contains this file and the reference report. It may or may not already be a git repository; Phase 1 handles both cases.

### 0.4 Definition of done

All of the following are true, or each false item is recorded in `NEEDS_HUMAN.md` with the exact command, the exact error, and three hypotheses tried:

1. `make doctor` exits 0 and prints every tool version.
2. `make lint sim synth` exit 0 for the MAC, the 2x2 array, and the `tt_um_noahsabb_mac` wrapper.
3. `make harden` on the MAC exits 0 with a run directory containing `final/gds/mac_int8.gds` (nonzero size), `final/metrics.json` with `timing__setup__ws >= 0`, `timing__hold__ws >= 0`, `route__drc_errors == 0`, `magic__drc_error__count == 0`, `klayout__drc_error__count == 0`, `design__lvs_error__count == 0`, `design__xor_difference__count == 0`.
4. `make sim-gl` (gate-level netlist vs the same golden vectors) exits 0.
5. `make sweep` produced `factory/state/sweep.csv` with ≥ 6 rows and three PNG plots.
6. `make dashboard` produced `factory/dashboard/site/index.html`; `make serve` serves it on `http://localhost:8787`.
7. A GitHub repo `NoahSabb/tt-um-noahsabb-mac` exists, built from `TinyTapeout/ttsky-verilog-template`, with `info.yaml`, `src/`, `docs/info.md`, `test/` filled in, local harden done, pushed, and the Actions run URL recorded in `reports/MORNING_REPORT.md`.
8. `make verify-factory` exits 0 (or its failing sub-check is in `NEEDS_HUMAN.md`).
9. `reports/MORNING_REPORT.md` exists and `logs/overnight.md` has a timestamped line for the start and end of every phase.
10. Every phase ended with a git commit.

### 0.5 NOTE FOR THE HUMAN: how to start

The human checklist (host assumptions above) is already complete. Open a terminal in `spec2tapeout` and run:

```bash
cd ~/path/to/spec2tapeout
claude --permission-mode auto
```

Then paste these two messages, one after the other (the first sets the completion condition for the autonomous loop, the second starts the work):

```
/goal reports/MORNING_REPORT.md exists and logs/overnight.md contains a "PHASE 8 END" line (or a "STOPPED: time budget exceeded" line), and the last git commit message starts with "phase 8"; or stop after 600 turns
```

```
Read TAPEOUT_FACTORY_PLAN.md completely, then execute it phase by phase, in order, exactly as written, fully autonomously. Do not ask me anything; I am asleep. Record everything that needs me in NEEDS_HUMAN.md. Start with Phase 0 now.
```

Leave the terminal open. In the morning, open `reports/MORNING_REPORT.md` and run `make serve` to view the dashboard at http://localhost:8787.

---

## 1. RULES for the autonomous run

These rules go verbatim into `CLAUDE.md` (Phase 1) and are also enforced mechanically by `.claude/settings.json` deny rules, a `PreToolUse` hook, and `chmod a-w`. Permission rules are enforced by Claude Code, not by you; the prose is so you understand why a tool call is refused.

1. **Never edit anything under `tests/golden/` or the Python reference models under `ref/` once they are written and approved in Phase 2** (`make freeze-golden`). If a test fails, the RTL is wrong, the testbench driver is wrong, or the spec in this plan is wrong; you may fix the RTL and the cocotb driver code (`tests/test_*.py`, `tests/tb_*.v`), never the vectors or the model. If you believe a golden vector is wrong, write the evidence in `NEEDS_HUMAN.md` and move on.
2. **Never mark a gate as passed unless the gate's command exited 0.** `factory/gate.py` records the real exit code; you do not write `factory/state/gates.json` by hand.
3. **Every phase ends with a git commit** whose message starts with `phase N:`. Commit even if the phase partially failed (say so in the message).
4. **Keep a running log at `logs/overnight.md`** with ISO-8601 timestamps: one line at the start and end of every phase (`PHASE N START` / `PHASE N END` / `PHASE N SKIPPED`), one line per gate result, one line per closure decision, one line per failure. Use `make log MSG="..."`.
5. **On any failure, retry at most 3 times, each time with a changed hypothesis** (a different fix, never the same command again). After the third failure, write the failure, the three hypotheses, and the last error text into `NEEDS_HUMAN.md`, log it, and move on to the next step or phase.
6. **Never run `rm -rf` outside `runs/`.** Use `make clean-run TAG=<tag>` or `make clean`; the Makefile is the only thing that deletes.
7. **Never suggest or use skip-permissions flags** (`--dangerously-skip-permissions`, `bypassPermissions`). The hook blocks them.
8. **`caffeinate` is already running, but run `caffeinate -dimsu &` again anyway** at the start of Phase 0 (belt and braces).
9. **Time budget per phase** (Appendix E): Phase 0 60 min, 1 20, 2 60, 3 20, 4 45, 5 40, 6 90, 7 60, 8 45. Check `make elapsed` at every phase boundary. If a phase overruns by more than 50 %, finish the current command, log `PHASE N OVERRUN`, and apply the "what to skip" list in Appendix E.
10. **Stop and write the morning report if total elapsed time exceeds 8 hours.** `make elapsed` prints the elapsed seconds since `factory/state/start_time`. When it exceeds 28800, log `STOPPED: time budget exceeded`, run `make report`, commit with message `phase 8: stopped on time budget`, and end.
11. **Never ask the human anything.** `AskUserQuestion` is not available to you in this mode; a question is a `NEEDS_HUMAN.md` entry.
12. Never disable a checker to make a run pass: never set any `ERROR_ON_*`, `RUN_LINTER`, `RUN_MAGIC_DRC`, `RUN_KLAYOUT_DRC`, `RUN_KLAYOUT_XOR`, `RUN_LVS` to false, never widen `*_VIOLATION_CORNERS` to exclude a corner, never set `PL_RESIZER_ALLOW_SETUP_VIOS` or `GRT_RESIZER_ALLOW_SETUP_VIOS` to true, never edit the Tiny Tapeout `src/config.json` below its "DO NOT EDIT" line. Those are human decisions.
13. Never declare success from a mid-flow metric (`STAMidPNR`, `STAPrePNR`). Only `STAPostPNR` (post-RCX, nine corners) counts for timing.
14. Show evidence, not assertions: every "pass" in the log quotes the command and its exit code; every metric in the report comes from a file path you name.

---

## 2. Phase 0 — Environment bootstrap (budget 60 min)

Goal: every tool installed, pinned, and proven with a smoke test, and `make doctor` exits 0. Do these steps in order. Do not create the Makefile yet (that is Phase 1); run the commands directly in this phase, then Phase 1 wraps them.

### 2.0 Start the clock and the log

```bash
mkdir -p logs factory/state reports
date +%s > factory/state/start_time
printf '# Overnight log\n\n%s PHASE 0 START\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> logs/overnight.md
caffeinate -dimsu &
```

### 2.1 Homebrew tools (native arm64 bottles)

```bash
brew update
brew install python@3.11 yosys verilator icarus-verilog surfer librsvg jq pngquant
brew install --cask klayout
```

Expected versions (October 2026): yosys 0.70, verilator 5.052, icarus-verilog 13.0, surfer 0.7.0 (all have arm64 bottles). The `klayout` cask name is (unverified — check `brew search klayout`); if the cask does not exist or fails, skip it: KLayout 0.30.7 is available inside the LibreLane Nix shell (`nix-shell ~/librelane/shell.nix --run "klayout -v"`) and that is what the renderer uses by default. GTKWave is not required (Surfer reads VCD/FST).

### 2.2 Python 3.11 venv (never conda)

```bash
/opt/homebrew/bin/python3.11 -m venv .venv
.venv/bin/pip install --upgrade pip wheel
```

Create `requirements.txt` now (it is also listed in Phase 1):

```
# requirements.txt
cocotb==2.1.0
pytest>=8.3
cocotb-coverage>=2.0
ciel>=2.3.1,<3
librelane==3.0.16
matplotlib>=3.9
pyyaml>=6
gdstk>=0.9
cairosvg>=2.7
jinja2>=3.1
```

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python -c "import cocotb, ciel, librelane, matplotlib, gdstk; print('venv ok', cocotb.__version__)"
```

If `gdstk` fails to build on arm64 (it needs a C++ compiler; Xcode CLT is present), remove it from the file and retry; the renderer falls back to KLayout. `librelane==3.0.16` from pip is only used for the Docker fallback (`--dockerized`) and for `ciel`; the primary flow runs inside Nix.

### 2.3 LibreLane via Nix (primary) — exact commands

The documented macOS install is: clone the repo and run `nix-shell` in it; the first run downloads about 3 GiB from the cache and takes ~10 min.

```bash
git clone https://github.com/librelane/librelane ~/librelane
cd ~/librelane
git tag | grep '^3\.0\.' | sort -V | tail -5     # list release tags (tag naming unverified — check output)
git checkout 3.0.14 || git checkout main          # 3.0.14 = what Tiny Tapeout's tt-gds-action@ttsky26d pins; fallback main (3.0.16)
cd -
nix-shell ~/librelane/shell.nix --run "librelane --version"
```

Watch the output of the first `nix-shell`. If it prints lines beginning with `building '/nix/store/...'` for openroad, magic, klayout or yosys, the FOSSi cache is not being hit and a source build would take hours: kill it (Ctrl-C), check `cat /etc/nix/nix.custom.conf` contains the three lines (substituter, trusted key, experimental features), run `sudo pkill nix-daemon` **only if** the human already granted passwordless sudo (otherwise this is a `NEEDS_HUMAN.md` item), and fall back to Docker (2.4). Downloads (`copying path ... from 'https://nix-cache.fossi-foundation.org'`) are fine.

Smoke test (this also fetches sky130A into `~/.ciel` via Ciel, pinned by LibreLane's `pdk_hashes.yaml`):

```bash
nix-shell ~/librelane/shell.nix --run "librelane --log-level ERROR --condensed --show-progress-bar --smoke-test"
```

Must end with no error and exit 0. Record the exact printed version in `logs/overnight.md`.

Non-interactive use for the rest of the night: every LibreLane command is run as `nix-shell ~/librelane/shell.nix --run "<command>"`. The Makefile variable `NIX_SHELL` wraps this.

Known Apple Silicon / Nix pitfalls and fixes (from the research notes and LibreLane's changelog):

| Symptom | Fix |
|---|---|
| `nix: command not found` in a fresh shell after a macOS update | `source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh` (Determinate installs to `/nix` on a separate APFS volume) |
| `error: experimental Nix feature 'nix-command' is disabled` | confirm `extra-experimental-features = nix-command flakes` in `/etc/nix/nix.custom.conf`; otherwise pass `--extra-experimental-features "nix-command flakes"` to every nix invocation |
| Everything is being built from source | cache misconfigured; see above; fall back to Docker |
| `yosys-ghdl` / VHDL plugin missing | expected: excluded on ARM and macOS ("never worked"); not needed |
| OpenROAD GUI crash | only affects GUI; fixed in 2.3.9; you never open the GUI overnight |
| KLayout dylib errors | LibreLane patches Mach-O binaries; if `klayout -z` fails inside nix-shell, use the gdstk renderer fallback |
| Verilator crash on `spm` | fixed since Verilator 5.018 (LibreLane ships 5.044) |
| Intel Mac warning | irrelevant on Apple Silicon |
| conda `(base)` shadows python | always use `.venv/bin/python`; inside `nix-shell --run` the Nix Python comes first on PATH; export `PYTHONPATH=` (empty) in the Makefile |

### 2.4 LibreLane via Docker (fallback only)

Use only if 2.3 failed after 3 hypotheses. Docker Desktop is already running with 8 GB / 4 CPUs (enough for a 1–2 tile design).

```bash
.venv/bin/python -m librelane --dockerized --smoke-test
```

`--dockerized` must precede all other options except `--docker-mount` and `--docker-no-tty`; it uses the image `ghcr.io/librelane/librelane:3.0.16` (the pip version), mounting your home and `PDK_ROOT`. Use `--docker-no-tty` when running from a script. If you fall back, set `HARDEN_MODE=docker` in `factory/state/env.mk` (Phase 1) so the Makefile uses this path. Record the fallback in `NEEDS_HUMAN.md` ("Nix install failed; using Docker; please check /etc/nix/nix.custom.conf").

### 2.5 PDK via Ciel (pinned hash)

The hash pinned by LibreLane 3.0.16 (`librelane/pdk_hashes.yaml`) and used by Tiny Tapeout's local-hardening guide is the same:

```bash
export PDK_ROOT="$HOME/.ciel"
.venv/bin/ciel ls --pdk-family sky130
.venv/bin/ciel enable --pdk-family sky130 8afc8346a57fe1ab7934ba5a6056ea8b43078e71
ls "$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v" "$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"
ls "$PDK_ROOT/sky130A/libs.tech/librelane/config.tcl" "$PDK_ROOT/sky130A/libs.tech/librelane/sky130_fd_sc_hd/config.tcl"
```

PDK root resolution order in LibreLane: `--pdk-root` flag → `PDK_ROOT` env → `~/.ciel`. The flow uses `sky130A` (default) with `sky130_fd_sc_hd`. If the Nix-shell LibreLane (3.0.14) pins a different hash, `librelane` will auto-fetch it via `ciel.fetch()` on first run; both can coexist in `~/.ciel`. The gate-level cell models that the GL testbench needs are the two `.v` files listed above.

### 2.6 Front-end sanity checks

```bash
yosys -V && verilator --version && iverilog -V | head -1 && surfer --version
.venv/bin/cocotb-config --version
.venv/bin/python -c "import gdstk; print('gdstk', gdstk.__version__)"
rsvg-convert --version
nix-shell ~/librelane/shell.nix --run "openroad -version; sta -version; magic --version; netgen -batch 'quit' 2>&1 | head -1; klayout -v; yosys -V; verilator --version"
```

(`magic --version` / `netgen` version flags are unverified — check `tool --help`; any output that shows a version string is enough.)

### 2.7 Finish Phase 0

Create `factory/state/env.mk` (Phase 1's Makefile includes it):

```make
# factory/state/env.mk — written by Phase 0
HARDEN_MODE ?= nix
LIBRELANE_DIR ?= $(HOME)/librelane
PDK_ROOT ?= $(HOME)/.ciel
PDK ?= sky130A
```

Log `PHASE 0 END` with the versions, then commit happens in Phase 1 (after `git init`). If a tool is missing after 3 attempts, record it in `NEEDS_HUMAN.md` and continue; `make doctor` will show it red.

---
## 3. Phase 1 — Repo skeleton (budget 20 min)

Goal: the directory tree, `CLAUDE.md`, `.claude/settings.json`, the guard hook, the Makefile gate ladder, `requirements.txt`, `.gitignore`, and the first commit. Create the files with the `Write` tool **except** the files under `.claude/`, which the deny rules below forbid the `Write` tool from touching; create those with Bash heredocs (`cat > path <<'HEREDOC_EOF'`). Do not change the file contents given here except where a line says so.

### 3.1 Directory tree

```
spec2tapeout/
├── CLAUDE.md                       # rules + flow order + report locations + pass criteria + never-edit list
├── TAPEOUT_FACTORY_PLAN.md         # this file
├── Open source RTL to tapeout pipeline.md   # reference only
├── Makefile                        # gate ladder (the only thing that deletes runs/)
├── requirements.txt
├── .gitignore
├── NEEDS_HUMAN.md                  # queue for the human (pre-populated in Phase 1 from §12)
├── .claude/
│   ├── settings.json               # permissions + hooks
│   ├── protected.txt               # path prefixes the hook blocks (grows at freeze)
│   └── hooks/
│       ├── guard.py                # PreToolUse guard (exit 2 = block)
│       └── stop_gate.py            # Stop hook: refuse to end before the report exists (or 8 h)
├── rtl/
│   ├── mac_int8.v
│   ├── mac_array_2x2.v
│   └── tt_um_noahsabb_mac.v
├── ref/                            # FROZEN after Phase 2: Python reference models
│   ├── mac_ref.py
│   └── gen_golden.py
├── tests/
│   ├── Makefile                    # cocotb (RTL and GATES=yes)
│   ├── tb_mac.v  tb_array.v  tb_tt.v
│   ├── test_mac.py  test_array.py  test_tt.py
│   └── golden/                     # FROZEN after Phase 2: *.json vectors
├── flow/
│   ├── mac_int8/config.json        # standalone hardening config (Phase 3)
│   ├── mac_int8/src/               # RTL copied in by `make harden`
│   └── sweep/                      # generated per-run configs
├── factory/
│   ├── orchestrate.py              # Phase 4
│   ├── gate.py  doctor.sh  lint.sh  render.py  sta_report.py  sweep.py  report.py  verify.py
│   ├── state/                      # pipeline.json, gates.json, decisions.json, sweep.csv, start_time, env.mk
│   └── dashboard/
│       ├── template.html  build.py
│       └── site/                   # generated: index.html, img/
├── runs/                           # LibreLane run dirs (gitignored)
├── logs/overnight.md               # the running log
├── reports/MORNING_REPORT.md       # generated by `make report`
└── tt_repo/                        # Phase 7: clone of NoahSabb/tt-um-noahsabb-mac (gitignored)
```

```bash
mkdir -p .claude/hooks rtl ref tests/golden flow/mac_int8/src flow/sweep factory/state factory/dashboard/site runs logs reports
git rev-parse --is-inside-work-tree 2>/dev/null || git init -b main
```

### 3.2 `CLAUDE.md` (full contents)

```markdown
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
```

### 3.3 `.claude/settings.json` (full contents; create via Bash heredoc)

Rule syntax notes (from the Claude Code docs): `Bash(make *)` matches `make` followed by anything (the space before `*` matters); a compound command must match on every subcommand, so `make lint && rm -rf runs` is not authorized by `Bash(make *)`. Rules are evaluated deny → ask → allow; a deny cannot be overridden by an allow. `defaultMode: auto` cannot be set from project settings (the CLI flag sets it).

```json
{
  "$schema": "https://json.schemastore.org/claude-code-settings.json",
  "permissions": {
    "allow": [
      "Read", "Glob", "Grep", "Edit", "Write",
      "Bash(make *)", "Bash(make)",
      "Bash(librelane *)", "Bash(nix-shell *)", "Bash(nix *)",
      "Bash(python *)", "Bash(python3 *)", "Bash(.venv/bin/python *)", "Bash(.venv/bin/pip *)", "Bash(.venv-tt/bin/python *)", "Bash(.venv-tt/bin/pip *)",
      "Bash(pip *)", "Bash(pip3 *)",
      "Bash(git *)", "Bash(brew *)", "Bash(ciel *)", "Bash(.venv/bin/ciel *)", "Bash(gh *)",
      "Bash(verilator *)", "Bash(iverilog *)", "Bash(vvp *)", "Bash(yosys *)", "Bash(klayout *)", "Bash(surfer *)",
      "Bash(docker *)", "Bash(caffeinate *)",
      "Bash(ls *)", "Bash(cat *)", "Bash(head *)", "Bash(tail *)", "Bash(grep *)", "Bash(find *)", "Bash(wc *)",
      "Bash(mkdir *)", "Bash(cp *)", "Bash(mv *)", "Bash(chmod *)", "Bash(touch *)", "Bash(date *)", "Bash(date)",
      "Bash(echo *)", "Bash(printf *)", "Bash(tee *)", "Bash(xattr *)", "Bash(curl *)", "Bash(tar *)",
      "Bash(rsvg-convert *)", "Bash(jq *)", "Bash(sed *)", "Bash(awk *)", "Bash(sort *)", "Bash(uniq *)",
      "Bash(diff *)", "Bash(which *)", "Bash(env *)", "Bash(env)", "Bash(export *)", "Bash(cd *)", "Bash(test *)",
      "Bash(true)", "Bash(sleep *)", "Bash(kill *)", "Bash(pgrep *)", "Bash(ps *)", "Bash(df *)", "Bash(du *)",
      "Bash(source *)", "Bash(bash *)", "Bash(sh *)", "Bash(./tt/tt_tool.py *)", "Bash(tt/tt_tool.py *)",
      "Bash(open_pdks *)", "Bash(openroad *)", "Bash(sta *)", "Bash(magic *)", "Bash(netgen *)"
    ],
    "deny": [
      "Edit(./tests/golden/**)", "Write(./tests/golden/**)",
      "Edit(./ref/**)", "Write(./ref/**)",
      "Edit(./.claude/**)", "Write(./.claude/**)",
      "Read(./.env)", "Read(./.env.*)",
      "Bash(rm -rf *)", "Bash(rm -fr *)", "Bash(rm -r *)", "Bash(rm -Rf *)",
      "Bash(sudo *)",
      "Bash(git push --force *)", "Bash(git push -f *)", "Bash(git reset --hard *)", "Bash(git clean *)",
      "Bash(claude *)",
      "Bash(shutdown *)", "Bash(reboot *)", "Bash(diskutil *)", "Bash(launchctl *)"
    ]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Edit|Write|MultiEdit|NotebookEdit|Bash",
        "hooks": [
          { "type": "command", "command": "/usr/bin/python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/guard.py\"", "timeout": 20 }
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "/usr/bin/python3 \"${CLAUDE_PROJECT_DIR}/.claude/hooks/stop_gate.py\"", "timeout": 20 }
        ]
      }
    ]
  }
}
```

The allow list makes those commands run without the auto-mode classifier; everything else still goes through auto mode's classifier. The deny list applies immediately even before the folder is trusted.

### 3.4 `.claude/protected.txt` (initial contents)

```
.claude/
Makefile
```

`make freeze-golden` (Phase 2) appends `ref/` and `tests/golden/`. (The Makefile is protected from edit tools from the start; the plan gives its full content, so you never need to edit it. If a Makefile bug blocks you, write the fix you would make into `NEEDS_HUMAN.md` and work around it with a direct command.)

### 3.5 `.claude/hooks/guard.py` (full contents; create via Bash heredoc)

Exit-code semantics (Claude Code hooks doc): exit 0 = allow, **exit 2 = block the tool call and feed stderr back to Claude**, any other code = non-blocking error. The hook receives JSON on stdin with `tool_name` and `tool_input`.

```python
#!/usr/bin/env python3
"""PreToolUse guard for the spec2tapeout overnight run.
Blocks (exit 2): edits/writes to protected prefixes, Bash commands that write to
protected prefixes, skip-permission flags, rm -r outside runs/, destructive git."""
import json, os, re, sys

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # malformed input: do not block
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    root = os.path.realpath(root)
    prot_file = os.path.join(root, ".claude", "protected.txt")
    protected = []
    if os.path.exists(prot_file):
        with open(prot_file) as f:
            protected = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    def rel(p):
        p = os.path.realpath(os.path.join(root, os.path.expanduser(p)))
        return os.path.relpath(p, root)

    def is_protected(relpath):
        for pre in protected:
            pre_n = pre.rstrip("/")
            if relpath == pre_n or relpath.startswith(pre_n + "/") or (pre.endswith("/") is False and relpath == pre):
                return pre
        return None

    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        if path:
            hit = is_protected(rel(path))
            if hit:
                sys.stderr.write(f"BLOCKED by .claude/hooks/guard.py: '{path}' is under protected prefix '{hit}'. "
                                 "Rule 1: never edit golden vectors, reference models or .claude/. "
                                 "Fix the RTL or testbench driver instead, or record the issue in NEEDS_HUMAN.md.\n")
                return 2
        return 0

    if tool == "Bash":
        cmd = ti.get("command", "") or ""
        if re.search(r"--dangerously-skip-permissions|bypassPermissions|--permission-mode\s+bypass", cmd):
            sys.stderr.write("BLOCKED: skip-permission flags are forbidden (rule 7).\n"); return 2
        # rm -r / rm -rf anywhere except under runs/
        for m in re.finditer(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|-[a-zA-Z]*R[a-zA-Z]*)\s+([^\s;&|]+)", cmd):
            target = m.group(2).strip("'\"")
            if not re.match(r"^(\./)?runs(/|$)", target):
                sys.stderr.write(f"BLOCKED: 'rm -r' outside runs/ ('{target}'). Use make clean / make clean-run TAG=... (rule 6).\n"); return 2
        if re.search(r"\bgit\s+(reset\s+--hard|clean\b|push\s+(-f\b|--force))", cmd):
            sys.stderr.write("BLOCKED: destructive git command.\n"); return 2
        # writes to protected prefixes via shell (reading/copying OUT of them is fine)
        if protected:
            pat = r"(\./)?(" + "|".join(re.escape(p.rstrip("/")) for p in protected) + r")(/|\b)"
            def block(why):
                sys.stderr.write(f"BLOCKED: {why} (rule 1: never modify ref/, tests/golden/ or .claude/). Command: {cmd[:200]}\n"); return 2
            if re.search(r"\b(rm|sed\s+-i|chmod|truncate|patch|dd|git\s+(checkout|restore))\b", cmd) and re.search(r"(^|[\s'\"=])" + pat, cmd):
                return block("destructive command names a protected path")
            if re.search(r">>?\s*['\"]?" + pat, cmd) or re.search(r"\btee\s+(-a\s+)?['\"]?" + pat, cmd):
                return block("redirection into a protected path")
            for m in re.finditer(r"\b(cp|mv|rsync|install)\b([^;&|\n]*)", cmd):
                args = [a for a in m.group(2).split() if not a.startswith("-")]
                if args and re.match(pat, args[-1].strip("'\"")):
                    return block("copy/move destination is a protected path")
        return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

### 3.6 `.claude/hooks/stop_gate.py` (full contents; create via Bash heredoc)

A `Stop` hook that prints `{"decision": "block", "reason": "..."}` sends Claude back to keep working. It allows stopping when the morning report exists, when the 8-hour budget is exceeded, or when `factory/state/STOP_OK` exists.

```python
#!/usr/bin/env python3
import json, os, sys, time
root = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
report = os.path.join(root, "reports", "MORNING_REPORT.md")
stop_ok = os.path.join(root, "factory", "state", "STOP_OK")
start = os.path.join(root, "factory", "state", "start_time")
try:
    data = json.load(sys.stdin)
except Exception:
    data = {}
if data.get("stop_hook_active"):
    sys.exit(0)  # do not loop forever
elapsed = 0
try:
    elapsed = time.time() - float(open(start).read().strip())
except Exception:
    pass
if os.path.exists(report) or os.path.exists(stop_ok) or elapsed > 8 * 3600:
    sys.exit(0)
print(json.dumps({"decision": "block",
                  "reason": "reports/MORNING_REPORT.md does not exist yet and the 8-hour budget is not exhausted. "
                            "Continue with the next step of TAPEOUT_FACTORY_PLAN.md. If you are truly finished or blocked, "
                            "run `make report` (which writes the report) and commit."}))
sys.exit(0)
```

(`stop_hook_active` is the documented field that is true when Claude is already continuing because of a Stop hook; this prevents an infinite loop.)

### 3.7 `Makefile` (full contents)

Tabs are required before recipe lines. `make` targets are the only commands that delete under `runs/`.

```make
# Makefile — spec2tapeout gate ladder. Every gate runs through factory/gate.py, which records
# the real exit code, timestamps and log path into factory/state/gates.json.
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-print-directory

-include factory/state/env.mk
HARDEN_MODE   ?= nix
LIBRELANE_DIR ?= $(HOME)/librelane
PDK_ROOT      ?= $(HOME)/.ciel
PDK           ?= sky130A
export PDK_ROOT PDK
export PYTHONPATH :=
export PATH := $(CURDIR)/.venv/bin:/opt/homebrew/bin:$(PATH)

PY        := $(CURDIR)/.venv/bin/python
GATE      := $(PY) factory/gate.py
NIX_SHELL := nix-shell $(LIBRELANE_DIR)/shell.nix --run
DESIGN    ?= mac_int8
WIDTH     ?= 8
TAG       ?= $(DESIGN)-$(shell date +%Y%m%d-%H%M%S)
CONFIG    ?= flow/$(DESIGN)/config.json
RUN_DIR   := runs/$(TAG)
GL_NETLIST ?= $(CURDIR)/$(RUN_DIR)/final/pnl/$(DESIGN).pnl.v
TT_REPO   ?= tt_repo

.PHONY: help doctor lint sim sim-gl synth harden harden-closure sta-report precheck sweep render dashboard serve \
        verify-factory report clean clean-run log elapsed freeze-golden gen-golden tt-harden tt-test tt-test-gl tt-precheck

help:
	@grep -E '^[a-z-]+:' Makefile | cut -d: -f1 | sort | tr '\n' ' '; echo

log:            ## make log MSG="text"
	@printf '%s %s\n' "$$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(MSG)" >> logs/overnight.md

elapsed:        ## seconds since factory/state/start_time
	@echo $$(( $$(date +%s) - $$(cat factory/state/start_time) ))

doctor:
	$(GATE) doctor -- bash factory/doctor.sh

lint:           ## Verilator lint of all three tops; fatal: LATCH MULTIDRIVEN CASEINCOMPLETE UNDRIVEN IMPLICIT
	$(GATE) lint -- bash factory/lint.sh

gen-golden:     ## generate tests/golden/*.json from ref/ (only before freeze)
	$(GATE) gen-golden -- $(PY) ref/gen_golden.py

freeze-golden:  ## make golden vectors and reference model immutable
	chmod -R a-w ref tests/golden
	grep -qx 'ref/' .claude/protected.txt || echo 'ref/' >> .claude/protected.txt
	grep -qx 'tests/golden/' .claude/protected.txt || echo 'tests/golden/' >> .claude/protected.txt
	git add -A ref tests/golden .claude/protected.txt && git commit -m "phase 2: freeze golden vectors and reference model" || true
	$(MAKE) log MSG="FROZEN ref/ and tests/golden/ (chmod a-w + hook)"

sim:            ## cocotb RTL sim vs golden: make sim TOP=mac|array|tt WIDTH=8
	$(GATE) sim-$(TOP)-w$(WIDTH) -- bash -c 'cd tests && $(MAKE) -B TOP=$(TOP) WIDTH=$(WIDTH) GATES=no && $(PY) -m cocotb_tools.check_results results.xml'
sim: TOP ?= mac

sim-gl:         ## gate-level sim of the hardened MAC: make sim-gl TAG=<tag>
	test -s "$(GL_NETLIST)" || { echo "missing $(GL_NETLIST)"; exit 1; }
	$(GATE) sim-gl-$(TOP) -- bash -c 'cd tests && $(MAKE) -B TOP=$(TOP) GATES=yes GL_NETLIST=$(GL_NETLIST) && $(PY) -m cocotb_tools.check_results results.xml'
sim-gl: TOP ?= mac

synth:          ## standalone Yosys synthesis check (fast; fails on latches/unmapped cells/$mem)
	$(GATE) synth-$(WIDTH) -- bash -c 'mkdir -p runs/synth && $(PY) factory/synth_check.py --width $(WIDTH) --out runs/synth'

harden:         ## full LibreLane Classic flow: make harden TAG=<tag> [CONFIG=...]
	mkdir -p flow/$(DESIGN)/src && cp rtl/*.v flow/$(DESIGN)/src/
	@if [ "$(HARDEN_MODE)" = "docker" ]; then \
	  $(GATE) harden-$(TAG) -- $(PY) -m librelane --dockerized --docker-no-tty --pdk-root $(PDK_ROOT) --run-tag $(TAG) --force-run-dir $(RUN_DIR) $(CONFIG); \
	else \
	  $(GATE) harden-$(TAG) -- $(NIX_SHELL) "librelane --pdk-root $(PDK_ROOT) --run-tag $(TAG) --force-run-dir $(RUN_DIR) $(CONFIG)"; \
	fi
	$(PY) factory/orchestrate.py ingest --run-dir $(RUN_DIR) --design $(DESIGN)

harden-closure: ## harden with the retry/decision loop (Phase 4)
	mkdir -p flow/$(DESIGN)/src && cp rtl/*.v flow/$(DESIGN)/src/
	$(PY) factory/orchestrate.py closure --config $(CONFIG) --design $(DESIGN) --tag $(TAG) --max-attempts 4

sta-report:     ## print the nine-corner summary and key metrics: make sta-report TAG=<tag>
	$(PY) factory/sta_report.py $(RUN_DIR)

render:         ## render a layout PNG per major stage: make render TAG=<tag>
	$(GATE) render-$(TAG) -- $(PY) factory/render.py --run-dir $(RUN_DIR) --design $(DESIGN)

sweep:          ## WIDTH x CLOCK_PERIOD sweep -> factory/state/sweep.csv + plots
	$(GATE) sweep -- $(PY) factory/sweep.py --widths 2,4,8 --periods 5,10,20

dashboard:      ## regenerate factory/dashboard/site/index.html from factory/state/*.json
	$(GATE) dashboard -- $(PY) factory/dashboard/build.py

serve:          ## serve the dashboard on http://localhost:8787
	cd factory/dashboard/site && $(PY) -m http.server 8787

precheck:       ## Tiny Tapeout precheck (local attempt; CI is authoritative)
	$(GATE) precheck -- bash -c 'cd $(TT_REPO) && ../.venv-tt/bin/python tt/tt_tool.py --create-tt-submission && cd tt/precheck && nix-shell --run "python precheck.py --gds ../../tt_submission/*.gds --tech sky130A"'

tt-harden:      ## local hardening of the Tiny Tapeout repo (Docker, LibreLane 3.0.14, bit-identical to CI)
	$(GATE) tt-harden -- bash -c 'cd $(TT_REPO) && export PDK_ROOT=$(PDK_ROOT) PDK=sky130A LIBRELANE_TAG=3.0.14 && ../.venv-tt/bin/python tt/tt_tool.py --create-user-config && ../.venv-tt/bin/python tt/tt_tool.py --harden && ../.venv-tt/bin/python tt/tt_tool.py --print-warnings && ../.venv-tt/bin/python tt/tt_tool.py --print-stats && ../.venv-tt/bin/python tt/tt_tool.py --print-cell-category'

tt-test:        ## RTL cocotb test in the TT repo
	$(GATE) tt-test -- bash -c 'cd $(TT_REPO)/test && make -B && $(PY) -m cocotb_tools.check_results results.xml'

tt-test-gl:     ## gate-level cocotb test in the TT repo (needs runs/wokwi)
	$(GATE) tt-test-gl -- bash -c 'cd $(TT_REPO) && cp runs/wokwi/final/pnl/tt_um_noahsabb_mac.pnl.v test/gate_level_netlist.v && cd test && make -B GATES=yes && $(PY) -m cocotb_tools.check_results results.xml'

verify-factory: ## Phase 8: full pipeline from clean + all checks
	$(GATE) verify-factory -- $(PY) factory/verify.py

report:         ## write reports/MORNING_REPORT.md
	$(PY) factory/report.py
	$(MAKE) log MSG="REPORT written reports/MORNING_REPORT.md"

clean-run:      ## delete one run: make clean-run TAG=<tag>
	@test -n "$(TAG)" && test -d "runs/$(TAG)" && rm -rf "runs/$(TAG)" || echo "no runs/$(TAG)"

clean:          ## delete all runs and sim builds (never touches ref/ tests/golden/)
	rm -rf runs/* tests/sim_build tests/results.xml tests/*.vcd tests/*.fst factory/dashboard/site/*
```

### 3.8 `factory/gate.py` (full contents)

```python
#!/usr/bin/env python3
"""Run a gate command, record exit code/timestamps/log path in factory/state/gates.json, exit with the command's code.
Usage: gate.py NAME -- cmd args..."""
import json, os, subprocess, sys, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "factory", "state", "gates.json")
LOGDIR = os.path.join(ROOT, "logs", "gates")

def now(): return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def main():
    if "--" not in sys.argv: print(__doc__); return 2
    i = sys.argv.index("--"); name = sys.argv[1]; cmd = sys.argv[i+1:]
    os.makedirs(LOGDIR, exist_ok=True); os.makedirs(os.path.dirname(STATE), exist_ok=True)
    log = os.path.join(LOGDIR, f"{name}.log")
    t0 = time.time(); started = now()
    with open(log, "w") as lf:
        lf.write(f"# gate {name}\n# cmd: {' '.join(cmd)}\n# started {started}\n")
        lf.flush()
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, cwd=ROOT)
        for line in p.stdout:
            sys.stdout.write(line); lf.write(line)
        rc = p.wait()
        lf.write(f"# exit {rc} after {time.time()-t0:.1f}s\n")
    gates = {}
    if os.path.exists(STATE):
        try: gates = json.load(open(STATE))
        except Exception: gates = {}
    gates[name] = {"status": "pass" if rc == 0 else "fail", "exit_code": rc, "started": started, "ended": now(),
                   "duration_s": round(time.time()-t0, 1), "log": os.path.relpath(log, ROOT), "cmd": " ".join(cmd)}
    json.dump(gates, open(STATE, "w"), indent=2)
    with open(os.path.join(ROOT, "logs", "overnight.md"), "a") as f:
        f.write(f"{now()} GATE {name} {'PASS' if rc == 0 else 'FAIL'} exit={rc} log={os.path.relpath(log, ROOT)}\n")
    return rc

if __name__ == "__main__":
    sys.exit(main())
```

### 3.9 `factory/doctor.sh` (full contents)

```bash
#!/usr/bin/env bash
# Prints every tool version; exits nonzero if anything required is missing.
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LIBRELANE_DIR="${LIBRELANE_DIR:-$HOME/librelane}"
PDK_ROOT="${PDK_ROOT:-$HOME/.ciel}"
missing=0
chk() { # chk "label" cmd...
  local label="$1"; shift
  if out="$("$@" 2>&1 | head -1)"; then printf '%-28s OK   %s\n' "$label" "$out"; else printf '%-28s MISSING (%s)\n' "$label" "$*"; missing=$((missing+1)); fi
}
chk "python (.venv)"      "$ROOT/.venv/bin/python" --version
chk "cocotb"              "$ROOT/.venv/bin/cocotb-config" --version
chk "ciel"                "$ROOT/.venv/bin/ciel" --version
chk "librelane (pip)"     "$ROOT/.venv/bin/python" -m librelane --bare-version
chk "yosys (brew)"        yosys -V
chk "verilator (brew)"    verilator --version
chk "iverilog (brew)"     iverilog -V
chk "surfer"              surfer --version
chk "rsvg-convert"        rsvg-convert --version
chk "jq"                  jq --version
chk "gh"                  gh --version
chk "docker"              docker --version
chk "nix"                 nix --version
chk "gdstk"               "$ROOT/.venv/bin/python" -c "import gdstk; print('gdstk', gdstk.__version__)"
chk "matplotlib"          "$ROOT/.venv/bin/python" -c "import matplotlib; print('matplotlib', matplotlib.__version__)"
chk "librelane (nix)"     nix-shell "$LIBRELANE_DIR/shell.nix" --run "librelane --bare-version"
chk "openroad (nix)"      nix-shell "$LIBRELANE_DIR/shell.nix" --run "openroad -version"
chk "klayout (nix)"       nix-shell "$LIBRELANE_DIR/shell.nix" --run "klayout -v"
chk "magic (nix)"         nix-shell "$LIBRELANE_DIR/shell.nix" --run "magic --version"
chk "netgen (nix)"        nix-shell "$LIBRELANE_DIR/shell.nix" --run "which netgen"
chk "yosys (nix)"         nix-shell "$LIBRELANE_DIR/shell.nix" --run "yosys -V"
for f in "$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v" \
         "$PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v" \
         "$PDK_ROOT/sky130A/libs.tech/librelane/config.tcl"; do
  if [ -f "$f" ]; then printf '%-28s OK   %s\n' "pdk file" "$f"; else printf '%-28s MISSING %s\n' "pdk file" "$f"; missing=$((missing+1)); fi
done
echo "free disk: $(df -h "$ROOT" | tail -1 | awk '{print $4}')"
echo "missing: $missing"
[ "$missing" -eq 0 ]
```

(`--bare-version` is a documented LibreLane CLI flag; if it is rejected, use `--version`.)

### 3.10 `factory/lint.sh` (full contents)

LibreLane's own lint is `verilator --lint-only --Wall --Wno-DECLFILENAME --Wno-EOFNEWLINE --top-module <top> ... --Wno-fatal --relative-includes --Werror-LATCH`. This script runs the same flags for all three tops, lists every warning, and fails on the must-fix set.

```bash
#!/usr/bin/env bash
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FATAL='LATCH|MULTIDRIVEN|CASEINCOMPLETE|UNDRIVEN|IMPLICIT|BLKSEQ|COMBDLY|SYNCASYNCNET|NEEDTIMINGOPT'
REVIEW='WIDTHEXPAND|WIDTHTRUNC|CASEOVERLAP|UNOPTFLAT'
rc=0
lint_one() {
  local top="$1"; shift
  echo "=== verilator lint: $top"
  out="$(verilator --lint-only --Wall --Wno-DECLFILENAME --Wno-EOFNEWLINE --Wno-fatal --relative-includes \
          --Werror-LATCH --Werror-MULTIDRIVEN --top-module "$top" "$@" 2>&1)" ; vrc=$?
  echo "$out"
  if echo "$out" | grep -E "%(Warning|Error)-($FATAL)" >/dev/null; then echo "FATAL lint warning(s) in $top"; rc=1; fi
  if echo "$out" | grep -E "%Error" | grep -vE "%Error-(UNUSEDSIGNAL|$REVIEW)" >/dev/null; then echo "lint error in $top"; rc=1; fi
  if echo "$out" | grep -E "%Warning-($REVIEW)" >/dev/null; then echo "REVIEW (not fatal): width/case warnings in $top — fix with explicit widths/\$signed"; fi
  echo "exit from verilator: $vrc"
}
lint_one mac_int8          "$ROOT/rtl/mac_int8.v"
lint_one mac_array_2x2     "$ROOT/rtl/mac_int8.v" "$ROOT/rtl/mac_array_2x2.v"
lint_one tt_um_noahsabb_mac "$ROOT/rtl/mac_int8.v" "$ROOT/rtl/mac_array_2x2.v" "$ROOT/rtl/tt_um_noahsabb_mac.v"
exit $rc
```

Fatal: `LATCH`, `MULTIDRIVEN`, `CASEINCOMPLETE`, `UNDRIVEN`, `IMPLICIT`, `BLKSEQ`, `COMBDLY`, `SYNCASYNCNET`, `NEEDTIMINGOPT` and any `%Error`. Review-each (not fatal): `WIDTHEXPAND`, `WIDTHTRUNC`, `CASEOVERLAP`, `UNOPTFLAT`. Cosmetic: `UNUSEDSIGNAL`.

### 3.11 `requirements.txt` and `.gitignore`

`requirements.txt` is given in §2.2. `.gitignore`:

```
runs/
.venv/
.venv-tt/
tt_repo/
*.vcd
*.fst
pdk/
__pycache__/
tests/sim_build/
tests/results.xml
flow/mac_int8/src/
flow/sweep/*/runs/
factory/dashboard/site/img/
logs/gates/
.DS_Store
```

### 3.12 `NEEDS_HUMAN.md` initial contents

Create it now with the pre-populated list from §12 (copy that section's bullet list verbatim under a heading `## Pre-populated (known in advance)`, then a heading `## Found overnight` that you append to).

### 3.13 Commit

```bash
chmod +x .claude/hooks/guard.py .claude/hooks/stop_gate.py factory/gate.py factory/doctor.sh factory/lint.sh
git add -A
git commit -m "phase 1: repo skeleton, rules, permissions, hook, Makefile gate ladder"
make doctor
make log MSG="PHASE 1 END"
```

`make doctor` must exit 0 here. If it does not, apply rule 5 (three hypotheses), then continue; Phase 8 re-checks it.

---
## 4. Phase 2 — The design and the verification discipline (budget 60 min)

Order of work in this phase is the discipline: **(1)** read the spec below; **(2)** write the reference model `ref/mac_ref.py` and the generator `ref/gen_golden.py` from the spec, using Bash heredocs (`cat > ref/mac_ref.py <<'PYEOF' ... PYEOF`) because the `Write` tool is denied for `ref/`; **(3)** `make gen-golden` (writes `tests/golden/*.json`); **(4)** `make freeze-golden`; **(5)** only then write the RTL with the `Write` tool; **(6)** `make lint`, `make sim TOP=mac WIDTH=2/4/8`, `make sim TOP=array`, `make sim TOP=tt`, fixing RTL (never vectors) until green; **(7)** `make synth`; **(8)** commit `phase 2: ...`.

### 4.1 Spec: `mac_int8` (parameterized signed MAC)

- Parameters: `WIDTH` (default 8) operand width; `ACC_WIDTH` (default 32) accumulator width. Accumulator width rule: for K accumulation steps without overflow, `ACC_WIDTH >= 2*WIDTH + ceil(log2 K)`; default 32 with WIDTH 8 allows K = 65536. Behaviour on overflow is two's-complement wrap modulo 2^ACC_WIDTH (the model and the RTL both wrap).
- Ports: `clk`; `rst_n` (synchronous, active-low); `clear` (synchronous, clears the accumulator to 0, priority over `en`); `en` (accumulate when 1); `a`, `b` signed `[WIDTH-1:0]`; `acc` signed `[ACC_WIDTH-1:0]` register output.
- On every rising edge: if `!rst_n` → `acc <= 0`; else if `clear` → `acc <= 0`; else if `en` → `acc <= acc + sign_extend(a*b)`; else hold. The product is signed, `2*WIDTH` bits, sign-extended to `ACC_WIDTH` before the add. No `initial` blocks, no latches, one clock.

### 4.2 Spec: `mac_array_2x2` (output-stationary)

Output-stationary dataflow: each of the four processing elements owns one accumulator (`acc_ij`), operands are broadcast (row operand `a_i` to PEs (i,0),(i,1); column operand `b_j` to PEs (0,j),(1,j)); nothing moves between PEs. Same parameters and control (`rst_n`, `clear`, `en`) as `mac_int8`, applied to all four PEs simultaneously. Ports: `a0,a1,b0,b1` signed `[WIDTH-1:0]`; `acc00,acc01,acc10,acc11` signed `[ACC_WIDTH-1:0]`. PE (i,j) computes `acc_ij += a_i * b_j`. After K steps it holds the 2x2 matrix product of a K×2 by 2×K stream.

### 4.3 Spec: `tt_um_noahsabb_mac` wrapper and byte-serial protocol

Tiny Tapeout fixes the ports (exactly these, no others): `ui_in[7:0]` (in), `uo_out[7:0]` (out), `uio_in[7:0]` (in), `uio_out[7:0]` (out), `uio_oe[7:0]` (out, 1=output), `ena` (in, always 1 when powered), `clk`, `rst_n` (active-low). The wrapper instantiates `mac_array_2x2 #(WIDTH=8, ACC_WIDTH=32)`.

Pin map: `ui_in[7:0]` = data byte `D`. `uio_in[0]` = `strobe`; `uio_in[2:1]` = `cmd`; `uio_in[7:3]` unused (ignored). `uo_out[7:0]` = selected result byte (continuously driven). `uio_out = 8'h00`, `uio_oe = 8'h00` (all bidirectional pins are inputs). `ena` is ignored.

Protocol (everything is sampled on the rising edge of `clk`; a command takes effect **at the edge on which `strobe` is sampled high**):

| `cmd` | Name | Effect at that edge |
|---|---|---|
| 0 | `LOAD_A` | `a[ptr_a] <= D` (as signed int8); `ptr_a` toggles 0→1→0 (so two consecutive LOAD_A write a0 then a1) |
| 1 | `LOAD_B` | `b[ptr_b] <= D`; `ptr_b` toggles |
| 2 | `STEP` | all four PEs accumulate `a_i*b_j` using the currently loaded a/b; `ptr_a <= 0`, `ptr_b <= 0` |
| 3 | `SELECT` | `sel_acc <= D[1:0]` (0=acc00, 1=acc01, 2=acc10, 3=acc11); `sel_byte <= D[3:2]` (0=bits 7:0 … 3=bits 31:24); if `D[7]==1` all four accumulators are cleared at this same edge |

`uo_out` = byte `sel_byte` of accumulator `sel_acc`, visible from the cycle after the SELECT edge. `rst_n` low (synchronous) zeroes a/b, pointers, selections and all accumulators. Reading a 32-bit result takes four SELECT commands. The host (RP2350 MicroPython SDK after fab: `tt.ui_in.value = D`, `tt.uio_in` bits, `tt.clock_project_once()`) replays exactly this byte sequence.

### 4.4 `ref/mac_ref.py` (full contents; create with a Bash heredoc; written from the spec, never from the RTL)

```python
"""Reference models for mac_int8, mac_array_2x2 and the tt_um_noahsabb_mac byte-serial protocol.
Written from TAPEOUT_FACTORY_PLAN.md sections 4.1-4.3. FROZEN after Phase 2 (rule 1). Pure Python, no RTL imports."""

def to_signed(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v & (1 << (bits - 1)) else v

def to_unsigned(v, bits):
    return v & ((1 << bits) - 1)

class MacRef:
    def __init__(self, width=8, acc_width=32):
        self.width, self.acc_width, self.acc = width, acc_width, 0

    def clock(self, rst_n, clear, en, a, b):
        """One rising edge. Priority: !rst_n > clear > en. a, b signed ints. Returns acc (signed) after the edge."""
        if not rst_n or clear:
            self.acc = 0
        elif en:
            self.acc = to_signed(self.acc + a * b, self.acc_width)
        return self.acc

class Array2x2Ref:
    """Output-stationary: pe[i][j].acc += a[i]*b[j]."""
    def __init__(self, width=8, acc_width=32):
        self.pe = [[MacRef(width, acc_width) for _ in range(2)] for _ in range(2)]

    def clock(self, rst_n, clear, en, a, b):
        return [[self.pe[i][j].clock(rst_n, clear, en, a[i], b[j]) for j in range(2)] for i in range(2)]

    def flat(self):  # [acc00, acc01, acc10, acc11]
        return [self.pe[0][0].acc, self.pe[0][1].acc, self.pe[1][0].acc, self.pe[1][1].acc]

class TTRef:
    """Byte-serial protocol of tt_um_noahsabb_mac. clock(rst_n, ui_in, uio_in) per rising edge -> uo_out after it."""
    def __init__(self):
        self.arr = Array2x2Ref(8, 32)
        self.reset()

    def reset(self):
        self.a, self.b = [0, 0], [0, 0]
        self.ptr_a = self.ptr_b = 0
        self.sel_acc = self.sel_byte = 0
        self.arr.clock(0, 0, 0, [0, 0], [0, 0])

    def clock(self, rst_n, ui_in, uio_in):
        if not rst_n:
            self.reset()
            return 0
        strobe, cmd, data = uio_in & 1, (uio_in >> 1) & 3, ui_in & 0xFF
        step = clr = 0
        if strobe:
            if cmd == 0:
                self.a[self.ptr_a] = to_signed(data, 8); self.ptr_a ^= 1
            elif cmd == 1:
                self.b[self.ptr_b] = to_signed(data, 8); self.ptr_b ^= 1
            elif cmd == 2:
                step = 1; self.ptr_a = self.ptr_b = 0
            else:
                self.sel_acc, self.sel_byte, clr = data & 3, (data >> 2) & 3, (data >> 7) & 1
        self.arr.clock(1, clr, step, list(self.a), list(self.b))
        return self.uo_out()

    def uo_out(self):
        v = to_unsigned(self.arr.flat()[self.sel_acc], 32)
        return (v >> (8 * self.sel_byte)) & 0xFF
```

### 4.5 `ref/gen_golden.py` (full contents; Bash heredoc)

Writes `tests/golden/*.json` **before** any RTL exists. Seeds are fixed so the files are reproducible byte-for-byte.

```python
#!/usr/bin/env python3
"""Generate golden vectors from the reference model. Run once (make gen-golden), then frozen."""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ref.mac_ref import MacRef, Array2x2Ref, TTRef, to_signed
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "golden")
os.makedirs(OUT, exist_ok=True)

def rnd_signed(rng, bits):
    return rng.randint(-(1 << (bits - 1)), (1 << (bits - 1)) - 1)

def gen_mac(width, acc_width, seed, n=600):
    rng = random.Random(seed); m = MacRef(width, acc_width); vec = []
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    directed = [(0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (1, 0, 0, 0, 0),           # reset held, then idle
                (1, 0, 1, hi, hi), (1, 0, 1, lo, lo), (1, 0, 1, lo, hi), (1, 0, 1, hi, lo),  # sign corners
                (1, 0, 1, 0, hi), (1, 0, 1, lo, 0), (1, 0, 0, hi, hi), (1, 1, 1, hi, hi),    # zero operand, hold, clear beats en
                (1, 0, 1, -1, -1), (1, 0, 1, -1, 1), (1, 0, 1, 1, -1)]
    for rst_n, clear, en, a, b in directed:
        vec.append([rst_n, clear, en, a, b, m.clock(rst_n, clear, en, a, b)])
    for _ in range(n):
        r = rng.random()
        rst_n = 0 if r < 0.01 else 1
        clear = 1 if 0.01 <= r < 0.04 else 0
        en = 1 if rng.random() < 0.85 else 0
        a, b = rnd_signed(rng, width), rnd_signed(rng, width)
        vec.append([rst_n, clear, en, a, b, m.clock(rst_n, clear, en, a, b)])
    # drive the accumulator toward wrap-around (fully wraps when acc_width is small, e.g. mac_w4_acc10); capped at 64 steps
    for _ in range(min(64, 2 * (1 << max(0, acc_width - 2 * width)) + 8)):
        vec.append([1, 0, 1, lo, lo, m.clock(1, 0, 1, lo, lo)])
    return {"model": "ref/mac_ref.py:MacRef", "params": {"WIDTH": width, "ACC_WIDTH": acc_width}, "seed": seed,
            "fields": ["rst_n", "clear", "en", "a", "b", "acc_after"], "vectors": vec}

def gen_array(width, acc_width, seed, n=400):
    rng = random.Random(seed); m = Array2x2Ref(width, acc_width); vec = []
    for i in range(3):
        acc = m.clock(0, 0, 0, [0, 0], [0, 0]); vec.append([0, 0, 0, 0, 0, 0, 0] + m.flat())
    for _ in range(n):
        r = rng.random(); rst_n = 0 if r < 0.01 else 1; clear = 1 if 0.01 <= r < 0.04 else 0
        en = 1 if rng.random() < 0.85 else 0
        a = [rnd_signed(rng, width), rnd_signed(rng, width)]; b = [rnd_signed(rng, width), rnd_signed(rng, width)]
        m.clock(rst_n, clear, en, a, b); vec.append([rst_n, clear, en, a[0], a[1], b[0], b[1]] + m.flat())
    return {"model": "ref/mac_ref.py:Array2x2Ref", "params": {"WIDTH": width, "ACC_WIDTH": acc_width}, "seed": seed,
            "fields": ["rst_n", "clear", "en", "a0", "a1", "b0", "b1", "acc00", "acc01", "acc10", "acc11"], "vectors": vec}

def gen_tt(seed, n=2500):
    rng = random.Random(seed); t = TTRef(); vec = []
    def step(rst_n, ui, uio): vec.append([rst_n, ui & 0xFF, uio & 0xFF, t.clock(rst_n, ui, uio)])
    S, LOAD_A, LOAD_B, STEP, SEL = 1, 0 << 1, 1 << 1, 2 << 1, 3 << 1
    for _ in range(3): step(0, 0, 0)
    step(1, 0, 0)
    # directed: a=(3,-5), b=(7,-2); three steps -> acc00=63, acc01=-18, acc10=-105, acc11=30
    step(1, 3, S | LOAD_A); step(1, 0xFB, S | LOAD_A); step(1, 7, S | LOAD_B); step(1, 0xFE, S | LOAD_B)
    for _ in range(3): step(1, 0, S | STEP)
    for acc in range(4):
        for byte in range(4):
            step(1, acc | (byte << 2), S | SEL); step(1, 0, 0)
    step(1, 0x80 | 2, S | SEL)                         # clear all, select acc10
    step(1, 0x7F, S | LOAD_A); step(1, 0x80, S | LOAD_A); step(1, 0x80, S | LOAD_B); step(1, 0x7F, S | LOAD_B)
    for _ in range(20): step(1, 0, S | STEP)           # 127*-128 and -128*-128 products accumulate
    for acc in range(4):
        for byte in range(4):
            step(1, acc | (byte << 2), S | SEL)
    for _ in range(n):                                 # randomized protocol traffic with occasional reset
        r = rng.random()
        if r < 0.005: step(0, rng.randrange(256), rng.randrange(256)); continue
        ui = rng.randrange(256); c = rng.choice([LOAD_A, LOAD_B, STEP, STEP, STEP, SEL]); s = S if rng.random() < 0.8 else 0
        step(1, ui, s | c | (rng.randrange(32) << 3))  # uio_in[7:3] is don't-care
    return {"model": "ref/mac_ref.py:TTRef", "params": {"WIDTH": 8, "ACC_WIDTH": 32}, "seed": seed,
            "fields": ["rst_n", "ui_in", "uio_in", "uo_out_after"], "vectors": vec}

def dump(name, obj):
    p = os.path.join(OUT, name); json.dump(obj, open(p, "w"), separators=(",", ":")); print("wrote", p, len(obj["vectors"]), "vectors")

if __name__ == "__main__":
    dump("mac_w2_acc20.json", gen_mac(2, 20, 2020))
    dump("mac_w4_acc24.json", gen_mac(4, 24, 4024))
    dump("mac_w8_acc32.json", gen_mac(8, 32, 8032))
    dump("mac_w4_acc10.json", gen_mac(4, 10, 4010))      # small accumulator: exercises wrap-around
    dump("array_w8_acc32.json", gen_array(8, 32, 2208))
    dump("tt_protocol.json", gen_tt(2611))
```

```bash
make gen-golden && ls -la tests/golden && make freeze-golden
```

After `make freeze-golden`, `ref/` and `tests/golden/` are read-only on disk, blocked by the hook, and denied to the edit tools. From now on only RTL and test drivers change.

### 4.6 RTL (write with the `Write` tool, into `rtl/`)

`rtl/mac_int8.v`:

```verilog
`default_nettype none
// Parameterized signed multiply-accumulate. Synchronous active-low reset. clear > en priority.
// Accumulator width rule: ACC_WIDTH >= 2*WIDTH + ceil(log2(K)) for K accumulation steps without wrap.
module mac_int8 #(
    parameter integer WIDTH     = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire                        clk,
    input  wire                        rst_n,
    input  wire                        clear,
    input  wire                        en,
    input  wire signed [WIDTH-1:0]     a,
    input  wire signed [WIDTH-1:0]     b,
    output reg  signed [ACC_WIDTH-1:0] acc
);
    wire signed [2*WIDTH-1:0]   product = a * b;                 // both operands signed -> signed product
    wire signed [ACC_WIDTH-1:0] product_ext = {{(ACC_WIDTH-2*WIDTH){product[2*WIDTH-1]}}, product};

    always @(posedge clk) begin
        if (!rst_n)      acc <= {ACC_WIDTH{1'b0}};
        else if (clear)  acc <= {ACC_WIDTH{1'b0}};
        else if (en)     acc <= acc + product_ext;
    end
endmodule
```

`rtl/mac_array_2x2.v`:

```verilog
`default_nettype none
// 2x2 output-stationary MAC array: PE(i,j) accumulates a_i * b_j; operands are broadcast, accumulators stay put.
module mac_array_2x2 #(
    parameter integer WIDTH     = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire                        clk,
    input  wire                        rst_n,
    input  wire                        clear,
    input  wire                        en,
    input  wire signed [WIDTH-1:0]     a0,
    input  wire signed [WIDTH-1:0]     a1,
    input  wire signed [WIDTH-1:0]     b0,
    input  wire signed [WIDTH-1:0]     b1,
    output wire signed [ACC_WIDTH-1:0] acc00,
    output wire signed [ACC_WIDTH-1:0] acc01,
    output wire signed [ACC_WIDTH-1:0] acc10,
    output wire signed [ACC_WIDTH-1:0] acc11
);
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) pe00 (.clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a0), .b(b0), .acc(acc00));
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) pe01 (.clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a0), .b(b1), .acc(acc01));
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) pe10 (.clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a1), .b(b0), .acc(acc10));
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) pe11 (.clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a1), .b(b1), .acc(acc11));
endmodule
```

`rtl/tt_um_noahsabb_mac.v`:

```verilog
`default_nettype none
// Tiny Tapeout wrapper: byte-serial protocol (plan section 4.3) around a 2x2 int8 MAC array.
module tt_um_noahsabb_mac (
    input  wire [7:0] ui_in,    // Dedicated inputs  : data byte D
    output wire [7:0] uo_out,   // Dedicated outputs : selected result byte
    input  wire [7:0] uio_in,   // IOs: Input path   : [0]=strobe [2:1]=cmd [7:3]=unused
    output wire [7:0] uio_out,  // IOs: Output path  : 0
    output wire [7:0] uio_oe,   // IOs: Enable path  : 0 (all inputs)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    localparam integer WIDTH = 8;
    localparam integer ACC_WIDTH = 32;

    wire       strobe = uio_in[0];
    wire [1:0] cmd    = uio_in[2:1];
    wire [7:0] data   = ui_in;

    reg signed [WIDTH-1:0] a0, a1, b0, b1;
    reg        ptr_a, ptr_b;
    reg [1:0]  sel_acc, sel_byte;

    wire step  = strobe & (cmd == 2'd2);
    wire clr   = strobe & (cmd == 2'd3) & data[7];

    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= {WIDTH{1'b0}}; a1 <= {WIDTH{1'b0}}; b0 <= {WIDTH{1'b0}}; b1 <= {WIDTH{1'b0}};
            ptr_a <= 1'b0; ptr_b <= 1'b0; sel_acc <= 2'd0; sel_byte <= 2'd0;
        end else if (strobe) begin
            case (cmd)
                2'd0: begin if (ptr_a) a1 <= data; else a0 <= data; ptr_a <= ~ptr_a; end
                2'd1: begin if (ptr_b) b1 <= data; else b0 <= data; ptr_b <= ~ptr_b; end
                2'd2: begin ptr_a <= 1'b0; ptr_b <= 1'b0; end
                default: begin sel_acc <= data[1:0]; sel_byte <= data[3:2]; end
            endcase
        end
    end

    wire signed [ACC_WIDTH-1:0] acc00, acc01, acc10, acc11;
    mac_array_2x2 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) u_arr (
        .clk(clk), .rst_n(rst_n), .clear(clr), .en(step),
        .a0(a0), .a1(a1), .b0(b0), .b1(b1),
        .acc00(acc00), .acc01(acc01), .acc10(acc10), .acc11(acc11));

    reg [ACC_WIDTH-1:0] acc_sel;
    reg [7:0]           byte_sel;
    always @* begin
        acc_sel = acc00;
        case (sel_acc)
            2'd0: acc_sel = acc00;
            2'd1: acc_sel = acc01;
            2'd2: acc_sel = acc10;
            default: acc_sel = acc11;
        endcase
        byte_sel = acc_sel[7:0];
        case (sel_byte)
            2'd0: byte_sel = acc_sel[7:0];
            2'd1: byte_sel = acc_sel[15:8];
            2'd2: byte_sel = acc_sel[23:16];
            default: byte_sel = acc_sel[31:24];
        endcase
    end

    assign uo_out  = byte_sel;
    assign uio_out = 8'h00;
    assign uio_oe  = 8'h00;
    wire _unused = &{ena, uio_in[7:3], 1'b0};
endmodule
```

If Verilator reports `WIDTHEXPAND`/`WIDTHTRUNC` on the `a0 <= data` lines (unsigned 8-bit into signed 8-bit of equal width should be clean), fix with `$signed(data)`; never silence with `lint_off`.

### 4.7 Testbenches (`tests/tb_*.v`) — the Tiny Tapeout convention with `GL_TEST` power pins

`tests/tb_mac.v`:

```verilog
`default_nettype none
`timescale 1ns / 1ps
module tb_mac;
    parameter integer WIDTH = 8;
    parameter integer ACC_WIDTH = 32;
    reg clk = 1'b0, rst_n = 1'b0, clear = 1'b0, en = 1'b0;
    reg  signed [WIDTH-1:0] a = 0, b = 0;
    wire signed [ACC_WIDTH-1:0] acc;
    initial begin $dumpfile("tb_mac.vcd"); $dumpvars(0, tb_mac); #1; end
`ifdef GL_TEST
    wire VPWR = 1'b1;
    wire VGND = 1'b0;
    mac_int8 dut (.VPWR(VPWR), .VGND(VGND),
`else
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) dut (
`endif
        .clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a), .b(b), .acc(acc));
endmodule
```

`tests/tb_array.v`:

```verilog
`default_nettype none
`timescale 1ns / 1ps
module tb_array;
    parameter integer WIDTH = 8;
    parameter integer ACC_WIDTH = 32;
    reg clk = 1'b0, rst_n = 1'b0, clear = 1'b0, en = 1'b0;
    reg  signed [WIDTH-1:0] a0 = 0, a1 = 0, b0 = 0, b1 = 0;
    wire signed [ACC_WIDTH-1:0] acc00, acc01, acc10, acc11;
    initial begin $dumpfile("tb_array.vcd"); $dumpvars(0, tb_array); #1; end
`ifdef GL_TEST
    wire VPWR = 1'b1;
    wire VGND = 1'b0;
    mac_array_2x2 dut (.VPWR(VPWR), .VGND(VGND),
`else
    mac_array_2x2 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) dut (
`endif
        .clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a0(a0), .a1(a1), .b0(b0), .b1(b1),
        .acc00(acc00), .acc01(acc01), .acc10(acc10), .acc11(acc11));
endmodule
```

`tests/tb_tt.v` (identical to the Tiny Tapeout template `test/tb.v` with the module name replaced; reuse it verbatim in Phase 7):

```verilog
`default_nettype none
`timescale 1ns / 1ps
/* This testbench just instantiates the module and makes some convenient wires
   that can be driven / tested by the cocotb test.py. */
module tb_tt ();
  initial begin
    $dumpfile("tb_tt.vcd");
    $dumpvars(0, tb_tt);
    #1;
  end
  reg clk;
  reg rst_n;
  reg ena;
  reg [7:0] ui_in;
  reg [7:0] uio_in;
  wire [7:0] uo_out;
  wire [7:0] uio_out;
  wire [7:0] uio_oe;
`ifdef GL_TEST
  wire VPWR = 1'b1;
  wire VGND = 1'b0;
`endif
  tt_um_noahsabb_mac user_project (
`ifdef GL_TEST
      .VPWR(VPWR),
      .VGND(VGND),
`endif
      .ui_in  (ui_in),
      .uo_out (uo_out),
      .uio_in (uio_in),
      .uio_out(uio_out),
      .uio_oe (uio_oe),
      .ena    (ena),
      .clk    (clk),
      .rst_n  (rst_n)
  );
endmodule
```

### 4.8 `tests/Makefile` (cocotb 2.x; RTL and `GATES=yes` gate-level path)

cocotb 2.x Makefile variable names: `COCOTB_TEST_MODULES` (was `MODULE`), `COCOTB_TOPLEVEL` (was `TOPLEVEL`), `COCOTB_RANDOM_SEED` (was `RANDOM_SEED`). The `GATES=yes` block is the Tiny Tapeout template's recipe verbatim: defines `-DGL_TEST -DFUNCTIONAL -DUSE_POWER_PINS -DSIM -DUNIT_DELAY=#1`, cell models `$(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/{primitives.v,sky130_fd_sc_hd.v}`, plus the powered netlist.

```make
# tests/Makefile — cocotb 2.x. Usage: make -B TOP=mac|array|tt WIDTH=8 ACC_WIDTH=32 [GATES=yes GL_NETLIST=/abs/path.pnl.v]
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
TOP ?= mac
WIDTH ?= 8
ACC_WIDTH ?= 32
GATES ?= no
PDK_ROOT ?= $(HOME)/.ciel
RTL_DIR := $(PWD)/../rtl

ifeq ($(TOP),mac)
  RTL_SRCS := $(RTL_DIR)/mac_int8.v
  TB := tb_mac
  COCOTB_TEST_MODULES := test_mac
  PARAM_ARGS := -P$(TB).WIDTH=$(WIDTH) -P$(TB).ACC_WIDTH=$(ACC_WIDTH)
else ifeq ($(TOP),array)
  RTL_SRCS := $(RTL_DIR)/mac_int8.v $(RTL_DIR)/mac_array_2x2.v
  TB := tb_array
  COCOTB_TEST_MODULES := test_array
  PARAM_ARGS := -P$(TB).WIDTH=$(WIDTH) -P$(TB).ACC_WIDTH=$(ACC_WIDTH)
else
  RTL_SRCS := $(RTL_DIR)/mac_int8.v $(RTL_DIR)/mac_array_2x2.v $(RTL_DIR)/tt_um_noahsabb_mac.v
  TB := tb_tt
  COCOTB_TEST_MODULES := test_tt
  PARAM_ARGS :=
endif

ifneq ($(GATES),yes)
  SIM_BUILD := sim_build/rtl_$(TOP)_w$(WIDTH)_a$(ACC_WIDTH)
  VERILOG_SOURCES += $(RTL_SRCS)
  COMPILE_ARGS += $(PARAM_ARGS)
else
  SIM_BUILD := sim_build/gl_$(TOP)
  COMPILE_ARGS += -DGL_TEST
  COMPILE_ARGS += -DFUNCTIONAL
  COMPILE_ARGS += -DUSE_POWER_PINS
  COMPILE_ARGS += -DSIM
  COMPILE_ARGS += -DUNIT_DELAY=\#1
  VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
  VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v
  VERILOG_SOURCES += $(GL_NETLIST)
endif

VERILOG_SOURCES += $(PWD)/$(TB).v
COCOTB_TOPLEVEL := $(TB)
COCOTB_RANDOM_SEED ?= 1
export WIDTH ACC_WIDTH GATES
include $(shell cocotb-config --makefiles)/Makefile.sim
```

(`-P<top>.<param>=<value>` is Icarus's parameter-override syntax; `-DUNIT_DELAY=\#1` is copied from the Tiny Tapeout template.) `make` returns success even if a test fails, which is why every gate also runs `python -m cocotb_tools.check_results results.xml` (cocotb 2.x API).

### 4.9 cocotb tests (`tests/test_*.py`)

Timing convention for both RTL and gate-level: drive inputs at the falling edge, let the rising edge happen, sample outputs at the following falling edge. Clock period 10 ns for RTL, 1000 ns under `GATES=yes` so the `#1` unit-delay cell chain (tens of cells on the multiplier/adder path) settles well before sampling. Under reset, gate-level flops are `x` until the first reset edge; every golden sequence starts with `rst_n=0`.

`tests/test_mac.py`:

```python
import json, os, random, sys
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from ref.mac_ref import MacRef   # frozen reference model (read-only)

WIDTH = int(os.environ.get("WIDTH", "8"))
ACC = int(os.environ.get("ACC_WIDTH", "32"))
GATES = os.environ.get("GATES", "no") == "yes"
PERIOD_NS = 1000 if GATES else 10
GOLDEN = HERE / "golden" / f"mac_w{WIDTH}_acc{ACC}.json"

def mask(v, bits): return v & ((1 << bits) - 1)

async def start(dut):
    cocotb.start_soon(Clock(dut.clk, PERIOD_NS, unit="ns").start())
    dut.rst_n.value = 0; dut.clear.value = 0; dut.en.value = 0; dut.a.value = 0; dut.b.value = 0
    await FallingEdge(dut.clk)

async def drive_and_sample(dut, rst_n, clear, en, a, b):
    dut.rst_n.value = rst_n; dut.clear.value = clear; dut.en.value = en
    dut.a.value = mask(a, WIDTH); dut.b.value = mask(b, WIDTH)
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    return dut.acc.value.to_signed()

@cocotb.test()
async def golden_vectors(dut):
    g = json.loads(GOLDEN.read_text())
    assert g["params"]["WIDTH"] == WIDTH and g["params"]["ACC_WIDTH"] == ACC, f"golden/params mismatch for {GOLDEN}"
    await start(dut)
    for i, (rst_n, clear, en, a, b, exp) in enumerate(g["vectors"]):
        got = await drive_and_sample(dut, rst_n, clear, en, a, b)
        assert got == exp, f"golden vector {i}: rst_n={rst_n} clear={clear} en={en} a={a} b={b}: acc={got} expected {exp}"
    dut._log.info(f"{len(g['vectors'])} golden vectors matched ({GOLDEN.name}, GATES={GATES})")

@cocotb.test()
async def randomized_vs_reference(dut):
    seed = int(os.environ.get("COCOTB_RANDOM_SEED", "1")); rng = random.Random(seed)
    dut._log.info(f"randomized test seed={seed}")
    m = MacRef(WIDTH, ACC); await start(dut)
    lo, hi = -(1 << (WIDTH - 1)), (1 << (WIDTH - 1)) - 1
    n = 300 if GATES else 3000
    got = await drive_and_sample(dut, 0, 0, 0, 0, 0); m.clock(0, 0, 0, 0, 0)
    for i in range(n):
        r = rng.random(); rst_n = 0 if r < 0.01 else 1; clear = 1 if 0.01 <= r < 0.04 else 0
        en = 1 if rng.random() < 0.85 else 0; a, b = rng.randint(lo, hi), rng.randint(lo, hi)
        exp = m.clock(rst_n, clear, en, a, b)
        got = await drive_and_sample(dut, rst_n, clear, en, a, b)
        assert got == exp, f"random vector {i} (seed {seed}): a={a} b={b} en={en} clear={clear} rst_n={rst_n}: acc={got} expected {exp}"
```

`tests/test_array.py`:

```python
import json, os, sys
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
HERE = Path(__file__).resolve().parent
WIDTH = int(os.environ.get("WIDTH", "8")); ACC = int(os.environ.get("ACC_WIDTH", "32"))
GATES = os.environ.get("GATES", "no") == "yes"; PERIOD_NS = 1000 if GATES else 10
GOLDEN = HERE / "golden" / f"array_w{WIDTH}_acc{ACC}.json"
def mask(v, bits): return v & ((1 << bits) - 1)

@cocotb.test()
async def golden_vectors(dut):
    g = json.loads(GOLDEN.read_text())
    cocotb.start_soon(Clock(dut.clk, PERIOD_NS, unit="ns").start())
    for s in (dut.rst_n, dut.clear, dut.en, dut.a0, dut.a1, dut.b0, dut.b1): s.value = 0
    await FallingEdge(dut.clk)
    for i, v in enumerate(g["vectors"]):
        rst_n, clear, en, a0, a1, b0, b1 = v[:7]; exp = v[7:]
        dut.rst_n.value = rst_n; dut.clear.value = clear; dut.en.value = en
        dut.a0.value = mask(a0, WIDTH); dut.a1.value = mask(a1, WIDTH); dut.b0.value = mask(b0, WIDTH); dut.b1.value = mask(b1, WIDTH)
        await RisingEdge(dut.clk); await FallingEdge(dut.clk)
        got = [dut.acc00.value.to_signed(), dut.acc01.value.to_signed(), dut.acc10.value.to_signed(), dut.acc11.value.to_signed()]
        assert got == exp, f"array vector {i}: inputs={v[:7]} got={got} expected={exp}"
    dut._log.info(f"{len(g['vectors'])} array vectors matched")
```

`tests/test_tt.py` (the same file is used in the Tiny Tapeout repo's `test/test.py`, where `dut` is `tb` and the golden file is `test/golden/tt_protocol.json`):

```python
import json, os
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "golden" / "tt_protocol.json"
GATES = os.environ.get("GATES", "no") == "yes"
PERIOD_NS = 1000   # 1 MHz: slow enough for #1 unit-delay gate-level models, fast enough for 2.5k vectors

@cocotb.test()
async def protocol_golden(dut):
    g = json.loads(GOLDEN.read_text())
    cocotb.start_soon(Clock(dut.clk, PERIOD_NS, unit="ns").start())
    dut.ena.value = 1; dut.ui_in.value = 0; dut.uio_in.value = 0; dut.rst_n.value = 0
    await FallingEdge(dut.clk)
    for i, (rst_n, ui, uio, exp) in enumerate(g["vectors"]):
        dut.rst_n.value = rst_n; dut.ui_in.value = ui; dut.uio_in.value = uio
        await RisingEdge(dut.clk); await FallingEdge(dut.clk)
        got = dut.uo_out.value.to_unsigned()
        assert got == exp, f"tt vector {i}: rst_n={rst_n} ui_in=0x{ui:02x} uio_in=0x{uio:02x}: uo_out=0x{got:02x} expected 0x{exp:02x}"
        assert dut.uio_oe.value.to_unsigned() == 0 and dut.uio_out.value.to_unsigned() == 0
    dut._log.info(f"{len(g['vectors'])} protocol vectors matched (GATES={GATES})")
```

Run order and expected result (all must print `PASS=... FAIL=0` and `check_results` must exit 0):

```bash
make lint
make sim TOP=mac WIDTH=8 ACC_WIDTH=32
make sim TOP=mac WIDTH=4 ACC_WIDTH=24
make sim TOP=mac WIDTH=2 ACC_WIDTH=20
make sim TOP=mac WIDTH=4 ACC_WIDTH=10
make sim TOP=array WIDTH=8 ACC_WIDTH=32
make sim TOP=tt
```

If a cocotb 2.x API name is wrong (e.g. `unit=` vs `units=`, `to_signed()`), fix the **test driver**, consult `.venv/bin/python -c "import cocotb; help(cocotb.clock.Clock)"`, and re-run. If the RTL disagrees with a vector, reason from the spec in §4.1–4.3; the model is the spec's arbiter.

### 4.10 `factory/synth_check.py` — standalone synthesis gate (brew Yosys, before LibreLane)

A fast check that the design maps to sky130 cells with no latches, no unmapped `$` cells and no inferred memories, mirroring what LibreLane's `Yosys.Synthesis` + `Checker.YosysUnmappedCells` will do. It composes the documented command sequence (`read_liberty -lib -ignore_miss_dir -setattr blackbox`, `read_verilog -sv -noautowire`, `hierarchy -check`, `synth -flatten`, `dfflibmap`, `abc -D <ps> -liberty`, `setundef -zero`, `hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO`, `splitnets; opt_clean -purge`, `check -mapped`, `stat -liberty`).

```python
#!/usr/bin/env python3
import argparse, json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDK_ROOT = os.environ.get("PDK_ROOT", os.path.expanduser("~/.ciel"))
LIB = f"{PDK_ROOT}/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
TOPS = {
    "mac_int8": ["rtl/mac_int8.v"],
    "mac_array_2x2": ["rtl/mac_int8.v", "rtl/mac_array_2x2.v"],
    "tt_um_noahsabb_mac": ["rtl/mac_int8.v", "rtl/mac_array_2x2.v", "rtl/tt_um_noahsabb_mac.v"],
}
def run(top, files, width, acc, out, period_ns=10):
    os.makedirs(out, exist_ok=True)
    chparam = f"chparam -set WIDTH {width} -set ACC_WIDTH {acc} {top}\n" if top != "tt_um_noahsabb_mac" else ""
    ys = f"""
read_liberty -lib -ignore_miss_dir -setattr blackbox {LIB}
{''.join(f'read_verilog -sv -noautowire {ROOT}/{f}' + chr(10) for f in files)}
{chparam}hierarchy -check -top {top}
proc
tee -o {out}/{top}.latch.rpt select -count t:$dlatch t:$adlatch t:$dlatchsr
tee -o {out}/{top}.mem.rpt select -count t:$mem t:$mem_v2
synth -top {top} -flatten
dfflibmap -liberty {LIB}
abc -D {period_ns*1000} -liberty {LIB}
setundef -zero
hilomap -hicell sky130_fd_sc_hd__conb_1 HI -locell sky130_fd_sc_hd__conb_1 LO
splitnets
opt_clean -purge
tee -o {out}/{top}.chk.rpt check -mapped
tee -o {out}/{top}.stat.json stat -json -liberty {LIB}
write_verilog -noattr -noexpr -nohex -nodec {out}/{top}.nl.v
"""
    open(f"{out}/{top}.ys", "w").write(ys)
    r = subprocess.run(["yosys", "-q", "-l", f"{out}/{top}.log", "-s", f"{out}/{top}.ys"], capture_output=True, text=True)
    sys.stdout.write(r.stdout[-2000:]); sys.stderr.write(r.stderr[-2000:])
    if r.returncode != 0: print(f"FAIL {top}: yosys exit {r.returncode}"); return False
    txt = open(f"{out}/{top}.stat.json").read()
    j = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
    d = j["design"] if "design" in j else list(j["modules"].values())[0]
    cells = d.get("num_cells", 0); area = d.get("area", 0.0)
    unmapped = {k: v for k, v in d.get("num_cells_by_type", {}).items() if k.startswith("$")}
    latches = int(re.search(r"(\d+)", open(f"{out}/{top}.latch.rpt").read() or "0").group(1) or 0)
    mems = int(re.search(r"(\d+)", open(f"{out}/{top}.mem.rpt").read() or "0").group(1) or 0)
    chk = open(f"{out}/{top}.chk.rpt").read(); problems = len(re.findall(r"^Warning:", chk, re.M))
    ok = not unmapped and latches == 0 and mems == 0 and problems == 0 and cells >= 20
    print(f"{'PASS' if ok else 'FAIL'} {top}: cells={cells} area={area:.1f}um2 unmapped={unmapped} latches={latches} mems={mems} check_warnings={problems}")
    json.dump({"top": top, "cells": cells, "area": area, "unmapped": unmapped, "latches": latches, "mems": mems, "check_warnings": problems},
              open(f"{out}/{top}.summary.json", "w"), indent=2)
    return ok
if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--width", type=int, default=8); ap.add_argument("--acc", type=int, default=0)
    ap.add_argument("--out", default=f"{ROOT}/runs/synth"); a = ap.parse_args()
    acc = a.acc or (2 * a.width + 16)
    ok = all(run(t, f, a.width, acc, a.out) for t, f in TOPS.items())
    sys.exit(0 if ok else 1)
```

(The liberty filename `sky130_fd_sc_hd__tt_025C_1v80.lib` is the standard name; confirm with `ls $PDK_ROOT/sky130A/libs.ref/sky130_fd_sc_hd/lib/`. `select -count` output format: parse the first integer — if the report is empty treat it as 0.) Tiny Tapeout warns when a design synthesizes to fewer than 20 cells; the check enforces `cells >= 20`. Expected scale: a single 8-bit MAC with 32-bit accumulator ≈ 300–600 cells; the 2x2 array + wrapper ≈ 1,500–2,500 cells (this is why the Tiny Tapeout tile defaults to `1x2` in Phase 3, with `2x2` as the fallback).

```bash
make synth WIDTH=8
git add -A && git commit -m "phase 2: RTL (mac_int8, mac_array_2x2, tt_um_noahsabb_mac), cocotb tests, synth check" && make log MSG="PHASE 2 END"
```

---
## 5. Phase 3 — Flow configuration (budget 20 min)

### 5.1 `flow/mac_int8/config.json` — standalone hardening of the MAC (full contents)

JSON must be pure ECMA-404 (no comments). Variable names are the LibreLane 3.0 names (after the renames: `FP_PDN_*`→`PDN_*`, `FP_IO_*`→`IO_PIN_*`, `QUIT_ON_*`→`ERROR_ON_*`, `PL_TIME_DRIVEN`→`PL_TIMING_DRIVEN`, `GRT_ANTENNA_ITERS`→`GRT_ANTENNA_REPAIR_ITERS`). `dir::` means "relative to the design directory" (`make harden` copies `rtl/*.v` into `flow/mac_int8/src/` first).

```json
{
  "DESIGN_NAME": "mac_int8",
  "VERILOG_FILES": ["dir::src/mac_int8.v"],
  "SYNTH_PARAMETERS": ["WIDTH=8", "ACC_WIDTH=32"],
  "CLOCK_PORT": "clk",
  "CLOCK_PERIOD": 10,
  "FP_SIZING": "relative",
  "FP_CORE_UTIL": 40,
  "FP_ASPECT_RATIO": 1,
  "PL_TARGET_DENSITY_PCT": 50,
  "PL_TIMING_DRIVEN": true,
  "PL_ROUTABILITY_DRIVEN": true,
  "PDN_MULTILAYER": false,
  "PDN_VPITCH": 38.87,
  "RT_MAX_LAYER": "met4",
  "GRT_ADJUSTMENT": 0.3,
  "GRT_ALLOW_CONGESTION": false,
  "SYNTH_STRATEGY": "AREA 0",
  "RUN_LINTER": true,
  "LINTER_INCLUDE_PDK_MODELS": false,
  "RUN_CTS": true,
  "RUN_POST_GPL_DESIGN_REPAIR": true,
  "RUN_POST_CTS_RESIZER_TIMING": true,
  "RUN_ANTENNA_REPAIR": true,
  "RUN_FILL_INSERTION": true,
  "RUN_SPEF_EXTRACTION": true,
  "RUN_MCSTA": true,
  "RUN_IRDROP_REPORT": true,
  "RUN_MAGIC_STREAMOUT": true,
  "RUN_KLAYOUT_STREAMOUT": true,
  "RUN_KLAYOUT_XOR": true,
  "RUN_MAGIC_DRC": true,
  "RUN_KLAYOUT_DRC": true,
  "RUN_LVS": true,
  "RUN_EQY": false,
  "ERROR_ON_LINTER_ERRORS": true,
  "ERROR_ON_LINTER_TIMING_CONSTRUCTS": true,
  "ERROR_ON_LINTER_WARNINGS": false,
  "ERROR_ON_SYNTH_CHECKS": true,
  "ERROR_ON_UNMAPPED_CELLS": true,
  "ERROR_ON_NL_ASSIGN_STATEMENTS": true,
  "ERROR_ON_PDN_VIOLATIONS": true,
  "ERROR_ON_DISCONNECTED_PINS": true,
  "ERROR_ON_TR_DRC": true,
  "ERROR_ON_MAGIC_DRC": true,
  "ERROR_ON_KLAYOUT_DRC": true,
  "ERROR_ON_XOR_ERROR": true,
  "ERROR_ON_ILLEGAL_OVERLAPS": true,
  "ERROR_ON_LVS_ERROR": true,
  "SETUP_VIOLATION_CORNERS": ["*"],
  "HOLD_VIOLATION_CORNERS": ["*"],
  "PL_RESIZER_SETUP_SLACK_MARGIN": 0.05,
  "PL_RESIZER_HOLD_SLACK_MARGIN": 0.1,
  "GRT_RESIZER_SETUP_SLACK_MARGIN": 0.025,
  "GRT_RESIZER_HOLD_SLACK_MARGIN": 0.05,
  "PL_RESIZER_ALLOW_SETUP_VIOS": false,
  "GRT_RESIZER_ALLOW_SETUP_VIOS": false,
  "GRT_ANTENNA_REPAIR_ITERS": 3,
  "GRT_ANTENNA_REPAIR_MARGIN": 10,
  "DRT_OPT_ITERS": 64,
  "CTS_SINK_CLUSTERING_SIZE": 25,
  "CTS_SINK_CLUSTERING_MAX_DIAMETER": 50
}
```

Why these values:
- `FP_SIZING: relative` + `FP_CORE_UTIL: 40` (docs: "typical 25–60 %, 40 % is a good starting value") lets the die grow to fit; `PL_TARGET_DENSITY_PCT` must exceed utilization (LibreLane default is util + 10 on sky130_fd_sc_hd where `GPL_CELL_PADDING` = 0). For the sweep (Phase 6) and any run where the design is tiny, the orchestrator switches to `FP_SIZING: "absolute"` with `DIE_AREA: "0 0 150 150"` (µm, "x0 y0 x1 y1") so that the die is never smaller than one PDN strap pitch.
- `PDN_MULTILAYER: false` + `PDN_VPITCH: 38.87`: the sky130 default straps are met4 vertical at 153.6 µm pitch / 16.32 µm offset and met5 horizontal at 153.18 µm; a die smaller than pitch + offset gets zero straps (floating rails, `design__power_grid_violation__count` > 0). Using only the lower layer at the Tiny Tapeout pitch (38.87 µm) guarantees straps on a 100 µm die. `RT_MAX_LAYER: met4` keeps the standalone run identical in layer usage to the TT tile.
- `CLOCK_PERIOD: 10` (100 MHz, LibreLane's default; the 4×4 MAC-array grid search closed around 5.2 ns at tt, so 10 ns leaves margin at ss). `IO_DELAY_CONSTRAINT` stays at the PDK's 20 % (2 ns in/out), `CLOCK_UNCERTAINTY_CONSTRAINT` 0.25 ns, `TIME_DERATING_CONSTRAINT` 5 %, `MAX_FANOUT_CONSTRAINT` 10, `MAX_TRANSITION_CONSTRAINT` 0.75 ns, `OUTPUT_CAP_LOAD` 33.442 fF (PDK defaults; not overridden).
- STA corners: the PDK's nine IPVT corners (`{nom,min,max}_{tt_025C_1v80,ss_100C_1v60,ff_n40C_1v95}`, `DEFAULT_CORNER = nom_tt_025C_1v80`); `SETUP_VIOLATION_CORNERS`/`HOLD_VIOLATION_CORNERS: ["*"]` makes the checkers fail on any corner (3.0 default for hold is already `['*']`; stated explicitly so the sign-off definition is in the file). Setup binds at `max_ss_100C_1v60`, hold at `min_ff_n40C_1v95`.
- `SYNTH_STRATEGY: "AREA 0"` first; the closure loop tries `DELAY 1`, then `DELAY 4` (Appendix C). `SYNTH_MUL_BOOTH`/`SYNTH_ADDER_TYPE: CSA` are optional later levers for the multiplier path.
- Every `RUN_*`/`ERROR_ON_*` is stated explicitly so a diff shows any tampering; rule 12 forbids turning them off.

Optional custom SDC (not used by default; add only if `violator_list.rpt` shows the worst paths are in-to-reg through `rst_n`): create `flow/mac_int8/custom.sdc` as a copy of `~/librelane/librelane/scripts/base.sdc` plus `set_false_path -from [get_ports rst_n]`, and set `"PNR_SDC_FILE": "dir::custom.sdc", "SIGNOFF_SDC_FILE": "dir::custom.sdc"`. Note `rst_n` here is synchronous, so it is a data input; leaving it constrained at 20 % I/O delay is correct and is the default.

### 5.2 Tiny Tapeout path (used in Phase 7)

- Template: `https://github.com/TinyTapeout/ttsky-verilog-template` (sky130A; the old `tt10-verilog-template` belongs to the cancelled TT10 — do not use it). Workflows in it pin `TinyTapeout/tt-gds-action@ttsky26d` with `pdk: sky130A`; `action.yml`'s `librelane-version` default is **3.0.14** → `LIBRELANE_TAG=3.0.14` locally for bit-identical results.
- Tools: `git clone https://github.com/TinyTapeout/tt-support-tools tt` inside the project; `tt_tool.py --create-user-config` writes `src/user_config.json` (`DESIGN_NAME`, `VERILOG_FILES`, `DIE_AREA` from `tt/tech/sky130A/tile_sizes.yaml`, `FP_DEF_TEMPLATE = ../tt/tech/sky130A/def/tt_block_<tiles>_<suffix>.def`, `VDD_PIN: VPWR`, `GND_PIN: VGND`, `RT_MAX_LAYER: met4`), merges it with `src/config.json` into `src/config_merged.json`; `--harden` runs `python -m librelane --dockerized --docker-no-tty --pdk-root "$PDK_ROOT" --run-tag wokwi --force-run-dir runs/wokwi src/config_merged.json` (`--no-docker` switches to a local LibreLane). Then `--print-warnings`, `--print-stats` (utilization from `GPL-0019`), `--print-cell-category`, `--create-tt-submission`, `--create-png` (needs `rsvg-convert` from `librsvg` and `pngquant`).
- Template `src/config.json` is left untouched ("DO NOT EDIT THIS FILE unless you know what you are doing"): `PL_TARGET_DENSITY_PCT: 60`, `CLOCK_PERIOD: 20` (20 ns = 50 MHz; pad limit 66 MHz in / 33 MHz out), `CLOCK_PORT: "clk"`, `PL_RESIZER_HOLD_SLACK_MARGIN: 0.1`, `GRT_RESIZER_HOLD_SLACK_MARGIN: 0.05`, `DESIGN_REPAIR_BUFFER_OUTPUT_PORTS: 0`, `FP_SIZING: absolute`, `GRT_ALLOW_CONGESTION: 1`, `RUN_CTS: 1`, `RT_MAX_LAYER: met4`, `FP_PDN_MULTILAYER: 0`, `FP_PDN_VPITCH: 38.87`, `RUN_KLAYOUT_XOR: 0`, `RUN_KLAYOUT_DRC: 0` (precheck runs them later), `MAGIC_DEF_LABELS: 0`, `MAGIC_WRITE_LEF_PINONLY: 1`, `RUN_LINTER: 1`, `LINTER_INCLUDE_PDK_MODELS: 1`.
- Tile sizes (sky130A `DIE_AREA`, µm): `1x1` 161.00×111.52; `1x2` 161.00×225.76; `2x2` 334.88×225.76; `3x2` 508.76×225.76; `4x2` 682.64×225.76; `6x2` 1030.40×225.76; `8x2` 1378.16×225.76. A 1x1 tile fits "roughly 1000 digital logic gates". **Decision rule for this design:** start with `tiles: "1x2"`; if `--harden` fails with `GPL-0302` (placement density) or `--print-stats` shows utilization above 65 %, or DRT does not converge, switch to `"2x2"` and re-run `--create-user-config` (required after any tile change). Record the final tile choice as a NEEDS_HUMAN item (it sets the price).
- `info.yaml` full contents for this design (yaml_version 6; `pinout` must have exactly these 24 keys):

```yaml
# Tiny Tapeout project information
project:
  title:        "2x2 int8 MAC array (byte-serial)"
  author:       "Noah Sabb"
  discord:      ""
  description:  "Output-stationary 2x2 array of signed int8 multiply-accumulators with 32-bit accumulators, loaded and read one byte at a time over ui_in/uio_in."
  language:     "Verilog"
  clock_hz:     50000000
  # How many tiles your design occupies? A single tile is about 167x108 uM.
  tiles: "1x2"          # Valid values: 1x1, 1x2, 2x2, 3x2, 4x2, 6x2 or 8x2
  # Your top module name must start with "tt_um_". Make it unique by including your github username:
  top_module:  "tt_um_noahsabb_mac"
  # List your project's source files here.
  # Source files must be in ./src and you must list each source file separately, one per line.
  source_files:
    - "project.v"
    - "mac_array_2x2.v"
    - "mac_int8.v"

# The pinout of your project. Leave unused pins blank. DO NOT delete or add any pins.
pinout:
  # Inputs
  ui[0]: "data[0]"
  ui[1]: "data[1]"
  ui[2]: "data[2]"
  ui[3]: "data[3]"
  ui[4]: "data[4]"
  ui[5]: "data[5]"
  ui[6]: "data[6]"
  ui[7]: "data[7]"

  # Outputs
  uo[0]: "result[0]"
  uo[1]: "result[1]"
  uo[2]: "result[2]"
  uo[3]: "result[3]"
  uo[4]: "result[4]"
  uo[5]: "result[5]"
  uo[6]: "result[6]"
  uo[7]: "result[7]"

  # Bidirectional pins
  uio[0]: "strobe (input)"
  uio[1]: "cmd[0] (input)"
  uio[2]: "cmd[1] (input)"
  uio[3]: ""
  uio[4]: ""
  uio[5]: ""
  uio[6]: ""
  uio[7]: ""

# Do not change!
yaml_version: 6
```

(Compare against the template's own `info.yaml` after cloning: keep any additional keys the template has and only change the values above. `project.v` is `rtl/tt_um_noahsabb_mac.v` renamed, as the template convention expects.)

### 5.3 Classic flow stages — the table the dashboard mirrors

The Classic flow is 80 step entries; the dashboard groups them into the 22 "stations" below. `Step dir prefix` is the slug LibreLane uses for `runs/<tag>/NN-<slug>/` (lower-cased `Tool.Step`); the orchestrator matches on these.

| # | Station | Step IDs (dir slugs) | Tool | Key outputs | Metric(s) to check |
|---|---|---|---|---|---|
| 1 | Lint | `verilator-lint`, `checker-lint*` | Verilator 5.044 | `verilator-lint.log` | `design__lint_error__count`=0, `design__inferred_latch__count`=0, `design__lint_timing_construct__count`=0 |
| 2 | Synthesis | `yosys-jsonheader`, `yosys-synthesis`, `checker-yosys*`, `checker-netlistassignstatements` | Yosys 0.62 + ABC | `mac_int8.nl.v`, `reports/{stat,chk,latch,pre_synth_chk}.rpt`, `stat.json` | `design__instance__count`, `design__instance__area`, `design__instance_unmapped__count`=0, `synthesis__check_error__count`=0 |
| 3 | Pre-PnR STA | `openroad-checksdcfiles`, `openroad-staprepnr` | OpenSTA (9 corners, lib-only) | `summary.rpt`, `<corner>/max.rpt` | `timing__setup__ws` (surrogate only) |
| 4 | Floorplan | `openroad-floorplan`, `openroad-dumprcvalues`, `odb-setpowerconnections`, `odb-checkmacroantennaproperties`, `odb-manualmacroplacement`, `openroad-cutrows` | OpenROAD `initialize_floorplan` | `.odb`, `.def` | `design__die__bbox`, `design__core__bbox` |
| 5 | Tap/endcap | `openroad-tapendcapinsertion` | OpenROAD `tapcell` | `.odb` | taps every `FP_TAPCELL_DIST`=13 µm |
| 6 | PDN | `odb-addpdnobstructions`, `openroad-generatepdn`, `odb-removepdnobstructions` | OpenROAD `pdngen` | `.odb`, `.def` | `design__power_grid_violation__count`=0 (checked at station 8) |
| 7 | I/O placement | `odb-addroutingobstructions`, `openroad-globalplacementskipio`, `openroad-ioplacement`, `odb-customioplacement`, `odb-applydeftemplate` | OpenROAD `place_pins` | `.def` | pins on met2/met3 (`IO_PIN_V/H_LAYER`) |
| 8 | Global placement | `openroad-globalplacement`, `odb-writeverilogheader`, `checker-powergridviolations`, `openroad-stamidpnr` (1st) | OpenROAD `gpl` (RePlAce) | `.odb`, `.vh` | `design__instance__utilization`, overflow < 0.1 in log |
| 9 | Repair design | `openroad-repairdesignpostgpl`, `odb-manualglobalplacement` | OpenROAD `rsz repair_design` (20 % slew/cap margin) | `.odb` | slew/cap/fanout violations in log |
| 10 | Detailed placement | `openroad-detailedplacement` | OpenROAD `dpl` | `.odb` | `check_placement` = 0 in log |
| 11 | CTS | `openroad-cts`, `openroad-stamidpnr` (2nd) | TritonCTS (`clkbuf_16` root, `clkbuf_*`) | `cts.rpt` | buffers inserted, `clock__skew__worst_setup/hold` |
| 12 | Post-CTS timing repair | `openroad-resizertimingpostcts`, `openroad-stamidpnr` (3rd) | `rsz repair_timing` (setup 0.05 / hold 0.1 ns margins, ≤50 % buffers) | `.odb` | `timing__hold__ws` (surrogate), `hold*` instance count |
| 13 | Global routing | `openroad-globalrouting`, `openroad-checkantennas` (1st), `openroad-repairdesignpostgrt` (off), `odb-diodesonports`, `odb-heuristicdiodeinsertion` (off) | FastRoute (`GRT_ADJUSTMENT` 0.3) | route guides in `.odb` | overflow = 0 in log, `antenna__violating__pins` |
| 14 | Antenna repair | `openroad-repairantennas`, `openroad-resizertimingpostgrt` (off), `openroad-stamidpnr` (4th) | `repair_antennas` with `diode_2` | `.odb` | `antenna__violating__pins`, `antenna__violating__nets` |
| 15 | Detailed routing | `openroad-detailedrouting`, `odb-removeroutingobstructions`, `openroad-checkantennas` (2nd), `checker-trdrc` | TritonRoute (64 iters, antenna repair 3 iters) | `.def`, `.odb` | `route__drc_errors`=0; violations→0 before iter 64 |
| 16 | Post-route checks | `odb-reportdisconnectedpins`, `checker-disconnectedpins`, `odb-reportwirelength`, `checker-wirelength` | OpenDB | reports | `design__critical_disconnected_pin__count`=0, `route__wirelength__max` |
| 17 | Fill | `openroad-fillinsertion`, `odb-cellfrequencytables` | `filler_placement` (`fill*`, `decap*`) | `.odb`, `.def` | cell frequency tables |
| 18 | RCX | `openroad-rcx` | OpenRCX (nom/min/max rules) | `<corner>/mac_int8.<corner>.spef` | three SPEFs exist |
| 19 | Signoff STA | `openroad-stapostpnr` | OpenSTA 9 corners with SPEF | `summary.rpt`, `<corner>/{max,min,checks,violator_list,clock,unpropagated,power}.rpt`, `.sdf`, `.lib` | `timing__setup__ws`≥0, `timing__hold__ws`≥0, `*_vio__count`=0, `timing__unannotated_net_filtered__count`=0, `power__total` |
| 20 | IR drop | `openroad-irdropreport` | OpenROAD `psm` | `irdrop.rpt` | `ir__drop__worst` (rule of thumb ≤ 3–5 % of 1.8 V ≈ 90 mV) |
| 21 | Stream-out + XOR | `magic-streamout`, `klayout-streamout`, `klayout-render`, `magic-writelef`, `odb-checkdesignantennaproperties`, `klayout-xor`, `checker-xor` | Magic 8.3.623, KLayout 0.30.7 | `final/gds/mac_int8.gds`, `final/klayout_gds/`, `final/lef/`, `final/render/mac_int8.png` | `design__xor_difference__count`=0 |
| 22 | DRC + LVS + signoff | `magic-drc`, `klayout-drc`, `checker-magicdrc`, `checker-klayoutdrc`, `magic-spiceextraction`, `checker-illegaloverlap`, `netgen-lvs`, `checker-lvs`, `yosys-eqy` (off), `checker-setupviolations`, `checker-holdviolations`, `checker-maxslewviolations`, `checker-maxcapviolations`, `misc-reportmanufacturability` | Magic DRC, KLayout `sky130A_mr.drc`, Netgen 1.5.316 | `reports/drc.klayout.xml`, `report/drc.lyrdb`, `netgen-lvs.log`, `lvs.netgen.rpt` | `magic__drc_error__count`=0, `klayout__drc_error__count`=0, `magic__illegal_overlap__count`=0, `design__lvs_error__count`=0, log ends "Final result: Circuits match uniquely." |

Checker semantics: lint/unmapped-cell/synth-check/assign-statement/disconnected-pin failures raise an **immediate** `StepError` (the run stops there); DRC, LVS, XOR, long-wire, timing, slew, cap, illegal-overlap and PDN failures are **deferred** (the flow finishes, a GDS exists, then the run exits nonzero with a `StepException`). The orchestrator distinguishes these when deciding what to retry.

```bash
git add -A && git commit -m "phase 3: standalone LibreLane config, TT info.yaml, stage table" && make log MSG="PHASE 3 END"
```

---
## 6. Phase 4 — The orchestrator `factory/orchestrate.py` (budget 45 min)

What it does: (a) `ingest` a LibreLane run directory into `factory/state/pipeline.json` (per-station status, timestamps, log paths, metrics, image); (b) `closure` runs `make harden` repeatedly with a rule table, logging every change as a decision record with before/after metrics. It wraps LibreLane via the CLI (`--run-tag`, `--force-run-dir`) so every run is also a recorded gate; the Python API alternative (`from librelane.flows import Flow; Classic = Flow.factory.get("Classic"); Classic(cfg, design_dir=".").start(tag=TAG)`, `config.copy(FP_CORE_UTIL=35)`, `start_step_async()` for parallel sweeps) would have to run inside the Nix shell's Python and is not used overnight.

Metrics it extracts (names verified from LibreLane source): `timing__setup__ws`, `timing__setup__wns`, `timing__setup__tns`, `timing__setup_vio__count`, `timing__hold__ws`, `timing__hold__wns`, `timing__hold__tns`, `timing__hold_vio__count` (each also per corner as `<name>__corner:<corner>`), `design__max_slew_violation__count`, `design__max_cap_violation__count`, `design__max_fanout_violation__count`, `clock__skew__worst_setup`, `clock__skew__worst_hold`, `timing__unannotated_net_filtered__count`, `design__instance__count`, `design__instance__area`, `design__instance__utilization`, `design__die__bbox`, `design__core__bbox`, `route__drc_errors`, `route__wirelength__max`, `route__antenna_violation__count`, `antenna__violating__pins`, `antenna__violating__nets`, `magic__drc_error__count`, `klayout__drc_error__count`, `magic__illegal_overlap__count`, `design__xor_difference__count`, `design__lvs_error__count`, `design__lvs_unmatched_net__count`, `design__lvs_unmatched_device__count`, `design__power_grid_violation__count`, `design__critical_disconnected_pin__count`, `design__lint_error__count`, `design__inferred_latch__count`, `synthesis__check_error__count`, `design__instance_unmapped__count`, `power__total`, `power__internal__total`, `power__switching__total`, `power__leakage__total`, `ir__drop__avg`, `ir__drop__worst`, `ir__voltage__worst`. (Verify the key spelling against an actual `final/metrics.json` after the first run; the extractor tolerates missing keys.)

### 6.1 `factory/orchestrate.py` (full contents)

```python
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
      ],
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

def closure(config_path, design, tag, max_attempts):
    base = jload(config_path); cfg = copy.deepcopy(base); counts = {}
    decisions = jload(os.path.join(STATE, "decisions.json"), [])
    best = None
    for attempt in range(1, max_attempts + 1):
        atag = f"{tag}-a{attempt}"
        acfg = os.path.join(os.path.dirname(config_path), f"config_{atag}.json")
        json.dump(cfg, open(acfg, "w"), indent=2)
        log(f"CLOSURE attempt {attempt}/{max_attempts} tag={atag} config={os.path.relpath(acfg, ROOT)}")
        t0 = time.time()
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
        best = atag if rc == 0 else (best or atag)
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
    c = sub.add_parser("closure"); c.add_argument("--config", required=True); c.add_argument("--design", default="mac_int8"); c.add_argument("--tag", required=True); c.add_argument("--max-attempts", type=int, default=4)
    args = ap.parse_args()
    if args.cmd == "ingest": ingest(args.run_dir, args.design, render=not args.no_render); sys.exit(0)
    sys.exit(closure(args.config, args.design, args.tag, args.max_attempts))
```

Rule table summary (also Appendix C): setup WNS < 0 → `SYNTH_STRATEGY "DELAY 1"` → `FP_CORE_UTIL −10` (floor 25, density = util+10) → `CLOCK_PERIOD ×1.1` (cap 20 ns) → `DELAY 4` + `SYNTH_ADDER_TYPE CSA`; DRT non-convergence / `route__drc_errors` > 0 → `PL_TARGET_DENSITY_PCT −10` → `GRT_ADJUSTMENT +0.1` (cap 0.6) → `FP_CORE_UTIL −10`; `GPL-0302` → density +10 (cap 80) → absolute 200×200 die; hold WS < 0 → raise `PL_RESIZER_HOLD_SLACK_MARGIN` +0.1 / `GRT_RESIZER_HOLD_SLACK_MARGIN` +0.05 → tighter CTS clustering (never `*_ALLOW_SETUP_VIOS`); antenna → `GRT_ANTENNA_REPAIR_ITERS` 6 / margin 20 / `DRT_ANTENNA_REPAIR_ITERS` 6 → `RUN_HEURISTIC_DIODE_INSERTION` → `DIODE_ON_PORTS in`; PDN violations → `PDN_VPITCH` 25 → absolute 150×150 die; DRC → density −10; LVS / XOR / immediate StepError → NEEDS_HUMAN (never a config "fix"). Every change is a decision record `{time, series, attempt, tag_before, tag_after, symptom, rule, changes:{VAR:[old,new]}, before:{metrics}, after:{metrics}, result}` in `factory/state/decisions.json`.

### 6.2 `factory/render.py` (full contents) — one layout image per major station

Order of methods: (1) LibreLane's own `KLayout.Render` step re-run standalone on a station's `state_out.json` (`python3 -m librelane.steps run --id KLayout.Render --config runs/<tag>/resolved.json --state-in <step>/state_out.json --output <dir>` inside the Nix shell — (unverified — check `python3 -m librelane.steps run --help` inside `nix-shell`; if `resolved.json` is rejected as `--config`, use the step's own `config.json` and add the `KLAYOUT_RENDER_*` keys from `resolved.json`); (2) for the final GDS, the flow's own `final/render/<design>.png`; (3) gdstk `write_svg` + `rsvg-convert --unlimited` (Tiny Tapeout's `--create-png` method), falling back to `cairosvg`.

```python
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
```

An alternative headless renderer for an ODB (congestion heat map) is OpenROAD's `save_image -web -width 1024 layout.png` / `save_image -web -display_option {rudy true} layout_rudy.png` inside `openroad` with the ODB loaded (unverified — check that the bundled OpenROAD commit `dcf36133` has `-web`; the README documenting it is from master).

### 6.3 `factory/sta_report.py` (full contents)

```python
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
```

### 6.4 Run it

```bash
make harden-closure TAG=mac-w8 DESIGN=mac_int8 CONFIG=flow/mac_int8/config.json
make sta-report TAG=$(cat factory/state/best_run.txt)
make sim-gl TAG=$(cat factory/state/best_run.txt)
make render TAG=$(cat factory/state/best_run.txt)
git add -A && git commit -m "phase 4: orchestrator, first closed MAC run $(cat factory/state/best_run.txt)" && make log MSG="PHASE 4 END"
```

Expected runtime per LibreLane run for a ~500-cell design on an M-series Mac: single-digit minutes (the fixed cost is nine-corner STA, two DRC decks and LVS). If the first run exits nonzero only because of a deferred checker, the closure loop handles it; if it exits nonzero at `Yosys.Synthesis` or `Verilator.Lint`, read `runs/<tag>/error.log` and the step log, fix the RTL, re-run `make lint sim synth`, then re-run the closure.

---
## 7. Phase 5 — The dashboard `factory/dashboard/` (budget 40 min)

A static single HTML file regenerated from `factory/state/pipeline.json` (plus `gates.json`, `decisions.json`, `sweep.csv`, `NEEDS_HUMAN.md`, images) and served with `python -m http.server`. The build script embeds the JSON into the page (so it works from `file://` too), copies images into `site/img/`, and also writes `site/pipeline.json` so the page can poll for updates every 15 s while a run is in progress. No external CDN assets: the page must work offline.

### 7.1 `factory/dashboard/build.py` (full contents)

```python
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
html = tpl.replace("__DATA_JSON__", json.dumps(data).replace("</", "<\\/"))
open(os.path.join(SITE, "index.html"), "w").write(html)
json.dump(data, open(os.path.join(SITE, "pipeline.json"), "w"))
print("wrote", os.path.join(SITE, "index.html"), "stations:", len(data.get("stations", [])), "gates:", len(data["gates"]), "decisions:", len(data["decisions"]))
```

### 7.2 `factory/dashboard/template.html` (full contents)

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>spec2tapeout factory</title>
<style>
  :root { --bg:#0f1115; --panel:#171a21; --line:#2a2f3a; --fg:#e6e6e6; --muted:#9aa3b2; --pass:#2ecc71; --fail:#e74c3c; --warn:#f1c40f; --run:#3498db; --pend:#4b5563; --skip:#7f8c8d; }
  body { margin:0; font:14px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; background:var(--bg); color:var(--fg); }
  header { display:flex; flex-wrap:wrap; gap:16px; align-items:center; padding:14px 20px; border-bottom:1px solid var(--line); background:var(--panel); position:sticky; top:0; z-index:5; }
  header h1 { font-size:18px; margin:0; } header .meta { color:var(--muted); } header label { margin-left:auto; cursor:pointer; }
  .badge { display:inline-block; padding:2px 8px; border-radius:10px; font-size:12px; font-weight:600; color:#000; }
  .pass{background:var(--pass)} .fail{background:var(--fail);color:#fff} .warn{background:var(--warn)} .running{background:var(--run);color:#fff} .pending{background:var(--pend);color:#fff} .skipped{background:var(--skip);color:#fff} .unknown{background:var(--pend);color:#fff}
  main { padding:16px 20px; display:grid; gap:16px; }
  section { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:14px; }
  section h2 { margin:0 0 10px; font-size:15px; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; }
  .line { display:flex; overflow-x:auto; gap:6px; padding:8px 0; }
  .station { min-width:120px; flex:0 0 auto; border:1px solid var(--line); border-radius:6px; padding:8px; cursor:pointer; background:#1d2129; position:relative; }
  .station.active { outline:2px solid var(--run); }
  .station .n { color:var(--muted); font-size:11px; } .station .name { font-weight:600; margin:2px 0; } .station .tool { font-size:11px; color:var(--muted); }
  .station .dot { position:absolute; right:8px; top:8px; width:10px; height:10px; border-radius:50%; }
  .station::after { content:"\25B8"; position:absolute; right:-9px; top:38%; color:var(--muted); } .station:last-child::after { content:""; }
  .detail { display:grid; grid-template-columns: 1.2fr 1fr; gap:14px; } .detail img { max-width:100%; border:1px solid var(--line); border-radius:4px; background:#fff; }
  table { border-collapse:collapse; width:100%; font-size:13px; } th, td { text-align:left; padding:4px 8px; border-bottom:1px solid var(--line); } th { color:var(--muted); font-weight:600; }
  td.num { font-variant-numeric: tabular-nums; text-align:right; } .neg { color:var(--fail); font-weight:600; } .pos { color:var(--pass); }
  .grid2 { display:grid; grid-template-columns: repeat(auto-fit, minmax(380px, 1fr)); gap:16px; }
  .learn { display:none; margin-top:8px; padding:8px 10px; border-left:3px solid var(--warn); background:#20232b; color:#d9dde5; }
  body.learning .learn { display:block; }
  .kv { display:grid; grid-template-columns: max-content 1fr; gap:2px 12px; font-size:13px; } .kv div:nth-child(odd) { color:var(--muted); }
  .timeline li { margin-bottom:8px; } code { background:#20232b; padding:1px 4px; border-radius:3px; font-size:12px; }
  .muted { color:var(--muted); } a { color:#8ab4f8; } .plots img { max-width:100%; }
  @media (max-width:900px) { .detail { grid-template-columns:1fr; } }
</style>
</head>
<body>
<header>
  <h1>spec2tapeout factory</h1>
  <span class="meta" id="runmeta"></span>
  <span id="runstatus" class="badge unknown">unknown</span>
  <label><input type="checkbox" id="learn"> learning mode (plain-English explanations)</label>
</header>
<main>
  <section>
    <h2>Factory line — click a station</h2>
    <div class="line" id="line"></div>
    <div class="learn">Each box is a "station" of the LibreLane Classic flow (80 steps grouped into 22). Green = every step in the station wrote its state_out.json and the run exited 0; red = a step failed or a deferred checker (timing, DRC, LVS, XOR) blamed this station; grey = not reached. The design flows left to right: text (RTL) becomes gates, gates get positions, positions get wires, wires get checked, and the result is a GDS file the foundry can print.</div>
  </section>
  <section id="detail"><h2>Station detail</h2><div class="muted">Select a station above.</div></section>
  <div class="grid2">
    <section><h2>Timing (signoff STA, per corner)</h2><div id="timing"></div>
      <div class="learn">Setup slack is how much earlier than required the data arrived at the slow/hot/low-voltage corner (ss_100C_1v60, max RC); negative means the chip cannot run at CLOCK_PERIOD. Hold slack is how long the data stayed stable after the clock edge at the fast/cold/high-voltage corner (ff_n40C_1v95, min RC); negative means the chip is broken at any frequency. The flow subtracts 0.25 ns clock uncertainty and applies ±5 % derate before reporting these numbers. TNS adds up all negative slacks; "vio" counts violating endpoints.</div></section>
    <section><h2>Area / utilization / power</h2><div id="area"></div>
      <div class="learn">Instance area is the sum of standard-cell areas (um²); utilization is that area divided by the core area; a sky130 1x1 Tiny Tapeout tile is 161.00 x 111.52 um and fits roughly 1000 gates. Power is OpenSTA's vectorless estimate (internal + switching + leakage) at the nominal corner.</div></section>
  </div>
  <section><h2>Gate ladder</h2><div id="gates"></div></section>
  <section><h2>Decisions timeline (closure loop)</h2><ul class="timeline" id="decisions"></ul>
    <div class="learn">When a run fails a checker, the orchestrator applies one rule from a fixed table (synthesis strategy → utilization → clock period for setup; density → routing adjustment for congestion; resizer margins → CTS clustering for hold; repair iterations → diodes for antennas) and re-runs. Every change is recorded with the metrics before and after, so a human can audit why the final configuration looks the way it does.</div></section>
  <section><h2>Sweep: WIDTH × CLOCK_PERIOD</h2><div id="sweep"></div><div class="plots" id="plots"></div>
    <div class="learn">The same MAC was hardened at operand widths 2, 4 and 8 bits and several clock periods. Area should grow roughly with the square of the width (the multiplier), worst slack should get worse as the clock period shrinks, and the point where WNS crosses zero is the fastest clock the design closes at.</div></section>
  <section><h2>NEEDS HUMAN</h2><ul id="needs"></ul></section>
</main>
<script id="data" type="application/json">__DATA_JSON__</script>
<script>
const LEARN = {
  lint: "A spell-checker for hardware: it reads the Verilog without building anything and warns about constructs that simulate fine but synthesize badly (latches from incomplete if/case, nets driven from two places, widths that silently truncate).",
  synth: "Synthesis translates the RTL into a netlist of sky130 standard cells. Yosys does the logic optimization and flip-flop mapping; ABC maps the remaining logic to NAND/NOR/AOI cells using the liberty timing tables, aiming for area (AREA strategies) or speed (DELAY strategies). The cell count and area here are the first real cost of the design.",
  sta_pre: "Static timing analysis before any layout: with ideal clocks and no wires it tells you whether the clock period is hopeless (a large negative slack here will not get better after routing).",
  floorplan: "Decide the size and shape of the chip core. Relative sizing grows the die until the cells fill FP_CORE_UTIL percent of it; absolute sizing (Tiny Tapeout) fixes the outline and utilization becomes a result.",
  tap: "Tap cells connect the silicon wells to power and ground every 13 um so that the parasitic thyristor between n-well and substrate can never switch on (latch-up); end-caps terminate the rows cleanly.",
  pdn: "The power grid: metal-1 rails that follow the cell rows and wider metal-4 straps every PDN_VPITCH um, joined by via stacks. Too sparse and the chip sees IR drop; too dense and signals cannot route.",
  io: "Where the chip's pins go on the edge of the die. Tiny Tapeout dictates them from a template DEF; standalone runs let OpenROAD choose.",
  gpl: "Global placement finds an (x,y) for every cell by treating cells as electric charges that repel where the density is too high while wires pull connected cells together, iterating until no bin is overfull (overflow < 10 %).",
  repair: "The resizer fixes electrical rule violations: nets with too many loads or too much capacitance get buffers, slow gates get upsized. 20 % margins because wire parasitics are still estimates.",
  dpl: "Legalization: every cell is moved to the nearest legal site in a row with no overlaps, keeping displacement small.",
  cts: "Clock tree synthesis builds a balanced tree of clock buffers from the clock pin to every flip-flop. From here the clock is 'propagated': real arrival-time differences (skew) exist, which is why hold violations only appear after this step.",
  rsz_cts: "With the real clock tree, the resizer repairs setup (upsizing, buffering, cloning) and then hold (inserting delay on short paths) with margins of 0.05 ns and 0.1 ns, refusing hold fixes that would break setup.",
  grt: "Global routing assigns every net to coarse routing cells and layers. Capacity is deliberately reduced by 30 % so the detailed router has slack; leftover overflow is congestion.",
  antenna: "During manufacturing, long metal wires connected only to a transistor gate collect plasma charge that can damage the gate oxide. The checker computes metal-to-gate area ratios and diodes are inserted to drain the charge where the ratio is too high.",
  drt: "Detailed routing draws the actual wires and vias on the tracks, then runs search-and-repair iterations with a built-in design-rule checker until there are zero violations (or 64 iterations).",
  postroute: "Sanity checks after routing: every pin connected, no wire longer than the PDK threshold.",
  fill: "Fill and decoupling-capacitor cells are placed in every gap so the power rails and wells are continuous and the metal density is uniform enough for manufacturing.",
  rcx: "Parasitic extraction: the resistance and capacitance of every real wire are computed from the layout for three interconnect corners (nominal, minimum, maximum) and written as SPEF files.",
  sta_post: "Signoff timing: OpenSTA re-times the design at nine corners with the extracted parasitics. This is the only timing result that counts; setup is judged at the slow corner, hold at the fast corner.",
  ir: "Static IR-drop analysis solves the resistive power grid with each cell's current to find the worst voltage droop; a few percent of 1.8 V is the usual budget.",
  gds: "The layout database is streamed out to GDSII by two independent tools (Magic and KLayout) and the two results are XOR-compared; an empty XOR means both tools agree about every polygon.",
  signoff: "Two design-rule-check decks (Magic and KLayout) verify manufacturing rules; Magic extracts transistors from the layout and Netgen compares that circuit with the gate netlist (LVS). Then all deferred checkers report: this is where 'tapeout ready' is decided."
};
const D = JSON.parse(document.getElementById('data').textContent);
const $ = s => document.querySelector(s);
const fmt = v => v === null || v === undefined ? '—' : (typeof v === 'number' ? (Number.isInteger(v) ? v : v.toFixed(3)) : v);
const cls = v => (typeof v === 'number' && v < 0) ? 'neg' : ((typeof v === 'number') ? 'pos' : '');
document.body.classList.toggle('learning', localStorage.getItem('learn') === '1');
$('#learn').checked = localStorage.getItem('learn') === '1';
$('#learn').onchange = e => { document.body.classList.toggle('learning', e.target.checked); localStorage.setItem('learn', e.target.checked ? '1' : '0'); };

function render() {
  $('#runmeta').textContent = `run ${D.run_tag} · ${D.design || ''} · generated ${D.generated_at || ''}` + (D.elapsed_s ? ` · elapsed ${(D.elapsed_s/3600).toFixed(2)} h` : '');
  $('#runstatus').textContent = D.status; $('#runstatus').className = 'badge ' + D.status;
  const line = $('#line'); line.innerHTML = '';
  (D.stations || []).forEach((s, i) => {
    const el = document.createElement('div'); el.className = 'station'; el.dataset.id = s.id;
    el.innerHTML = `<div class="n">${i+1}</div><div class="name">${s.name}</div><div class="tool">${s.tool}</div><div class="dot ${s.status}" style="background:var(--${{pass:'pass',fail:'fail',warn:'warn',running:'run',pending:'pend',skipped:'skip'}[s.status]||'pend'})"></div>`;
    el.onclick = () => showStation(s, el); line.appendChild(el);
  });
  const m = D.metrics || {}, C = D.corners || {};
  const corners = Object.keys(C).sort();
  let t = `<table><tr><th>corner</th><th>setup ws</th><th>setup tns</th><th>setup vio</th><th>hold ws</th><th>hold tns</th><th>hold vio</th></tr>`;
  corners.forEach(c => { const r = C[c]; t += `<tr><td>${c}</td><td class="num ${cls(r.timing__setup__ws)}">${fmt(r.timing__setup__ws)}</td><td class="num">${fmt(r.timing__setup__tns)}</td><td class="num">${fmt(r.timing__setup_vio__count)}</td><td class="num ${cls(r.timing__hold__ws)}">${fmt(r.timing__hold__ws)}</td><td class="num">${fmt(r.timing__hold__tns)}</td><td class="num">${fmt(r.timing__hold_vio__count)}</td></tr>`; });
  t += `<tr><th>overall</th><td class="num ${cls(m.timing__setup__ws)}">${fmt(m.timing__setup__ws)}</td><td class="num">${fmt(m.timing__setup__tns)}</td><td class="num">${fmt(m.timing__setup_vio__count)}</td><td class="num ${cls(m.timing__hold__ws)}">${fmt(m.timing__hold__ws)}</td><td class="num">${fmt(m.timing__hold__tns)}</td><td class="num">${fmt(m.timing__hold_vio__count)}</td></tr></table>`;
  t += `<div class="kv" style="margin-top:8px"><div>max slew / cap / fanout violations</div><div>${fmt(m.design__max_slew_violation__count)} / ${fmt(m.design__max_cap_violation__count)} / ${fmt(m.design__max_fanout_violation__count)}</div><div>worst skew setup / hold</div><div>${fmt(m.clock__skew__worst_setup)} / ${fmt(m.clock__skew__worst_hold)} ns</div><div>unannotated nets (filtered)</div><div>${fmt(m.timing__unannotated_net_filtered__count)}</div></div>`;
  $('#timing').innerHTML = t;
  $('#area').innerHTML = `<div class="kv"><div>instances</div><div>${fmt(m.design__instance__count)}</div><div>instance area</div><div>${fmt(m.design__instance__area)} um²</div><div>utilization</div><div>${fmt(m.design__instance__utilization)}</div><div>die bbox</div><div>${fmt(m.design__die__bbox)}</div><div>core bbox</div><div>${fmt(m.design__core__bbox)}</div><div>power total / internal / switching / leakage</div><div>${fmt(m.power__total)} / ${fmt(m.power__internal__total)} / ${fmt(m.power__switching__total)} / ${fmt(m.power__leakage__total)} W</div><div>IR drop worst / avg</div><div>${fmt(m.ir__drop__worst)} / ${fmt(m.ir__drop__avg)}</div><div>route DRC / Magic DRC / KLayout DRC</div><div>${fmt(m.route__drc_errors)} / ${fmt(m.magic__drc_error__count)} / ${fmt(m.klayout__drc_error__count)}</div><div>LVS errors / XOR diff / antenna pins</div><div>${fmt(m.design__lvs_error__count)} / ${fmt(m.design__xor_difference__count)} / ${fmt(m.antenna__violating__pins)}</div><div>GDS</div><div>${D.gds || '—'} (${D.gds_bytes || 0} bytes)</div></div>`;
  let g = `<table><tr><th>gate</th><th>status</th><th>exit</th><th>duration</th><th>ended</th><th>log</th></tr>`;
  Object.entries(D.gates || {}).sort((a,b) => (a[1].ended||'').localeCompare(b[1].ended||'')).forEach(([k, v]) => { g += `<tr><td>${k}</td><td><span class="badge ${v.status}">${v.status}</span></td><td class="num">${v.exit_code}</td><td class="num">${v.duration_s}s</td><td>${v.ended}</td><td><code>${v.log}</code></td></tr>`; });
  $('#gates').innerHTML = g + '</table>';
  const dl = $('#decisions'); dl.innerHTML = (D.decisions || []).length ? '' : '<li class="muted">No closure decisions were needed.</li>';
  (D.decisions || []).forEach(d => { const li = document.createElement('li'); li.innerHTML = `<b>${d.time}</b> attempt ${d.attempt} · symptom <code>${d.symptom}</code> · ${d.rule}<br>changes: <code>${JSON.stringify(d.changes)}</code><br>before: <code>${JSON.stringify(d.before)}</code><br>after: <code>${JSON.stringify(d.after)}</code> → <span class="badge ${d.result||'pending'}">${d.result||'pending'}</span>`; dl.appendChild(li); });
  if ((D.sweep || []).length) {
    const cols = Object.keys(D.sweep[0]); let s = '<table><tr>' + cols.map(c => `<th>${c}</th>`).join('') + '</tr>';
    D.sweep.forEach(r => { s += '<tr>' + cols.map(c => `<td class="num ${c.includes('ws') ? cls(parseFloat(r[c])) : ''}">${r[c]}</td>`).join('') + '</tr>'; });
    $('#sweep').innerHTML = s + '</table>';
  } else $('#sweep').innerHTML = '<div class="muted">No sweep yet (make sweep).</div>';
  $('#plots').innerHTML = Object.entries(D.sweep_plots || {}).map(([k, v]) => `<img src="${v}" alt="sweep ${k}">`).join('');
  const nl = $('#needs'); nl.innerHTML = (D.needs_human || []).length ? '' : '<li class="muted">Nothing queued.</li>';
  (D.needs_human || []).forEach(x => { const li = document.createElement('li'); li.textContent = x.replace(/^- /, ''); nl.appendChild(li); });
  const first = (D.stations || []).find(s => s.status === 'fail') || (D.stations || []).slice(-1)[0];
  if (first) showStation(first, [...document.querySelectorAll('.station')].find(e => e.dataset.id === first.id));
}
function showStation(s, el) {
  document.querySelectorAll('.station').forEach(e => e.classList.remove('active')); if (el) el.classList.add('active');
  const steps = (s.steps || []).map(e => `<tr><td>${e.n}</td><td>${e.slug}</td><td><span class="badge ${e.ok ? 'pass' : 'fail'}">${e.ok ? 'ok' : 'no state_out'}</span></td><td>${e.started || ''}</td><td>${e.ended || ''}</td><td>${e.log_url ? `<a href="${e.log_url}" target="_blank">log</a>` : (e.log || '')}</td></tr>`).join('');
  const mets = Object.entries(s.metrics || {}).map(([k, v]) => `<div>${k}</div><div class="${cls(v)}">${fmt(v)}</div>`).join('');
  $('#detail').innerHTML = `<h2>Station detail — ${s.name} <span class="badge ${s.status}">${s.status}</span></h2>
    <div class="detail"><div>
      <p>${s.explain}</p>
      <div class="kv"><div>tool</div><div>${s.tool}</div><div>inputs</div><div>${(s.inputs||[]).join(', ')}</div><div>outputs</div><div>${(s.outputs||[]).join(', ')}</div><div>duration</div><div>${(s.duration_s||0).toFixed(1)} s</div><div>run dir</div><div><code>${s.dir || '—'}</code></div></div>
      <div class="learn">${LEARN[s.id] || ''}</div>
      <h3 style="font-size:13px;color:var(--muted)">key metrics</h3><div class="kv">${mets || '<div class="muted">none</div>'}</div>
      <h3 style="font-size:13px;color:var(--muted)">steps</h3><table><tr><th>#</th><th>step</th><th>state</th><th>started</th><th>ended</th><th>log</th></tr>${steps}</table>
    </div><div>${s.image_url ? `<img src="${s.image_url}?t=${Date.now()}" alt="layout at ${s.name}">` : '<div class="muted">no layout image for this station</div>'}</div></div>`;
}
render();
setInterval(() => { fetch('pipeline.json?t=' + Date.now()).then(r => r.ok ? r.json() : null).then(j => { if (j && j.generated_at !== D.generated_at) { Object.assign(D, j); render(); } }).catch(() => {}); }, 15000);
</script>
</body>
</html>
```

### 7.3 Build and serve

```bash
make dashboard
make serve &     # http://localhost:8787 ; stop with: kill %1  (or pkill -f "http.server 8787")
curl -s http://localhost:8787/ | head -5
git add -A && git commit -m "phase 5: dashboard generator and template" && make log MSG="PHASE 5 END"
```

Verify with `curl` that `index.html` is served and contains the string `spec2tapeout factory`; verify `site/img/` has at least the `gds.png` image for the best run. Leave the server running in the background for the morning (the `serve` process is harmless); `make report` prints the one-line command to start it again.

---
## 8. Phase 6 — Sweep (budget 90 min)

`WIDTH ∈ {2,4,8}` × `CLOCK_PERIOD ∈ {5,10,20}` ns = 9 runs, sequential (one Nix LibreLane process at a time; `-j` default), unique run tags `sweep-w<W>-p<P>`. Each run uses the Phase 3 config with `SYNTH_PARAMETERS` and `CLOCK_PERIOD` replaced and an **absolute** floorplan (`FP_SIZING: absolute`, `DIE_AREA` from a per-width table) so a 40-cell `WIDTH=2` design still gets PDN straps; `ACC_WIDTH = 2*WIDTH + 16` (20/24/32) to keep the accumulator rule. Failing runs (e.g. `WIDTH=8` at 5 ns is expected to miss setup — the 4×4 MAC-array study found ~5.2 ns for multiply+accumulate at the nominal corner) are **kept** in the CSV with their negative WNS; the sweep gate passes if at least 6 of 9 runs produced a `final/metrics.json`. If `make elapsed` says you are behind schedule (Appendix E), run only `--periods 10,20`.

### 8.1 `factory/sweep.py` (full contents)

```python
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
```

(`make harden` with `CONFIG=flow/sweep/<tag>/config.json` copies `rtl/*.v` into `flow/mac_int8/src/`, which is harmless; the sweep config points at its own `dir::src/`.) The sweep is resumable: rows already in `sweep.csv` are skipped.

```bash
make sweep                       # or: .venv/bin/python factory/sweep.py --periods 10,20   if behind schedule
make dashboard
git add -A && git commit -m "phase 6: sweep WIDTH x CLOCK_PERIOD" && make log MSG="PHASE 6 END"
```

Expected shape: area roughly quadratic in `WIDTH` (the multiplier dominates), `WIDTH=8` failing setup at 5 ns and closing at 10 and 20 ns, `WIDTH=2` closing everywhere; `fmax_est_MHz` = `1000/(period − ws_ss)` is only meaningful for runs that close.

---

## 9. Phase 7 — Tiny Tapeout repository (budget 60 min)

Shuttle: **TTSKY26d** (sky130A via ChipFoundry, closes 2026-11-30, chips expected 2027-05-12). Template `TinyTapeout/ttsky-verilog-template`; its `gds.yaml` already pins `TinyTapeout/tt-gds-action@ttsky26d` with `pdk: sky130A` and runs four jobs: `gds` → `precheck`, `gl_test`, `viewer`. Submission itself (app.tinytapeout.com → "Create a new project" → repo URL → pay / coupon → "Submit a new revision") is a web click and is a NEEDS_HUMAN item.

### 9.1 Create the repo from the template and clone it

```bash
gh repo create NoahSabb/tt-um-noahsabb-mac --template TinyTapeout/ttsky-verilog-template --public --description "2x2 int8 MAC array for Tiny Tapeout TTSKY26d"
sleep 20    # template repos are populated asynchronously; retry the clone until it has files
git clone https://github.com/NoahSabb/tt-um-noahsabb-mac tt_repo
ls tt_repo/src tt_repo/test tt_repo/docs tt_repo/.github/workflows
```

If `gh repo create --template` is rejected (the flag requires the source to be marked as a template repository; (unverified — check `gh repo create --help`)), fall back to: `git clone https://github.com/TinyTapeout/ttsky-verilog-template tt_repo && cd tt_repo && rm -rf .git && git init -b main && gh repo create NoahSabb/tt-um-noahsabb-mac --public --source=. --remote=origin` (this `rm -rf .git` is inside `tt_repo/`, which the hook allows only via `make`; use `git clone --depth 1` and then `git remote set-url origin https://github.com/NoahSabb/tt-um-noahsabb-mac` instead, which needs no deletion).

### 9.2 Fill `src/`, `info.yaml`, `docs/info.md`, `test/`

```bash
cp rtl/tt_um_noahsabb_mac.v tt_repo/src/project.v
cp rtl/mac_array_2x2.v rtl/mac_int8.v tt_repo/src/
```

`tt_repo/info.yaml`: the full contents from §5.2 (compare with the template's file; keep its structure). `tt_repo/src/config.json`: **unchanged** from the template.

`tt_repo/docs/info.md` (full contents; the three headings are mandatory and feed the datasheet; images must be < 512 kB each):

```markdown
<!---
This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.
You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

## How it works

A 2x2 output-stationary array of signed 8-bit multiply-accumulate units with 32-bit accumulators. Each processing
element PE(i,j) owns one accumulator and computes acc_ij += a_i * b_j on every STEP command, so after K steps the
four accumulators hold the 2x2 matrix product of a K×2 operand stream A and a 2×K operand stream B. Operands are
loaded one byte at a time over `ui_in` and results are read back one byte at a time on `uo_out`, which fits the
8-in / 8-out / 8-bidirectional pad budget of a Tiny Tapeout tile. All logic is synchronous to `clk`; `rst_n`
(active low) clears operands, pointers and accumulators.

Protocol (sampled on the rising edge of `clk`; a command takes effect at the edge where `uio[0]` (strobe) is 1):

| `uio[2:1]` cmd | name   | effect                                                                                       |
|----------------|--------|----------------------------------------------------------------------------------------------|
| 0              | LOAD_A | `a[ptr_a] <= ui_in` (signed int8), `ptr_a` toggles (two LOAD_A in a row write a0 then a1)     |
| 1              | LOAD_B | `b[ptr_b] <= ui_in`, `ptr_b` toggles                                                          |
| 2              | STEP   | every PE accumulates `a_i*b_j`; pointers reset to 0                                           |
| 3              | SELECT | `ui_in[1:0]` selects the accumulator (0=acc00,1=acc01,2=acc10,3=acc11), `ui_in[3:2]` the byte (0=LSB … 3=MSB); if `ui_in[7]`=1 all accumulators are cleared |

`uo_out` continuously shows the selected byte of the selected accumulator (valid from the cycle after SELECT).
`uio[7:3]` are ignored; all `uio` pins are configured as inputs (`uio_oe = 0`).

## How to test

1. Hold `rst_n` low for a few clocks, then release it.
2. Load A: put 3 on `ui_in`, set `uio_in = 0b001` (strobe, cmd 0), clock once; put 0xFB (-5) on `ui_in`, clock once.
3. Load B: `ui_in = 7`, `uio_in = 0b011` (strobe, cmd 1), clock; `ui_in = 0xFE` (-2), clock.
4. STEP three times: `uio_in = 0b101`, clock once each.
5. Read acc00 low byte: `ui_in = 0b0000_0000`, `uio_in = 0b111`, clock; `uo_out` now shows 63 (= 3*7*3).
   acc01 (`ui_in = 1`) reads 0xEE (-18), acc10 (`ui_in = 2`) 0x97 (-105), acc11 (`ui_in = 3`) 30.
6. Clear everything with `ui_in = 0x80`, `uio_in = 0b111`.

The cocotb test in `test/test.py` replays `test/golden/tt_protocol.json` (2,500+ vectors generated from a Python
reference model) against the RTL and the gate-level netlist. On the demo board the same bytes can be replayed from
MicroPython: `tt.shuttle.tt_um_noahsabb_mac.enable()`, `tt.reset_project(True/False)`, `tt.ui_in.value = D`,
`tt.uio_in.value = cmd_bits`, `tt.clock_project_once()`, read `tt.uo_out.value`.

## External hardware

None. The RP2350 demo board drives all inputs and reads `uo_out`.
```

`tt_repo/test/tb.v`: the template's `tb.v` with `tt_um_example` replaced by `tt_um_noahsabb_mac` (the content is `tests/tb_tt.v` from §4.7 with the module name `tb` instead of `tb_tt` and the dump file `tb.vcd`). `tt_repo/test/test.py`: the file from §4.9 `test_tt.py` verbatim (its `dut` is the template's `tb`, which exposes the same `ena/ui_in/uio_in/uo_out/uio_oe/uio_out/clk/rst_n` regs/wires). `tt_repo/test/golden/tt_protocol.json`: copied from `tests/golden/tt_protocol.json` (copying out of the frozen directory is allowed; the hook only blocks writes into it). `tt_repo/test/Makefile`: the template's file with one line changed:

```make
PROJECT_SOURCES = project.v mac_array_2x2.v mac_int8.v
```

`tt_repo/test/requirements.txt`: if it pins `cocotb==1.x`, replace with:

```
pytest==8.3.4
cocotb==2.1.0
```

(The template's `test.yaml` runs `python -m cocotb_tools.check_results results.xml`, a cocotb 2.x API, so 2.x is what CI expects.)

```bash
cp tests/test_tt.py tt_repo/test/test.py
mkdir -p tt_repo/test/golden && cp tests/golden/tt_protocol.json tt_repo/test/golden/
sed -i '' 's/tt_um_example/tt_um_noahsabb_mac/' tt_repo/test/tb.v
grep -n PROJECT_SOURCES tt_repo/test/Makefile
make tt-test
```

### 9.3 Local harden with tt-support-tools (LibreLane 3.0.14 in Docker, bit-identical to CI)

```bash
brew install libpng qhull cairo
/opt/homebrew/bin/python3.11 -m venv .venv-tt
.venv-tt/bin/pip install --upgrade pip
git clone https://github.com/TinyTapeout/tt-support-tools tt_repo/tt
.venv-tt/bin/pip install -r tt_repo/tt/requirements.txt
.venv-tt/bin/pip install librelane==3.0.14
export PDK_ROOT="$HOME/.ciel" PDK=sky130A LIBRELANE_TAG=3.0.14
.venv-tt/bin/ciel enable --pdk-family sky130 8afc8346a57fe1ab7934ba5a6056ea8b43078e71   # if ciel is in that venv; else .venv/bin/ciel
make tt-harden
```

`make tt-harden` runs `tt_tool.py --create-user-config`, `--harden` (which executes `python -m librelane --dockerized --docker-no-tty --pdk-root "$PDK_ROOT" --run-tag wokwi --force-run-dir runs/wokwi src/config_merged.json`; the first run pulls `ghcr.io/librelane/librelane:3.0.14`, ~3–4 GB), `--print-warnings`, `--print-stats`, `--print-cell-category`. The whole local procedure "should take roughly 10 minutes". If Docker fails three ways, use the Nix shell instead: `nix-shell ~/librelane/shell.nix --run "cd tt_repo && ../.venv-tt/bin/python tt/tt_tool.py --harden --no-docker"` (unverified — `--no-docker` makes `tt_tool.py` call the pip-installed `librelane` module, which then needs OpenROAD/Magic/KLayout/Netgen from the Nix PATH; record whichever path worked).

Tile decision: read `--print-stats` (utilization comes from the `GPL-0019` line). If utilization > 65 %, or `--harden` failed with `GPL-0302`, or detailed routing did not converge: set `tiles: "2x2"` in `info.yaml`, re-run `make tt-harden` (it re-runs `--create-user-config`). Write the final choice and both utilization numbers into `NEEDS_HUMAN.md` (it decides the price).

```bash
make tt-test-gl        # copies runs/wokwi/final/pnl/tt_um_noahsabb_mac.pnl.v to test/gate_level_netlist.v, make -B GATES=yes
cd tt_repo && ../.venv-tt/bin/python tt/tt_tool.py --create-png && ls -la gds_render.png; cd ..
```

Then capture the TT run's numbers without disturbing the dashboard (which shows the MAC run; `ingest` would overwrite `pipeline.json`):

```bash
cp tt_repo/runs/wokwi/final/metrics.json factory/state/tt_metrics.json
.venv/bin/python factory/sta_report.py tt_repo/runs/wokwi | tee factory/state/tt_sta_report.txt
```

`factory/report.py` (Phase 8) reads `factory/state/tt_metrics.json` for the Tiny Tapeout timing/area table.

### 9.4 Precheck locally (attempt; GitHub Action is authoritative)

The `precheck` job runs `tt-support-tools/precheck/precheck.py --gds <file> --tech sky130A` inside a Nix shell with KLayout 0.30.4 and Magic 8.3.568, after installing a precheck-specific sky130A PDK via `TinyTapeout/ciel-action@v1` (hash `0536d02d…` — the full hash was not captured; read it with `gh api repos/TinyTapeout/tt-gds-action/contents/precheck/action.yml?ref=ttsky26d -H "Accept: application/vnd.github.raw"` and `ciel enable` it if the local precheck complains about the PDK). Local attempt:

```bash
.venv-tt/bin/pip install -r tt_repo/tt/precheck/requirements.txt
make precheck
```

`make precheck` does `tt_tool.py --create-tt-submission` then `cd tt/precheck && nix-shell --run "python precheck.py --gds ../../tt_submission/*.gds --tech sky130A"` (`tt/precheck/default.nix` defines that shell; its first evaluation downloads KLayout 0.30.4/Magic 8.3.568 — if it tries to **build** them from source, abort after 10 minutes and mark precheck "GitHub Action only" in `NEEDS_HUMAN.md`). Results land in `tt_repo/tt/precheck/reports/results.md`. Checks for sky130A, in order: Magic DRC; KLayout `sky130A_mr.drc` FEOL, BEOL, offgrid; pin-label-overlap; zero-area; top-cell name = `tt_um_noahsabb_mac`, no `met5`, prBoundary present; pins vs template DEF; boundary = exact die bbox; power pins `VGND`/`VDPWR` with `USE POWER/GROUND` on met4 ≥ 1.2 µm; valid layers; cell names without `#`/`/`; nwell/urpm; Verilog syntax via `yowasp-yosys`. No LVS, density or antenna check for sky130 (LVS ran inside LibreLane).

### 9.5 Push and record the Actions run

```bash
cd tt_repo
git add -A
git commit -m "tt_um_noahsabb_mac: 2x2 int8 MAC array, byte-serial protocol, golden-vector cocotb test"
git push -u origin main
gh api -X POST repos/NoahSabb/tt-um-noahsabb-mac/pages -f build_type=workflow || echo "Pages enable failed (unverified API) -> NEEDS_HUMAN: enable GitHub Pages (Settings > Pages > Source: GitHub Actions) for the viewer job"
sleep 30
gh run list --repo NoahSabb/tt-um-noahsabb-mac --limit 10 --json databaseId,name,status,conclusion,url
cd ..
```

Then watch (the `gds` workflow takes ~10–20 min on GitHub's runners):

```bash
cd tt_repo && for id in $(gh run list --repo NoahSabb/tt-um-noahsabb-mac --limit 5 --json databaseId -q '.[].databaseId'); do gh run watch $id --exit-status --repo NoahSabb/tt-um-noahsabb-mac || true; done; gh run list --repo NoahSabb/tt-um-noahsabb-mac --limit 5 --json name,conclusion,url; cd ..
```

Record every run's `url` and `conclusion` (`test`, `docs`, `gds` with its `precheck`/`gl_test`/`viewer` jobs) in `factory/state/tt_actions.json` (write it with `gh run list ... --json name,conclusion,url,databaseId > factory/state/tt_actions.json`) and in the morning report. If `gds` fails, read `gh run view <id> --log-failed --repo ...`, fix (RTL/test/info.yaml only), push, re-watch (rule 5: three hypotheses). If only `viewer` fails because Pages is not enabled, that is a NEEDS_HUMAN item, not a failure.

```bash
git add -A && git commit -m "phase 7: Tiny Tapeout repo created, hardened, pushed; actions recorded" && make log MSG="PHASE 7 END"
```

---
## 10. Phase 8 — `make verify-factory` and the morning report (budget 45 min)

### 10.1 `factory/verify.py` (full contents)

Runs, from a clean run directory: (a) the full pipeline on the MAC (`doctor → lint → sim → synth → harden → sim-gl → render`); (b) checks every required gate's exit code in `gates.json`; (c) checks `pipeline.json` has every station `pass`/`skipped`; (d) checks the GDS exists with nonzero size and that an SVG renders from it; (e) gate-level sim vs golden vectors (the `sim-gl-mac` gate); (f) optional, experimental eqy equivalence; (g) rebuilds the dashboard. Writes `factory/state/verify.json`; exits nonzero if any required check fails.

```python
#!/usr/bin/env python3
"""make verify-factory: re-prove the whole factory from a clean run. Writes factory/state/verify.json."""
import glob, json, os, shutil, subprocess, sys, time, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); STATE = os.path.join(ROOT, "factory", "state")
sys.path.insert(0, os.path.join(ROOT, "factory")); import orchestrate as O
TAG = "verify-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
results = {}
def check(name, ok, detail=""):
    results[name] = {"ok": bool(ok), "detail": str(detail)[:2000]}; O.log(f"VERIFY {name}: {'PASS' if ok else 'FAIL'} {detail[:200] if detail else ''}")
def make(*args):
    return subprocess.call(["make", *args], cwd=ROOT)

# (a) full pipeline from clean on the MAC
rc = make("doctor"); check("a_doctor", rc == 0, f"exit {rc}")
rc = make("lint"); check("a_lint", rc == 0, f"exit {rc}")
rc = make("sim", "TOP=mac", "WIDTH=8", "ACC_WIDTH=32"); check("a_sim_rtl", rc == 0, f"exit {rc}")
rc = make("synth", "WIDTH=8"); check("a_synth", rc == 0, f"exit {rc}")
make("clean-run", f"TAG={TAG}")
rc = make("harden", f"TAG={TAG}", "DESIGN=mac_int8", "CONFIG=" + (open(os.path.join(STATE, "best_config.txt")).read().strip() if os.path.exists(os.path.join(STATE, "best_config.txt")) else "flow/mac_int8/config.json"))
check("a_harden", rc == 0, f"exit {rc} tag {TAG}")
rc = make("sim-gl", f"TAG={TAG}", "TOP=mac"); check("e_sim_gl_vs_golden", rc == 0, f"exit {rc}")
rc = make("render", f"TAG={TAG}"); check("a_render", rc == 0, f"exit {rc}")

# (b) every gate exit code
gates = O.jload(os.path.join(STATE, "gates.json"), {})
required = ["doctor", "lint", "sim-mac-w8", "synth-8", f"harden-{TAG}", "sim-gl-mac"]
missing = [g for g in required if g not in gates]; failed = [g for g in required if g in gates and gates[g]["exit_code"] != 0]
check("b_gates", not missing and not failed, f"missing={missing} failed={failed}")

# (c) pipeline.json all stations pass
p = O.jload(os.path.join(STATE, "pipeline.json"), {})
bad = [s["id"] for s in p.get("stations", []) if s["status"] not in ("pass", "skipped")]
check("c_pipeline_all_pass", p.get("run_tag") == TAG and not bad and p.get("status") == "pass", f"run_tag={p.get('run_tag')} status={p.get('status')} bad_stations={bad}")

# (d) GDS exists nonzero and SVG renders
gds = glob.glob(os.path.join(ROOT, "runs", TAG, "final", "gds", "*.gds"))
ok_gds = bool(gds) and os.path.getsize(gds[0]) > 0
svg_ok = False; detail = ""
if ok_gds:
    try:
        import gdstk; lib = gdstk.read_gds(gds[0]); top = lib.top_level()[0]; svg = os.path.join(ROOT, "runs", TAG, "final", "gds", "verify.svg")
        top.write_svg(svg, pad="5%"); svg_ok = os.path.getsize(svg) > 0; detail = f"{gds[0]} {os.path.getsize(gds[0])} bytes; svg {os.path.getsize(svg)} bytes; top cell {top.name}"
    except Exception as e: detail = f"gdstk failed: {e}"
check("d_gds_and_svg", ok_gds and svg_ok, detail)

# (f) optional eqy (experimental): LibreLane's Yosys.EQY on the final state; never required
eqy_ok = None; eqy_detail = "skipped"
try:
    steps = O.step_dirs(os.path.join(ROOT, "runs", TAG)); last = [d for _, _, d in steps if os.path.exists(os.path.join(d, "state_out.json"))]
    if last and shutil.which("nix-shell"):
        out = os.path.join(ROOT, "runs", TAG, "eqy"); os.makedirs(out, exist_ok=True)
        cmd = f"cd {ROOT}/runs/{TAG} && python3 -m librelane.steps run --id Yosys.EQY --config resolved.json --state-in {last[-1]}/state_out.json --output {out}"
        r = subprocess.run(["nix-shell", os.path.expanduser("~/librelane/shell.nix"), "--run", cmd], capture_output=True, text=True, timeout=1800)
        txt = r.stdout + r.stderr; eqy_ok = ("DONE (PASS" in txt) or (r.returncode == 0 and "FAIL" not in txt); eqy_detail = f"exit {r.returncode}; " + txt[-600:]
except Exception as e: eqy_detail = f"eqy attempt failed: {e}"
results["f_eqy_experimental"] = {"ok": eqy_ok, "detail": eqy_detail, "required": False}; O.log(f"VERIFY f_eqy_experimental: {eqy_ok} {eqy_detail[:200]}")

# (g) rebuild dashboard
rc = make("dashboard"); check("g_dashboard", rc == 0 and os.path.exists(os.path.join(ROOT, "factory", "dashboard", "site", "index.html")), f"exit {rc}")

results["_tag"] = TAG; results["_time"] = O.now()
json.dump(results, open(os.path.join(STATE, "verify.json"), "w"), indent=2)
req_fail = [k for k, v in results.items() if isinstance(v, dict) and v.get("required", True) and v.get("ok") is False]
print("verify-factory:", "PASS" if not req_fail else f"FAIL {req_fail}")
sys.exit(0 if not req_fail else 1)
```

(The closure loop in `orchestrate.py` writes the winning config path into `factory/state/best_config.txt`; `verify.py` re-runs exactly that configuration.) The eqy step is explicitly experimental in LibreLane ("you are expected to provide your own EQY script"; the generic script "fails in a number of scenarios") — a FAIL there is informational and goes into the report, never into a config change.

### 10.2 `factory/report.py` (full contents) — writes `reports/MORNING_REPORT.md`

```python
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
```

### 10.3 Run Phase 8

```bash
make verify-factory
make report
git add -A && git commit -m "phase 8: verify-factory and morning report" && make log MSG="PHASE 8 END"
```

If `make verify-factory` fails on a required check after three hypotheses, record it in `NEEDS_HUMAN.md`, still run `make report`, and commit with `phase 8: verify-factory partial`. The Stop hook lets the session end once `reports/MORNING_REPORT.md` exists.

---

## 11. NEEDS HUMAN — pre-populated

Put these in `NEEDS_HUMAN.md` under `## Pre-populated (known in advance)` in Phase 1; append discoveries under `## Found overnight` with timestamps.

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

---
## Appendix A — LibreLane CLI cheat sheet and run-directory layout

All commands run as `nix-shell ~/librelane/shell.nix --run "librelane ..."` (or `.venv/bin/python -m librelane --dockerized --docker-no-tty ...` in the Docker fallback; `--dockerized` must precede every other option except `--docker-mount` and `--docker-no-tty`).

| Flag | Meaning |
|---|---|
| `librelane config.json` | run the Classic flow; run dir `runs/RUN_<date>` under the design dir |
| `--run-tag T` | name the run `runs/T` |
| `--force-run-dir DIR` | put the run at DIR (Tiny Tapeout uses `runs/wokwi`) |
| `--last-run` | resume the most recent run (newest `state_out.json` by mtime) |
| `--from ID` / `--to ID` / `--only ID` | start at / stop after / run just step ID (e.g. `--last-run --from OpenROAD.CTS`) |
| `--skip ID` (repeatable) | skip a step in a sequential flow |
| `--overwrite` | delete an existing run with the same tag first |
| `-c KEY=VALUE` | override a variable; VALUE must be valid JSON and KEY must not be a deprecated name (e.g. `-c FP_CORE_UTIL=35`, `-c 'SYNTH_STRATEGY="DELAY 1"'`) |
| `--flow OpenInKLayout` / `OpenInOpenROAD` / `OpenInMagic` | open a prior run in the GUI (`--last-run`, optionally `--with-initial-state runs/<tag>/NN-step/state_out.json` for an intermediate view) |
| `--with-initial-state FILE` | start from a given state (resume/experiment) |
| `--initial-state-element-override FORMAT=PATH` | replace one view in the initial state |
| `--pdk-root DIR`, `--pdk sky130A`, `-s sky130_fd_sc_hd` | PDK selection (`PDK_ROOT` env and `~/.ciel` are the fallbacks) |
| `-j N` | parallel jobs; `-j1` to limit load |
| `--log-level ERROR --condensed --show-progress-bar` | quieter output |
| `--smoke-test` | temporary end-to-end test (fetches the PDK) |
| `--run-example spm` | run the bundled example in a fresh directory |
| `--save-views-to DIR` | copy final views out |
| `--reproducible ID` | bundle a step for a bug report |
| `--manual-pdk` | do not auto-fetch the PDK with Ciel |
| `--version` / `--bare-version` | version strings |
| `python3 -m librelane.steps run --id <Step.ID> --config <config.json> --state-in <state_in.json> --output <dir>` | run one step standalone |
| `librelane.help <Flow or Step ID>` (unverified — check `python3 -m librelane.help --help`) | print the markdown help for a flow/step |
| `--flow SynthesisExploration` | sweep `SYNTH_STRATEGY` values |

Run directory layout (`runs/<tag>/`):

```
flow.log  error.log  warning.log  info.log  resolved.json  tmp/
NN-<tool>-<step>/      COMMANDS  config.json  state_in.json  state_out.json  <step>.log  *.process_stats.json  <views>
   e.g. 01-verilator-lint/verilator-lint.log
        06-yosys-synthesis/{mac_int8.nl.v, mac_int8.nl.v.json, reports/{stat,chk,latch,pre_synth_chk,pre_techmap,post_dff}.rpt, reports/stat.json, *.abc, synthesis.abc.sdc}
        12-openroad-staprepnr/{summary.rpt, <corner>/...}
        NN-openroad-stapostpnr/{summary.rpt, <corner>/{max.rpt,min.rpt,checks.rpt,violator_list.rpt,clock.rpt,unpropagated.rpt,skew.max.rpt,skew.min.rpt,tns.*.rpt,wns.*.rpt,ws.*.rpt,power.rpt,sta.log,<design>__<corner>.sdf,<design>__<corner>.lib}}
        NN-openroad-rcx/<corner>/<design>.<corner>.spef
        NN-openroad-checkantennas/reports/antenna.rpt
        NN-magic-drc/reports/{drc.rpt,drc.klayout.xml}   NN-klayout-drc/report/drc.lyrdb
        NN-netgen-lvs/{netgen-lvs.log, lvs.netgen.rpt}
final/   def gds json_h klayout_gds lef lib mag mag_gds nl odb pnl sdc sdf spef spice vh render   metrics.json  metrics.csv
```

Design-format IDs (3.0.16): `nl` (.nl.v, unpowered), `pnl` (.pnl.v, powered with VPWR/VGND), `logical_nl`, `sdf_pnl`, `logical_pnl`, `def`, `lef`, `sdc`, `sdf` (per corner), `spef` (nom/min/max), `lib` (per corner), `spice`, `cdl`, `gds`, `vh`, `spice_rcx`, `render` (.png), `klayout_gds`, `mag`, `mag_gds`, `json_h`.

## Appendix B — Metrics and report files, and what "good" looks like

| Metric (final/metrics.json) | Written by | Good | Notes |
|---|---|---|---|
| `design__lint_error__count`, `design__lint_warning__count`, `design__inferred_latch__count`, `design__lint_timing_construct__count` | Verilator.Lint | 0 / any / 0 / 0 | errors and latches fatal; warnings not |
| `design__instance__count`, `design__instance__area` | Yosys.Synthesis (`stat.json` num_cells/area) | ≥ 20 cells; area in µm² | ~300–600 cells for one 8-bit MAC |
| `design__instance_unmapped__count`, `synthesis__check_error__count` | Yosys.Synthesis | 0 / 0 | a `$` cell survived / Yosys `check` warning |
| `design__instance__utilization` | OpenROAD.GlobalPlacement | 0.3–0.6 | TT uses target density 60 % |
| `design__die__bbox`, `design__core__bbox` | Floorplan | — | µm |
| `design__power_grid_violation__count` | GeneratePDN → Checker.PowerGridViolations | 0 | "may ignore if LVS passes" (docs), but the checker still fails |
| `clock__skew__worst_setup`, `clock__skew__worst_hold` | STA | tens of ps to ~0.2 ns | from `skew.max/min.rpt` |
| `timing__setup__ws`, `timing__setup__wns`, `timing__setup__tns`, `timing__setup_vio__count` (+`__corner:<c>`) | STAPostPNR | ws ≥ 0, wns = 0, tns = 0, vio = 0 at every corner | `wns = min(0, ws)`; setup binds at `max_ss_100C_1v60` |
| `timing__hold__ws`, `timing__hold__wns`, `timing__hold__tns`, `timing__hold_vio__count` | STAPostPNR | ws ≥ 0 at every corner (binds at `min_ff_n40C_1v95`) | negative hold = dead chip |
| `timing__setup_r2r__ws`, `timing__hold_r2r__ws` | STA | ≥ 0 | reg-to-reg only |
| `design__max_slew_violation__count`, `design__max_cap_violation__count`, `design__max_fanout_violation__count` | STA | 0 ideally; acceptable if setup/hold clean (guide tip 10) | report-only by default |
| `timing__unannotated_net__count`, `timing__unannotated_net_filtered__count` | STAPostPNR | filtered = 0 | nets without parasitics make the report untrustworthy |
| `route__antenna_violation__count`, `antenna__violating__pins`, `antenna__violating__nets` | CheckAntennas | 0 | three checks: post-GRT, in RepairAntennas, post-DRT |
| `route__drc_errors` | DetailedRouting → Checker.TrDRC | 0 | violations should hit 0 well before iteration 64 |
| `route__wirelength__max` | ReportWireLength | < PDK `WIRE_LENGTH_THRESHOLD` | |
| `design__critical_disconnected_pin__count` | ReportDisconnectedPins | 0 | immediate error |
| `power__total`, `power__internal__total`, `power__switching__total`, `power__leakage__total` | STAPostPNR (`report_power`) | W; vectorless | |
| `ir__drop__avg`, `ir__drop__worst`, `ir__voltage__worst` | IRDropReport | worst ≤ ~90 mV (3–5 % of 1.8 V rule of thumb) | no official TT budget |
| `design__xor_difference__count` | KLayout.XOR | 0 | Magic vs KLayout stream-out |
| `magic__drc_error__count`, `klayout__drc_error__count` | Magic.DRC, KLayout.DRC | 0 / 0 | markers in `drc.klayout.xml` / `drc.lyrdb` |
| `magic__illegal_overlap__count` | Magic.SpiceExtraction | 0 | |
| `design__lvs_error__count`, `design__lvs_device_difference__count`, `design__lvs_net_difference__count`, `design__lvs_unmatched_device__count`, `design__lvs_unmatched_net__count`, `design__lvs_unmatched_pin__count`, `design__lvs_property_fail__count` | Netgen.LVS | all 0; log ends "Final result: Circuits match uniquely." | |

Report-file reading guide: `summary.rpt` (one row per corner + Overall: hold ws/tns/vio, setup ws/tns/vio, max cap/slew); `max.rpt`/`min.rpt` = worst paths first, each with header (Startpoint, Endpoint, Path Group, Path Type, Corner), data-arrival block with Fanout/Cap/Slew/Delay/Time per pin, data-required block (`clock uncertainty` −0.25, `library setup time`), then `slack (MET|VIOLATED)`; `checks.rpt` = unconstrained paths, `report_check_types -violators`, `report_parasitic_annotation`, `check_setup` warnings (must be empty); `violator_list.rpt` = `[setup reg-reg] start -> end : slack` (tells you whether in-reg/reg-out I/O-budget paths dominate); `clock.rpt` must show the right period and `Propagated: yes` post-CTS; `unpropagated.rpt` must be empty post-CTS. The classic false pass: zero violations with a huge positive slack because the clock was not found (`check_setup` lists every flop under "no clock").

## Appendix C — Closure decision tree

Operational sign-off: post-RCX `STAPostPNR`, nine corners, `timing__setup__ws ≥ 0` (binds at `max_ss_100C_1v60`), `timing__hold__ws ≥ 0` (binds at `min_ff_n40C_1v95`), zero setup/hold violations at all nine with the 0.25 ns uncertainty and ±5 % derate applied, zero unconstrained endpoints, `timing__unannotated_net_filtered__count = 0`, DRV violations reviewed; plus gate-level simulation on the final `pnl` netlist (and, ideally, an SDF-annotated run at the ss corner: compile the cell models *without* `-DFUNCTIONAL`, add `$sdf_annotate("runs/<tag>/final/sdf/max_ss_100C_1v60/mac_int8__max_ss_100C_1v60.sdf", tb_mac.dut)` with a `1ns/1ps` timescale — recipe unverified for Icarus flags; optional).

Ordered interventions (free → expensive); the orchestrator automates 3–7, the agent does 1–2 by reading reports, and 8–9 are RTL/human:

1. **Constraint sanity (free).** `clock.rpt` shows the intended period; `checks.rpt` has no `check_setup` warnings, no unconstrained endpoints; the 20 % I/O delay placeholder is either acceptable or replaced (`PNR_SDC_FILE`/`SIGNOFF_SDC_FILE` with `set_false_path`/`set_multicycle_path`); a single clock domain.
2. **Read the worst path** in `max.rpt` at `max_ss_100C_1v60` and classify: long logic depth (RTL/synthesis), one huge-fanout or slow-slew net (DRV/resizer), clock-network-delay dominated (CTS), I/O-dominated (constraint). Check which `[setup reg-reg|in-reg|reg-out]` kind dominates `violator_list.rpt`.
3. **Synthesis strategy** (re-run from synthesis): `SYNTH_STRATEGY` `DELAY 1` → `DELAY 4`; `SYNTH_ADDER_TYPE CSA`/`FA`; `SYNTH_MUL_BOOTH true`; `SYNTH_SIZING`/`SYNTH_ABC_BUFFERING`. The 1,440-run sky130 grid search moved a MAC-array path by 2.4 ns with strategy alone, at ~59 % more cells.
4. **Utilization / density:** `FP_CORE_UTIL` 50 → 35–40, `PL_TARGET_DENSITY_PCT` = util + 10; for congestion also `GRT_ADJUSTMENT` +0.1, `GPL_CELL_PADDING`, more layers (`RT_MAX_LAYER`), `ROUTING_OBSTRUCTIONS`; `GRT_ALLOW_CONGESTION` only last (trades overflow for DRC).
5. **Resizer:** raise `PL_RESIZER_SETUP_SLACK_MARGIN`/`GRT_RESIZER_SETUP_SLACK_MARGIN` for post-route headroom; raise `*_MAX_BUFFER_PCT` (and lower `FP_CORE_UTIL` with it); `DESIGN_REPAIR_REMOVE_BUFFERS true`; protect structures with `RSZ_DONT_TOUCH_RX`.
6. **CTS:** restrict `CTS_CLK_BUFFERS` to smaller drives; shrink `CTS_SINK_CLUSTERING_MAX_DIAMETER`/`_SIZE`; lower `CTS_MAX_SLEW`.
7. **Hold:** keep over-fix margins ≥ 0.1/0.05 ns; if hold fixing eats setup, reduce skew (step 6) rather than `*_ALLOW_SETUP_VIOS` (human decision: it converts a frequency problem into a decision about the chip's rated speed).
8. **Relax the clock** if frequency is negotiable (`CLOCK_PERIOD` +10 % steps, cap 20 ns standalone; TT fixed at 20 ns; anything ≥ 15.2 ns is within the 66 MHz pad limit). Note `MAX_TRANSITION_CONSTRAINT` (10 % of period, capped by `DEFAULT_MAX_TRAN`) and I/O delays (20 %) scale with it.
9. **Back to RTL:** pipeline between multiply and accumulate (the grid-search authors' recommendation for 250 MHz), retime, reduce control fanout, CSA/carry-save accumulators, narrower datapath.

Other failure classes: `GPL-0302` → raise `PL_TARGET_DENSITY_PCT` (TT: up to 80) or absolute die; DRT plateau at non-zero violations → structural (pin access, PDN via on a pin, off-grid pin, allowed congestion), not more iterations; antenna → `GRT_ANTENNA_REPAIR_ITERS`/`_MARGIN`, `DRT_ANTENNA_REPAIR_ITERS`, `RUN_HEURISTIC_DIODE_INSERTION`, `DIODE_ON_PORTS`; PDN floating straps on a small die → `PDN_MULTILAYER false`, smaller `PDN_VPITCH`, absolute die; LVS mismatch → check power pins (`VDD_PIN`/`GND_PIN`), strap/pin shorts (`MAGIC_EXT_SHORT_RESISTOR`), `report_floating_nets`, `MAGIC_DEF_LABELS` — and hand it to the human with the log excerpt; XOR ≠ 0 → a Magic-vs-KLayout stream-out disagreement, human.

## Appendix D — One-line glossary of every stage

- **Lint (Verilator):** static check of the RTL for constructs that synthesize badly (latches, multiple drivers, width mismatches).
- **Synthesis (Yosys + ABC):** RTL → optimized generic logic → sky130 flip-flops (`dfflibmap`) and gates (ABC with liberty timing, `SYNTH_STRATEGY`); outputs `.nl.v` and `stat.rpt`.
- **Pre-PnR STA:** timing with ideal clocks and no wires; a surrogate, not sign-off.
- **Floorplan:** die/core outline (relative from `FP_CORE_UTIL` or absolute `DIE_AREA`), rows on the `unithd` site.
- **Tap/endcap insertion:** well taps every 13 µm against latch-up; end-caps close rows.
- **PDN (pdngen):** met1 follow-pin rails + met4 straps (+ met5 when multilayer), via stacks; `check_power_grid`.
- **I/O placement:** pins on the die edge (met2/met3) or from a template DEF.
- **Global placement (RePlAce):** electrostatic analytic placement minimizing wirelength + density penalty until overflow < 0.1.
- **Repair design (resizer):** buffer ports, fix max slew/cap/fanout and long wires with 20 % margins, size gates.
- **Detailed placement (OpenDP):** legalize to row sites with minimum displacement; `check_placement` = 0.
- **CTS (TritonCTS):** clustered buffer tree (`clkbuf_16` root, `clkbuf_*`), then `set_propagated_clock` — hold violations become visible.
- **Post-CTS timing repair:** `repair_timing -setup` then `-hold` (0.05/0.1 ns margins, ≤ 50 % buffers, no setup violations allowed).
- **Global routing (FastRoute):** Steiner trees over GCells with capacity derated by `GRT_ADJUSTMENT`; overflow = congestion.
- **Antenna check/repair:** metal-to-gate area ratios vs the LEF antenna rule; `diode_2` insertion.
- **Detailed routing (TritonRoute):** tracks, vias, search-and-repair with built-in DRC to zero violations.
- **Post-route checks:** disconnected pins, wire-length threshold.
- **Fill:** `fill*`/`decap*` cells in every gap for rail/well continuity and density.
- **RCX (OpenRCX):** per-corner SPEF extraction of wire R and C from the routed design.
- **Signoff STA (OpenSTA):** nine IPVT corners with SPEF; setup at ss, hold at ff; SDF/LIB per corner.
- **IR drop (psm):** static resistive solve of the PDN with per-cell currents.
- **Stream-out + XOR:** Magic and KLayout write GDS from the DEF; XOR must be empty.
- **DRC:** Magic deck and KLayout `sky130A_mr.drc` (feol/beol/offgrid); rule IDs are SkyWater's (`m1.1` width 0.14 µm, `m1.2` spacing 0.14, `li.6` area 0.0561 µm², `m5.1/m5.2` 1.6 µm…).
- **LVS (Magic ext + Netgen):** extracted SPICE vs the powered netlist; "Circuits match uniquely."
- **Precheck (Tiny Tapeout):** boundary, pins vs template DEF, power pins, forbidden met5, valid layers, cell names, both DRC decks, Verilog syntax.
- **Gate-level sim:** same cocotb test on `final/pnl/*.pnl.v` with `primitives.v`/`sky130_fd_sc_hd.v`, `UNIT_DELAY=#1`, `VPWR=1/VGND=0`.

## Appendix E — Time budget and what to skip if behind

| Phase | Budget | Cumulative | If behind (overrun > 50 %), skip in this order |
|---|---|---|---|
| 0 Environment | 60 min | 1:00 | skip `brew install --cask klayout` (use Nix KLayout); skip gdstk if it fails to build |
| 1 Skeleton | 20 min | 1:20 | nothing (all files are given) |
| 2 Design + verification | 60 min | 2:20 | run `make sim TOP=mac WIDTH=8` and `TOP=tt` only (skip W=2/4 sims; the sweep exercises them) |
| 3 Flow config | 20 min | 2:40 | nothing |
| 4 Orchestrator + first closure | 45 min | 3:25 | reduce `--max-attempts 4` to 2; skip per-station renders (`--no-render`), keep the final GDS render |
| 5 Dashboard | 40 min | 4:05 | nothing (template is given) |
| 6 Sweep | 90 min | 5:35 | `--periods 10,20` (6 runs); then `--widths 2,8 --periods 10` (2 runs); record "sweep reduced" in the log |
| 7 Tiny Tapeout | 60 min | 6:35 | skip local precheck (mark "GitHub Action only"); skip `--create-png`; do not wait for the Actions run beyond 20 min — record the URLs |
| 8 Verify + report | 45 min | 7:20 | skip the eqy attempt; if the fresh `harden` would push past 8 h, verify against the existing best run instead and say so in the report |
| Reserve | 40 min | 8:00 | stop at 8:00 regardless: `make report`, commit `phase 8: stopped on time budget` |

Check `make elapsed` at every phase boundary and before any LibreLane run that would start after 7:30 elapsed.

## Reference links

- LibreLane repo: https://github.com/librelane/librelane — docs: https://librelane.readthedocs.io/en/latest/ (macOS Nix install: https://librelane.readthedocs.io/en/latest/installation/nix_installation/installation_macos.html ; Newcomers' tutorial: https://librelane.readthedocs.io/en/latest/getting_started/newcomers/index.html ; configuration reference: https://librelane.readthedocs.io/en/latest/reference/configuration.html ; step variables: https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html ; flows: https://librelane.readthedocs.io/en/latest/reference/flows.html ; custom flows / Python API: https://librelane.readthedocs.io/en/latest/usage/writing_custom_flows.html ; FAQ: https://librelane.readthedocs.io/en/latest/faq.html)
- Ciel (PDK manager): https://pypi.org/project/ciel/ — pinned hashes: https://github.com/librelane/librelane/blob/main/librelane/pdk_hashes.yaml
- OpenLane 2 timing-closure guide (still applicable): https://openlane2.readthedocs.io/en/dev/usage/timing_closure/index.html
- Tiny Tapeout template: https://github.com/TinyTapeout/ttsky-verilog-template — tt-support-tools: https://github.com/TinyTapeout/tt-support-tools — tt-gds-action: https://github.com/TinyTapeout/tt-gds-action — local hardening guide: https://www.tinytapeout.com/guides/local-hardening — testing: https://tinytapeout.com/hdl/testing/ — clock/GPIO specs: https://www.tinytapeout.com/specs/clock/ , https://tinytapeout.com/specs/gpio/ — shuttles: https://tinytapeout.com/chips/ — submit: https://tinytapeout.com/guides/advanced-workshop/submit-your-design/ — app: https://app.tinytapeout.com/projects/create — MicroPython SDK: https://github.com/TinyTapeout/tt-micropython-firmware
- cocotb 2.x: https://docs.cocotb.org/en/stable/ (release notes / 2.0 upgrade guide, runner, simulator support)
- Verilator warnings: https://veripool.org/guide/latest/warnings.html — Yosys: https://github.com/YosysHQ/yosys — OSS CAD Suite (optional sby/eqy): https://github.com/YosysHQ/oss-cad-suite-build — eqy quickstart: https://github.com/YosysHQ/eqy/blob/main/docs/source/quickstart.rst
- OpenROAD module docs: https://openroad.readthedocs.io/en/latest/ (gpl, dpl, rsz, cts, grt, drt, ant, rcx, psm, pdn READMEs) — OpenSTA: https://github.com/parallaxsw/OpenSTA
- SkyWater PDK rules: https://skywater-pdk.readthedocs.io/en/main/rules/periphery.html , antenna: https://skywater-pdk.readthedocs.io/en/main/_sources/rules/antenna.rst.txt — open_pdks sky130 LibreLane config: https://github.com/RTimothyEdwards/open_pdks/blob/master/sky130/librelane/config.tcl
- Claude Code docs: https://code.claude.com/docs/en/permissions , https://code.claude.com/docs/en/hooks , https://code.claude.com/docs/en/goal , https://code.claude.com/docs/en/settings
- Anthropic, "Effective harnesses for long-running agents": https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
- sky130 OpenLane parameter-sweep study (1,440 runs; the MAC-array timing numbers): https://www.preprints.org/frontend/manuscript/bb3f29f28a8f6c2645e902cb192138d6/download_pub

*End of plan.*
