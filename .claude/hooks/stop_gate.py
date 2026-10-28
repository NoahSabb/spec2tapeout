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
