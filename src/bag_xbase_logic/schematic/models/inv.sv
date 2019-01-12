`include 'header.sv'

module {{ _cell_name }}(
    input  wire VDD,
    input  wire VSS,
    input  wire in,
    output wire out
);

parameter DELAY = {{ delay }};

assign #DELAY out = ~in;

endmodule
