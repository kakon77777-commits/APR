import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from apr_runtime import NativeEvent, SchedulerConfig, UnifiedEventScheduler


def main():
    scheduler = UnifiedEventScheduler(config=SchedulerConfig(max_queue=5))

    for i in range(20):
        scheduler.ingest(
            NativeEvent(
                kind="DOM.characterDataModified",
                source="browser_cdp",
                target="browser.dom.node:42",
                significance=0.35,
                node_id=42,
                payload={"text_version": i},
            ),
            now=100 + i * 0.005,
            persist=False,
        )

    for i in range(5):
        scheduler.ingest(
            NativeEvent(
                kind="win.focus",
                source="win32_winevent",
                target=f"window:{100 + i}",
                significance=0.20,
                hwnd=100 + i,
            ),
            now=101 + i * 0.01,
            persist=False,
        )

    scheduler.ingest(
        NativeEvent(
            kind="semantic.warning",
            source="semantic",
            target="desktop.warning",
            significance=0.98,
            payload={"severity": "critical"},
        ),
        now=102,
        persist=False,
    )

    print("metrics:", scheduler.metrics)
    print("pending:", scheduler.pending_count())
    print("\nDispatch order:")
    for item in scheduler.pop_batch(max_items=10, now=102):
        print(
            f"  priority={item.effective_priority(102, scheduler.config):.3f}",
            f"kind={item.event.kind:28s}",
            f"target={item.event.target:24s}",
            f"coalesced={item.coalesced_count}",
        )


if __name__ == "__main__":
    main()
