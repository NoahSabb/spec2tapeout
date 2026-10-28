`default_nettype none
`timescale 1ns / 1ps
module tb_mac;
    parameter integer WIDTH = 8;
    parameter integer ACC_WIDTH = 32;
    reg clk = 1'b0, rst_n = 1'b0, clear = 1'b0, en = 1'b0;
    reg  signed [WIDTH-1:0] a = 0, b = 0;
    wire signed [ACC_WIDTH-1:0] acc;
    initial begin $dumpfile("tb_mac.vcd"); $dumpvars(0, tb_mac); #1; end
`ifdef GL_TEST
    wire VPWR = 1'b1;
    wire VGND = 1'b0;
    mac_int8 dut (.VPWR(VPWR), .VGND(VGND),
`else
    mac_int8 #(.WIDTH(WIDTH), .ACC_WIDTH(ACC_WIDTH)) dut (
`endif
        .clk(clk), .rst_n(rst_n), .clear(clear), .en(en), .a(a), .b(b), .acc(acc));
endmodule
