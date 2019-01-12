

module or_gate(
    input  wire VDD,
    input  wire VSS,
    input  wire in1,
    input  wire in2,
    output wire ns,
    output wire out_b,
    output wire out
);

parameter DELAY = 1;

assign #DELAY out = in1|in2;
assign #DELAY ns = in1 ? 1'bz : 1'b0;
assign #DELAY out_b = ~(in1|in2);

endmodule
