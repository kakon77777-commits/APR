# APR Runtime v0.8 — Action Readiness Gates + Evidence Preconditions

**日期：2026-08-09**

## 1. v0.7 → v0.8

v0.7 回答：

> 任務現在需要知道哪些 facts？

v0.8 再進一步：

> 在執行 action 之前，哪些 facts 必須已經被可靠證明？

因此形成：

$$
\boxed{
Action
\rightarrow
EvidencePreconditions
\rightarrow
ALLOW/VERIFY/BLOCK
}
$$

---

## 2. 三態 Action Gate

### ALLOW

所有 preconditions：

- 值符合 action 語義；
- confidence 足夠；
- freshness 足夠；
- evidence diversity 足夠；
- 沒有 blocking contradiction。

### VERIFY

目前不能安全執行，但資訊缺口可以透過更多感知補足。

例如：

```text
payee.identity confidence = 0.82
required = 0.95
```

或：

```text
robot.pose age = 8s
max_age_for_action = 2s
```

### BLOCK

不是「多看一下就好」，而是目前語義條件本身不允許執行。

例如：

```text
user.confirmed = false
required allowed_values = [true]
```

或 blocking contradiction。

---

## 3. FactRequirement

每個 action 可宣告：

```text
fact_key
min_confidence
max_age
allowed_values
forbidden_values
min_independent_evidence
min_modalities
min_evidence_confidence
require_revisitable_asset
contradiction_blocks
```

因此 action 不再只依賴：

```text
planner says do it
```

而是依賴明確可審計的 evidence contract。

---

## 4. 高風險 Evidence Floor

Runtime-wide policy 可以設定：

```text
high_risk_threshold
critical_risk_threshold
high_risk_min_confidence
critical_min_confidence
high_risk_min_independent_evidence
```

例如付款：

```text
risk = 0.92
```

即使 individual requirement 只寫：

```text
min_confidence = 0.85
```

global policy 仍可提升到：

```text
0.95
```

---

## 5. Independent Evidence

v0.8 不把同一張 archived image 的重讀當成新的獨立證據。

若：

```text
E1 -> frame_100.png
E2 -> historical revisit of frame_100.png
```

則：

$$
IndependentEvidence(E1,E2)=1
$$

不是 2。

預設 independence group：

```text
modality:source
```

adapter 也可顯式提供：

```text
metadata.independence_group
```

---

## 6. Action Readiness → Need Graph

Action registration 會將 requirement 加入：

```text
PerceptualNeedGraph
```

例如：

```text
action::send_payment::payee.identity
action::send_payment::invoice.total
```

所以 Action Runtime 和 Perception Runtime 共用同一資訊需求層。

---

## 7. VERIFY → Perception Work

如果 gate 回傳：

```text
VERIFY
```

Runtime 可產生：

```text
apr.action.verify
```

NativeEvent。

Event payload 包含：

```text
action_id
action_risk
fact_key
required_confidence
current_confidence
max_age
affected_facts
reason
```

接著沿用 v0.7：

```text
TaskAwareEventRouter
 -> Scheduler
 -> targeted perception
```

所以 Planner 不必自己手動管理「再看一下」。

---

## 8. Guarded Execution

新增：

```python
runtime.execute(action, func)
```

只有：

```text
ALLOW
```

才真的呼叫 `func()`。

VERIFY：

```text
不執行
+ 可自動排 verification work
```

BLOCK：

```text
不執行
```

這讓 action gating 成為 execution boundary，而不只是 advisory message。

---

## 9. Evidence vs Semantic Preconditions

v0.8 明確區分：

### Epistemic condition

```text
我知不知道？
證據夠不夠？
狀態新不新？
```

不足 → VERIFY。

### Semantic/action condition

```text
door.open == true ?
user.confirmed == true ?
```

若確認為 false → BLOCK。

因此：

$$
\boxed{
Unknown
\neq
False
}
$$

這是 action safety 很重要的區別。

---

## 10. 與近期研究的位置

2026 年 uncertainty-aware embodied planning 已開始把 latent assumptions、
execution cost、scenario likelihood 與 action selection做結構化；也有
neuro-symbolic planner 使用 deterministic safety ontology 做 execution
gate / repair。APR v0.8 的位置不是宣稱 preconditions 新穎，而是把它
與 APR 已有的：

```text
Persistent World State
Evidence Archive
Need Graph
Task-aware Event Routing
Historical Revisit
```

接成同一 runtime。

---

## 11. 下一版 v0.9

建議進入：

### Action Outcome Verification + Recovery

```text
ALLOW
 -> execute action
 -> expected state transition
 -> observe outcome
 -> verify postconditions
 -> SUCCESS / RETRY / REPLAN / ROLLBACK
```

這會把 action gate 從：

```text
pre-action readiness
```

延伸到：

```text
closed-loop execution verification
```
