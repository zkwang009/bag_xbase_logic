module {{ _cell_name }}(
    input  wire VDD,
    input  wire VSS,
    input  wire in1,
    input  wire in2,
{% if debug %}
    output wire ns,
    output wire out_b,
{% endif %}
    output wire out
);

parameter DELAY = {{ delay }};

assign #DELAY out = in1|in2;
{% if debug %}
assign #DELAY ns = in1 ? 1'bz : 1'b0;
assign #DELAY out_b = ~(in1|in2);
{% endif %}

endmodule
