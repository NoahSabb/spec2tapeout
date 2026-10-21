# spec2tapeout environment. Source this from the repo root (bash or zsh):
#   source ./env.sh
# It sets PDK_ROOT/PDK for LibreLane + ciel and puts the project venv on PATH.

if [ -n "${BASH_SOURCE:-}" ]; then
  _s2t_src="${BASH_SOURCE[0]}"
elif [ -n "${ZSH_VERSION:-}" ]; then
  eval '_s2t_src="${(%):-%x}"'
else
  _s2t_src="$0"
fi
export S2T_ROOT="$(cd "$(dirname "$_s2t_src")" && pwd)"
unset _s2t_src

# PDK (installed by `ciel enable --pdk-root "$PDK_ROOT" ...`; see logs/PHASE0_REPORT.md)
export PDK_ROOT="$S2T_ROOT/pdk"
export PDK="sky130A"
export STD_CELL_LIBRARY="sky130_fd_sc_hd"

# LibreLane: pip route, executed inside the ghcr.io/librelane/librelane:3.0.16 container.
# Phase 0 found the native Nix route blocked (wrong FOSSi cache key in /etc/nix/nix.custom.conf).
export LIBRELANE_VERSION="3.0.16"
export LIBRELANE_IMAGE_OVERRIDE="ghcr.io/librelane/librelane:${LIBRELANE_VERSION}"

# Project Python venv (Python 3.11: librelane, ciel, cocotb 2.x, gdstk, matplotlib, pyyaml, klayout module)
export VIRTUAL_ENV="$S2T_ROOT/.venv"
# tools/bin holds thin wrappers (klayout). The venv comes first so `python3` is the project
# interpreter even when conda "(base)" is active in the calling shell.
for _d in "$S2T_ROOT/tools/bin" "$VIRTUAL_ENV/bin"; do
  case ":$PATH:" in *":$_d:"*) ;; *) export PATH="$_d:$PATH" ;; esac
done
# Nix user profile (klayout CLI; Determinate Nix uses the XDG path ~/.local/state/nix/profiles/profile) and Homebrew
for _d in "$HOME/.local/state/nix/profiles/profile/bin" "$HOME/.nix-profile/bin" /nix/var/nix/profiles/default/bin /opt/homebrew/bin; do
  case ":$PATH:" in *":$_d:"*) ;; *) [ -d "$_d" ] && export PATH="$PATH:$_d" ;; esac
done
unset _d
