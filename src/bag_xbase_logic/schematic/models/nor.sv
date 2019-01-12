module {{ _cell_name }}(
    input  wire VDD,
    input  wire VSS,
    input  wire in1,
    input  wire in2,
{% if debug %}
    output wire ps,
{% endif %}
    output wire out
);

parameter DELAY = {{ delay }};

assign #DELAY out = ~(in1|in2);
{% if debug %}
assign #DELAY ns = in1 ? 1'bz : 1'b1;
{% endif %}

endmodule
