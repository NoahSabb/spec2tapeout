`default_nettype none
// 2x2 output-stationary MAC array: PE(i,j) accumulates a_i * b_j; operands are broadcast, accumulators stay put.
module mac_array_2x2 #(
    parameter integer WIDTH     = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire                        clk,
    input  wire                        rst_n,
    input  wire                        clear,
    input  wire                        en,
    input  wire signed [WIDTH-1:0]     a0,
    input  wire signed [WIDTH-1:0]     a1,
    input  wire signed [WIDTH-1:0]     b0,
    input  wire signed [WIDTH-1:0]     b1,
    output wire signed [ACC_WIDTH-1:0] acc00,
    output wire signed [ACC_WIDTH-1:0] acc01,
    output wire signed [ACC_WIDTH-1:0] acc10,
    output wire signed [ACC_WIDTH-1:0] acc11
);
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) pe00 (.clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a0), .b(b0), .acc(acc00));
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) pe01 (.clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a0), .b(b1), .acc(acc01));
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) pe10 (.clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a1), .b(b0), .acc(acc10));
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) pe11 (.clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a1), .b(b1), .acc(acc11));
endmodule
