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
