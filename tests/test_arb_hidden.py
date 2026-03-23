from __future__ import annotations

import os
import random
from pathlib import Path

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly, NextTimeStep
from cocotb_tools.runner import get_runner


def expected_grant(req):
    if req & 0b1000:
        return 0b1000
    elif req & 0b0100:
        return 0b0100
    elif req & 0b0010:
        return 0b0010
    elif req & 0b0001:
        return 0b0001
    else:
        return 0b0000


@cocotb.test()
async def arbiter_fp_test(dut):

    # 🕒 Clock setup
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start(start_high=False))

    dut.req.value = 0
    await RisingEdge(dut.clk)

    # ✅ BASIC directed tests (no overlapping requests)
    directed_tests = [
        0b0000,
        0b0001,
        0b0010,
        0b0100,
        0b1000,
    ]

    for req in directed_tests:
        await NextTimeStep()
        dut.req.value = req

        await RisingEdge(dut.clk)
        await ReadOnly()

        actual = int(dut.grant.value)
        expected = expected_grant(req)

        assert actual == expected, (
            f"[DIRECTED FAIL] req={req:04b}, expected={expected:04b}, got={actual:04b}"
        )

    # 🎲 LIMITED random testing (not exhaustive)
    for _ in range(20):
        await NextTimeStep()
        req = random.randint(0, 15)
        dut.req.value = req

        await RisingEdge(dut.clk)
        await ReadOnly()

        actual = int(dut.grant.value)
        expected = expected_grant(req)

        assert actual == expected, (
            f"[RANDOM FAIL] req={req:04b}, expected={expected:04b}, got={actual:04b}"
        )

        # Optional: one-hot check
        assert (actual & (actual - 1)) == 0, (
            f"[ONE-HOT FAIL] req={req:04b}, grant={actual:04b}"
        )


def test_arbiter_fp_runner():
    sim = os.getenv("SIM", "icarus")

    proj_path = Path(__file__).resolve().parent.parent
    sources = [proj_path / "sources/arb.sv"]

    runner = get_runner(sim)
    runner.build(
        sources=sources,
        hdl_toplevel="arbiter_fp",  
        always=True,
    )

    runner.test(
        hdl_toplevel="arbiter_fp",   
        test_module="test_arb_hidden" 
    )
