# Phase 0 log — environment bootstrap

Machine: MacBook Pro, Apple M3 (T6030), 12 cores, 18 GB RAM, macOS 26.5.1 (Darwin 25.5.0), 420 GiB free.
Pre-installed by user: Nix (Determinate Nix 3.23.3 / nix 2.35.3) with nix-cache.fossi-foundation.org as substituter + trusted key, Homebrew 7.0.10, gh (authenticated), Docker CLI 29.4.3, caffeinate running.
Python: conda base is 3.13 (ignored); Homebrew python@3.11 3.11.15_1 present at /opt/homebrew/opt/python@3.11/bin/python3.11.

All timestamps are local time (America/Los_Angeles).

2026-10-21 01:14:09 PDT

## 00. Environment survey

- `uname -a; sw_vers; nix --version; docker info; brew --version; gh auth status; nix show-config | grep substituters` — OK.
- NOTE: `docker info` → "Cannot connect to the Docker daemon at unix:///Users/noahsabbavarapu/.docker/run/docker.sock". Docker Desktop does not appear to be running at this moment (CLI 29.4.3 is present). Docker is only needed for the fallback route; will re-check if the fallback is needed.
- Repo: branch main, no commits yet. Only untracked file: "Open source RTL to tapeout pipeline.md".

## 01. LibreLane via Nix — investigation (2026-10-21 01:17:21)

- Latest LibreLane release: 3.0.16 (2026-10-06, GitHub + PyPI). pyproject pins `ciel>=2.3.1,<3`, python>=3.10. PyPI ciel latest is 3.1.0 (so pip must pin ciel<3). cocotb latest 2.1.0.
- `nix flake show github:librelane/librelane/3.0.16` (26 s): exposes devShells.aarch64-darwin.{default,dev,docs,notebook} and packages.aarch64-darwin.{default,librelane,openroad,openroad-abc,opensta,colab-env}. Flake pins nix-eda 6.11.0.
- Docs (installation_macos.html) say: clone repo, `nix-shell`, then `librelane --smoke-test`.
- **FINDING: wrong FOSSi cache key.** The key configured in /etc/nix/nix.custom.conf is
  `nix-cache.fossi-foundation.org:3+K59iFwXZKoO0eVZZkfpNRJDVeUB2v5s8YOqCVSZBc=`
  but the key published in the LibreLane docs (HTML page and docs source in the repo) is
  `nix-cache.fossi-foundation.org:3+K59iFwXqKsL7BNu6Guy0v+uTlwsxYQxjspXzqLYQs=`
  Verified empirically against the cache (client-side, no daemon):
  `nix store verify --store https://nix-cache.fossi-foundation.org --option trusted-public-keys "<USER KEY>" /nix/store/icn6jlv55q9rjxl95ks7anlf82kjw422-openroad-2026-02-17` → "path ... is untrusted"
  same with the DOCS key → passes.
  Consequence: the daemon will reject every FOSSi-built binary (OpenROAD, OpenSTA, Yosys, Magic, KLayout, Netgen, ...) and try to build them from source (many hours on this machine).
- `sudo -n true` → "a password is required"; trusted-users = root only. I cannot edit /etc/nix/nix.custom.conf (outside repo, needs password).
- Docker: `docker info` says daemon not reachable → launching Docker Desktop with `open -a Docker` in case the fallback is needed.
- Attempt 1 (01:20): use config as-is → `nix store verify` says FOSSi paths "untrusted" (see above).
- Attempt 2 (01:17:30–01:18:42): `nix build github:librelane/librelane/3.0.16#packages.aarch64-darwin.opensta --option extra-trusted-public-keys "<DOCS KEY>"` → daemon output: "warning: ignoring the client-specified setting 'trusted-public-keys', because it is a restricted setting and you are not a trusted user" and "warning: ignoring substitute for '/nix/store/sc7lam0v6gsfzzcn993qcnkdzkzvnsk9-opensta' from 'https://nix-cache.fossi-foundation.org', as it's not signed by any of the keys in 'trusted-public-keys'". It then built OpenSTA from source (72 s). Nixpkgs-cached deps came from cache.nixos.org fine. (log: logs/raw/nix_attempt2_opensta.log)
- Attempt 3 (01:19:08): `nix copy --no-check-sigs --from https://nix-cache.fossi-foundation.org /nix/store/sc7lam0v6gsfzzcn993qcnkdzkzvnsk9-opensta` → rc=1 "error: path '/nix/store/0fkkmd5k0bmsfgbfhdx8qdv5ix07c86y-tcl-8.6.16' is not valid" (untrusted users cannot bypass signature checks via the daemon). (log: logs/raw/nix_attempt3_copy.log)
- **Nix route result: BLOCKED by one line of system config that needs the user's password.** Building the full toolchain (OpenROAD, KLayout, Yosys, Magic, Netgen, OR-Tools…) from source would take many hours. Falling back to pip + `--dockerized` per instructions.
- Fix for the user (one command, then the Nix route should work as documented):
  `sudo sed -i '' 's|3+K59iFwXZKoO0eVZZkfpNRJDVeUB2v5s8YOqCVSZBc=|3+K59iFwXqKsL7BNu6Guy0v+uTlwsxYQxjspXzqLYQs=|' /etc/nix/nix.custom.conf && sudo pkill nix-daemon`

## 02. Homebrew tools (01:20)

- `brew install icarus-verilog verilator yosys surfer` → rc=0. icarus-verilog 13.0 (already present), verilator upgraded 5.048→5.052, yosys 0.70, surfer 0.7.0. (logs/raw/brew_formulae.log)
- `brew install --cask klayout` → rc=1: "Error: klayout: Cask 'klayout' has been disabled because it does not pass the macOS Gatekeeper check! It was disabled on 2026-10-12." (logs/raw/brew_klayout.log). Looking for an alternative.

## 03. Python venv (01:20)

- `/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv`; pip install cocotb>=2,<3 gdstk matplotlib pyyaml ciel>=2.3.1,<3 → rc=0 in ~15 s. Versions: cocotb 2.1.0, gdstk 1.0.2, matplotlib 3.11.2, PyYAML 6.0.3, ciel 2.6.1. (logs/raw/venv.log)

## 04. LibreLane via pip (fallback route) (01:23)

- 01:20:09–01:20:15: `.venv/bin/python -m pip install librelane==3.0.16` → rc=0 (6 s). Pulled in klayout 0.30.12 (Python module), lln-libparse 0.56.0, click 8.2.1, etc. `librelane --version` → "LibreLane v3.0.16". (logs/raw/pip_librelane.log)
- Default container image = `ghcr.io/librelane/librelane:3.0.16` (librelane/__main__.py, overridable via LIBRELANE_IMAGE_OVERRIDE). Docker Desktop came up after `open -a Docker`: server 29.4.3, 12 CPUs, 7.75 GiB RAM for the VM.
- 01:21: `docker pull ghcr.io/librelane/librelane:3.0.16` started in background (logs/raw/docker_pull.log).

## 05. sky130A PDK via ciel (01:23)

- LibreLane 3.0.16 pins (librelane/pdk_hashes.yaml): sky130 = `8afc8346a57fe1ab7934ba5a6056ea8b43078e71` (also gf180mcu 54435919…, ihp-sg13g2 c4b8b4e5…).
- `ciel ls-remote --pdk-family sky130` → 124 versions; the pinned hash is entry 61.
- 01:21:19–01:22:00 (41 s): `ciel enable --pdk-family sky130 --pdk-root $PWD/pdk 8afc8346a57fe1ab7934ba5a6056ea8b43078e71` → rc=0. 2.1 GiB in pdk/ciel/sky130/versions/<hash>/; pdk/sky130A and pdk/sky130B symlinks. `ciel ls` confirms the version. (logs/raw/ciel_enable.log)
- PDK_ROOT=<repo>/pdk, PDK=sky130A persisted in env.sh (also puts .venv/bin on PATH, sets LIBRELANE_IMAGE_OVERRIDE). Tested with `source ./env.sh` under bash and zsh.

## 06. KLayout (01:23)

- brew cask disabled (Gatekeeper, see 02). Alternatives evaluated:
  - pip `klayout` 0.30.12 Python module: present in .venv as a librelane dependency (`import klayout.db` works). No `klayout` executable.
  - nixpkgs `klayout` 0.30.12 supports aarch64-darwin and `nix build --dry-run nixpkgs#klayout` reports all 149 paths fetchable from cache.nixos.org (466 MiB) — no FOSSi key needed. Chosen route: `nix profile add nixpkgs#klayout` (started 01:23 in background, logs/raw/nix_klayout.log).
  - Official DMG from klayout.de: not used (same unsigned app the cask was disabled for, and would install outside the repo).

## 07. LibreLane smoke test (01:25)

- `docker pull ghcr.io/librelane/librelane:3.0.16` 01:21:19–01:23:13 (≈2 min; 1.47 GB content, 7.5 GB on disk, image id 02d50f259d48). (logs/raw/docker_pull.log)
- Attempt 1 (01:23:39, 1 s): `librelane --dockerized --docker-no-tty --pdk-root $PDK_ROOT --smoke-test` → rc=1, "cannot attach stdin to a TTY-enabled container because stdin is not a terminal". Cause: `--docker-no-tty` must come BEFORE `--dockerized` (per `librelane --help`); after it, it is passed into the container and ignored. (logs/raw/smoke_test_1.log)
- Attempt 2 (01:23:56–01:24:41): `librelane --docker-no-tty --dockerized --pdk-root $PDK_ROOT --smoke-test` → rc=0, **"Smoke test passed."** Wall time **45.1 s** (full Classic flow on the bundled SPM design inside the container, PDK bind-mounted from <repo>/pdk). Only ordinary warnings (CustomIOPlacement, STA-1140 duplicate lib, RSZ-0020 floating nets, DRT-0349 LEF58_ENCLOSURE, VSRC_LOC_FILES). (logs/raw/smoke_test_2.log)
- In an interactive terminal the `--docker-no-tty` flag is unnecessary: `librelane --dockerized --smoke-test` suffices (PDK_ROOT is read from the environment after `source ./env.sh`).

## 08. KLayout via nixpkgs (01:25)

- 01:22:59–01:23:25 (26 s): `nix profile add nixpkgs#klayout` → rc=0, klayout-0.30.12 (/nix/store/rslb2hkgqa3fxvq4f0l5b65m79nnfg4d-klayout-0.30.12), all from cache.nixos.org. (logs/raw/nix_klayout.log)
- Gotcha: Determinate Nix created the user profile at ~/.local/state/nix/profiles/profile (XDG), not ~/.nix-profile, and the login shell PATH only contains ~/.nix-profile/bin (which does not exist). So `klayout` is not on PATH in a fresh shell. Handled by adding ~/.local/state/nix/profiles/profile/bin to PATH in env.sh and in the Makefile. (Creating ~/.nix-profile would be a change outside the repo — left for the user; see report.)
- nixpkgs klayout on darwin ships only `Applications/klayout.app` (no bin/). Binary: `~/.local/state/nix/profiles/profile/Applications/klayout.app/Contents/MacOS/klayout` → `-v` prints "KLayout 0.30.12"; batch mode (`-b -r script.py`, pya.Layout) works. Added wrapper `tools/bin/klayout` (committed) and put tools/bin on PATH in env.sh and the Makefile.
- Also: the Nix shell hook (nix-daemon.sh) looks for `~/.local/state/nix/profile` (singular) or `~/.nix-profile`; neither exists, so the profile is not on PATH in login shells. Harmless for this project because the wrapper uses the absolute path.

## 09. Functional checks of simulators + cocotb (01:27)

Scratch test: 4-bit counter in Verilog + cocotb 2.1 test via `cocotb_tools.runner` (icarus and verilator).
- Run 1 (01:26:12, without `source ./env.sh`, conda base on PATH):
  - icarus: test FAILED — my test bug: no `timescale` → "Bad period: Unable to accurately represent 10(ns) with the simulator precision of 1e0". Fixed by adding ``timescale 1ns/1ps`.
  - verilator: BUILD FAILED — "Error in sitecustomize ... AssertionError: SRE module mismatch" from `python3 .../verilator_includer`. Cause: `python3` resolved to conda's /opt/miniconda3/bin/python3 (3.13) while cocotb's runner exports PYTHONHOME for the venv's Python 3.11 → mixed stdlib. **Conda "(base)" on PATH breaks Verilator+cocotb builds unless the venv is first on PATH.**
- Run 2 (01:26:58–01:27:02, after `source ./env.sh`, which puts .venv/bin first): icarus PASS=1 (<1 s), verilator PASS=1 (4 s incl. C++ build). Both OK.

## 10. Makefile `doctor` (01:27–01:28)

- First Makefile used `.ONESHELL`; Apple's /usr/bin/make is GNU Make 3.81 (no .ONESHELL support) → "syntax error: unexpected end of file". Fixed by moving the logic to tools/doctor.sh and keeping the Makefile trivial.
- 01:28:13 `make doctor` → rc=0, all 17 checks OK (python 3.11.15, LibreLane v3.0.16, Ciel v2.6.1, sky130A @ open_pdks 8afc8346, Docker Engine 29.4.3, image ghcr.io/librelane/librelane:3.0.16, Icarus 13.0, Verilator 5.052, Yosys 0.70+post, surfer 0.7.0, KLayout 0.30.12, cocotb 2.1.0, gdstk 1.0.2, matplotlib 3.11.2, PyYAML 6.0.3, klayout-py 0.30.12, Nix 2.35.3). (logs/raw/make_doctor_2.log)
- Failure path verified: `LIBRELANE_IMAGE=ghcr.io/librelane/librelane:0.0.0 make doctor` → "MISS image", exit 2. Also passes from a minimal environment (`env -i HOME=$HOME PATH=/usr/bin:/bin /usr/bin/make doctor`), i.e. without `source ./env.sh`.
- Yosys functional check: synth of the scratch counter with `dfflibmap`/`abc -liberty` against sky130_fd_sc_hd__tt_025C_1v80.lib → 12 cells, 128.87 µm². gdstk/yaml/matplotlib (Agg) import and basic use OK.

## 11. `make smoke` target + Docker Desktop crash (01:28–)

- 01:28:38 `make smoke` (= `librelane --docker-no-tty --dockerized --pdk-root $PDK_ROOT --smoke-test`) ran the flow up to step 46 OpenROAD.CheckAntennas (≈90 s in), then at 01:30:10 docker printed `error waiting for container: unexpected EOF`, rc=125. (logs/raw/make_smoke.log)
- Docker Desktop VM went down: backend log "dockerd has exited successfully, waiting for VM services to stop" at 08:30:10Z, then "Docker Desktop is unable to start" on every API call. VM console log just before: a hung-task dump (oom_reaper listed only as a sleeping task — not an OOM kill) and control-plane error `{"name":"fs","err":"injecting event blocked for 60s"}` at 08:30:09Z, i.e. the host file-sharing service stalled. Note `make doctor` (several `docker image inspect` calls) was running concurrently with this smoke run; the earlier standalone smoke run (01:23:56) passed cleanly.
- Docker memory settings are defaults (VM reported 7.75 GiB, 12 CPUs).
- 01:31:17 retry `make smoke` → immediate failure "Docker Desktop is unable to start" + librelane TypeError ('NoneType' object is not iterable — it could not parse `docker info`), rc=2. (logs/raw/make_smoke_2.log)
- No com.docker.virtualization process present at 01:32; waiting up to 4 min for Docker Desktop to self-recover before restarting the app.
- 01:32: `docker desktop status` → "Status stopped" (the backend/app process is alive, VM gone). `docker desktop start` → "Docker Desktop is already running" but engine never came back within 3 min (01:32:23–01:35:23). Next: `docker desktop restart`.
- 01:35:36 `docker desktop restart` → engine back at 01:35:57 (VM: `--cpus 12 --memoryMiB 8192`, virtiofs shares for /Users /Volumes /private /tmp /var/folders, Rosetta on).
- 01:36:01 `make smoke` (3rd run of the target, nothing else running) → identical crash: flow reached step 46 OpenROAD.CheckAntennas-1 at 08:36:30Z, then at 08:37:30Z `error waiting for container: unexpected EOF`, rc=125 (logs/raw/make_smoke_3.log). Docker backend log: `engine linux/virtualization-framework run error: service fs failed: injecting event blocked for 60s` → dockerd exits → "Docker Desktop is unable to start" (error dialog offers Quit / Reset to factory defaults). The 60 s block starts exactly when CheckAntennas-1 starts in both crashing runs (08:29:06Z, 08:36:30Z). The passing run (01:23:56) went through the same step in 1 s.
- Per-step timing before the crash is identical to the passing run (synthesis→detailed routing in ~27 s), so this is not a slow VM; the guest stops servicing the virtiofs event channel at that step.
- Mounts used by `--dockerized` (librelane/container.py): $HOME, the ciel PDK root, cwd (if outside $HOME), `--docker-mount` extras; /tmp is container-local. Run dir is in the container's /tmp, so flow I/O itself is not on virtiofs; only PDK reads are.
- Next (last changed-hypothesis retry): restart Docker again and run the smoke test exactly as the passing run did (shell + `source ./env.sh`, not via make) while sampling `docker stats` to test the "guest out of memory" hypothesis.
- 01:39:13 `docker desktop restart` → engine up 01:39:31.
- 01:39:40–01:40:25 smoke test invoked from the shell after `source ./env.sh` (same command as the make target) → **passed, 45 s** (logs/raw/smoke_test_4.log). `docker stats` sampled every 3 s: container peak 693 MiB of 7.75 GiB, CPU peak 677 % (detailed routing) → VM memory is NOT the problem.
- Crashing runs never reached "Logging subprocess to …" inside CheckAntennas-1, i.e. they stalled in step setup (state/PDK file access over virtiofs) before OpenROAD was even launched. Docker's host-side `fs` service then reported `injecting event blocked for 60s` and the engine shut down.
- Score so far: 3 runs launched from a shell with `source ./env.sh` → 3 passes (45 s each); 2 runs launched through the original `make smoke` recipe (bare make environment) → 2 Docker VM crashes at the same step. Root cause inside Docker Desktop 4.73.0 / virtiofs not identified.
- 01:41:45–01:42:30: `make smoke` rewritten to call tools/smoke.sh (which sources env.sh and runs the identical command) → **passed, 45 s** (logs/raw/make_smoke_4.log). Docker stayed "running". Keeping this form; the bare-recipe form is retired.

## 12. Nix route, final evidence (01:45)

- `nix build --dry-run github:librelane/librelane/3.0.16#devShells.aarch64-darwin.default`: 316 paths to fetch (415 MiB), 7 trivial devshell derivations to build. Checking each narinfo: 290 paths are on cache.nixos.org (fine), **26 exist only on the FOSSi cache** and would be rejected by the daemon with the current key: openroad-2026-02-17 (+python env), or-tools-9.14, klayout-0.30.7 (+python), yosys-0.62 + eqy/sby/slang/ghdl plugins, magic-vlsi-8.3.623, netgen-1.5.316, verilator-5.044, iverilog-s20250103, ghdl-bin-5.1.1, bitwuzla, tk-8.6.16, python3.13-librelane-3.0.16, ciel-2.4.0, libparse, cloup, yamlcore, pybind11. Building those from source = several hours and a real chance of macOS build failures, so not attempted.

## 13. Final state (01:45)

- `make doctor` → rc=0 (logs/raw/make_doctor_final.log). `make smoke` → pass, 45 s.
- Docker Desktop: running. Nix store: opensta built from source during attempt 2 (harmless, 25 MiB). Nix profile: klayout 0.30.12.
- Elapsed: 01:13 → 01:45 (≈32 min).
