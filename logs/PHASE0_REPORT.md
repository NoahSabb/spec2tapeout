# Phase 0 report — environment bootstrap (2026-10-21, 01:13–01:46)

Machine: MacBook Pro, Apple M3, 12 cores, 18 GB RAM, macOS 26.5.1. Full command-by-command log with timestamps: `logs/phase0.md`; raw tool output: `logs/raw/`.

## TL;DR

| Goal | Status | Notes |
|---|---|---|
| 1. LibreLane 3.0.16 | **Works via fallback** (pip + `--dockerized`) | Nix route blocked by a wrong cache key in `/etc/nix/nix.custom.conf` (needs your sudo, 1 line) |
| 2. sky130A PDK via ciel | **Done** | open_pdks `8afc8346a57fe1ab7934ba5a6056ea8b43078e71` (LibreLane's pin), 2.1 GiB in `pdk/`, `PDK_ROOT` in `env.sh` |
| 3. `librelane --smoke-test` | **Passes, 45 s** | 4 of 6 runs passed; the 2 failures crashed the Docker Desktop VM (details below) |
| 4. iverilog / verilator / yosys / surfer / klayout / cocotb / gdstk / matplotlib / pyyaml | **All installed and verified** | KLayout via nixpkgs instead of the brew cask (cask disabled upstream) |
| 5. `make doctor` | **Passes** (17 checks, nonzero exit verified) | |
| 6. `.gitignore` + commit | **Done** | commit "Phase 0: environment bootstrap" |
| 7. This report | **Done** | |

Total wall time ≈ 33 min. Nothing outside this repo was modified except through brew / pip / nix / ciel installs and (re)starting Docker Desktop.

## How to enter the environment

```sh
cd ~/Documents/GitHub/spec2tapeout
source ./env.sh              # PDK_ROOT, PDK=sky130A, .venv + tools/bin on PATH
make doctor                  # every tool + version; exit 1 if anything is missing
make smoke                   # librelane --dockerized --smoke-test (45 s)
librelane --dockerized --smoke-test          # same thing by hand (interactive terminal)
librelane --dockerized                        # drops you into a shell inside ghcr.io/librelane/librelane:3.0.16
librelane --dockerized path/to/config.json    # run a flow
```

Route that works: **pip** (`librelane==3.0.16` in `.venv`, Python 3.11.15) executing inside the container `ghcr.io/librelane/librelane:3.0.16` (image id `02d50f259d48`, 1.47 GB). Your `$HOME` and `pdk/` are bind-mounted into the container, so configs, RTL and `runs/` live in this repo as usual. `env.sh` also sets `LIBRELANE_IMAGE_OVERRIDE` so the host CLI and container stay pinned to 3.0.16.

Always `source ./env.sh` (or go through `make`) before running `librelane --dockerized` or cocotb; see "Docker Desktop crash" and "conda" below for why.

## Install times

| Step | Time |
|---|---|
| Homebrew: icarus-verilog (already present), verilator 5.048→5.052, yosys 0.70, surfer 0.7.0 | ~1 min |
| Python venv + cocotb/gdstk/matplotlib/pyyaml/ciel | 15 s |
| `pip install librelane==3.0.16` | 6 s |
| `ciel enable` sky130 (2.1 GiB) | 41 s |
| `docker pull ghcr.io/librelane/librelane:3.0.16` | ~2 min |
| `nix profile add nixpkgs#klayout` (466 MiB from cache.nixos.org) | 26 s |
| `librelane --dockerized --smoke-test` | 45 s per passing run |
| Diagnosing Nix cache key + Docker crashes | ~20 min of the 33 |

## Installed versions (from `make doctor`)

Python 3.11.15 (venv) · LibreLane 3.0.16 · Ciel 2.6.1 · sky130A @ open_pdks 8afc8346 · Docker Engine 29.4.3 (Docker Desktop 4.73.0) · Icarus Verilog 13.0 · Verilator 5.052 · Yosys 0.70+post · surfer 0.7.0 · KLayout 0.30.12 (CLI via nix + `tools/bin/klayout` wrapper; Python module 0.30.12 in venv) · cocotb 2.1.0 · gdstk 1.0.2 · matplotlib 3.11.2 · PyYAML 6.0.3 · Nix 2.35.3 (Determinate 3.23.3).

Note the host-side Yosys/Verilator/iverilog (Homebrew, newest) differ from the ones inside the LibreLane container (Yosys 0.62, Verilator 5.044, iverilog s20250103). The flow uses the container's; use the Homebrew ones for simulation/lint outside the flow.

Functional checks beyond `--version`: cocotb 2.1 test on a 4-bit counter passes on both Icarus and Verilator; Yosys synthesises it to 12 sky130_fd_sc_hd cells against the PDK liberty; KLayout batch mode builds a layout via `pya`; gdstk/yaml/matplotlib import and run.

## Every failure, with its exact error

### F1. Nix route blocked: wrong FOSSi cache public key (NEEDS YOU)

`/etc/nix/nix.custom.conf` (written by the Determinate installer from the options you gave it) contains

```
extra-trusted-public-keys = nix-cache.fossi-foundation.org:3+K59iFwXZKoO0eVZZkfpNRJDVeUB2v5s8YOqCVSZBc=
```

but the real key (LibreLane docs, HTML and source, verified empirically against the cache) is

```
nix-cache.fossi-foundation.org:3+K59iFwXqKsL7BNu6Guy0v+uTlwsxYQxjspXzqLYQs=
```

Evidence: `nix store verify --store https://nix-cache.fossi-foundation.org --option trusted-public-keys "<your key>" /nix/store/icn6jlv55q9rjxl95ks7anlf82kjw422-openroad-2026-02-17` → `path ... is untrusted`; with the docs key → OK. A real build (`nix build ...#opensta`) printed:

```
warning: ignoring the client-specified setting 'trusted-public-keys', because it is a restricted setting and you are not a trusted user
warning: ignoring substitute for '/nix/store/sc7lam0v6gsfzzcn993qcnkdzkzvnsk9-opensta' from 'https://nix-cache.fossi-foundation.org', as it's not signed by any of the keys in 'trusted-public-keys'
```

and then compiled OpenSTA from source. 26 of the 316 store paths in the LibreLane devshell exist only on the FOSSi cache (OpenROAD, OR-Tools, KLayout, Yosys + plugins, Magic, Netgen, Verilator, GHDL, Bitwuzla, the LibreLane Python env). Building them from source would take hours, so after 3 attempts (config as-is; `--option extra-trusted-public-keys`; `nix copy --no-check-sigs`) I switched to the fallback. `sudo -n` needs a password and `trusted-users = root`, so I could not fix it myself.

**Fix (10 seconds):**

```sh
sudo sed -i '' 's|3+K59iFwXZKoO0eVZZkfpNRJDVeUB2v5s8YOqCVSZBc=|3+K59iFwXqKsL7BNu6Guy0v+uTlwsxYQxjspXzqLYQs=|' /etc/nix/nix.custom.conf
sudo pkill nix-daemon        # Determinate restarts it automatically
nix develop github:librelane/librelane/3.0.16      # ~415 MiB download, then `librelane --smoke-test`
```

(or the documented form: `git clone https://github.com/librelane/librelane && cd librelane && git checkout 3.0.16 && nix-shell`). After that, the native route gives you host-side OpenROAD/Magic/Netgen/KLayout 0.30.7 without Docker; the pip+Docker route keeps working either way.

### F2. `brew install --cask klayout` refused

```
Error: klayout: Cask 'klayout' has been disabled because it does not pass the macOS Gatekeeper check! It was disabled on 2026-10-12.
```

Workaround used: `nix profile add nixpkgs#klayout` (0.30.12, aarch64-darwin, fully cached on cache.nixos.org, no FOSSi key needed). It installs only `Applications/klayout.app`, so `tools/bin/klayout` wraps `.../klayout.app/Contents/MacOS/klayout`. Also, Determinate Nix put the user profile at `~/.local/state/nix/profiles/profile`, which the login-shell hook does not add to PATH; `env.sh` and the wrapper use absolute paths so it does not matter here. The venv also has the `klayout` 0.30.12 Python module (pulled in by librelane).

### F3. Smoke test attempt 1: flag order

```
cannot attach stdin to a TTY-enabled container because stdin is not a terminal
```

`--docker-no-tty` must come *before* `--dockerized` (anything after `--dockerized` is forwarded into the container). Only matters in non-interactive runs (CI, scripts); `tools/smoke.sh` handles both cases.

### F4. Docker Desktop VM crashed twice during `make smoke` (WATCH THIS)

Two runs launched from the original bare `make smoke` recipe reached flow step 46 (`OpenROAD.CheckAntennas-1`) and then:

```
time="2026-10-21T01:37:30-07:00" level=error msg="error waiting for container: unexpected EOF"
```

Docker Desktop backend log: `engine linux/virtualization-framework run error: service fs failed: injecting event blocked for 60s` → dockerd exits → every `docker` command says `Docker Desktop is unable to start` and the GUI shows an error dialog (Quit / Reset to factory defaults). It did not self-recover; `docker desktop restart` brought it back in ~20 s each time (I did this twice).

What I ruled out: VM memory (container peak 693 MiB of 7.75 GiB), slow VM (step timings identical to passing runs), flow differences (same step list). The stall is in step setup before OpenROAD launches, i.e. in file access over virtiofs. Four runs launched with `source ./env.sh` (shell or via the new `tools/smoke.sh`) all passed in 45 s; the two bare-make runs both crashed. I do not have a root cause inside Docker Desktop 4.73.0 / macOS 26.5.1 virtiofs. Mitigations in place: `make smoke` now goes through `tools/smoke.sh` (sources `env.sh`). If it recurs: `docker desktop restart`, and consider Docker Desktop → Settings → Resources → File sharing implementation: switch virtiofs → gRPC FUSE (a settings change I did not make for you), or the native Nix route (F1), which needs no Docker at all.

Also: Docker Desktop was **not** running when I started (`docker info` → cannot connect to the daemon); I launched it with `open -a Docker`.

### F5. cocotb + Verilator breaks when conda's Python shadows the venv

With conda "(base)" first on PATH and without `env.sh`, Verilator's build step runs `python3 .../verilator_includer` with conda's 3.13 while cocotb has set `PYTHONHOME` for the venv's 3.11:

```
Error in sitecustomize; set PYTHONVERBOSE for traceback:
AssertionError: SRE module mismatch
make: *** [Vtop__ALL.cpp] Error 1
```

`env.sh` puts `.venv/bin` first on PATH, which fixes it (Icarus and Verilator both pass). Consider `conda config --set auto_activate_base false` for this project's shells (your call; not changed).

### F6. Apple's `make` is GNU Make 3.81

`.ONESHELL` is unsupported → `syntax error: unexpected end of file`. The Makefile is now a thin shim over `tools/doctor.sh` / `tools/smoke.sh`.

## Things that need you

1. **Fix the Nix cache key** (F1, one `sudo sed`). Until then, only the pip+Docker route works.
2. **Docker Desktop reliability** (F4): it must be running before any `--dockerized` call, and it crashed twice tonight under the flow. Keep an eye on it; the native Nix route removes the dependency.
3. Optional: `conda config --set auto_activate_base false` (F5), and add `~/.local/state/nix/profiles/profile/bin` or a `~/.nix-profile` symlink if you want nix-profile tools in plain shells (nothing in this repo needs it).
4. I did **not** commit `Open source RTL to tapeout pipeline.md` (your reference doc); it is still untracked. Add it if you want it in the repo.
5. Side effects outside the repo: Homebrew upgraded verilator to 5.052 and installed yosys 0.70, surfer 0.7.0 (+ deps); Nix profile has klayout 0.30.12; the Nix store gained an OpenSTA built from source (harmless); Docker has the 7.5 GB LibreLane image; Docker Desktop was started and restarted twice.

## Repo contents after Phase 0

```
env.sh            source me: PDK_ROOT/PDK, venv + tools/bin on PATH, LibreLane image pin
Makefile          doctor, smoke
tools/doctor.sh   17 version checks, exit 1 on any miss
tools/smoke.sh    librelane --dockerized --smoke-test with the known-good environment
tools/bin/klayout wrapper around the nix-installed klayout.app
.gitignore        runs/ .venv/ pdk/ *.vcd *.fst sim_build/ ...
logs/phase0.md    timestamped command log
logs/raw/*.log    raw output of every install / test
.venv/ (ignored)  Python 3.11: librelane 3.0.16, ciel 2.6.1, cocotb 2.1.0, gdstk, matplotlib, pyyaml, klayout
pdk/   (ignored)  sky130A/sky130B @ open_pdks 8afc8346 (2.1 GiB)
```
