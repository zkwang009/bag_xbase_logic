

module buffer(
    input  wire VDD,
    input  wire VSS,
    input  wire data,
    output wire data_ob,
    output wire data_o
);

parameter DELAY = 1;

assign #DELAY data_o = data;
assign #DELAY data_ob = ~data;

endmodule
