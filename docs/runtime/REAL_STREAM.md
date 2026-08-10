# APR Runtime v0.2 — Real Stream

## Goal

v0.2 replaces simulated-only inputs with a real desktop Fast Loop while
preserving the model-agnostic control plane.

Implemented real channels:

1. **Screen**
   - `python-mss` capture
   - sampled BGRA frame differencing
   - change ratio / mean delta / bounding box
2. **Windows foreground state**
   - zero-dependency Win32 foreground window title / HWND / PID
3. **Windows Accessibility**
   - bounded `pywinauto` UI Automation snapshot
   - structured digest and element count
4. **Real event stream**
   - polling diffs converted to compact `StreamEvent`
   - foreground change
   - UIA structural change
   - screen change

## Why polling first?

Windows exposes native UI Automation events and WinEvents, and those are a
natural future source for APR. v0.2 deliberately uses polling snapshots first
because it is simpler to test, deterministic, and already validates the APR
architecture:

```text
raw/structured source
  -> cheap monitor
  -> compact delta
  -> significance
  -> escalation candidate
```

A native `SetWinEventHook` adapter can replace the polling source later without
changing the World State or policy interfaces.

## Windows install

```bash
pip install -e ".[desktop]"
```

## Real desktop demo

```bash
python examples/run_real_desktop.py
```

No screenshot is sent to a cloud model.

## Structured goal demo

```bash
python examples/run_structured_desktop_goal.py
```

This asks APR for `desktop.foreground.title`.

First call:

```text
UNKNOWN -> structured observation
```

Second call:

```text
KNOWN + fresh -> NO_OBSERVATION
```

That is the first real-world verification of the APR principle:

```text
Available information != information that must be repeatedly processed
```

## UI Automation scope

The UI Automation snapshot is intentionally bounded (`max_elements`) instead
of serializing the entire desktop tree. The digest acts as a structured change
signal. A future slow-loop adapter can inspect a selected subtree when the
digest changes.

## v0.2 known limits

- UIA is Windows-only.
- Browser-specific DOM via CDP/Playwright is not yet implemented.
- Native WinEvent hooks are not yet implemented.
- Screen delta is low-level; it does not claim semantic change detection.
- No VLM is invoked in the Fast Loop.
- UIA browser visibility depends on the application's accessibility support.

## Next version

v0.3 should add:

- evidence archive (SQLite + optional frame crops);
- semantic inspection adapter (local/cloud VLM);
- ROI escalation from frame-delta bbox;
- browser/CDP structured DOM adapter;
- optional native WinEvent source.
