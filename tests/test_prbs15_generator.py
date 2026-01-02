import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, FallingEdge, Timer


ADDR_WIDTH = 15
ZERO_SEED = 0x0000


def prbs15_step(lfsr):
    """
    Perform one PRBS15 step:
    Polynomial: x^15 + x^14 + 1
    """
    if lfsr == 0:
        return 0
    feedback = ((lfsr >> 14) ^ (lfsr >> 13)) & 0x1
    return ((lfsr << 1) & 0x7FFF) | feedback


def prbs15_generate_byte(lfsr):
    """
    Generate 8 PRBS bits and return (byte, next_lfsr)
    Matches DUT behavior:
      - Output MSB first
      - Shift LFSR 8 times
    """
    if lfsr == 0:
        return 0x00, 0

    value = 0
    next_lfsr = lfsr

    for i in range(8):
        bit = (next_lfsr >> 14) & 0x1
        value = (value << 1) | bit
        next_lfsr = prbs15_step(next_lfsr)

    return value, next_lfsr


@cocotb.test()
async def test_prbs15_generator(dut):
    """Cocotb test for prbs15_generator"""

    # Start clock: 10ns period
    cocotb.start_soon(Clock(dut.clock, 10, unit="ns").start())

    # Initialize inputs
    dut.reset_n.value = 0
    dut.enable.value = 0
    dut.load.value = 0
    dut.prbs_seed.value = 0

    await Timer(20, unit="ns")

    # Release reset
    dut.reset_n.value = 1
    await RisingEdge(dut.clock)

    dut._log.info("Reset released")

    # ----------------------------------------------------
    # Test 1: Load non-zero seed
    # ----------------------------------------------------
    seed = 0x7ACE & 0x7FFF
    dut.prbs_seed.value = seed
    dut.load.value = 1

    await RisingEdge(dut.clock)
    dut.load.value = 0

    dut._log.info(f"Seed loaded: {hex(seed)}")

    # ----------------------------------------------------
    # Test 2: Enable PRBS generation
    # ----------------------------------------------------
    dut.enable.value = 1
    lfsr_model = seed

    # Wait for first clock edge to generate first output
    await RisingEdge(dut.clock)
    await FallingEdge(dut.clock)  # Check output at falling edge
    exp_byte, lfsr_model = prbs15_generate_byte(lfsr_model)
    got = dut.prbs_out.value.to_unsigned()
    assert got == exp_byte, (
        f"PRBS mismatch: expected {hex(exp_byte)}, got {hex(got)}"
    )

    # Continue checking for remaining cycles
    for _ in range(9):
        await RisingEdge(dut.clock)
        await FallingEdge(dut.clock)  # Check output at falling edge
        exp_byte, lfsr_model = prbs15_generate_byte(lfsr_model)

        got = dut.prbs_out.value.to_unsigned()
        assert got == exp_byte, (
            f"PRBS mismatch: expected {hex(exp_byte)}, got {hex(got)}"
        )

    dut._log.info("PRBS generation verified")

    # ----------------------------------------------------
    # Test 3: Disable enable → output should hold
    # ----------------------------------------------------
    dut.enable.value = 0
    await RisingEdge(dut.clock)
    await FallingEdge(dut.clock)  # Check output at falling edge
    held_value = dut.prbs_out.value.to_unsigned()

    for _ in range(3):
        await RisingEdge(dut.clock)
        await FallingEdge(dut.clock)  # Check output at falling edge
        assert dut.prbs_out.value.to_unsigned() == held_value, (
            "Output changed while enable=0"
        )

    dut._log.info("Enable gating verified")

    # ----------------------------------------------------
    # Test 4: Re-enable PRBS generation
    # ----------------------------------------------------
    dut.enable.value = 1

    for _ in range(5):
        await RisingEdge(dut.clock)
        await FallingEdge(dut.clock)  # Check output at falling edge
        exp_byte, lfsr_model = prbs15_generate_byte(lfsr_model)
        got = dut.prbs_out.value.to_unsigned()
        assert got == exp_byte, (
            f"PRBS mismatch after re-enable: exp {hex(exp_byte)}, got {hex(got)}"
        )

    dut._log.info("Re-enable behavior verified")

    # ----------------------------------------------------
    # Test 5: Load zero seed
    # ----------------------------------------------------
    dut.enable.value = 0
    dut.prbs_seed.value = ZERO_SEED
    dut.load.value = 1

    await RisingEdge(dut.clock)
    dut.load.value = 0
    dut.enable.value = 1

    for _ in range(3):
        await RisingEdge(dut.clock)
        await FallingEdge(dut.clock)  # Check output at falling edge
        assert dut.prbs_out.value.to_unsigned() == 0x00, (
            "Output not zero with zero seed"
        )

    dut._log.info("Zero-seed behavior verified")

    dut._log.info("✅ PRBS15 cocotb test PASSED")


# ✅ CRITICAL: Pytest wrapper function
def test_prbs15_generator_runner():
    import os
    from pathlib import Path
    from cocotb_tools.runner import get_runner
    
    sim = os.getenv("SIM", "icarus")
    proj_path = Path(__file__).resolve().parent.parent
    
    sources = [
        proj_path / "sources/prbs15_generator.sv",
    ]
    
    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="prbs15_generator",
        always=True,
    )
    
    runner.test(
        hdl_toplevel="prbs15_generator",
        test_module="test_prbs15_generator"
    )