# Makefile — spec2tapeout gate ladder. Every gate runs through factory/gate.py, which records
# the real exit code, timestamps and log path into factory/state/gates.json.
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
MAKEFLAGS += --no-print-directory

-include factory/state/env.mk
HARDEN_MODE   ?= nix
LIBRELANE_DIR ?= $(HOME)/librelane
PDK_ROOT      ?= $(HOME)/.ciel
PDK           ?= sky130A
export PDK_ROOT PDK
export PYTHONPATH :=
export PATH := $(CURDIR)/.venv/bin:$(CURDIR)/tools/bin:/opt/homebrew/bin:$(PATH):/nix/var/nix/profiles/default/bin

PY        := $(CURDIR)/.venv/bin/python
GATE      := $(PY) factory/gate.py
NIX_SHELL := nix-shell $(LIBRELANE_DIR)/shell.nix --run
DESIGN    ?= mac_int8
WIDTH     ?= 8
TAG       ?= $(DESIGN)-$(shell date +%Y%m%d-%H%M%S)
CONFIG    ?= flow/$(DESIGN)/config.json
RUN_DIR   := runs/$(TAG)
GL_NETLIST ?= $(CURDIR)/$(RUN_DIR)/final/pnl/$(DESIGN).pnl.v
TT_REPO   ?= tt_repo

.PHONY: help doctor lint sim sim-gl synth harden harden-closure sta-report precheck sweep render dashboard serve \
        verify-factory report clean clean-run log elapsed freeze-golden gen-golden tt-harden tt-test tt-test-gl tt-precheck

help:
	@grep -E '^[a-z-]+:' Makefile | cut -d: -f1 | sort | tr '\n' ' '; echo

log:            ## make log MSG="text"
	@printf '%s %s\n' "$$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(MSG)" >> logs/overnight.md

elapsed:        ## seconds since factory/state/start_time
	@echo $$(( $$(date +%s) - $$(cat factory/state/start_time) ))

doctor:
	$(GATE) doctor -- bash factory/doctor.sh

lint:           ## Verilator lint of all three tops; fatal: LATCH MULTIDRIVEN CASEINCOMPLETE UNDRIVEN IMPLICIT
	$(GATE) lint -- bash factory/lint.sh

gen-golden:     ## generate tests/golden/*.json from ref/ (only before freeze)
	$(GATE) gen-golden -- $(PY) ref/gen_golden.py

freeze-golden:  ## make golden vectors and reference model immutable
	chmod -R a-w ref tests/golden
	grep -qx 'ref/' .claude/protected.txt || echo 'ref/' >> .claude/protected.txt
	grep -qx 'tests/golden/' .claude/protected.txt || echo 'tests/golden/' >> .claude/protected.txt
	git add -A ref tests/golden .claude/protected.txt && git commit -m "phase 2: freeze golden vectors and reference model" || true
	$(MAKE) log MSG="FROZEN ref/ and tests/golden/ (chmod a-w + hook)"

sim:            ## cocotb RTL sim vs golden: make sim TOP=mac|array|tt WIDTH=8
	$(GATE) sim-$(TOP)-w$(WIDTH) -- bash -c 'cd tests && $(MAKE) -B TOP=$(TOP) WIDTH=$(WIDTH) ACC_WIDTH=$(ACC_WIDTH) GATES=no && $(PY) -m cocotb_tools.check_results results.xml'
sim: TOP ?= mac
sim: ACC_WIDTH ?= 32

sim-gl:         ## gate-level sim of the hardened MAC: make sim-gl TAG=<tag>
	test -s "$(GL_NETLIST)" || { echo "missing $(GL_NETLIST)"; exit 1; }
	$(GATE) sim-gl-$(TOP) -- bash -c 'cd tests && $(MAKE) -B TOP=$(TOP) GATES=yes GL_NETLIST=$(GL_NETLIST) && $(PY) -m cocotb_tools.check_results results.xml'
sim-gl: TOP ?= mac

synth:          ## standalone Yosys synthesis check (fast; fails on latches/unmapped cells/$mem)
	$(GATE) synth-$(WIDTH) -- bash -c 'mkdir -p runs/synth && $(PY) factory/synth_check.py --width $(WIDTH) --out runs/synth'

harden:         ## full LibreLane Classic flow: make harden TAG=<tag> [CONFIG=...]
	mkdir -p flow/$(DESIGN)/src && cp rtl/*.v flow/$(DESIGN)/src/
	@if [ "$(HARDEN_MODE)" = "docker" ]; then \
	  $(GATE) harden-$(TAG) -- $(PY) -m librelane --dockerized --docker-no-tty --pdk-root $(PDK_ROOT) --run-tag $(TAG) --force-run-dir $(RUN_DIR) $(CONFIG); \
	else \
	  $(GATE) harden-$(TAG) -- $(NIX_SHELL) "librelane --pdk-root $(PDK_ROOT) --run-tag $(TAG) --force-run-dir $(RUN_DIR) $(CONFIG)"; \
	fi
	$(PY) factory/orchestrate.py ingest --run-dir $(RUN_DIR) --design $(DESIGN)

harden-closure: ## harden with the retry/decision loop (Phase 4)
	mkdir -p flow/$(DESIGN)/src && cp rtl/*.v flow/$(DESIGN)/src/
	$(PY) factory/orchestrate.py closure --config $(CONFIG) --design $(DESIGN) --tag $(TAG) --max-attempts 4

sta-report:     ## print the nine-corner summary and key metrics: make sta-report TAG=<tag>
	$(PY) factory/sta_report.py $(RUN_DIR)

render:         ## render a layout PNG per major stage: make render TAG=<tag>
	$(GATE) render-$(TAG) -- $(PY) factory/render.py --run-dir $(RUN_DIR) --design $(DESIGN)

sweep:          ## WIDTH x CLOCK_PERIOD sweep -> factory/state/sweep.csv + plots
	$(GATE) sweep -- $(PY) factory/sweep.py --widths 2,4,8 --periods 5,10,20

dashboard:      ## regenerate factory/dashboard/site/index.html from factory/state/*.json
	$(GATE) dashboard -- $(PY) factory/dashboard/build.py

serve:          ## serve the dashboard on http://localhost:8787
	cd factory/dashboard/site && $(PY) -m http.server 8787

precheck:       ## Tiny Tapeout precheck (local attempt; CI is authoritative)
	$(GATE) precheck -- bash -c 'cd $(TT_REPO) && ../.venv-tt/bin/python tt/tt_tool.py --create-tt-submission && cd tt/precheck && nix-shell --run "python precheck.py --gds ../../tt_submission/*.gds --tech sky130A"'

tt-harden:      ## local hardening of the Tiny Tapeout repo (Docker, LibreLane 3.0.14, bit-identical to CI)
	$(GATE) tt-harden -- bash -c 'cd $(TT_REPO) && export PDK_ROOT=$(PDK_ROOT) PDK=sky130A LIBRELANE_TAG=3.0.14 && ../.venv-tt/bin/python tt/tt_tool.py --create-user-config && ../.venv-tt/bin/python tt/tt_tool.py --harden && ../.venv-tt/bin/python tt/tt_tool.py --print-warnings && ../.venv-tt/bin/python tt/tt_tool.py --print-stats && ../.venv-tt/bin/python tt/tt_tool.py --print-cell-category'

tt-test:        ## RTL cocotb test in the TT repo
	$(GATE) tt-test -- bash -c 'cd $(TT_REPO)/test && make -B && $(PY) -m cocotb_tools.check_results results.xml'

tt-test-gl:     ## gate-level cocotb test in the TT repo (needs runs/wokwi)
	$(GATE) tt-test-gl -- bash -c 'cd $(TT_REPO) && cp runs/wokwi/final/pnl/tt_um_noahsabb_mac.pnl.v test/gate_level_netlist.v && cd test && make -B GATES=yes && $(PY) -m cocotb_tools.check_results results.xml'

verify-factory: ## Phase 8: full pipeline from clean + all checks
	$(GATE) verify-factory -- $(PY) factory/verify.py

report:         ## write reports/MORNING_REPORT.md
	$(PY) factory/report.py
	$(MAKE) log MSG="REPORT written reports/MORNING_REPORT.md"

clean-run:      ## delete one run: make clean-run TAG=<tag>
	@test -n "$(TAG)" && test -d "runs/$(TAG)" && rm -rf "runs/$(TAG)" || echo "no runs/$(TAG)"

clean:          ## delete all runs and sim builds (never touches ref/ tests/golden/)
	rm -rf runs/* tests/sim_build tests/results.xml tests/*.vcd tests/*.fst factory/dashboard/site/*
