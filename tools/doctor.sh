#!/usr/bin/env bash
# spec2tapeout toolchain check. Prints every tool's version; exits 1 if any is missing.
# Invoked by `make doctor`; can also be run directly after `source ./env.sh`.
set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="$ROOT/.venv"
PY="$VENV/bin/python"
: "${PDK_ROOT:=$ROOT/pdk}"
: "${PDK:=sky130A}"
: "${LIBRELANE_IMAGE:=ghcr.io/librelane/librelane:3.0.16}"
export PATH="$VENV/bin:$ROOT/tools/bin:$PATH:$HOME/.local/state/nix/profiles/profile/bin:$HOME/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/opt/homebrew/bin:/usr/local/bin"
export PDK_ROOT PDK

fail=0
check() { # name, install hint, command...
  local name="$1" hint="$2" out; shift 2
  if out="$("$@" 2>/dev/null | head -n 1)" && [ -n "$out" ]; then
    printf '  \033[32mOK\033[0m   %-14s %s\n' "$name" "$out"
  else
    printf '  \033[31mMISS\033[0m %-14s (install: %s)\n' "$name" "$hint"; fail=1
  fi
}
ver_py() { "$PY" -c "import $1 as m; print('$1', m.__version__)"; }
pdk_version() {
  [ -d "$PDK_ROOT/$PDK/libs.ref/sky130_fd_sc_hd" ] || return 1
  local target; target="$(readlink "$PDK_ROOT/$PDK" || echo "$PDK_ROOT/$PDK")"
  echo "$PDK @ $PDK_ROOT ($(echo "$target" | sed -E 's|.*versions/([0-9a-f]{8})[0-9a-f]*/.*|open_pdks \1|'))"
}

echo "spec2tapeout doctor — $(date '+%F %T')"
echo "  PDK_ROOT=$PDK_ROOT  PDK=$PDK"
check python      "/opt/homebrew/opt/python@3.11/bin/python3.11 -m venv .venv"   "$PY" --version
check librelane   "pip install librelane==3.0.16"                  bash -c 'librelane --version | head -n1'
check ciel        "pip install 'ciel>=2.3.1,<3'"                   bash -c 'ciel --version | head -n1'
check pdk         "ciel enable --pdk-family sky130 --pdk-root \$PDK_ROOT 8afc8346a57fe1ab7934ba5a6056ea8b43078e71" pdk_version
check docker      "start Docker Desktop"                            bash -c 'docker version --format "Docker Engine {{.Server.Version}}"'
check image       "docker pull $LIBRELANE_IMAGE"                   bash -c "docker image inspect $LIBRELANE_IMAGE --format '$LIBRELANE_IMAGE {{.Id}}' | cut -c1-72"
check iverilog    "brew install icarus-verilog"                    bash -c 'iverilog -V | head -n1'
check verilator   "brew install verilator"                         verilator --version
check yosys       "brew install yosys"                             yosys -V
check surfer      "brew install surfer"                            surfer --version
check klayout     "nix profile add nixpkgs#klayout (wrapper tools/bin/klayout)" bash -c 'klayout -v | head -n1'
check cocotb      "pip install 'cocotb>=2,<3'"                     ver_py cocotb
check gdstk       "pip install gdstk"                              ver_py gdstk
check matplotlib  "pip install matplotlib"                         ver_py matplotlib
check pyyaml      "pip install pyyaml"                             ver_py yaml
check klayout-py  "pip install klayout"                            ver_py klayout
check nix         "Determinate Nix installer"                      nix --version

if [ "$fail" -ne 0 ]; then echo "doctor: FAILED — missing tools listed above"; exit 1; fi
echo "doctor: all tools present"
