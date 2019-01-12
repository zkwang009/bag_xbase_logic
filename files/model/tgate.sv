

`include 'header.sv'


module tgate(
    input  wire VDD,
    input  wire VSS,
    input  wire in,
    input  wire en,
    input  wire enb,
    output wire out
);

parameter DELAY = 1;

wire [1:0] en_ctrl;

assign en_ctrl = {~enb, en}

always @(*)
    if (en_ctrl == 0)
        out = #DELAY 1'z;
    else
        out = #DELAY in;

endmodule
