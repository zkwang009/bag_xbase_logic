

`include 'header.sv'

module xnor(
    input  wire VDD,
    input  wire VSS,
    input  wire in1,
    input  wire in2,
    output wire out
);

parameter DELAY = 2;

assign #DELAY out = ~in1^in2;

endmodule
