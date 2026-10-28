`default_nettype none
`timescale 1ns / 1ps
module tb_array;
    parameter integer WIDTH = 8;
    parameter integer ACC_WIDTH = 32;
    reg clk = 1'b0, rst_n = 1'b0, clear = 1'b0, en = 1'b0;
    reg  signed [WIDTH-1:0] a0 = 0, a1 = 0, b0 = 0, b1 = 0;
    wire signed [ACC_WIDTH-1:0] acc00, acc01, acc10, acc11;
    initial begin $dumpfile("tb_array.vcd"); $dumpvars(0, tb_array); #1; end
`ifdef GL_TEST
    wire VPWR = 1'b1;
    wire VGND = 1'b0;
    mac_array_2x2 dut (.VPWR(VPWR), .VGND(VGND),
`else
    mac_array_2x2 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) dut (
`endif
        .clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a0(a0), .a1(a1), .b0(b0), .b1(b1),
        .acc00(acc00), .acc01(acc01), .acc10(acc10), .acc11(acc11));
endmodule
