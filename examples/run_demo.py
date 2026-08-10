import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    APRRuntime,
    Budget,
    ChannelProfile,
    Evidence,
    EvidenceStore,
    Goal,
    Modality,
    ObservationSpec,
    PolicyController,
    SimulatorAdapter,
    WorldState,
)


def print_step(title, runtime, action, evidence=None):
    print(f"\n=== {title} ===")
    print(
        "action:",
        action.mode.value,
        "| modality:",
        getattr(action.modality, "value", None),
    )
    print("reason:", action.reason)
    if evidence:
        print(
            "evidence:",
            evidence.observed_value,
            f"(confidence={evidence.confidence:.3f})",
        )
    print("world:", runtime.world.snapshot())
    print(
        "budget:",
        {"spent": runtime.budget.spent, "remaining": runtime.budget.remaining},
    )


def main():
    store = EvidenceStore()
    world = WorldState(store)

    sensor = SimulatorAdapter(
        modality=Modality.SENSOR,
        source="door_sensor",
        reliability=0.99,
        base_cost=1.0,
        world={
            "door.state": ObservationSpec("open", confidence=0.99, pointer="sensor://door/4"),
        },
    )

    vision = SimulatorAdapter(
        modality=Modality.VISION,
        source="camera_vlm",
        reliability=0.94,
        base_cost=5.0,
        world={
            "door.state": ObservationSpec("open", confidence=0.96, pointer="frame://100"),
        },
    )

    profiles = {
        Modality.SENSOR: ChannelProfile(
            Modality.SENSOR, reliability=0.99, cost=1.0, directness=1.0
        ),
        Modality.VISION: ChannelProfile(
            Modality.VISION, reliability=0.94, cost=5.0, directness=0.65
        ),
    }

    runtime = APRRuntime(
        world=world,
        evidence_store=store,
        policy=PolicyController(profiles),
        budget=Budget(units=30.0),
        adapters={Modality.SENSOR: sensor, Modality.VISION: vision},
    )

    # 1) Unknown fact: policy acquires evidence.
    goal = Goal(
        "door.state",
        risk=0.3,
        min_confidence=0.85,
        description="Know whether the door is open.",
    )
    action, evidence = runtime.step(goal)
    print_step("1. Unknown -> acquire evidence", runtime, action, evidence)

    # 2) Fresh high-confidence fact: no new perception.
    action, evidence = runtime.step(goal)
    print_step("2. Fresh fact -> NO_OBSERVATION", runtime, action, evidence)

    # 3) Force state to become stale: policy should inspect it.
    fact = runtime.world.get("door.state")
    fact.ttl = 0.01
    fact.last_verified = time.time() - 1.0

    action, evidence = runtime.step(goal)
    print_step("3. Stale fact -> INSPECT", runtime, action, evidence)

    # 4) Inject conflicting visual evidence.
    conflicting = Evidence(
        claim_key="door.state",
        observed_value="closed",
        modality=Modality.VISION,
        source="camera_vlm",
        confidence=0.94,
        cost=5.0,
        pointer="frame://101",
    )
    runtime.world.revise(conflicting)
    print("\nInjected visual contradiction:", runtime.world.snapshot()["door.state"])

    # 5) Make sensor unavailable so a targeted revisit uses vision.
    runtime.policy.channels[Modality.SENSOR].available = False
    vision.set_observation(
        "door.state",
        ObservationSpec(
            "open", confidence=0.98, pointer="frame://102", metadata={"high_res": True}
        ),
    )

    high_risk_goal = Goal(
        "door.state",
        risk=0.9,
        min_confidence=0.9,
        description="Verify door state before crossing.",
    )
    action, evidence = runtime.step(high_risk_goal)
    print_step("4. Contradicted -> targeted REVISIT", runtime, action, evidence)

    print("\nEvidence provenance:")
    for ev in store.for_claim("door.state"):
        print(
            f"- {ev.id[:8]} | {ev.modality.value:10s} | "
            f"value={ev.observed_value!r} | conf={ev.confidence:.3f} | {ev.pointer}"
        )


if __name__ == "__main__":
    main()
