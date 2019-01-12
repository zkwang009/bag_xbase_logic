

`include 'header.sv'

`include 'header.sv'

module inv(
    input  wire VDD,
    input  wire VSS,
    input  wire in,
    output wire out
);

parameter DELAY = 7;

assign #DELAY out = ~in;

endmodule
