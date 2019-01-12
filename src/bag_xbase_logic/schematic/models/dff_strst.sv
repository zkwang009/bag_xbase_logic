module {{ _cell_name }}(
    input  wire VDD,
    input  wire VSS,
    input  wire in,
    input  wire clk,
    input  wire st,
    input  wire rst,
    output wire out
);

parameter DELAY = {{ delay }};

reg out;

alway@(posedge clk or st or rst)
    if (st == 1)
        out <= #DELAY 1;
    else if (rst == 1)
        out <= #DELAY 0;
    else
        out <= #DELAY in;

endmodule
