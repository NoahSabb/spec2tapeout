"""Reference models for mac_int8, mac_array_2x2 and the tt_um_noahsabb_mac byte-serial protocol.
Written from TAPEOUT_FACTORY_PLAN.md sections 4.1-4.3. FROZEN after Phase 2 (rule 1). Pure Python, no RTL imports."""

def to_signed(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v & (1 << (bits - 1)) else v

def to_unsigned(v, bits):
    return v & ((1 << bits) - 1)

class MacRef:
    def __init__(self, width=8, acc_width=32):
        self.width, self.acc_width, self.acc = width, acc_width, 0

    def clock(self, rst_n, clear, en, a, b):
        """One rising edge. Priority: !rst_n > clear > en. a, b signed ints. Returns acc (signed) after the edge."""
        if not rst_n or clear:
            self.acc = 0
        elif en:
            self.acc = to_signed(self.acc + a * b, self.acc_width)
        return self.acc

class Array2x2Ref:
    """Output-stationary: pe[i][j].acc += a[i]*b[j]."""
    def __init__(self, width=8, acc_width=32):
        self.pe = [[MacRef(width, acc_width) for _ in range(2)] for _ in range(2)]

    def clock(self, rst_n, clear, en, a, b):
        return [[self.pe[i][j].clock(rst_n, clear, en, a[i], b[j]) for j in range(2)] for i in range(2)]

    def flat(self):  # [acc00, acc01, acc10, acc11]
        return [self.pe[0][0].acc, self.pe[0][1].acc, self.pe[1][0].acc, self.pe[1][1].acc]

class TTRef:
    """Byte-serial protocol of tt_um_noahsabb_mac. clock(rst_n, ui_in, uio_in) per rising edge -> uo_out after it."""
    def __init__(self):
        self.arr = Array2x2Ref(8, 32)
        self.reset()

    def reset(self):
        self.a, self.b = [0, 0], [0, 0]
        self.ptr_a = self.ptr_b = 0
        self.sel_acc = self.sel_byte = 0
        self.arr.clock(0, 0, 0, [0, 0], [0, 0])

    def clock(self, rst_n, ui_in, uio_in):
        if not rst_n:
            self.reset()
            return 0
        strobe, cmd, data = uio_in & 1, (uio_in >> 1) & 3, ui_in & 0xFF
        step = clr = 0
        if strobe:
            if cmd == 0:
                self.a[self.ptr_a] = to_signed(data, 8); self.ptr_a ^= 1
            elif cmd == 1:
                self.b[self.ptr_b] = to_signed(data, 8); self.ptr_b ^= 1
            elif cmd == 2:
                step = 1; self.ptr_a = self.ptr_b = 0
            else:
                self.sel_acc, self.sel_byte, clr = data & 3, (data >> 2) & 3, (data >> 7) & 1
        self.arr.clock(1, clr, step, list(self.a), list(self.b))
        return self.uo_out()

    def uo_out(self):
        v = to_unsigned(self.arr.flat()[self.sel_acc], 32)
        return (v >> (8 * self.sel_byte)) & 0xFF
