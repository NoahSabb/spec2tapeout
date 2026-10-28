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

