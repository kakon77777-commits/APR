# APR Runtime 0.x 工程收斂報告

**Adaptive Perceptual Reading / Agentic Perception Runtime**  
**範圍：v0.1 → v0.10**  
**日期：2026-08-09**

---

## 1. 收斂結論

APR Runtime 0.x 已從最初的感知控制 MVP，逐步形成一個完整閉環：

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

它已不再只是「減少 vision tokens」或「只看變化區域」的實驗，而成為一個可替換模型、可接多模態來源、具有持續世界狀態、證據鏈、事件治理、任務資訊需求、行動門控、結果驗證與 recovery 的 Agent Runtime 控制層。

---

## 2. 版本演進

### v0.1 — Belief Control

建立：

- Persistent World State；
- Evidence provenance；
- TTL；
- `KNOWN / UNKNOWN / UNCERTAIN / STALE / CONTRADICTED`；
- `NO_OBSERVATION`；
- `INSPECT / REVISIT`；
- Budget。

核心：

$$
AvailableInformation
\neq
InformationThatMustBeProcessed
$$

### v0.2 — Real Stream

加入：

- screen capture；
- sampled frame delta；
- foreground window；
- Windows UI Automation；
- volatile facts。

核心：

$$
RealStream
\rightarrow
CheapDelta
\rightarrow
WorldState
$$

### v0.3 — Semantic Evidence

加入：

- ROI crop；
- PNG evidence asset；
- SQLite Evidence Archive；
- SemanticInspector；
- semantic fact；
- Fast/Slow loop。

核心：

$$
\Delta^{pix}
\rightarrow
ROI
\rightarrow
\Delta^{sem}
$$

### v0.4 — Historical Revisit

加入：

- Fact → Evidence IDs；
- archived ROI；
- historical semantic re-read；
- Browser Native State；
- URL/title/DOM/ARIA。

核心：

$$
CurrentObservation
\neq
HistoricalRevisit
$$

### v0.5 — Event-Native Targeted Read

加入：

- CDP native events；
- WinEvent；
- targeted DOM subtree；
- partial AX tree；
- targeted UIA subtree；
- Event Ledger。

核心：

$$
Event
\neq
Evidence
\neq
WorldState
$$

### v0.6 — Event Flow Governance

加入：

- Unified Scheduler；
- dedup；
- burst coalescing；
- priority；
- age boost；
- backpressure；
- async execution；
- retention。

核心：

$$
RawEventHistory
\neq
PerceptualWorkSet
$$

### v0.7 — Task-Aware Need Graph

加入：

- Perceptual Need Graph；
- Event → Fact dependencies；
- task-aware priority；
- current/historical query router；
- goal-driven refresh。

核心：

$$
EventImportance
=
f(
Event,
CurrentTaskNeed
)
$$

### v0.8 — Evidence-Gated Action

加入：

- ActionSpec；
- FactRequirement；
- ALLOW / VERIFY / BLOCK；
- evidence diversity；
- action-specific freshness；
- guarded execution。

核心：

$$
Unknown
\neq
False
$$

### v0.9 — Outcome Verification

加入：

- PostconditionRequirement；
- ExecutionReceipt；
- Execution Ledger；
- post-action evidence；
- `SUCCESS / VERIFY / RETRY / REPLAN / ROLLBACK`。

核心：

$$
ExpectedPostcondition
\neq
ObservedWorldState
$$

### v0.10 — Closed-Loop Recovery

加入：

- executable retry；
- retry lineage；
- reversibility classification；
- idempotency guard；
- compensating actions；
- compensation gate；
- compensation verification；
- partial-success policy；
- timeout/cancellation；
- RecoveryTrace。

核心：

$$
Rollback
=
ExplicitCompensatingAction
$$

而不是時間倒轉。

---

## 3. 最終 Runtime 架構

```text
                  ┌─────────────────────┐
                  │ Goal / Task / Plan  │
                  └──────────┬──────────┘
                             │
                             ▼
                  ┌─────────────────────┐
                  │ Perceptual Need     │
                  │ Graph               │
                  └──────────┬──────────┘
                             │
World / Browser / Desktop ───┼───────────────┐
Sensors / Audio / State      │               │
                             ▼               │
                  ┌─────────────────────┐     │
                  │ Native Events /     │     │
                  │ Deltas              │     │
                  └──────────┬──────────┘     │
                             ▼               │
                  ┌─────────────────────┐     │
                  │ Unified Event       │     │
                  │ Scheduler           │     │
                  └──────────┬──────────┘     │
                             ▼               │
                  ┌─────────────────────┐     │
                  │ Targeted Perception │     │
                  └──────────┬──────────┘     │
                             ▼               │
                  ┌─────────────────────┐     │
                  │ Evidence Archive    │◄────┘
                  └──────────┬──────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Persistent World    │
                  │ State               │
                  └──────────┬──────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Action Readiness    │
                  │ Gate                │
                  └─────┬──────┬────────┘
                        │      │
                 VERIFY │      │ BLOCK
                        │      │
                        ▼      │
                    Perception │
                               │
                         ALLOW ▼
                  ┌─────────────────────┐
                  │ Execute Action      │
                  └──────────┬──────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Post-action         │
                  │ Observation         │
                  └──────────┬──────────┘
                             ▼
                  ┌─────────────────────┐
                  │ Outcome Verification│
                  └───┬───┬───┬───┬────┘
                      │   │   │   │
                 SUCCESS VERIFY RETRY REPLAN
                                  │
                                  └──── COMPENSATE
                                            │
                                            ▼
                                   same gate + verify
```

---

## 4. 核心不變量

### 4.1 感知

$$
AvailableInformation
\neq
RequiredProcessing
$$

### 4.2 事件

$$
Event
\neq
Evidence
$$

### 4.3 狀態

$$
Evidence
\neq
CurrentBelief
$$

### 4.4 行動

$$
ActionIntent
\neq
ActionExecution
$$

### 4.5 結果

$$
ExpectedOutcome
\neq
ObservedOutcome
$$

### 4.6 Recovery

$$
Compensation
\neq
HistoricalRollback
$$

---

## 5. 驗證狀態

v0.10 完整 regression：

$$
\boxed{
86/86\ tests\ PASS
}
$$

涵蓋：

- belief / TTL / conflict；
- evidence provenance；
- screen delta；
- Windows structured state；
- browser DOM/ARIA state；
- historical revisit；
- native events；
- scheduler/backpressure；
- retention；
- task-aware routing；
- action readiness；
- post-action evidence；
- retry；
- compensation；
- irreversible-action retry guard；
- timeout/cancellation；
- trace export。

---

## 6. 0.x 尚未宣稱完成的事情

0.x 是控制面 MVP，不代表產品完成。

尚需真機／產品化：

- 長時間 Windows desktop live run；
- 真實 Chromium CDP 長時間 event validation；
- 真 VLM / audio adapter；
- 多裝置 sensor adapter；
- process isolation；
- service lifecycle；
- authentication / authorization；
- metrics / dashboard；
- production-grade async persistence；
- crash recovery；
- distributed execution；
- benchmark dataset；
- learned routing / VOI / recovery。

---

## 7. v1.0 建議

### Track A — Runtime Service

將目前 Python package 轉為：

```text
APR Runtime Service
Event Bus
World State Service
Evidence Service
Action Governance Service
Recovery Service
```

不必一開始微服務化，可以先 modular monolith + SQLite/PostgreSQL。

### Track B — Live Integration

至少驗證：

1. Windows desktop；
2. Chromium browser；
3. local/cloud VLM；
4. structured state；
5. computer-use action executor。

### Track C — APR Benchmark

測量：

$$
TaskSuccess
$$

$$
CriticalMissRate
$$

$$
UnnecessaryObservationRate
$$

$$
StateAccuracy
$$

$$
StateFreshness
$$

$$
EvidenceCost
$$

$$
RecoverySuccess
$$

$$
Latency
$$

$$
TotalCompute
$$

### Track D — Learned Policy

等 heuristic runtime 穩定後，再學：

- event priority；
- modality VOI；
- reading mode；
- budget allocation；
- recovery strategy。

---

## 8. 0.x 封頂判定

APR Runtime 0.x 已完成其原始工程目的：

> 證明 Adaptive Perceptual Reading 可以被具體化為一個不依賴單一模型、具有世界狀態與證據、會選擇性感知、能治理事件、會在行動前要求證據、行動後驗證結果，並在失敗時進行受治理 recovery 的可執行 Runtime 架構。

因此建議：

$$
\boxed{
v0.10
=
0.x\ Freeze\ Candidate
}
$$

下一步不再持續堆 v0.11、v0.12，而轉入 v1.0 productization / benchmark / live validation。
