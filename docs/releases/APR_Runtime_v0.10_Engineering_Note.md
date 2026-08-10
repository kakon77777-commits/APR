# APR Runtime v0.10 — Closed-Loop Recovery Orchestrator

**日期：2026-08-09**  
**定位：APR Runtime 0.x 第一個工程封頂版本**

## 1. v0.9 → v0.10

v0.9 已能判斷：

```text
SUCCESS / VERIFY / RETRY / REPLAN / ROLLBACK
```

v0.10 讓 Runtime 真正執行 recovery：

```text
Gate
 -> Execute
 -> Observe
 -> Verify
 -> Retry / Compensate
 -> Gate Again
 -> Verify Recovery
```

---

## 2. Rollback 不等於時間倒轉

外部世界、網路服務、實體機器人通常不存在真正 ACID rollback。

所以 APR v0.10 使用：

$$
\boxed{
Rollback = ExplicitCompensatingAction
}
$$

例如：

```text
reserve inventory
 -> compensation: release inventory
```

而不是：

```text
pretend prior external side effects never happened
```

Compensating action 是獨立 ActionSpec：

- 自己要過 readiness gate；
- 自己有 outcome spec；
- 自己要 post-action verification。

---

## 3. Reversibility classification

每個 action 具有：

```text
REVERSIBLE
COMPENSATABLE
IRREVERSIBLE
```

### REVERSIBLE
可安全地回復狀態。

### COMPENSATABLE
不能真正倒轉，但有明確補償 action。

### IRREVERSIBLE
例如某些：

```text
send external message
physical destructive action
non-refundable transfer
irreversible publish
```

Runtime 不會假裝有 rollback。

---

## 4. Retry mode

```text
NEVER
IDEMPOTENT
DEDUPLICATED
```

### NEVER
禁止自動重試。

### IDEMPOTENT
重複執行語義上安全。

### DEDUPLICATED
只有帶 idempotency key 才能重試。

對 IRREVERSIBLE action：

```text
IDEMPOTENT retry
```

不足以成為預設安全證明。

v0.10 要求：

```text
IRREVERSIBLE + automatic retry
 -> DEDUPLICATED + idempotency_key
```

否則：

```text
REPLAN_REQUIRED
```

---

## 5. Retry lineage

每個 retry 都是新的 ExecutionReceipt。

鏈：

```text
execution_1
  ↓ parent_execution_id
execution_2
  ↓
execution_3
```

而不是覆蓋第一次 execution。

因此：

$$
\boxed{
RetryHistory
}
$$

可審計。

---

## 6. Rollback lineage

若：

```text
execution_forward
 -> failure
 -> compensation action
```

compensation receipt 的：

```text
parent_execution_id = execution_forward
```

並且：

```text
metadata.compensates_execution_id
```

可傳入 handler context。

---

## 7. Partial success

如果某些 postconditions 已滿足而其他失敗：

```text
PartialSuccessPolicy
```

可以是：

```text
REPLAN
ACCEPT
COMPENSATE
```

高風險 action 不應預設 ACCEPT。

---

## 8. Timeout / cancellation

v0.10 提供：

```text
RecoveryContext
deadline
cancelled
checkpoint()
```

這是 cooperative cancellation。

Python Runtime 無法安全強制 kill 任意 blocking user function，所以 handler
需要在可能長時間執行的邊界主動呼叫：

```python
ctx.checkpoint()
```

Production adapter 可以把真正 timeout 交給：

```text
HTTP client
subprocess
robot controller
tool RPC
```

本身的 cancellable timeout。

---

## 9. Execution trace

每次 recovery run 都有：

```text
RecoveryTrace
```

可輸出：

```text
JSON
Markdown
```

包含：

```text
readiness
execution
observation
outcome verification
retry decision
rollback decision
partial success
timeout/cancellation
```

所以 APR 可以把完整：

> 為什麼做、做了幾次、為什麼重試、如何補償、最後怎麼判定

交付給人類或其他 Agent 審核。

---

## 10. Closed-loop invariant

v0.10 的完整 invariant：

$$
\boxed{
ActionIntent
\neq
ActionExecution
\neq
ActionOutcome
\neq
RecoveryOutcome
}
$$

每一層都有自己的 evidence boundary。

---

## 11. 與近期工程／研究位置

2026 年 agent runtime governance、self-healing orchestrator 與 embodied capability
rollback 研究都開始把 execution monitoring、bounded recovery、policy gate、
rollback handling 放到獨立 runtime 層。

Saga / compensating transaction 的傳統工程也提醒：

> 已提交的外部 side effect 不能靠想像自動 rollback，必須設計補償操作。

APR v0.10 的位置是將：

```text
Perception
Persistent World State
Evidence
Action Gate
Outcome Verification
Recovery
```

收斂成同一 runtime。

---

## 12. 0.x 封頂

APR Runtime 0.x：

```text
v0.1  Belief Control
v0.2  Real Stream
v0.3  Semantic Evidence
v0.4  Historical Revisit
v0.5  Event-Native Targeted Read
v0.6  Event Flow Governance
v0.7  Task-Aware Need Graph
v0.8  Evidence-Gated Action
v0.9  Outcome Verification
v0.10 Closed-Loop Recovery Orchestration
```

因此 0.x 已完成：

$$
\boxed{
Perceive
\rightarrow
Believe
\rightarrow
Need
\rightarrow
Act
\rightarrow
Verify
\rightarrow
Recover
}
$$

---

## 13. 下一階段

v0.10 後不建議無限追加 0.11、0.12。

下一階段應分成：

### Track A — v1.0 Productization
- async runtime service;
- real VLM/audio adapters;
- persistent config;
- observability dashboard;
- browser/desktop live validation;
- benchmark suite;
- packaging / CLI / service API.

### Track B — APR Benchmark
- event efficiency;
- state consistency;
- task-aware perception;
- action readiness;
- outcome verification;
- recovery success;
- total compute / latency / critical miss.

### Track C — Learned Policy
- learned VOI;
- routing model;
- constrained RL;
- recovery policy learning.

0.x 到此可以工程封頂。
