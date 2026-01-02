`timescale 1ns/1ps
module prbs15_generator (input clock,//Positive edge-triggered clock
                       input reset_n,//Asynchronous active low reset
			           input enable, //When HIGH, prbs generation starts and when low prbs generation stops
                       input [14:0]prbs_seed, //Seed for PRBS15 (15-bit seed)
					   input load, //loads the data from seed 
			           output reg [7:0]prbs_out // PRBS output
			           );
	
	// TODO: Implement PRBS15 generator
	// PRBS15 polynomial: x^15 + x^14 + 1
	// See docs/Specification.md for details
	
		
endmodule
