`default_nettype none
// Tiny Tapeout wrapper: byte-serial protocol (plan section 4.3) around a 2x2 int8 MAC array.
module tt_um_noahsabb_mac (
    input  wire [7:0] ui_in,    // Dedicated inputs  : data byte D
    output wire [7:0] uo_out,   // Dedicated outputs : selected result byte
    input  wire [7:0] uio_in,   // IOs: Input path   : [0]=strobe [2:1]=cmd [7:3]=unused
    output wire [7:0] uio_out,  // IOs: Output path  : 0
    output wire [7:0] uio_oe,   // IOs: Enable path  : 0 (all inputs)
    input  wire       ena,      // always 1 when the design is powered, so you can ignore it
    input  wire       clk,      // clock
    input  wire       rst_n     // reset_n - low to reset
);
    localparam integer WIDTH = 8;
    localparam integer ACC_WIDTH = 32;

    wire       strobe = uio_in[0];
    wire [1:0] cmd    = uio_in[2:1];
    wire [7:0] data   = ui_in;

    reg signed [WIDTH-1:0] a0, a1, b0, b1;
    reg        ptr_a, ptr_b;
    reg [1:0]  sel_acc, sel_byte;

    wire step  = strobe & (cmd == 2'd2);
    wire clr   = strobe & (cmd == 2'd3) & data[7];

    always @(posedge clk) begin
        if (!rst_n) begin
            a0 <= {WIDTH{1'b0}}; a1 <= {WIDTH{1'b0}}; b0 <= {WIDTH{1'b0}}; b1 <= {WIDTH{1'b0}};
            ptr_a <= 1'b0; ptr_b <= 1'b0; sel_acc <= 2'd0; sel_byte <= 2'd0;
        end else if (strobe) begin
            case (cmd)
                2'd0: begin if (ptr_a) a1 <= data; else a0 <= data; ptr_a <= ~ptr_a; end
                2'd1: begin if (ptr_b) b1 <= data; else b0 <= data; ptr_b <= ~ptr_b; end
                2'd2: begin ptr_a <= 1'b0; ptr_b <= 1'b0; end
                default: begin sel_acc <= data[1:0]; sel_byte <= data[3:2]; end
            endcase
        end
    end

    wire signed [ACC_WIDTH-1:0] acc00, acc01, acc10, acc11;
    mac_array_2x2 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) u_arr (
        .clk(clk), .rst_n(rst_n), .clear(clr), .en(step),
        .a0(a0), .a1(a1), .b0(b0), .b1(b1),
        .acc00(acc00), .acc01(acc01), .acc10(acc10), .acc11(acc11));

    reg [ACC_WIDTH-1:0] acc_sel;
    reg [7:0]           byte_sel;
    always @* begin
        acc_sel = acc00;
        case (sel_acc)
            2'd0: acc_sel = acc00;
            2'd1: acc_sel = acc01;
            2'd2: acc_sel = acc10;
            default: acc_sel = acc11;
        endcase
        byte_sel = acc_sel[7:0];
        case (sel_byte)
            2'd0: byte_sel = acc_sel[7:0];
            2'd1: byte_sel = acc_sel[15:8];
            2'd2: byte_sel = acc_sel[23:16];
            default: byte_sel = acc_sel[31:24];
        endcase
    end

    assign uo_out  = byte_sel;
    assign uio_out = 8'h00;
    assign uio_oe  = 8'h00;
    wire _unused = &{ena, uio_in[7:3], 1'b0};
endmodule
