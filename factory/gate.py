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
