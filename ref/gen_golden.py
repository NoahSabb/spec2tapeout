#!/usr/bin/env python3
"""Generate golden vectors from the reference model. Run once (make gen-golden), then frozen."""
import json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ref.mac_ref import MacRef, Array2x2Ref, TTRef, to_signed
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "golden")
os.makedirs(OUT, exist_ok=True)

def rnd_signed(rng, bits):
    return rng.randint(-(1 << (bits - 1)), (1 << (bits - 1)) - 1)

def gen_mac(width, acc_width, seed, n=600):
    rng = random.Random(seed); m = MacRef(width, acc_width); vec = []
    lo, hi = -(1 << (width - 1)), (1 << (width - 1)) - 1
    directed = [(0, 0, 0, 0, 0), (0, 0, 0, 0, 0), (1, 0, 0, 0, 0),           # reset held, then idle
                (1, 0, 1, hi, hi), (1, 0, 1, lo, lo), (1, 0, 1, lo, hi), (1, 0, 1, hi, lo),  # sign corners
                (1, 0, 1, 0, hi), (1, 0, 1, lo, 0), (1, 0, 0, hi, hi), (1, 1, 1, hi, hi),    # zero operand, hold, clear beats en
                (1, 0, 1, -1, -1), (1, 0, 1, -1, 1), (1, 0, 1, 1, -1)]
    for rst_n, clear, en, a, b in directed:
        vec.append([rst_n, clear, en, a, b, m.clock(rst_n, clear, en, a, b)])
    for _ in range(n):
        r = rng.random()
        rst_n = 0 if r < 0.01 else 1
        clear = 1 if 0.01 <= r < 0.04 else 0
        en = 1 if rng.random() < 0.85 else 0
        a, b = rnd_signed(rng, width), rnd_signed(rng, width)
        vec.append([rst_n, clear, en, a, b, m.clock(rst_n, clear, en, a, b)])
    # drive the accumulator toward wrap-around (fully wraps when acc_width is small, e.g. mac_w4_acc10); capped at 64 steps
    for _ in range(min(64, 2 * (1 << max(0, acc_width - 2 * width)) + 8)):
        vec.append([1, 0, 1, lo, lo, m.clock(1, 0, 1, lo, lo)])
    return {"model": "ref/mac_ref.py:MacRef", "params": {"WIDTH": width, "ACC_WIDTH": acc_width}, "seed": seed,
            "fields": ["rst_n", "clear", "en", "a", "b", "acc_after"], "vectors": vec}

def gen_array(width, acc_width, seed, n=400):
    rng = random.Random(seed); m = Array2x2Ref(width, acc_width); vec = []
    for i in range(3):
        acc = m.clock(0, 0, 0, [0, 0], [0, 0]); vec.append([0, 0, 0, 0, 0, 0, 0] + m.flat())
    for _ in range(n):
        r = rng.random(); rst_n = 0 if r < 0.01 else 1; clear = 1 if 0.01 <= r < 0.04 else 0
        en = 1 if rng.random() < 0.85 else 0
        a = [rnd_signed(rng, width), rnd_signed(rng, width)]; b = [rnd_signed(rng, width), rnd_signed(rng, width)]
        m.clock(rst_n, clear, en, a, b); vec.append([rst_n, clear, en, a[0], a[1], b[0], b[1]] + m.flat())
    return {"model": "ref/mac_ref.py:Array2x2Ref", "params": {"WIDTH": width, "ACC_WIDTH": acc_width}, "seed": seed,
            "fields": ["rst_n", "clear", "en", "a0", "a1", "b0", "b1", "acc00", "acc01", "acc10", "acc11"], "vectors": vec}

def gen_tt(seed, n=2500):
    rng = random.Random(seed); t = TTRef(); vec = []
    def step(rst_n, ui, uio): vec.append([rst_n, ui & 0xFF, uio & 0xFF, t.clock(rst_n, ui, uio)])
    S, LOAD_A, LOAD_B, STEP, SEL = 1, 0 << 1, 1 << 1, 2 << 1, 3 << 1
    for _ in range(3): step(0, 0, 0)
    step(1, 0, 0)
    # directed: a=(3,-5), b=(7,-2); three steps -> acc00=63, acc01=-18, acc10=-105, acc11=30
    step(1, 3, S | LOAD_A); step(1, 0xFB, S | LOAD_A); step(1, 7, S | LOAD_B); step(1, 0xFE, S | LOAD_B)
    for _ in range(3): step(1, 0, S | STEP)
    for acc in range(4):
        for byte in range(4):
            step(1, acc | (byte << 2), S | SEL); step(1, 0, 0)
    step(1, 0x80 | 2, S | SEL)                         # clear all, select acc10
    step(1, 0x7F, S | LOAD_A); step(1, 0x80, S | LOAD_A); step(1, 0x80, S | LOAD_B); step(1, 0x7F, S | LOAD_B)
    for _ in range(20): step(1, 0, S | STEP)           # 127*-128 and -128*-128 products accumulate
    for acc in range(4):
        for byte in range(4):
            step(1, acc | (byte << 2), S | SEL)
    for _ in range(n):                                 # randomized protocol traffic with occasional reset
        r = rng.random()
        if r < 0.005: step(0, rng.randrange(256), rng.randrange(256)); continue
        ui = rng.randrange(256); c = rng.choice([LOAD_A, LOAD_B, STEP, STEP, STEP, SEL]); s = S if rng.random() < 0.8 else 0
        step(1, ui, s | c | (rng.randrange(32) << 3))  # uio_in[7:3] is don't-care
    return {"model": "ref/mac_ref.py:TTRef", "params": {"WIDTH": 8, "ACC_WIDTH": 32}, "seed": seed,
            "fields": ["rst_n", "ui_in", "uio_in", "uo_out_after"], "vectors": vec}

def dump(name, obj):
    p = os.path.join(OUT, name); json.dump(obj, open(p, "w"), separators=(",", ":")); print("wrote", p, len(obj["vectors"]), "vectors")

if __name__ == "__main__":
    dump("mac_w2_acc20.json", gen_mac(2, 20, 2020))
    dump("mac_w4_acc24.json", gen_mac(4, 24, 4024))
    dump("mac_w8_acc32.json", gen_mac(8, 32, 8032))
    dump("mac_w4_acc10.json", gen_mac(4, 10, 4010))      # small accumulator: exercises wrap-around
    dump("array_w8_acc32.json", gen_array(8, 32, 2208))
    dump("tt_protocol.json", gen_tt(2611))
