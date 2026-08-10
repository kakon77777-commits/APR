import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import (
    EventFactDependencyMap,
    EventFactRule,
    EventLedger,
    Evidence,
    EvidenceStore,
    Modality,
    NativeEvent,
    NeedRefreshPlanner,
    PerceptualNeed,
    PerceptualNeedGraph,
    TaskAwareEventRouter,
    TaskAwarePerceptionRuntime,
    UnifiedEventRuntime,
    UnifiedEventScheduler,
    WorldState,
)


def main():
    store = EvidenceStore()
    world = WorldState(store)
    needs = PerceptualNeedGraph()
    needs.add_need(
        PerceptualNeed(
            id="download_failure",
            fact_key="download.failed",
            description="Know whether the current download failed.",
            min_confidence=0.90,
            risk=0.95,
        )
    )
    needs.add_need(
        PerceptualNeed(
            id="browser_url",
            fact_key="browser.url",
            min_confidence=0.90,
            risk=0.10,
        )
    )

    # URL is already known; download.failed is unknown.
    world.revise(
        Evidence(
            "browser.url",
            "https://example.test/download",
            Modality.STRUCTURED,
            "browser_native_state",
            0.99,
            0.1,
        )
    )

    dependencies = EventFactDependencyMap(
        [
            EventFactRule(
                ("download.failed",),
                kind_prefix="browser_dom_changed",
                weight=1.0,
            ),
            EventFactRule(
                ("browser.url",),
                kind_prefix="browser_navigation",
                weight=1.0,
            ),
        ]
    )

    router = TaskAwareEventRouter(world, needs, dependencies)

    with tempfile.TemporaryDirectory() as tmp:
        ledger = EventLedger(Path(tmp) / "events.sqlite3")
        scheduler = UnifiedEventScheduler(ledger=ledger)
        runtime = TaskAwarePerceptionRuntime(
            UnifiedEventRuntime(scheduler),
            router,
            NeedRefreshPlanner(world, needs),
        )

        # Larger raw event, but unrelated to the unsatisfied critical fact.
        unrelated = NativeEvent(
            kind="pointer.motion",
            source="screen_delta",
            target="desktop.pointer",
            significance=0.55,
        )

        # Smaller raw event, but it may change download.failed.
        relevant = NativeEvent(
            kind="browser_dom_changed",
            source="browser_native_state",
            target="browser.dom",
            significance=0.35,
        )

        report = runtime.submit_native(
            [unrelated, relevant],
            persist=True,
            now=100.0,
        )

        print("Task-aware ingest:", report)
        print("\nScheduler order:")
        for item in scheduler.pending(now=100.1):
            ev = item.event
            print(
                f"  {ev.kind:22s} "
                f"raw={ev.payload.get('apr_original_significance', ev.significance):.3f} "
                f"routed={ev.significance:.3f} "
                f"need={ev.payload.get('apr_need_relevance', 0):.3f}"
            )

        print("\nNeed frontier before evidence:")
        for a in needs.frontier(world):
            print(" ", a.fact_key, a.state.value, f"urgency={a.urgency:.3f}")

        # Need-driven refresh can also create work without a new sensor event.
        refresh_report = runtime.emit_need_refreshes(now=101.0, persist=True)
        print("\nNeed refresh ingest:", refresh_report)

        # Semantic/structured evidence satisfies the critical need.
        world.configure_fact("download.failed", volatile=True, ttl=10.0)
        world.revise(
            Evidence(
                "download.failed",
                True,
                Modality.STRUCTURED,
                "browser_download_state",
                0.98,
                0.2,
            )
        )

        print("\nNeed graph ready:", needs.ready(world))
        print("Remaining frontier:", needs.frontier(world))

        print("\nRaw Event Ledger significance values:")
        for row in ledger.recent(limit=10):
            print(" ", row["kind"], row["significance"])


if __name__ == "__main__":
    main()
