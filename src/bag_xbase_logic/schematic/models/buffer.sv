module {{ _cell_name }}(
    input  wire VDD,
    input  wire VSS,
    input  wire data,
{% if debug %}
    output wire data_ob,
{% endif %}
    output wire data_o
);

parameter DELAY = {{ delay }};

{% if invert %}
assign #DELAY data_o = ~data;
{% if debug %}
assign #DELAY data_ob = data;
{% endif %}
{% else %}
assign #DELAY data_o = data;
{% if debug %}
assign #DELAY data_ob = ~data;
{% endif %}
{% endif %}

endmodule
