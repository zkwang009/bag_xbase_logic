module {{ _cell_name }}(
    input  wire VDD,
    input  wire VSS,
    input  wire in1,
    input  wire in2,
    output wire out
);

parameter DELAY = {{ delay }};

assign #DELAY out = ~in1^in2;

endmodule
