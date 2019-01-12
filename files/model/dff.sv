

`include 'header.sv'

module dff(
    input  wire VDD,
    input  wire VSS,
    input  wire in,
    input  wire clk,
    output wire out
);

parameter DELAY = 2;

reg out;

alway@(posedge clk)
    out <= #DELAY in;

endmodule
