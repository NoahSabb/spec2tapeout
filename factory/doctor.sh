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
