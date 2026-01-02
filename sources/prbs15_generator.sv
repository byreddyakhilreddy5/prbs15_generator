// Code your design here

`timescale 1ns/1ps
module prbs15_generator (input clock,//Positive edge-triggered clock
                       input reset_n,//Asynchronous active low reset
			           input enable, //When HIGH, prbs generation starts and when low prbs generation stops
                       input [14:0]prbs_seed, //Seed for PRBS15 (15-bit seed)
					   input load, //loads the data from seed 
			           output reg [7:0]prbs_out // PRBS output
			           );
	
	// Internal signal declarations
	reg [14:0] lfsr;  // 15-bit LFSR for PRBS15
	reg [14:0] lfsr_next;
	reg [7:0] output_bits;
	reg load_d1;
	integer i;
	

	// Combinational logic to generate 8 bits from LFSR
	// PRBS15 polynomial: x^15 + x^14 + 1
	always @(*) begin
		// Handle zero seed case: if lfsr is 0, output should remain 0
		if (lfsr == 15'h0000) begin
			lfsr_next = 15'h0000;
			output_bits = 8'h00;
		end else begin
			lfsr_next = lfsr;  // Start with current LFSR state
			output_bits = 8'h00;
			
			// Generate 8 bits by shifting LFSR 8 times
			for (i = 0; i < 8; i = i + 1) begin
				output_bits[7-i] = lfsr_next[14];  // MSB (bit[14]) is used for output
				// Feedback: bit[14] XOR bit[13]
				lfsr_next[14:0] = {lfsr_next[13:0], (lfsr_next[14] ^ lfsr_next[13])};
			end
		end
	end
	
	// Combined always block to handle reset, load, and enable
	always @(posedge clock or negedge reset_n) begin
		if (!reset_n) begin
			lfsr <= 15'h0000;
			prbs_out <= 8'h00;
			load_d1 <= 1'b0;
		end else begin
			load_d1 <= load;
			// Load takes priority - when load transitions LOW to HIGH, load the seed
			if (load && !load_d1) begin
				// Load the seed for PRBS15 (15-bit seed)
				lfsr <= prbs_seed;
			end else if (enable) begin
				// Handle zero seed case: if lfsr is 0, output should remain 0 and lfsr stays 0
				if (lfsr == 15'h0000) begin
					prbs_out <= 8'h00;
					// lfsr stays 0, don't update it
				end else begin
					// Normal operation: update LFSR and output
					lfsr <= lfsr_next;
					// Update output only when enable is high
					prbs_out <= output_bits;
				end
			end
			// When enable is low, output remains stable (no change to prbs_out)
		end
	end
	
endmodule
