module {{ _cell_name }}(
    input  wire VDD,
    input  wire VSS,
    input  wire in,
    input  wire clk,
    output wire out
);

parameter DELAY = {{ delay }};

reg out;

alway@(posedge clk)
    out <= #DELAY in;

endmodule
