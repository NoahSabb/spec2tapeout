import json, os, random, sys
from pathlib import Path
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from ref.mac_ref import MacRef   # frozen reference model (read-only)

WIDTH = int(os.environ.get("WIDTH", "8"))
ACC = int(os.environ.get("ACC_WIDTH", "32"))
GATES = os.environ.get("GATES", "no") == "yes"
PERIOD_NS = 1000 if GATES else 10
GOLDEN = HERE / "golden" / f"mac_w{WIDTH}_acc{ACC}.json"

def mask(v, bits): return v & ((1 << bits) - 1)

async def start(dut):
    cocotb.start_soon(Clock(dut.clk, PERIOD_NS, unit="ns").start())
    dut.rst_n.value = 0; dut.clear.value = 0; dut.en.value = 0; dut.a.value = 0; dut.b.value = 0
    await FallingEdge(dut.clk)

async def drive_and_sample(dut, rst_n, clear, en, a, b):
    dut.rst_n.value = rst_n; dut.clear.value = clear; dut.en.value = en
    dut.a.value = mask(a, WIDTH); dut.b.value = mask(b, WIDTH)
    await RisingEdge(dut.clk)
    await FallingEdge(dut.clk)
    return dut.acc.value.to_signed()

@cocotb.test()
async def golden_vectors(dut):
    g = json.loads(GOLDEN.read_text())
    assert g["params"]["WIDTH"] == WIDTH and g["params"]["ACC_WIDTH"] == ACC, f"golden/params mismatch for {GOLDEN}"
    await start(dut)
    for i, (rst_n, clear, en, a, b, exp) in enumerate(g["vectors"]):
        got = await drive_and_sample(dut, rst_n, clear, en, a, b)
        assert got == exp, f"golden vector {i}: rst_n={rst_n} clear={clear} en={en} a={a} b={b}: acc={got} expected {exp}"
    dut._log.info(f"{len(g['vectors'])} golden vectors matched ({GOLDEN.name}, GATES={GATES})")

@cocotb.test()
async def randomized_vs_reference(dut):
    seed = int(os.environ.get("COCOTB_RANDOM_SEED", "1")); rng = random.Random(seed)
    dut._log.info(f"randomized test seed={seed}")
    m = MacRef(WIDTH, ACC); await start(dut)
    lo, hi = -(1 << (WIDTH - 1)), (1 << (WIDTH - 1)) - 1
    n = 300 if GATES else 3000
    got = await drive_and_sample(dut, 0, 0, 0, 0, 0); m.clock(0, 0, 0, 0, 0)
    for i in range(n):
        r = rng.random(); rst_n = 0 if r < 0.01 else 1; clear = 1 if 0.01 <= r < 0.04 else 0
        en = 1 if rng.random() < 0.85 else 0; a, b = rng.randint(lo, hi), rng.randint(lo, hi)
        exp = m.clock(rst_n, clear, en, a, b)
        got = await drive_and_sample(dut, rst_n, clear, en, a, b)
        assert got == exp, f"random vector {i} (seed {seed}): a={a} b={b} en={en} clear={clear} rst_n={rst_n}: acc={got} expected {exp}"
