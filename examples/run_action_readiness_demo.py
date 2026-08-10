import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    ActionGatePolicy,
    ActionReadinessGate,
    ActionReadinessRuntime,
    ActionSpec,
    Evidence,
    EvidenceStore,
    FactRequirement,
    Modality,
    WorldState,
)


def add_evidence(world, key, value, modality, source, confidence):
    evidence = Evidence(
        claim_key=key,
        observed_value=value,
        modality=modality,
        source=source,
        confidence=confidence,
        cost=0.0,
        metadata={"independence_group": f"{modality.value}:{source}"},
    )
    world.revise(evidence)
    return evidence


def main():
    store = EvidenceStore()
    world = WorldState(store)

    action = ActionSpec(
        id="send_payment",
        name="Send payment",
        risk=0.92,
        requirements=(
            FactRequirement(
                "payee.identity",
                min_confidence=0.95,
                max_age=60,
                min_independent_evidence=2,
                description="Payee identity must be verified.",
            ),
            FactRequirement(
                "invoice.total",
                min_confidence=0.95,
                max_age=120,
                min_independent_evidence=2,
            ),
            FactRequirement(
                "payment.confirmed",
                min_confidence=0.99,
                allowed_values=(True,),
                min_independent_evidence=1,
                inherit_risk_floor=False,
            ),
        ),
    )

    gate = ActionReadinessGate(
        world,
        store,
        policy=ActionGatePolicy(
            high_risk_min_independent_evidence=2,
            critical_min_confidence=0.95,
        ),
    )
    runtime = ActionReadinessRuntime(gate)
    runtime.register(action)
    world.configure_fact("payment.confirmed", volatile=True, ttl=30)

    print("1) Nothing verified:")
    print(runtime.decision("send_payment").kind.value)

    # Two independent sources for payee identity.
    add_evidence(
        world,
        "payee.identity",
        "ACME",
        Modality.STRUCTURED,
        "invoice_api",
        0.99,
    )
    add_evidence(
        world,
        "payee.identity",
        "ACME",
        Modality.VISION,
        "invoice_vlm",
        0.97,
    )

    # Only one source for total -> still VERIFY under critical policy.
    add_evidence(
        world,
        "invoice.total",
        1250.0,
        Modality.STRUCTURED,
        "invoice_api",
        0.99,
    )

    add_evidence(
        world,
        "payment.confirmed",
        True,
        Modality.STRUCTURED,
        "user_confirmation",
        0.99,
    )

    decision = runtime.decision("send_payment")
    print("\n2) One critical fact still under-evidenced:")
    print(decision.kind.value)
    for item in decision.assessments:
        print(
            " ",
            item.fact_key,
            item.state.value,
            item.reason,
            f"independent={item.evidence.independent_groups}",
        )

    add_evidence(
        world,
        "invoice.total",
        1250.0,
        Modality.VISION,
        "invoice_vlm",
        0.96,
    )

    decision = runtime.decision("send_payment")
    print("\n3) All evidence preconditions satisfied:")
    print(decision.kind.value)

    # Semantic authorization precondition becomes false.
    add_evidence(
        world,
        "payment.confirmed",
        False,
        Modality.STRUCTURED,
        "user_confirmation",
        0.99,
    )

    decision = runtime.decision("send_payment")
    print("\n4) Confirmation is false:")
    print(decision.kind.value, decision.blocking_facts)


if __name__ == "__main__":
    main()
