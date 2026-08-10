# APR Runtime v0.6 — Unified Event Scheduler + Backpressure + Retention

**日期：2026-08-09**

## 1. v0.5 → v0.6

v0.5 已能做到：

```text
native event -> targeted read -> verified evidence
```

但長時間常駐後會出現第二個問題：

> 如果事件本身太多，誰決定先處理哪一個？

v0.6 新增：

```text
Browser CDP ─┐
WinEvent     ├─> UnifiedEventScheduler
ScreenDelta  ┤      ├─ dedup
Semantic     ┘      ├─ coalescing
                    ├─ priority
                    ├─ backpressure
                    ├─ aging
                    └─ periodic refresh
                           ↓
                    AsyncEventExecutor
                           ↓
                     targeted handlers
```

## 2. 事件不是 FIFO 工作列

同一 DOM node 在短時間內可能連續發生：

```text
characterDataModified x 30
```

APR 不一定需要 30 次 subtree read。

因此 scheduler 使用：

```text
coalesce_key = source + kind + target + node/window identity
```

在 coalescing window 內壓成一個 `ScheduledEvent`，並保留：

```text
coalesced_count
duplicate_count
source_event_ids
latest payload
max significance
```

## 3. Backpressure

Queue 有固定上限：

$$
|Q|\le B_Q
$$

滿載時：

- critical event 可淘汰低 priority event；
- 高價值 event 必須比最低 pending item 高出 admission margin；
- 低價值新事件直接 drop。

因此事件洪水不會無限擴張記憶體。

## 4. Priority + Aging

單純 significance priority 可能讓低優先事件永遠飢餓。

v0.6 使用：

$$
P_{eff}=P_{base}+\min(P_{age,max},\lambda_{age}\Delta t)
$$

所以等待夠久的低 priority 工作仍有機會被處理。

## 5. Critical admission

若：

$$
Significance\ge\tau_{critical}
$$

即使 queue 已滿，也允許它淘汰最低 priority 工作。

這是 APR-05 的 risk/safety budget 在 event runtime 的實作版本。

## 6. Unified ingress

v0.6 新增 `UnifiedEventRuntime`，把：

```text
NativeEvent
StreamEvent
```

都正規化進同一 scheduler。

因此：

```text
screen_change
DOM.attributeModified
win.focus
semantic.warning
```

不再各有獨立排隊邏輯。

## 7. AsyncEventExecutor

Slow-loop targeted read 可能很慢：

- VLM inspection；
- DOM subtree；
- UIA subtree；
- database / API；
- historical revisit。

v0.6 使用 bounded concurrency：

```text
max_concurrency = N
```

每個 handler 有 timeout，單一工作失敗不會讓整個 batch 停止。

## 8. Periodic Refresh

Native event 仍可能漏失。

Scheduler 可以註冊：

```text
RefreshSpec
```

例如：

```text
browser.page every 10s
foreground window every 5s
critical safety state every 1s
```

到期後產生：

```text
apr.periodic_refresh
```

並進同一 queue。

因此：

$$
\boxed{EventNative + PeriodicRefresh}
$$

仍然是長時間 Runtime 的設計。

## 9. Retention

v0.6 同時處理長時間儲存成長。

Event Ledger：

```text
delete old low-significance events
retain high-significance events
```

Evidence Archive：

```text
delete old low-confidence evidence
BUT protect evidence IDs referenced by current World State
```

若一個 asset 已無任何 evidence row 引用，才刪除實際檔案。

因此：

$$
CurrentBeliefEvidence
$$

不會因 retention policy 被意外清掉。

## 10. 版本里程碑

```text
v0.1 belief control
v0.2 real stream
v0.3 semantic evidence
v0.4 historical revisit
v0.5 event-native targeted read
v0.6 event-flow governance
```

v0.6 對應 APR 理論中的：

$$
\boxed{PerceptualBudgetEconomy\rightarrow EventBudgetEconomy}
$$

不只是資訊要選擇性讀，連「哪些資訊需求先被服務」也開始被治理。

## 11. 下一版 v0.7

建議進入 **World-State Refresh + Query Router + Perceptual Need Graph**：

1. current vs historical query classification；
2. required-fact graph；
3. stale fact refresh scheduling；
4. critical fact verification policy；
5. event → fact dependency mapping；
6. query-time evidence retrieval；
7. perceptual need graph integration。

讓 Scheduler 不只看 event priority，而知道：

> 這個事件會影響哪一個正在被任務依賴的 World State fact？
