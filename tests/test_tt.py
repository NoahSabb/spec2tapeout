import json, os
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
HERE = Path(__file__).resolve().parent
GOLDEN = HERE / "golden" / "tt_protocol.json"
GATES = os.environ.get("GATES", "no") == "yes"
PERIOD_NS = 1000   # 1 MHz: slow enough for #1 unit-delay gate-level models, fast enough for 2.5k vectors

@cocotb.test()
async def protocol_golden(dut):
    g = json.loads(GOLDEN.read_text())
    cocotb.start_soon(Clock(dut.clk, PERIOD_NS, unit="ns").start())
    dut.ena.value = 1; dut.ui_in.value = 0; dut.uio_in.value = 0; dut.rst_n.value = 0
    await FallingEdge(dut.clk)
    for i, (rst_n, ui, uio, exp) in enumerate(g["vectors"]):
        dut.rst_n.value = rst_n; dut.ui_in.value = ui; dut.uio_in.value = uio
        await RisingEdge(dut.clk); await FallingEdge(dut.clk)
        got = dut.uo_out.value.to_unsigned()
        assert got == exp, f"tt vector {i}: rst_n={rst_n} ui_in=0x{ui:02x} uio_in=0x{uio:02x}: uo_out=0x{got:02x} expected 0x{exp:02x}"
        assert dut.uio_oe.value.to_unsigned() == 0 and dut.uio_out.value.to_unsigned() == 0
    dut._log.info(f"{len(g['vectors'])} protocol vectors matched (GATES={GATES})")
