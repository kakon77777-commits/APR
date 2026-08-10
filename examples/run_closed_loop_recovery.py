import sys
import tempfile
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
    ClosedLoopRecoveryOrchestrator,
    Evidence,
    EvidenceStore,
    ExecutionLedger,
    FactRequirement,
    Modality,
    PartialSuccessPolicy,
    PostconditionRequirement,
    RecoveryPolicy,
    RetryMode,
    ReversibilityClass,
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
    world.configure_fact("door.unlocked", volatile=True, ttl=30)
    world.configure_fact("door.state", volatile=True, ttl=30)

    add(world, "door.unlocked", True, "lock_sensor")
    add(world, "door.state", "closed", "door_sensor")

    open_action = ActionSpec(
        "open_door",
        "Open door",
        0.3,
        (
            FactRequirement(
                "door.unlocked",
                allowed_values=(True,),
                inherit_risk_floor=False,
            ),
        ),
    )
    close_action = ActionSpec(
        "close_door",
        "Close door",
        0.3,
        (),
    )

    gate = ActionReadinessGate(
        world,
        store,
        policy=ActionGatePolicy(
            high_risk_min_independent_evidence=1,
        ),
    )
    readiness = ActionReadinessRuntime(gate)
    readiness.register(open_action)
    readiness.register(close_action)

    verifier = ActionOutcomeVerifier(world, store)

    with tempfile.TemporaryDirectory() as tmp:
        ledger = ExecutionLedger(Path(tmp) / "executions.sqlite3")
        outcomes = ActionOutcomeRuntime(readiness, verifier, ledger)

        orchestrator = ClosedLoopRecoveryOrchestrator(
            readiness,
            outcomes,
            ledger,
        )

        attempt = {"count": 0}

        def open_handler(ctx):
            attempt["count"] += 1
            return {"motor_command": "open", "attempt": attempt["count"]}

        def observe_open(execution_id, ctx):
            # First attempt fails; second succeeds.
            value = "closed" if attempt["count"] == 1 else "open"
            add(world, "door.state", value, f"post_sensor_{attempt['count']}")

        def close_handler(ctx):
            return {"motor_command": "close"}

        def observe_close(execution_id, ctx):
            add(world, "door.state", "closed", "rollback_sensor")

        orchestrator.register(
            open_action,
            ActionOutcomeSpec(
                "open_door",
                (
                    PostconditionRequirement(
                        "door.state",
                        expected_values=("open",),
                        must_change_from_pre_state=True,
                    ),
                ),
                max_retries=1,
                retry_safe=True,
                rollback_action_id="close_door",
            ),
            open_handler,
            recovery=RecoveryPolicy(
                reversibility=ReversibilityClass.COMPENSATABLE,
                retry_mode=RetryMode.IDEMPOTENT,
                max_attempts=2,
                rollback_action_id="close_door",
                partial_success=PartialSuccessPolicy.REPLAN,
            ),
            observer=observe_open,
        )

        orchestrator.register(
            close_action,
            ActionOutcomeSpec(
                "close_door",
                (
                    PostconditionRequirement(
                        "door.state",
                        expected_values=("closed",),
                    ),
                ),
            ),
            close_handler,
            recovery=RecoveryPolicy(
                reversibility=ReversibilityClass.REVERSIBLE,
                retry_mode=RetryMode.NEVER,
                max_attempts=1,
            ),
            observer=observe_close,
        )

        result = orchestrator.run("open_door")
        print("status:", result.status.value)
        print("final execution:", result.final_execution_id)
        print("door:", world.get("door.state").value)

        trace_json = result.trace.export_json(Path(tmp) / "trace.json")
        trace_md = result.trace.export_markdown(Path(tmp) / "trace.md")
        print("trace json:", trace_json)
        print("trace md:", trace_md)

        print("\nsteps:")
        for step in result.trace.steps:
            print(
                step.kind,
                step.action_id,
                step.execution_id,
                step.decision,
                step.detail,
            )


if __name__ == "__main__":
    main()
