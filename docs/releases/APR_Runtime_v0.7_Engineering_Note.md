# APR Runtime v0.7 — Perceptual Need Graph + Task-Aware Event Routing

**日期：2026-08-09**

## 1. v0.6 → v0.7

v0.6 解決：

```text
事件很多時，哪些工作先處理？
```

但它主要根據：

```text
event significance
source weight
age
queue pressure
```

v0.7 再加入一個更高階問題：

> **這個事件是否影響我現在完成任務真正需要依賴的資訊？**

所以排程變成：

$$
Priority
=
f(
EventSignificance,
TaskNeed,
FactRisk,
FactFreshness,
Uncertainty,
Age
)
$$

---

## 2. Perceptual Need Graph

新增：

```text
PerceptualNeedGraph
```

每個 need 定義：

```text
id
fact_key
min_confidence
risk
weight
mandatory
dependencies
```

例如：

```text
Goal: submit payment

needs:
- invoice.total
- payee.identity
- account.balance
- confirmation.dialog.visible
```

若某個 need 依賴另一 need：

```text
payment.safe
  -> payee.identity
  -> invoice.total
```

前置資訊不足時，parent need 為 `BLOCKED`。

---

## 3. Need state

Need 不重新發明世界狀態，而是把 World State 投影成任務需求：

```text
SATISFIED
UNKNOWN
STALE
UNCERTAIN
CONTRADICTED
BLOCKED
```

因此：

$$
WorldState
\rightarrow
TaskInformationNeed
$$

---

## 4. Event → Fact Dependency

新增：

```text
EventFactDependencyMap
```

例如：

```text
browser_dom_changed
 -> download.failed
 -> confirmation.dialog.visible
```

或：

```text
win.foreground
 -> desktop.foreground.title
```

事件也可以直接在 payload 中帶：

```text
affected_facts
```

這讓 Scheduler 能知道：

> event 不是只「大不大」，而是會不會破壞目前任務依賴的 belief。

---

## 5. Task-aware significance

原始 event：

$$
s_e
$$

task need relevance：

$$
r_n
$$

若相關：

$$
s'_e
=
s_e+(1-s_e)\alpha r_n
$$

若與目前 task 無關，且不是 critical event：

$$
s'_e=\beta s_e,
\quad \beta<1
$$

因此：

```text
small but task-critical event
```

可以超過：

```text
large but irrelevant event
```

---

## 6. Need-driven Refresh

新增：

```text
NeedRefreshPlanner
```

如果 required fact：

```text
UNKNOWN / STALE / UNCERTAIN / CONTRADICTED
```

會發出：

```text
apr.need.refresh
```

事件。

高風險 need 即使 raw world event 很小，也可直接達到 critical scheduler priority。

這意味著 APR 第一次能由：

```text
缺什麼資訊
```

主動產生感知工作，而不是只能被外部事件觸發。

---

## 7. Query Router

v0.7 正式區分：

```text
CURRENT
HISTORICAL
```

Current query：

```text
fresh state sufficient -> ANSWER_FROM_STATE
otherwise -> REFRESH_CURRENT
```

Historical query：

```text
archived revisitable evidence exists
 -> HISTORICAL_REVISIT
```

因此 v0.4 的 Historical Revisit 開始被真正放進 Runtime decision layer。

---

## 8. Task-aware ingress

新增：

```text
TaskAwarePerceptionRuntime
```

現在 event 進 Scheduler 前先：

```text
raw event
 -> affected facts
 -> current need urgency
 -> reweight significance
 -> UnifiedEventScheduler
```

v0.6 的 scheduler 不需要重寫，只在 ingress 前多一層 task-conditioned policy。

---

## 9. 與近期研究的關係

2026 的 embodied-agent 研究已明確顯示 task-aligned scene/state representation、belief-guided exploratory inference 與 task-state alignment 的重要性。APR v0.7 不主張 task graph 或 belief-guided action 本身為新，而是把「任務需要哪些 facts」直接接到感知事件排程與刷新策略。

其工程命題是：

$$
\boxed{
EventPriority
\neq
EventMagnitudeOnly
}
$$

而是：

$$
\boxed{
EventPriority
=
EventValueForCurrentInformationNeeds
}
$$

---

## 10. 下一版 v0.8

建議進入：

```text
Perceptual Need Graph
 -> planner/tool preconditions
 -> action readiness gates
 -> evidence requirements
 -> risk-adaptive verification
```

也就是把 APR 從 task-aware perception 再接到真正的 Action Planner：

> **哪些資訊未被證明，就禁止哪些行動。**
