import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    ActionGatePolicy,
    ActionOutcomeRuntime,
    ActionOutcomeSpec,
    ActionOutcomeVerifier,
    ActionReadinessGate,
    ActionReadinessRuntime,
    ActionSpec,
    Evidence,
    EvidenceStore,
    ExecutionLedger,
    FactRequirement,
    Modality,
    PostconditionRequirement,
    WorldState,
)


def add(world, key, value, source, confidence=0.99):
    ev = Evidence(
        claim_key=key,
        observed_value=value,
        modality=Modality.STRUCTURED,
        source=source,
        confidence=confidence,
        cost=0.0,
    )
    world.revise(ev)
    return ev


def main():
    store = EvidenceStore()
    world = WorldState(store)

    # Preconditions.
    world.configure_fact("door.unlocked", volatile=True, ttl=30)
    add(world, "door.unlocked", True, "lock_sensor")

    action = ActionSpec(
        id="open_door",
        name="Open door",
        risk=0.4,
        requirements=(
            FactRequirement(
                "door.unlocked",
                allowed_values=(True,),
                min_confidence=0.9,
            ),
        ),
    )

    readiness_gate = ActionReadinessGate(
        world,
        store,
        policy=ActionGatePolicy(
            high_risk_min_independent_evidence=1,
        ),
    )
    readiness = ActionReadinessRuntime(readiness_gate)
    readiness.register(action)

    outcome_spec = ActionOutcomeSpec(
        action_id="open_door",
        postconditions=(
            PostconditionRequirement(
                "door.state",
                expected_values=("open",),
                min_confidence=0.9,
                must_change_from_pre_state=True,
            ),
        ),
        verification_timeout=0.5,
        max_retries=1,
        retry_safe=True,
    )

    verifier = ActionOutcomeVerifier(world, store)

    with tempfile.TemporaryDirectory() as tmp:
        ledger = ExecutionLedger(Path(tmp) / "executions.sqlite3")
        runtime = ActionOutcomeRuntime(
            readiness,
            verifier,
            ledger,
        )
        runtime.register_outcome(outcome_spec)

        # Existing pre-action state.
        world.configure_fact("door.state", volatile=True, ttl=30)
        add(world, "door.state", "closed", "door_sensor")

        result = runtime.execute(
            "open_door",
            lambda: {"command": "motor_open"},
            auto_request_verification=False,
        )
        print("executed:", result.executed, result.execution_id)

        # The old CLOSED evidence cannot prove either success or failure yet.
        decision = runtime.verify(
            result.execution_id,
            auto_request_more_evidence=False,
        )
        print("after execution, before observation:", decision.kind.value)

        # Post-action sensor confirms OPEN.
        time.sleep(0.001)
        add(world, "door.state", "open", "door_sensor_post")

        decision = runtime.verify(
            result.execution_id,
            auto_request_more_evidence=False,
        )
        print("after post-action evidence:", decision.kind.value)

        receipt = ledger.get(result.execution_id)
        print("receipt status:", receipt.status)
        print("evidence links:", ledger.evidence_links(result.execution_id))


if __name__ == "__main__":
    main()
