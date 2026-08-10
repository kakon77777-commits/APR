import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    APRRuntime,
    Budget,
    ChannelProfile,
    DesktopStructuredAdapter,
    EvidenceStore,
    Goal,
    Modality,
    PolicyController,
    Win32ForegroundWindowSource,
    WorldState,
)


def main():
    store = EvidenceStore()
    world = WorldState(store)

    adapter = DesktopStructuredAdapter(
        Win32ForegroundWindowSource(),
        uia=None,
        reliability=0.99,
        base_cost=0.5,
    )

    policy = PolicyController(
        {
            Modality.STRUCTURED: ChannelProfile(
                modality=Modality.STRUCTURED,
                reliability=0.99,
                cost=0.5,
                directness=1.0,
            )
        }
    )

    runtime = APRRuntime(
        world,
        store,
        policy,
        Budget(10),
        {Modality.STRUCTURED: adapter},
    )

    action, evidence = runtime.step(Goal("desktop.foreground.title", risk=0.1, min_confidence=0.9))
    print("first:", action.mode.value, evidence.observed_value if evidence else None)

    action, evidence = runtime.step(Goal("desktop.foreground.title", risk=0.1, min_confidence=0.9))
    print("second:", action.mode.value, evidence)


if __name__ == "__main__":
    main()
