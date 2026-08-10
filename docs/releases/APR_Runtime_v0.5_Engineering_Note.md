# APR Runtime v0.5 — Event-Native + Targeted Subtree Runtime

**版本：v0.5**  
**日期：2026-08-08**

## 1. 版本目標

v0.4 的主要 Fast Loop 仍是：

```text
poll -> snapshot -> compare -> event
```

v0.5 新增真正的 event-native 路線：

```text
native event
 -> identify affected target
 -> targeted subtree/window read
 -> verify change
 -> Evidence
 -> World State
```

最重要的語義是：

$$
\boxed{Event \neq Evidence \neq WorldState}
$$

Event 只表示「某個位置值得重新檢查」，不能直接成為真實狀態。

---

## 2. Browser CDP Native Events

`BrowserCDPEventSource` 訂閱：

```text
DOM.attributeModified
DOM.attributeRemoved
DOM.characterDataModified
DOM.childNodeCountUpdated
DOM.childNodeInserted
DOM.childNodeRemoved
DOM.documentUpdated
Accessibility.nodesUpdated
Accessibility.loadComplete
```

啟動時：

```text
DOM.enable
DOM.getDocument(depth=N)
```

先建立 bounded known-node set，再接收 CDP events。

---

## 3. Document Generation / Node Lifecycle

`DOM.documentUpdated` 代表整份 Document 已更新，舊 frontend NodeId 不再可信。

因此 v0.5 加入：

```text
document_generation
```

每次 document update：

```text
generation += 1
```

事件也保存當下 generation。

若：

```text
event_generation != current_generation
```

`TargetedBrowserReader` 不會使用 stale NodeId，而改：

```text
DOM.getDocument()
```

重新 seed。

---

## 4. Targeted Browser Read

若事件指出：

```text
nodeId = 42
```

只讀：

```text
DOM.describeNode(nodeId=42, depth=N)
DOM.getOuterHTML(nodeId=42)
Accessibility.getPartialAXTree(nodeId=42)
```

而不是：

```text
dump full DOM
dump full AX tree
```

因此形成：

$$
\boxed{NativeEvent \rightarrow TargetedSubtree}
$$

若 node 在事件送達後已消失，則 fallback 到 document reseed。

---

## 5. Persistent Event Ledger

新增：

```text
events.sqlite3
```

欄位：

```text
id
kind
source
target
significance
timestamp
node_id
backend_node_id
hwnd
payload
```

Ledger 是 append-only event history，不是 World State。

支援：

```text
recent()
kind filter
target filter
minimum significance
compaction
```

舊低價值事件可以刪除，但高 significance events 可長期保留。

---

## 6. Event → Verification → Evidence

新增 `EventNativeRuntime`：

```text
NativeEvent
 -> EventLedger
 -> Targeted Reader
 -> write_verified_state()
 -> Evidence
 -> WorldState
```

Evidence metadata 會保留：

```text
native_event_id
native_event_kind
```

所以之後能追蹤：

> 這一個 World State 更新，是由哪一個原生事件觸發的？

---

## 7. Windows Native Events

新增 `Win32NativeEventSource`，使用 `SetWinEventHook`。

目前監控：

```text
EVENT_SYSTEM_FOREGROUND
EVENT_OBJECT_FOCUS
EVENT_OBJECT_SHOW
EVENT_OBJECT_HIDE
```

事件包含：

```text
HWND
object_id
child_id
thread
time
```

APR 可由 HWND 直接進：

```text
PywinautoTargetedUIAReader.read_hwnd(hwnd)
```

---

## 8. Targeted UIA Reader

v0.2 的 UIA 是 bounded foreground snapshot。

v0.5 增加 HWND targeted path：

```text
WinEvent(hwnd)
 -> target exact window
 -> root
 -> bounded descendants
```

所以 Windows 桌面也形成：

$$
\boxed{Event \rightarrow TargetedSubtree}
$$

---

## 9. Polling 保留為 Fallback

v0.5 不刪除 v0.2/v0.4 polling。

原因：

- native event 可能遺失；
- event 可能重複；
- UI provider 可能不完整；
- browser node 可能在 read 前消失；
- UIA event 不一定代表實際 state change；
- event stream 可能斷線。

因此正式策略是：

$$
\boxed{NativeEvent + PeriodicRefresh}
$$

Polling 的角色從主資訊來源改成：

```text
recovery
consistency check
periodic refresh
```

---

## 10. 成本模型變化

v0.2：

$$
C_t \propto PollRate
$$

v0.5 理想情況：

$$
C_t \propto EventRate + RefreshRate
$$

而不是：

$$
C_t \propto RawFrameRate
$$

這更接近 APR 最初的持續感知目標。

---

## 11. Correctness 條件

v0.5 的核心 correctness requirements：

1. Event 不直接改寫 World State；
2. targeted verification 後才產生 Evidence；
3. `documentUpdated` 後不得使用舊 NodeId；
4. node 消失時必須 graceful fallback；
5. Event Ledger 與 Evidence Archive 分離；
6. native sources 關閉時不得破壞使用者外部應用；
7. polling 仍可作 recovery path。

---

## 12. 下一版 v0.6

建議進入：

# Unified Event Scheduler + Backpressure + Retention

需要統一：

```text
Browser events
Windows events
Screen delta events
Semantic events
```

並加入：

```text
deduplication
coalescing
priority queue
burst backpressure
async execution
periodic refresh
retention policy
current/historical query routing
```

也就是從「多個 event source」推進成真正 Runtime Scheduler。
