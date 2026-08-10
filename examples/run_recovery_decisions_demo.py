import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    ActionOutcomeSpec,
    ActionOutcomeVerifier,
    Evidence,
    EvidenceStore,
    Modality,
    PostconditionRequirement,
    WorldState,
)


def observed(world, key, value, source, ts):
    world.configure_fact(key, volatile=True, ttl=60)
    world.revise(Evidence(key, value, Modality.STRUCTURED, source, 0.99, 0.0, timestamp=ts))


def main():
    store = EvidenceStore()
    world = WorldState(store)
    verifier = ActionOutcomeVerifier(world, store)

    t0 = time.time()
    observed(world, "door.state", "closed", "post_sensor", t0 + 0.01)

    retry_spec = ActionOutcomeSpec(
        action_id="open_door",
        postconditions=(PostconditionRequirement("door.state", expected_values=("open",)),),
        max_retries=1,
        retry_safe=True,
    )

    first = verifier.decide(
        retry_spec,
        execution_id="exec-1",
        executed_at=t0,
        pre_state={"door.state": "closed"},
        retry_count=0,
        now=t0 + 0.1,
    )
    second = verifier.decide(
        retry_spec,
        execution_id="exec-2",
        executed_at=t0,
        pre_state={"door.state": "closed"},
        retry_count=1,
        now=t0 + 0.1,
    )

    print("retryable failure, attempt 1:", first.kind.value)
    print("retry budget exhausted:", second.kind.value)

    observed(world, "deployment.healthy", False, "health_check", t0 + 0.02)
    rollback_spec = ActionOutcomeSpec(
        action_id="deploy",
        postconditions=(PostconditionRequirement("deployment.healthy", expected_values=(True,)),),
        rollback_on_failure=True,
        rollback_action_id="rollback_deploy",
    )
    rollback = verifier.decide(
        rollback_spec,
        execution_id="exec-deploy",
        executed_at=t0,
        pre_state={"deployment.healthy": True},
        retry_count=0,
        now=t0 + 0.1,
    )
    print("rollback policy:", rollback.kind.value, rollback.rollback_action_id)


if __name__ == "__main__":
    main()
