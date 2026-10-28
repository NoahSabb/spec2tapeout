# tests/Makefile — cocotb 2.x. Usage: make -B TOP=mac|array|tt WIDTH=8 ACC_WIDTH=32 [GATES=yes GL_NETLIST=/abs/path.pnl.v]
SIM ?= icarus
TOPLEVEL_LANG ?= verilog
TOP ?= mac
WIDTH ?= 8
ACC_WIDTH ?= 32
GATES ?= no
PDK_ROOT ?= $(HOME)/.ciel
RTL_DIR := $(PWD)/../rtl

ifeq ($(TOP),mac)
  RTL_SRCS := $(RTL_DIR)/mac_int8.v
  TB := tb_mac
  COCOTB_TEST_MODULES := test_mac
  PARAM_ARGS := -P$(TB).WIDTH=$(WIDTH) -P$(TB).ACC_WIDTH=$(ACC_WIDTH)
else ifeq ($(TOP),array)
  RTL_SRCS := $(RTL_DIR)/mac_int8.v $(RTL_DIR)/mac_array_2x2.v
  TB := tb_array
  COCOTB_TEST_MODULES := test_array
  PARAM_ARGS := -P$(TB).WIDTH=$(WIDTH) -P$(TB).ACC_WIDTH=$(ACC_WIDTH)
else
  RTL_SRCS := $(RTL_DIR)/mac_int8.v $(RTL_DIR)/mac_array_2x2.v $(RTL_DIR)/tt_um_noahsabb_mac.v
  TB := tb_tt
  COCOTB_TEST_MODULES := test_tt
  PARAM_ARGS :=
endif

ifneq ($(GATES),yes)
  SIM_BUILD := sim_build/rtl_$(TOP)_w$(WIDTH)_a$(ACC_WIDTH)
  VERILOG_SOURCES += $(RTL_SRCS)
  COMPILE_ARGS += $(PARAM_ARGS)
else
  SIM_BUILD := sim_build/gl_$(TOP)
  COMPILE_ARGS += -DGL_TEST
  COMPILE_ARGS += -DFUNCTIONAL
  COMPILE_ARGS += -DUSE_POWER_PINS
  COMPILE_ARGS += -DSIM
  COMPILE_ARGS += -DUNIT_DELAY=\#1
  VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v
  VERILOG_SOURCES += $(PDK_ROOT)/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v
  VERILOG_SOURCES += $(GL_NETLIST)
endif

VERILOG_SOURCES += $(PWD)/$(TB).v
COCOTB_TOPLEVEL := $(TB)
COCOTB_RANDOM_SEED ?= 1
export WIDTH ACC_WIDTH GATES
include $(shell cocotb-config --makefiles)/Makefile.sim
