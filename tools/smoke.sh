#!/usr/bin/env bash
# Run the LibreLane smoke test inside the ghcr.io/librelane/librelane container,
# with exactly the environment that passed in Phase 0 (`source ./env.sh`).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# shellcheck source=../env.sh
source "$ROOT/env.sh"
cd "$ROOT"
start=$(date +%s)
if [ -t 0 ]; then
  librelane --dockerized --pdk-root "$PDK_ROOT" --smoke-test
else
  librelane --docker-no-tty --dockerized --pdk-root "$PDK_ROOT" --smoke-test
fi
echo "smoke test wall time: $(( $(date +%s) - start )) s"
