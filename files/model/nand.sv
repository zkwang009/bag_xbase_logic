

`include 'header.sv'

module nand(
    input  wire VDD,
    input  wire VSS,
    input  wire in1,
    input  wire in2,
    output wire ns,
    output wire out
);

parameter DELAY = 1;

assign #DELAY out = ~(in1&in2);
assign #DELAY ns = in1 ? 1'b0 : 1'bz;

endmodule
