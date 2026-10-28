`default_nettype none
// Parameterized signed multiply-accumulate. Synchronous active-low reset. clear > en priority.
// Accumulator width rule: ACC_WIDTH >= 2*WIDTH + ceil(log2(K)) for K accumulation steps without wrap.
module mac_int8 #(
    parameter integer WIDTH     = 8,
    parameter integer ACC_WIDTH = 32
) (
    input  wire                        clk,
    input  wire                        rst_n,
    input  wire                        clear,
    input  wire                        en,
    input  wire signed [WIDTH-1:0]     a,
    input  wire signed [WIDTH-1:0]     b,
    output reg  signed [ACC_WIDTH-1:0] acc
);
    wire signed [2*WIDTH-1:0]   product = a * b;                 // both operands signed -> signed product
    wire signed [ACC_WIDTH-1:0] product_ext = {{(ACC_WIDTH-2*WIDTH){product[2*WIDTH-1]}}, product};

    always @(posedge clk) begin
        if (!rst_n)      acc <= {ACC_WIDTH{1'b0}};
        else if (clear)  acc <= {ACC_WIDTH{1'b0}};
        else if (en)     acc <= acc + product_ext;
    end
endmodule
