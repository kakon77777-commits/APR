# APR Runtime v0.9 — Action Outcome Verification + Recovery

**日期：2026-08-09**

## 1. v0.8 → v0.9

v0.8：

```text
Action
 -> preconditions
 -> ALLOW / VERIFY / BLOCK
```

v0.9 補上 action 後半段：

```text
ALLOW
 -> execute
 -> expected transition contract
 -> targeted post-action observation
 -> postcondition verification
 -> SUCCESS / VERIFY / RETRY / REPLAN / ROLLBACK
```

因此 APR 第一次形成完整 execution loop。

---

## 2. Expected transition is not observed truth

最重要的不變量：

$$
\boxed{
ExpectedPostcondition
\neq
ObservedWorldState
}
$$

Action 說：

```text
expected: door.state = open
```

Runtime 不會直接把：

```text
door.state = open
```

寫進 World State。

它只會產生：

```text
apr.action.outcome.verify
```

要求 targeted perception 去確認。

---

## 3. Pre-action evidence cannot prove post-action success

如果 action 前：

```text
lamp.state = on
```

執行：

```text
turn_on_lamp
```

action 後沒有新 evidence，

不能因為 World State 仍是：

```text
lamp.state = on
```

就聲稱：

```text
SUCCESS
```

預設：

```text
require_post_action_evidence = true
```

所以必須有：

```text
evidence.timestamp >= execution.executed_at
```

才可以證明 action outcome。

這避免 stale state / unchanged cache 冒充 execution success。

---

## 4. PostconditionRequirement

支援：

```text
fact_key
expected_values
forbidden_values
min_confidence
min_independent_evidence
min_modalities
min_evidence_confidence
require_post_action_evidence
must_change_from_pre_state
max_observation_age
```

`must_change_from_pre_state` 可以表達：

```text
closed -> open
```

而不只是：

```text
open
```

---

## 5. Outcome decisions

### SUCCESS
所有 postconditions 都由 post-action evidence 支持。

### VERIFY
證據還不完整，但仍在 verification timeout 內。

### RETRY
已確認 outcome 不符，或 verification timeout，且 action 被宣告 retry-safe。

### REPLAN
失敗且 retry 不可用／已耗盡。

### ROLLBACK
ActionOutcomeSpec 明確指定 rollback policy。

### FAILED
保留作不可恢復終態。

---

## 6. Execution Receipt

新增持久化：

```text
executions.sqlite3
```

Receipt 保存：

```text
execution id
action id/name
started_at
executed_at
readiness
result repr
retry_count
parent_execution_id
status
outcome
completed_at
pre_state
metadata
```

另有：

```text
execution_evidence
```

把 action execution 與 postcondition evidence 連起來。

---

## 7. Action provenance

現在可以追：

```text
ActionSpec
 -> readiness ALLOW
 -> ExecutionReceipt
 -> post-action Evidence IDs
 -> OutcomeDecision
```

所以：

> 為什麼 Runtime 認為這次 action 成功？

可以回答：

> 因為 execution X 之後，evidence A/B 支持 postconditions Y/Z。

---

## 8. Recovery policy

v0.9 先採 declarative policy：

```text
max_retries
retry_safe
rollback_action_id
rollback_on_failure
verification_timeout
```

決策順序：

```text
all satisfied -> SUCCESS

missing evidence and not timed out -> VERIFY

failure + rollback policy -> ROLLBACK

failure + retry safe + retry budget -> RETRY

otherwise -> REPLAN
```

未來可由 learned recovery policy 取代，但 execution contract 保持不變。

---

## 9. 與近期前沿的關係

2026 年 App Agent 工作已開始將 action semantics 明確建模成 UI state transition；
FLARE、RePlan-Bot 與工業機器人 recovery 系統則都把 deviation / failure
detection / retry / replanning 納入 execution loop。

APR v0.9 不主張 recovery 本身為新，而是將它與：

```text
Persistent World State
Evidence Archive
Task-aware perception
Action Readiness Gates
Historical Revisit
```

整合成同一 execution-verification runtime。

---

## 10. 下一版 v0.10

建議進入第一個 Runtime 收斂版：

### Closed-Loop Recovery Orchestrator

```text
pre-gate
 -> execute
 -> verify
 -> retry
 -> verify
 -> replan / rollback
 -> verify recovery
```

加上：

1. retry lineage；
2. rollback action gate；
3. recovery action postconditions；
4. timeout / cancellation；
5. partial-success semantics；
6. irreversible action classification；
7. execution trace export；
8. end-to-end scenario benchmark。

這可以作為 APR Runtime 0.x 的第一個工程封頂版本。
