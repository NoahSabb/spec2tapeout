#!/usr/bin/env python3
"""PreToolUse guard for the spec2tapeout overnight run.
Blocks (exit 2): edits/writes to protected prefixes, Bash commands that write to
protected prefixes, skip-permission flags, rm -r outside runs/, destructive git."""
import json, os, re, sys

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0  # malformed input: do not block
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    root = os.path.realpath(root)
    prot_file = os.path.join(root, ".claude", "protected.txt")
    protected = []
    if os.path.exists(prot_file):
        with open(prot_file) as f:
            protected = [l.strip() for l in f if l.strip() and not l.startswith("#")]
    tool = data.get("tool_name", "")
    ti = data.get("tool_input", {}) or {}

    def rel(p):
        p = os.path.realpath(os.path.join(root, os.path.expanduser(p)))
        return os.path.relpath(p, root)

    def is_protected(relpath):
        for pre in protected:
            pre_n = pre.rstrip("/")
            if relpath == pre_n or relpath.startswith(pre_n + "/") or (pre.endswith("/") is False and relpath == pre):
                return pre
        return None

    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        if path:
            hit = is_protected(rel(path))
            if hit:
                sys.stderr.write(f"BLOCKED by .claude/hooks/guard.py: '{path}' is under protected prefix '{hit}'. "
                                 "Rule 1: never edit golden vectors, reference models or .claude/. "
                                 "Fix the RTL or testbench driver instead, or record the issue in NEEDS_HUMAN.md.\n")
                return 2
        return 0

    if tool == "Bash":
        cmd = ti.get("command", "") or ""
        if re.search(r"--dangerously-skip-permissions|bypassPermissions|--permission-mode\s+bypass", cmd):
            sys.stderr.write("BLOCKED: skip-permission flags are forbidden (rule 7).\n"); return 2
        # rm -r / rm -rf anywhere except under runs/
        for m in re.finditer(r"\brm\s+(-[a-zA-Z]*r[a-zA-Z]*|-[a-zA-Z]*R[a-zA-Z]*)\s+([^\s;&|]+)", cmd):
            target = m.group(2).strip("'\"")
            if not re.match(r"^(\./)?runs(/|$)", target):
                sys.stderr.write(f"BLOCKED: 'rm -r' outside runs/ ('{target}'). Use make clean / make clean-run TAG=... (rule 6).\n"); return 2
        if re.search(r"\bgit\s+(reset\s+--hard|clean\b|push\s+(-f\b|--force))", cmd):
            sys.stderr.write("BLOCKED: destructive git command.\n"); return 2
        # writes to protected prefixes via shell (reading/copying OUT of them is fine)
        if protected:
            pat = r"(\./)?(" + "|".join(re.escape(p.rstrip("/")) for p in protected) + r")(/|\b)"
            def block(why):
                sys.stderr.write(f"BLOCKED: {why} (rule 1: never modify ref/, tests/golden/ or .claude/). Command: {cmd[:200]}\n"); return 2
            if re.search(r"\b(rm|sed\s+-i|chmod|truncate|patch|dd|git\s+(checkout|restore))\b", cmd) and re.search(r"(^|[\s'\"=])" + pat, cmd):
                return block("destructive command names a protected path")
            if re.search(r">>?\s*['\"]?" + pat, cmd) or re.search(r"\btee\s+(-a\s+)?['\"]?" + pat, cmd):
                return block("redirection into a protected path")
            for m in re.finditer(r"\b(cp|mv|rsync|install)\b([^;&|\n]*)", cmd):
                args = [a for a in m.group(2).split() if not a.startswith("-")]
                if args and re.match(pat, args[-1].strip("'\"")):
                    return block("copy/move destination is a protected path")
        return 0
    return 0

if __name__ == "__main__":
    sys.exit(main())
