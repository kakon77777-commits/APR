# Adaptive Perceptual Reading / Agentic Perception
# 統一技術白皮書 v1.0

**英文副題：A Runtime Architecture for Adaptive, Stateful, Budgeted, Cross-Modal Perception**  
**版本：v1.0**  
**日期：2026-08-07**  
**系列來源：APR-01 ～ APR-07**

---

## 0. 執行摘要

Adaptive Perceptual Reading（APR）系列的核心問題並不是「如何讓模型看更多」，而是：

> **當資訊流持續存在、資源有限、任務會變、世界會變時，智能體應如何治理自己的感知活動？**

傳統多模態系統通常採用近似固定流程：

$$
Input
\rightarrow
Encode
\rightarrow
Reason
\rightarrow
Answer
$$

APR 將它改寫為：

$$
\boxed{
WorldState
\rightarrow
Need
\rightarrow
PerceptualPolicy
\rightarrow
EvidenceAcquisition
\rightarrow
BeliefRevision
\rightarrow
Action
\rightarrow
WorldState
}
$$

系統不假設每一張影像、每一個 frame、每一段 audio、每一個文字 token 都值得相同計算，也不假設所有可用模態都必須同時啟用。

APR Runtime 的核心目標是讓 Agent 能夠自主決定：

- 是否需要新的感知；
- 哪一個模態最值得使用；
- 哪一個區域／時間片段值得讀；
- 應使用 Monitor、Skim、Search、Track、Inspect、Deep 或 Revisit 哪一種讀法；
- 應配置多少解析度、採樣率、token、推理深度與歷史跨度；
- 哪些資訊應寫入 Persistent World State；
- 哪些原始資料只需要保留為 Evidence；
- 世界狀態何時 stale、contradicted 或需要重新確認；
- 是否值得為取得更多資訊而採取 epistemic action；
- 何時已有足夠證據，應停止感知。

APR Runtime 因此不是新的 VLM，也不是新的視覺 encoder。

它是一個：

$$
\boxed{
\text{Perceptual Governance Runtime}
}
$$

其下方可以替換任何感知模型、工具、API、感測器與硬體。

---

## 1. 系列統合

APR 七篇形成以下功能鏈：

| 論文 | 核心問題 | Runtime 對應 |
|---|---|---|
| APR-01 | 為何不應均勻處理所有感知輸入？ | Adaptive Perceptual Policy |
| APR-02 | 哪一種變化真的重要？ | Differential Change + Significance |
| APR-03 | 同一份資料可以有哪些不同讀法？ | Reading Modes |
| APR-04 | 如何維持「現在世界是什麼」？ | Persistent World State + Evidence |
| APR-05 | 有限資源應如何配置？ | Perceptual Budget Controller |
| APR-06 | 文字、影像、聲音、狀態能否共享控制語義？ | Cross-Modal Router |
| APR-07 | 誰自主決定整個感知活動？ | Agentic Perception Runtime |

最終總式：

$$
\boxed{
\text{Perception}
=
\text{Goal-conditioned}
+
\text{Stateful}
+
\text{Risk-aware}
+
\text{Budgeted}
+
\text{Selective Information Acquisition}
}
$$

Agentic Perception 則是：

$$
\boxed{
\text{Autonomy over that acquisition process}
}
$$

---

## 2. 設計原則

### P1. Available does not mean required

$$
AvailableInformation
\neq
InformationThatMustBeProcessed
$$

攝影機有 30 FPS，不代表大型模型必須每秒理解 30 張完整影格。

### P2. State is not history

$$
History
\neq
Memory
\neq
WorldState
\neq
Belief
$$

World State 表示「現在相信世界是什麼」，History 與 Evidence 則保存「為什麼這樣相信」。

### P3. Difference is hierarchical

$$
\Delta^{pix}
\rightarrow
\Delta^{feat}
\rightarrow
\Delta^{obj}
\rightarrow
\Delta^{state}
\rightarrow
\Delta^{sem}
\rightarrow
\Delta^{sig}
$$

大量 pixel change 未必重要；微小 pixel change 也可能具有巨大決策意義。

### P4. Same input may deserve different reading

$$
SameInput
\not\Rightarrow
SamePerceptualAct
$$

### P5. Multimodal does not mean all-on

$$
Multimodal
\neq
AllModalitiesAlwaysOn
$$

### P6. Re-observation is normal

$$
Reobserve
\neq
Failure
$$

重讀、回看、提高 FPS、換模態、重新讀取 evidence，都屬正常 epistemic action。

### P7. No-observation is valid

若目前 state 足夠：

$$
VOI(newObservation)<Cost(newObservation)
$$

則：

$$
NO\_OBSERVATION
$$

是合法且可能最優的行動。

### P8. Compute allocation is part of cognition

$$
Situation+Goal+Risk+Budget
\Rightarrow
Compute
$$

而不是永遠：

$$
Architecture\Rightarrow FixedCompute
$$

---

## 3. 核心狀態模型

Runtime state：

$$
\boxed{
\mathcal S_t
=
(
W_t,
G_t,
M_t,
U_t,
R_t,
\mathbf B_t,
H_t
)
}
$$

其中：

- $W_t$：Persistent World State；
- $G_t$：Goal / required facts；
- $M_t$：memory indexes；
- $U_t$：uncertainty；
- $R_t$：risk；
- $\mathbf B_t$：resource budget；
- $H_t$：perception/action history。

### 3.1 World State Fact

每一個 fact 不只保存 value：

```text
key
value
confidence
status
source
last_verified
ttl
version
evidence_ids
```

Status 至少支援：

```text
KNOWN
UNKNOWN
UNCERTAIN
STALE
CONTRADICTED
```

### 3.2 Evidence

Evidence 是可回溯證據，不等同於 state：

```text
id
claim_key
observed_value
modality
source
timestamp
confidence
cost
pointer
metadata
```

### 3.3 Evidence Contract

任何會改寫 World State 的 adapter，都應盡可能輸出 Evidence Contract。

這讓：

$$
Claim
\rightarrow
Evidence
$$

可追溯，並允許：

$$
Conflict
\rightarrow
TargetedReobservation
$$

---

## 4. 感知行動模型

APR Runtime 的感知 action：

$$
\boxed{
a_t^P
=
(
m_t,
r_t,
\Omega_t,
\rho_t,
\nu_t,
d_t,
h_t,
q_t,
p_t
)
}
$$

其中：

- $m_t$：modality；
- $r_t$：reading mode；
- $\Omega_t$：region / segment / fact；
- $\rho_t$：resolution；
- $\nu_t$：sampling rate；
- $d_t$：reasoning depth；
- $h_t$：history horizon；
- $q_t$：re-observation；
- $p_t$：epistemic action。

MVP v0.1 將此縮減為可執行欄位：

```text
target
modality
mode
expected_gain
estimated_cost
reason
epistemic_action
```

---

## 5. Reading Modes

統一閱讀操作：

$$
\mathcal R
=
\{
Monitor,
Skim,
Search,
Track,
Inspect,
Deep,
Revisit
\}
$$

### Monitor
最低成本監控是否值得升級。

### Skim
取得 gist / overview。

### Search
定位特定證據。

### Track
維持 entity / concept / variable 的時間連續性。

### Inspect
提高局部資料精度。

### Deep
提高 reasoning depth。

### Revisit
回到先前 evidence 重新讀取。

這些是高階控制語義，不要求每個模態底層實作相同。

---

## 6. 差分與重要性

Runtime 應將 change detection 與 significance 分開。

簡化 MVP 定義：

$$
Sig
=
\alpha Novelty
+
\beta GoalRelevance
+
\gamma Risk
+
\delta Uncertainty
+
\eta Conflict
$$

真正產品可替換為 learned estimator。

重要原則：

$$
ChangeMagnitude
\neq
ChangeSignificance
$$

例如：

- camera pan：像素變化大，world-state 變化低；
- warning icon：像素變化小，risk/significance 高。

---

## 7. Persistent World State

Runtime 不應每一輪重新建立完整 scene description。

使用：

$$
W_t
=
Update(
W_{t-1},
\Delta W_t,
E_t
)
$$

### 7.1 TTL

不同 state 使用不同 freshness：

$$
TTL(s_i)
=
f(volatility,risk,task)
$$

例如：

```text
wall.position      -> long TTL
door.state         -> medium TTL
person.position    -> short TTL
```

### 7.2 Conflict

若高可信 evidence 產生不同 value：

$$
e_a\Rightarrow x
$$

$$
e_b\Rightarrow y
$$

且：

$$
x\neq y
$$

World State 轉為：

$$
CONTRADICTED
$$

Policy 應優先：

$$
REVISIT
$$

而不是 LastWriteWins。

---

## 8. State–Evidence 雙層

### State Layer

主工作層：

$$
W_t
$$

保持 compact。

### Evidence Layer

原始或近原始證據：

$$
E_{0:t}
$$

可冷熱分層。

因此：

$$
MemoryCompression
\neq
EvidenceDestruction
$$

Agent 平時使用 state；新問題或 conflict 才重新取 evidence。

---

## 9. 跨模態 Router

候選模態：

$$
\mathcal M
=
\{
TEXT,
VISION,
VIDEO,
AUDIO,
STRUCTURED,
SENSOR
\}
$$

MVP 使用 reliability/cost/availability 與 target-specific affinity 估計：

$$
Score(m)
=
VOI(m)
\cdot
Reliability(m)
-
\lambda Cost(m)
$$

完整系統則可以使用 learned router。

### 9.1 Prefer direct state

若 STRUCTURED / SENSOR 能直接提供可靠狀態：

$$
Cost(State)<Cost(Vision)
$$

且：

$$
Reliability(State)\ge Reliability(Vision)
$$

則不應強迫 screenshot → OCR → state。

### 9.2 Cross-modal conflict

不同模態矛盾時，不應立即平均。

觸發：

$$
CrossModalReobserve
$$

---

## 10. 感知預算經濟

多維預算：

$$
\boxed{
\mathbf B_t
=
(
B^{tok},
B^{flop},
B^{lat},
B^{mem},
B^{eng},
B^{io}
)
}
$$

MVP v0.1 使用一個可解釋 weighted budget：

```text
units
```

作為抽象資源。

完整 Runtime 可把 action cost 向量化。

### 10.1 Marginal value

理想政策：

$$
a_t^*
=
\arg\max_a
\frac{ExpectedGain(a)}{Cost(a)}
$$

並受：

$$
Risk
$$

與：

$$
CriticalMiss
$$

約束。

### 10.2 Progressive commitment

不一次花滿：

$$
Monitor
\rightarrow
Skim
\rightarrow
Search
\rightarrow
Inspect
\rightarrow
Deep/Revisit
$$

證據足夠即可停止。

---

## 11. Policy Controller

最小輸入：

```text
goal
required_fact
world_state
uncertainty
risk
budget
available_modalities
conflict_state
```

輸出：

```text
NO_OBSERVATION
MONITOR
SEARCH
INSPECT
REVISIT
EPISTEMIC_ACTION
```

MVP v0.1 採 heuristic policy，理由如下：

1. 能先驗證 architecture，而不把效果混同於 foundation model 能力；
2. deterministic，容易單元測試；
3. 之後可替換成 bandit / RL / small policy model；
4. adapter 與 policy interface 已預先解耦。

---

## 12. Epistemic Action

Action 分兩類：

### Task Action

$$
a_t^{task}
$$

改變世界以完成任務。

### Epistemic Action

$$
a_t^{info}
$$

改變觀察條件以取得資訊。

例如：

```text
camera_pan
scroll
zoom
open_details
query_api
move_closer
```

Policy 比較：

$$
VOI(epistemicAction)
$$

與：

$$
VOI(passiveObservation)
$$

選擇更高者。

MVP 先提供 adapter hook，不實際操控外部裝置。

---

## 13. 雙時間尺度

### Fast Loop

應由低成本模組處理：

```text
event
delta
threshold
tracking
safety interrupt
```

### Slow Loop

由較昂貴模型處理：

```text
semantic interpretation
cross-modal reasoning
planning
deep inspection
belief revision
```

架構原則：

$$
RawSensor
\rightarrow
FastMonitor
\rightarrow
EscalateWhenNeeded
\rightarrow
SlowCognition
$$

避免所有 raw stream 都經過大型模型。

---

## 14. Runtime 架構

```text
Goal / Required Facts
        │
        ▼
Persistent World State
        │
        ├──────── Evidence Store
        │
        ▼
Freshness / Conflict / Uncertainty
        │
        ▼
Change Significance
        │
        ▼
Perceptual Policy Controller
        │
        ├── Modality Router
        ├── Reading Mode
        ├── Budget Controller
        └── Epistemic Action
        │
        ▼
Adapter / Evidence Acquisition
        │
        ▼
Evidence Contract
        │
        ▼
Belief Revision
        │
        ▼
Persistent World State
```

---

## 15. Adapter 介面

APR Runtime 不綁定模型。

一個 adapter 只需要回答：

```python
observe(target, mode) -> Evidence
```

並提供：

```text
modality
reliability
base_cost
availability
```

未來可建立：

```text
OpenAIVisionAdapter
LocalVLMAdapter
AudioModelAdapter
DOMAdapter
AccessibilityAdapter
CameraAdapter
RobotSensorAdapter
DatabaseAdapter
GameStateAdapter
```

---

## 16. MVP v0.1 範圍

### 已實作

- Persistent World State；
- fact confidence / TTL；
- status：KNOWN / UNKNOWN / UNCERTAIN / STALE / CONTRADICTED；
- Evidence Store；
- provenance；
- conflict detection；
- Budget；
- Modality Router；
- Reading Mode heuristic；
- `NO_OBSERVATION`；
- `REVISIT`；
- epistemic-action hook；
- simulator adapter；
- demo；
- unit tests。

### 暫不實作

- 真 VLM；
- OCR；
- audio model；
- frame differencing；
- actual screen capture；
- robot control；
- vector DB；
- learned VOI；
- RL policy；
- distributed runtime。

這些應在控制面可驗證後再接入。

---

## 17. MVP 驗證情境

### Scenario A：已有可靠狀態

Goal：

```text
door.state
```

若 World State：

```text
value=open
confidence=0.98
status=KNOWN
```

Policy：

```text
NO_OBSERVATION
```

驗證：

$$
KnownState
\Rightarrow
NoNeedToSpend
$$

### Scenario B：狀態 stale

若 TTL 到期：

```text
status=STALE
```

Policy：

```text
INSPECT
```

選擇最高 value/cost 模態。

### Scenario C：跨模態衝突

Sensor：

```text
door=open
```

Vision：

```text
door=closed
```

World State：

```text
status=CONTRADICTED
```

Policy：

```text
REVISIT
```

### Scenario D：高風險

即使 confidence 中等，只要：

```text
risk >= threshold
```

就提高檢查強度。

### Scenario E：看不到，需要改變觀察

Adapter 可以回傳：

```text
occluded=true
```

Policy 下一版可選：

```text
epistemic_action=camera_pan
```

---

## 18. 可替換 Policy 路線

### v0.1
Heuristic。

### v0.2
Contextual bandit：

$$
a_t
=
\arg\max_a
[
\hat U(a)-\lambda Cost(a)
]
$$

### v0.3
Learned VOI predictor。

### v0.5
Constrained RL：

$$
r
=
TaskSuccess
-\lambda Cost
-\mu CriticalMiss
$$

### v1.0
Hierarchical policy：

```text
Fast controller
Perceptual router
Cognitive controller
```

---

## 19. 安全與隱私

APR 不應只追求省算力。

### Safety reserve

保留：

$$
B^{safety}
$$

避免純 goal attention 形成盲區。

### Periodic refresh

避免：

$$
BeliefDrift
$$

### Critical states

高風險 fact 可要求：

$$
N_{independentEvidence}\ge2
$$

### Privacy

若不需要完整畫面：

$$
DoNotObserveFullFrame
$$

如果可以使用 direct state：

$$
PreferStructuredState
$$

可降低不必要資料取得。

---

## 20. Benchmark

APR Runtime 的 benchmark 不應只測答案。

至少測：

### Select
是否選對 modality / region / time。

### Scale
是否使用合理 resolution / reasoning depth。

### Maintain
World State 是否正確且新鮮。

### Revisit
是否在 conflict / stale / uncertainty 時重讀。

### Act-to-See
是否知道何時需要 epistemic action。

### Stop
是否知道什麼時候不要再花計算。

核心指標：

```text
TaskSuccess
StateAccuracy
StateFreshness
CriticalMissRate
Cost
Latency
Memory
ReobserveCount
ConflictRecoveryRate
UnnecessaryObservationRate
```

---

## 21. 目前文獻邊界

2026 年的 OmniAgent 已把長影片 omni-modal understanding 明確建模為 POMDP 式 Observation–Thought–Action，並按需取得 audio-visual evidence；AOP-Agent 採 observe–reflect–replan；WorldMemArena 則指出 agent memory 必須處理 evolving world 與 stale state，而非只做靜態 recall。

因此 APR 不應宣稱：

- active perception 是新概念；
- POMDP sensing 是新概念；
- memory agent 是新概念；
- video navigation 是新概念。

APR 的主要整合位置是：

$$
\boxed{
Change
+
WorldState
+
Evidence
+
ReadingMode
+
Modality
+
Budget
+
Reobservation
+
EpistemicAction
}
$$

由同一個 Perceptual Governance Layer 管理。

---

## 22. MVP 之後的工程路線

### v0.2 — Real Stream

接：

```text
screen capture
frame difference
DOM
system event
```

建立真正 Continuous Desktop Perception。

### v0.3 — Local / Cloud VLM Adapter

接：

```text
local vision model
cloud VLM
```

實作 `Inspect` 與 `Deep`。

### v0.4 — Evidence Archive

加入：

```text
SQLite
frame archive
semantic index
```

### v0.5 — Cross-modal

接：

```text
audio
ASR
system sensor
```

### v0.6 — Learned Router

以實際 cost / success trajectory 訓練 VOI predictor。

### v0.8 — Computer-use Agent

接 mouse / keyboard / browser。

### v1.0 — Agentic Perception Runtime

完成：

```text
Fast Loop
Slow Loop
Persistent World State
Evidence Archive
Cross-modal Router
Budget Controller
Epistemic Action
Benchmark
```

---

## 23. 最終工程定義

APR Runtime 可以被壓縮成一個函數：

$$
\boxed{
Perceive(
Goal,
WorldState,
Uncertainty,
Risk,
Budget,
Channels,
Tools
)
\rightarrow
(
Evidence,
UpdatedWorldState,
NextAction
)
}
$$

但其真正重點是：

$$
\boxed{
Perceive
}
$$

不再等同於：

$$
ProcessEverythingAvailable
$$

而是：

$$
\boxed{
DecideWhatIsWorthKnowingNext
}
$$

---

## 24. 結論

APR 七篇系列的統一技術結論是：

$$
\boxed{
\text{Intelligence does not require uniform processing of all available information.}
}
$$

感知更合理的工程定義為：

$$
\boxed{
\text{Goal-conditioned, stateful, risk-aware, budgeted information acquisition}
}
$$

而 Agentic Perception 是：

$$
\boxed{
\text{Autonomous governance of that information-acquisition process}
}
$$

APR Runtime MVP v0.1 因而故意從小型、可測的控制層開始。

它暫時不追求「看得最強」，而先驗證一件更基礎的事情：

> **一個 Agent 是否可以不再把所有可用資訊視為必須立即處理的輸入，而是維持世界狀態、保存證據、判斷資訊缺口，並自主選擇下一個值得支付成本的感知行動。**

如果這個控制面成立，再接入更強的視覺、聲音、GUI、機器人與本地模型，只是能力面的持續擴張。

---

## 參考與前沿定位

1. Xing et al. (2026). *Native Active Perception as Reasoning for Omni-Modal Understanding*. arXiv:2606.19341.
2. Xu et al. (2026). *Agentic Active Omni-Modal Perception for Multi-Hop Audio-Visual Reasoning*. arXiv:2605.28192.
3. Liu et al. (2026). *WorldMemArena: Evaluating Multimodal Agent Memory Through Action-World Interaction*. arXiv:2605.29341.
4. Zhang et al. (2026). *WorldLines: Benchmarking and Modeling Long-Horizon Stateful Embodied Agents*. arXiv:2606.18847.
5. OSWorld (2024). *Benchmarking Multimodal Agents for Open-Ended Tasks in Real Computer Environments*. arXiv:2404.07972.
