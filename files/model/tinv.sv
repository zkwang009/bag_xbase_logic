

`include 'header.sv'


module tinv(
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
    else if (en_ctrl == 1)
        if (in == 0)
            out = #DELAY 1'z;
        else
            out = #DELAY 0;
    else if (en_ctrl == 2)
        if (in == 0)
            out = #DELAY 1;
        else
            out = #DELAY 1'z;
    else
        out = #DELAY ~in;

endmodule
