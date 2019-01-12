

`include 'header.sv'

module nor(
    input  wire VDD,
    input  wire VSS,
    input  wire in1,
    input  wire in2,
    output wire ps,
    output wire out
);

parameter DELAY = 1;

assign #DELAY out = ~(in1|in2);
assign #DELAY ns = in1 ? 1'bz : 1'b1;

endmodule
