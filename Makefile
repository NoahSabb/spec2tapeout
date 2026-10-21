# spec2tapeout — Phase 0 Makefile (works with Apple's GNU make 3.81 and newer)
#   make doctor   print every tool's version; exit nonzero if any is missing
#   make smoke    run `librelane --dockerized --smoke-test` (needs Docker Desktop)

SHELL := /bin/bash
ROOT  := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
export PDK_ROOT ?= $(ROOT)/pdk
export PDK      ?= sky130A
export LIBRELANE_IMAGE ?= ghcr.io/librelane/librelane:3.0.16
export PATH := $(ROOT)/.venv/bin:$(ROOT)/tools/bin:$(PATH):$(HOME)/.local/state/nix/profiles/profile/bin:$(HOME)/.nix-profile/bin:/nix/var/nix/profiles/default/bin:/opt/homebrew/bin:/usr/local/bin

.PHONY: help doctor smoke

help:
	@echo "targets: doctor, smoke"

doctor:
	@"$(ROOT)/tools/doctor.sh"

smoke:
	@"$(ROOT)/tools/smoke.sh"
