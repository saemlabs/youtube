import pytest
from pydantic import ValidationError

from saemphysics.ir import (
    CapabilityError,
    DEFAULT_MACHINE_CAPABILITIES,
    MachineCapabilities,
    MachineInstruction,
    NumericMode,
    SemanticIR,
    compile_request,
)
from saemphysics.runtime import execute_plan


def make_request(**updates):
    fields = {
        "operation": "solve_constant_acceleration",
        "question_id": "synthetic_cart_motion",
        "initial_velocity_m_s": "2",
        "acceleration_m_s2": "3",
        "time_s": "4",
    }
    fields.update(updates)
    return SemanticIR(**fields)


def test_semantic_request_compiles_and_executes_with_exact_results():
    plan = compile_request(make_request())

    assert plan.semantic_ir.numeric_mode == NumericMode.EXACT
    assert plan.execution_ir.steps
    assert plan.machine_ir.profile_id == DEFAULT_MACHINE_CAPABILITIES.profile_id
    result = execute_plan(plan)

    assert result.result.displacement_m == "32"
    assert result.result.final_velocity_m_s == "14"
    assert result.verification.status == "passed"
    assert [event.layer for event in result.trace] == [
        "semantic_ir",
        "execution_ir",
        "machine_ir",
        "runtime",
        "verification",
    ]


def test_exact_fraction_survives_semantic_and_runtime_layers():
    plan = compile_request(
        make_request(
            initial_velocity_m_s="1/2",
            acceleration_m_s2="3/2",
            time_s="2",
        )
    )

    result = execute_plan(plan)

    assert result.result.displacement_m == "4"
    assert result.result.final_velocity_m_s == "7/2"


def test_semantic_ir_rejects_invalid_rational_inputs():
    with pytest.raises(ValidationError, match="exact rational numbers"):
        make_request(time_s="not-a-number")


def test_backend_rejects_unsupported_approximate_mode():
    request = make_request(numeric_mode=NumericMode.APPROXIMATE)
    capabilities = MachineCapabilities(
        profile_id=DEFAULT_MACHINE_CAPABILITIES.profile_id,
        supported_operations=DEFAULT_MACHINE_CAPABILITIES.supported_operations,
        supported_numeric_modes=frozenset(
            {NumericMode.EXACT, NumericMode.APPROXIMATE}
        ),
    )

    with pytest.raises(CapabilityError, match="not implemented"):
        compile_request(request, capabilities)


def test_backend_rejects_unsupported_operation():
    capabilities = MachineCapabilities(
        profile_id=DEFAULT_MACHINE_CAPABILITIES.profile_id,
        supported_operations=frozenset(),
        supported_numeric_modes=frozenset({NumericMode.EXACT}),
    )

    with pytest.raises(CapabilityError, match="does not support"):
        compile_request(make_request(), capabilities)


def test_planner_rejects_unregistered_machine_profiles():
    capabilities = MachineCapabilities(
        profile_id="unregistered-device",
        supported_operations=frozenset({"solve_constant_acceleration"}),
        supported_numeric_modes=frozenset({NumericMode.EXACT}),
    )

    with pytest.raises(CapabilityError, match="no registered executor"):
        compile_request(make_request(), capabilities)


def test_runtime_rejects_modified_machine_ir():
    plan = compile_request(make_request())
    altered_machine_ir = plan.machine_ir.model_copy(
        update={
            "instructions": (
                MachineInstruction.RETURN_VERIFIED_RESULT,
            )
        }
    )
    altered_plan = plan.model_copy(update={"machine_ir": altered_machine_ir})

    with pytest.raises(ValueError, match="Machine IR does not match"):
        execute_plan(altered_plan)
