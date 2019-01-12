module {{ _cell_name }}(
    input  wire VDD,
    input  wire VSS,
    input  wire in1,
    input  wire in2,
{% if debug %}
    output wire ns,
{% endif %}
    output wire out
);

parameter DELAY = {{ delay }};

assign #DELAY out = ~(in1&in2);
{% if debug %}
assign #DELAY ns = in1 ? 1'b0 : 1'bz;
{% endif %}

endmodule
