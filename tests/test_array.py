import json, os, sys
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge
HERE = Path(__file__).resolve().parent
WIDTH = int(os.environ.get("WIDTH", "8")); ACC = int(os.environ.get("ACC_WIDTH", "32"))
GATES = os.environ.get("GATES", "no") == "yes"; PERIOD_NS = 1000 if GATES else 10
GOLDEN = HERE / "golden" / f"array_w{WIDTH}_acc{ACC}.json"
def mask(v, bits): return v & ((1 << bits) - 1)

@cocotb.test()
async def golden_vectors(dut):
    g = json.loads(GOLDEN.read_text())
    cocotb.start_soon(Clock(dut.clk, PERIOD_NS, unit="ns").start())
    for s in (dut.rst_n, dut.clear, dut.en, dut.a0, dut.a1, dut.b0, dut.b1): s.value = 0
    await FallingEdge(dut.clk)
    for i, v in enumerate(g["vectors"]):
        rst_n, clear, en, a0, a1, b0, b1 = v[:7]; exp = v[7:]
        dut.rst_n.value = rst_n; dut.clear.value = clear; dut.en.value = en
        dut.a0.value = mask(a0, WIDTH); dut.a1.value = mask(a1, WIDTH); dut.b0.value = mask(b0, WIDTH); dut.b1.value = mask(b1, WIDTH)
        await RisingEdge(dut.clk); await FallingEdge(dut.clk)
        got = [dut.acc00.value.to_signed(), dut.acc01.value.to_signed(), dut.acc10.value.to_signed(), dut.acc11.value.to_signed()]
        assert got == exp, f"array vector {i}: inputs={v[:7]} got={got} expected={exp}"
    dut._log.info(f"{len(g['vectors'])} array vectors matched")
