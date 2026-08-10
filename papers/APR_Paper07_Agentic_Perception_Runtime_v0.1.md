# Agentic Perception：具備自主感知策略的多模態智能架構

**英文題名：Agentic Perception: An Autonomous Multimodal Architecture for Perceptual Policy, World-State Maintenance, and Active Evidence Acquisition**  
**系列：Adaptive Perceptual Reading（APR）／自適應感知閱讀理論，第 7 篇（系列封頂篇）**  
**版本：v0.1（2026-08-07）**

---

## 摘要

多模態大型模型正在由被動接受文字、影像、聲音與影片輸入，逐步發展為能夠主動搜尋影片片段、調節感知資源、維持多模態記憶、調用工具並在環境中採取行動的 Agent。2026 年的 OmniAgent、AOP-Agent、VideoARM、LongVideo-R1、WorldMemArena 與 Mimir 等研究分別表明：主動感知、階層記憶、世界狀態維護、行動—世界互動與 evidence grounding 已成為多模態 Agent 的重要前沿。然而，這些工作通常聚焦於特定任務，例如長影片理解、具身導航、記憶評估或特定 audio-visual reasoning，尚未形成一個將「何時感知、感知什麼、使用哪個模態、以何種讀法、投入多少資源、更新哪些世界狀態、何時重新觀察、以及何時停止」整合為單一控制層的一般架構。

本文提出 Agentic Perception Runtime（APR-Runtime），作為 Adaptive Perceptual Reading 系列的統合封頂架構。系統核心狀態表示為：

$$
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
$$

其中 $W_t$ 為 Persistent World State，$G_t$ 為當前目標，$M_t$ 為記憶，$U_t$ 為不確定性，$R_t$ 為風險，$\mathbf B_t$ 為多維計算預算，$H_t$ 為感知與行動歷史。Agentic Perception Controller 根據此狀態選擇一個感知—行動決策：

$$
a_t
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
$$

其中 $m_t$ 為模態，$r_t$ 為閱讀模式，$\Omega_t$ 為感知範圍，$\rho_t$ 為解析度，$\nu_t$ 為採樣速率，$d_t$ 為推理深度，$h_t$ 為歷史跨度，$q_t$ 為重觀察決策，$p_t$ 為是否透過身體、工具或 API 主動改變觀察條件。

本文將 APR-01 至 APR-06 的感知資源配置、階層差分感知、多尺度閱讀模式、持續世界狀態、感知預算經濟與跨模態閱讀政策整合為閉環：

$$
\boxed{
WorldState
\rightarrow
Prediction
\rightarrow
Monitoring
\rightarrow
DifferentialChange
\rightarrow
Significance
\rightarrow
PerceptualPolicy
\rightarrow
Observation/Action
\rightarrow
BeliefRevision
\rightarrow
WorldState
}
$$

本文進一步提出雙時間尺度控制、感知行動（epistemic action）、停止／不感知決策、證據導向重觀察、失配修正、Agentic Perception API、benchmark 與 MVP。核心命題為：

**成熟的多模態 Agent 不應只是擁有感官，而應能治理自己的感知活動：知道何時看、看什麼、怎麼看、看多少、何時換一種感知方式、何時為了看得更好而行動，以及何時已經不需要再看。**

**關鍵詞：** Agentic Perception、主動感知、多模態 Agent、Persistent World State、Active Perception、World Model、感知預算、自主觀察、Epistemic Action、Adaptive Multimodal Intelligence

---

## 1. 從「會感知」到「治理感知」

早期多模態系統的核心問題是：

> 模型能不能處理圖片、影片或聲音？

其典型形式為：

$$
X
\rightarrow
Encoder
\rightarrow
Model
\rightarrow
Answer
$$

後來問題擴展為：

> 模型能不能處理更長的影片、更多影格與更多模態？

因此出現：

$$
LongContext
$$

$$
TokenCompression
$$

$$
Memory
$$

$$
MultimodalFusion
$$

但 Agent 所面對的問題更進一步：

> 如果環境一直存在、資料永遠在流動、資源永遠有限，誰決定下一步應該取得什麼資訊？

此時真正的智能操作不再只是：

$$
Perceive(X)
$$

而是：

$$
\boxed{
ChooseHowToPerceive
}
$$

因此本文將 Agentic Perception 定義為：

> **智能體依據目標、世界狀態、不確定性、風險、記憶與資源，自主選擇下一個最有價值的感知或資訊取得行動，並根據結果持續修正自身世界信念的能力。**

---

## 2. 2026：Agentic Perception 已成為明確研究方向

本文不主張「主動感知」或「Agent 自主選擇影片片段」本身為新。

2026 年 OmniAgent 已將 long-video omni-modal understanding 建模為 POMDP 式 iterative Observation–Thought–Action cycle，按需提取 audio-visual cues 並寫入 persistent textual memory，而不是預先完整處理影片。

AOP-Agent 透過 hierarchical omni-modal memory 與 observe–reflect–replan loop 主動取得分散在音訊與視覺中的多跳證據。

VideoARM 建立 observing–thinking–acting–memorizing 的連續循環，由 controller 自主調用工具，以 coarse-to-fine 方式處理長影片並持續更新階層式多模態記憶。

LongVideo-R1 則直接把長影片理解變成低成本 active navigation 問題：模型從高階摘要出發，選擇下一個最值得看的 clip，取得足夠資訊後立即停止。

另一方面，WorldMemArena 把多模態 Agent memory 放進 Action–World Interaction Loop，強調 memory 必須隨 evolving world 更新，而不只是靜態 recall。

2026 年 8 月提出的 Mimir 更進一步顯式分離 world memory 與 task memory；world memory 維護物件位置、狀態與 perceptual evidence，而 task memory 保存目標進度、失敗與執行約束，再於行動前進行 grounding。

這些成果意味著：

$$
\boxed{
\text{Perception}
\rightarrow
\text{Agentic Perception}
}
$$

已經不是純理論預測，而是實際研究方向。

---

## 3. APR-07 的研究位置

如果只提出：

> Agent 應該主動選擇要看的影片片段。

這已經不夠。

如果只提出：

> Agent 應該有 persistent memory。

也已經不夠。

甚至：

> Agent 應該 observe–think–act。

也已有大量接近工作。

APR-07 的位置是把前六篇形成一個統一的：

$$
\boxed{
\text{Perceptual Governance Layer}
}
$$

治理的不是某一個視覺工具，而是整個：

$$
\{
Perception,
Memory,
WorldState,
Reasoning,
Resources,
Evidence,
Reobservation,
EpistemicAction
\}
$$

系統。

因此本文的核心不是：

$$
\text{Active Video Search}
$$

而是：

$$
\boxed{
\text{Autonomous Governance of Information Acquisition}
}
$$

---

## 4. Agentic Perception State

本文定義 Agent 的感知治理狀態：

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

### 世界狀態

$$
W_t
$$

表示 Agent 當前對環境的結構化信念。

### 目標

$$
G_t
$$

表示當前任務、子任務與資訊需求。

### 記憶

$$
M_t
$$

包含 episodic、semantic、task、skill 與 evidence indices。

### 不確定性

$$
U_t
$$

表示對狀態與推論的 epistemic uncertainty。

### 風險

$$
R_t
$$

表示錯過資訊或採取錯誤行動的後果。

### 資源

$$
\mathbf B_t
$$

包含 token、FLOPs、延遲、記憶體、能源與 I/O 預算。

### 歷史

$$
H_t
$$

保存 perception–reasoning–action trajectory。

這些共同決定 Agent 下一步是否需要進一步取得資訊。

---

## 5. Agentic Perception Action

感知行動定義為：

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
- $\Omega_t$：region / segment / evidence scope；
- $\rho_t$：resolution；
- $\nu_t$：sampling rate；
- $d_t$：reasoning depth；
- $h_t$：history horizon；
- $q_t$：re-observation；
- $p_t$：active sensing / epistemic action。

因此 Agent 的「下一步」可以是：

$$
Observe(image,ROI)
$$

也可以是：

$$
Listen(audio,[t_1,t_2])
$$

或：

$$
Read(DOM)
$$

或：

$$
Retrieve(frame_{old})
$$

甚至：

$$
MoveCamera(left)
$$

或：

$$
DoNothing
$$

---

## 6. 「不感知」也是一個合法動作

Agentic Perception 必須允許：

$$
a_t^P=\varnothing
$$

如果：

$$
Confidence(W_t)\ge\tau_C
$$

且：

$$
ExpectedVOI(new\ observation)
<
Cost(new\ observation)
$$

則：

$$
\boxed{
DoNotObserve
}
$$

可能是最佳決策。

這是一個非常重要的差異。

傳統 perception pipeline 假設：

$$
SensorInput
\Rightarrow
Process
$$

Agentic Perception 則允許：

$$
SensorInputAvailable
\not\Rightarrow
SensorInputMustBeProcessed
$$

這讓「不看」成為與「看」同樣正式的認知行動。

---

## 7. Persistent Perceptual Loop

APR-04 已提出 Persistent World State。

APR-07 將整個系統封裝成：

$$
\boxed{
W_t
\rightarrow
Predict
\rightarrow
Monitor
\rightarrow
Detect
\rightarrow
Evaluate
\rightarrow
Acquire
\rightarrow
Revise
\rightarrow
W_{t+1}
}
$$

### Predict

根據：

$$
W_t
$$

預測下一時刻可能觀察：

$$
\hat O_{t+1}
$$

### Monitor

以低成本維持環境監控。

### Detect

得到 APR-02 的差分：

$$
\Delta^{pix}
\rightarrow
\Delta^{sig}
$$

### Evaluate

估計：

$$
VOI,
U,
Risk,
GoalRelevance,
Cost
$$

### Acquire

依 APR-03 / APR-06 選擇：

$$
modality+mode+resolution
$$

### Revise

依 APR-04 更新：

$$
W_{t+1}
$$

然後重新循環。

---

## 8. Prediction Error 作為感知觸發器

Persistent World State 可以產生預期觀測：

$$
\hat O_t
=
g(W_{t-1},A_{t-1})
$$

實際觀測：

$$
O_t
$$

定義：

$$
e_t
=
D(O_t,\hat O_t)
$$

若：

$$
e_t<\tau_1
$$

只需要 Monitor。

若：

$$
\tau_1\le e_t<\tau_2
$$

進入：

$$
Glance/Scan
$$

若：

$$
e_t\ge\tau_2
$$

進入：

$$
Inspect/Deep/Reobserve
$$

因此：

$$
\boxed{
PredictionError
\rightarrow
PerceptualEscalation
}
$$

這不要求 APR 成為特定的 predictive coding 理論，而只是提供一個可工程化的 trigger。

---

## 9. 事件觸發與問題觸發是兩種不同感知

Agentic Perception 至少包含兩類入口。

### 9.1 Environment-driven

外部世界發生變化：

$$
\Delta^{sig}\uparrow
$$

觸發 Agent 感知。

例如：

- 警報亮起；
- 人物進入；
- 音訊突變；
- GUI 出現 error。

### 9.2 Goal-driven

世界可能完全沒變，但 Agent 產生新問題：

$$
G_t\rightarrow G_{t+1}
$$

例如：

> 剛才那個人拿的是什麼？

因此：

$$
Reobserve(E_{past})
$$

這說明：

$$
\boxed{
Perception can be driven by world change or by question change.
}
$$

這也是「同一張圖可以重讀」最完整的 Agent 版本。

---

## 10. Epistemic Action：為了知道而行動

傳統 action 的目的通常是改變世界：

$$
Action
\rightarrow
WorldChange
$$

但 Agent 也可以為了取得更好的資訊而行動：

$$
Action
\rightarrow
BetterObservation
$$

稱為：

$$
\boxed{
EpistemicAction
}
$$

例如：

- 移動攝影機；
- 靠近物件；
- 轉動頭部；
- 打開燈；
- 翻轉物件；
- 捲動頁面；
- 展開選單；
- 點擊「詳細資訊」；
- 呼叫 diagnostic API。

所以：

$$
p_t
=
\arg\max_p
[
VOI(p)-Cost(p)-Risk(p)
]
$$

若：

$$
VOI(move\ camera)
>
VOI(reason\ harder)
$$

Agent 應該移動攝影機，而不是繼續猜。

---

## 11. Perception–Action Dual Loop

因此 Agent 不只有：

$$
Perception\rightarrow Action
$$

而有雙向迴圈：

$$
\boxed{
Perception
\rightarrow
Belief
\rightarrow
Action
\rightarrow
NewObservation
\rightarrow
Belief
}
$$

其中 Action 可以分成：

### Pragmatic Action

目的是完成外部任務：

$$
a_t^{task}
$$

### Epistemic Action

目的是降低不確定性：

$$
a_t^{info}
$$

總動作：

$$
a_t
\in
\{
a_t^{task},
a_t^{info}
\}
$$

有時候最佳下一步不是：

> 做任務。

而是：

> 先確認自己是否理解正確。

---

## 12. 雙時間尺度感知控制

成熟 Agent 不應每次都呼叫最昂貴的大模型。

本文提出：

$$
\boxed{
FastLoop
+
SlowLoop
}
$$

### Fast Perceptual Loop

高頻、低成本：

$$
10\text{--}1000Hz
$$

視硬體而定。

功能：

- event detection；
- tracking；
- threshold monitoring；
- low-level state update；
- safety interrupt。

### Slow Cognitive Loop

低頻、高成本：

$$
0.1\text{--}10Hz
$$

功能：

- semantic interpretation；
- cross-modal reasoning；
- planning；
- deep inspection；
- re-observation selection；
- world-model revision。

二者形成：

$$
FastLoop
\rightarrow
EscalationSignal
\rightarrow
SlowLoop
$$

這避免：

$$
LLM
$$

成為所有感知事件的 mandatory bottleneck。

---

## 13. 三層感知 Controller

工程上可進一步拆成：

### Layer 0：Reflex Monitor

只處理：

$$
\Delta,\ threshold,\ safety
$$

### Layer 1：Perceptual Router

決定：

$$
modality,
mode,
ROI,
resolution,
fps
$$

### Layer 2：Cognitive Controller

決定：

$$
deep\ reasoning,
memory\ retrieval,
reobserve,
epistemic\ action,
task\ action
$$

因此：

$$
\boxed{
RawSensor
\not\rightarrow
LLM\ every\ time
}
$$

更合理的是：

$$
RawSensor
\rightarrow
Monitor
\rightarrow
Router
\rightarrow
Cognition\ when\ necessary
$$

---

## 14. APR 統一政策

APR 前六篇可以被收斂成：

$$
\boxed{
\Pi_{APR}
:
\mathcal S_t
\rightarrow
a_t
}
$$

其中：

$$
\mathcal S_t
=
(
W_t,G_t,M_t,U_t,R_t,\mathbf B_t,H_t
)
$$

且：

$$
a_t
=
(
m,
r,
\Omega,
\rho,
\nu,
d,h,q,p
)
$$

策略目標：

$$
\Pi_{APR}^*
=
\arg\max_\Pi
\mathbb E
\left[
\sum_t
\gamma^t
(
U_t^{task}
-\lambda C_t
-\mu Risk_t
)
\right]
$$

subject to：

$$
P(CriticalMiss)<\epsilon
$$

$$
C_t\le\mathbf B_t
$$

以及系統安全與權限約束。

---

## 15. APR-01：資源配置

APR-01 建立：

$$
\text{Perception}
=
\text{AdaptiveResourceAllocation}
$$

APR-07 中它成為：

$$
\Pi_{APR}
$$

的總控制原則。

Agent 不再把：

$$
SensorAvailability
$$

等同於：

$$
ComputeObligation
$$

---

## 16. APR-02：差分與重要性

APR-02 建立：

$$
\Delta^{pix}
\neq
\Delta^{feat}
\neq
\Delta^{obj}
\neq
\Delta^{state}
\neq
\Delta^{sem}
\neq
\Delta^{sig}
$$

APR-07 中：

$$
\Delta^{sig}
$$

成為主要感知 escalation signal 之一。

因此不是：

$$
PixelChanged
\Rightarrow
SpendCompute
$$

而是：

$$
\boxed{
SignificantStateChange
\Rightarrow
ConsiderSpendingCompute
}
$$

---

## 17. APR-03：閱讀模式

APR-03 建立：

$$
\{
Monitor,
Glance,
Scan,
Track,
Inspect,
Deep,
Reobserve
\}
$$

APR-07 中這些成為：

$$
r_t
$$

即 Agent 可以正式選擇的感知 actions。

因此「看」不再是一個 function，而是一組 policy actions。

---

## 18. APR-04：世界狀態

APR-04 建立：

$$
History
\neq
Memory
\neq
WorldState
\neq
Belief
$$

APR-07 中：

$$
W_t
$$

成為所有感知策略的基準。

Agent 不問：

> 這一幀有什麼？

而先問：

> 我原本認為世界是什麼？現在有哪些信念可能需要改？

這使 perception 從：

$$
SceneDescription
$$

提升成：

$$
\boxed{
BeliefMaintenance
}
$$

---

## 19. APR-05：預算經濟

APR-05 建立：

$$
\mathbf B_t
=
(
Token,
FLOPs,
Latency,
Memory,
Energy,
I/O
)
$$

APR-07 中，Agent 每一個 perceptual action 都必須報價：

$$
C(a_t)
$$

並計算：

$$
VOI(a_t)
$$

選擇：

$$
a_t^*
=
\arg\max_a
[
VOI(a)-Cost(a)-Risk(a)
]
$$

---

## 20. APR-06：跨模態閱讀

APR-06 建立：

$$
\text{Multimodal}
\neq
\text{AllModalitiesAlwaysOn}
$$

APR-07 中：

$$
m_t
$$

可以是：

$$
Text
$$

$$
Vision
$$

$$
Audio
$$

$$
Video
$$

$$
Sensor
$$

$$
StructuredState
$$

或：

$$
\varnothing
$$

所以最終 Agentic Perception 的第一個問題甚至不是：

> 我該怎麼看？

而是：

$$
\boxed{
\text{Do I need to perceive, and through which channel?}
}
$$

---

## 21. 感知治理決策樹

最小 runtime 可以採以下邏輯：

### Step 1：目前狀態足夠嗎？

若：

$$
Confidence(W_t,Q)\ge\tau
$$

且風險低：

$$
StopPerceiving
$$

### Step 2：是否發生顯著變化？

若：

$$
\Delta^{sig}>\tau_\Delta
$$

則決定是否升級。

### Step 3：哪個模態最有價值？

計算：

$$
VOI(m)
$$

### Step 4：使用哪個閱讀模式？

選：

$$
r
\in
\{
Monitor,Glance,Scan,Track,Inspect,Deep,Reobserve
\}
$$

### Step 5：分配多少資源？

求：

$$
\mathbf a_t
$$

### Step 6：需要改變觀察位置嗎？

若：

$$
VOI(epistemic\ action)>VOI(passive\ observation)
$$

執行：

$$
p_t
$$

### Step 7：更新世界狀態

$$
W_{t+1}
=
Revise(W_t,E_t)
$$

### Step 8：決定繼續、行動或停止

---

## 22. Agentic Perception Runtime

本文提出最小架構：

```text
┌─────────────────────────────┐
│ Goal / Task / Constraints   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Persistent World State      │
│ belief / confidence / TTL   │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Change & Uncertainty Monitor│
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Perceptual Policy Controller│
│ modality / mode / budget    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Evidence Acquisition Layer  │
│ vision/audio/state/tools    │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Evidence & Conflict Manager │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Belief Revision             │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Planner / Action Controller │
└──────────────┬──────────────┘
               ↓
        World / Interface
               │
               └──────────→ loop
```

---

## 23. 核心模組

### 23.1 World State Store

保存：

$$
W_t
$$

### 23.2 Evidence Store

保存可重讀證據：

$$
E_{0:t}
$$

### 23.3 Change Monitor

計算：

$$
\Delta^{sig}
$$

### 23.4 Uncertainty Estimator

估計：

$$
U_t
$$

### 23.5 Risk Estimator

估計：

$$
R_t
$$

### 23.6 Budget Controller

維持：

$$
\mathbf B_t
$$

### 23.7 Modality Router

選擇：

$$
m_t
$$

### 23.8 Reading-Mode Controller

選擇：

$$
r_t
$$

### 23.9 Evidence Acquisition Tools

執行：

- crop；
- zoom；
- replay；
- DOM query；
- sensor query；
- audio replay；
- camera move。

### 23.10 Belief Revision Engine

更新：

$$
W_{t+1}
$$

### 23.11 Planner / Actor

決定 task action 或 epistemic action。

---

## 24. Evidence Contract

所有可改寫世界狀態的感知輸出最好帶有：

$$
\boxed{
EvidenceContract
}
$$

至少包含：

```text
claim
source
timestamp
modality
location
confidence
cost
evidence_pointer
validity
```

例如：

```text
claim: door_4.state = open
source: visual_detector
timestamp: 17:42:03.182
modality: vision
roi: [821, 114, 1030, 700]
confidence: 0.91
cost: 42 visual_tokens
evidence: frame_99182
validity: transient
```

這使 Agent 可以追蹤：

> 我為什麼相信這件事？

而不是只有不可追溯的 latent memory。

---

## 25. Perceptual Provenance

如果世界狀態：

$$
s_i
$$

由多個證據支持：

$$
E(s_i)
=
\{e_1,e_2,\ldots,e_n\}
$$

則每次 belief revision 應保留 provenance。

當新證據：

$$
e_{n+1}
$$

與舊信念衝突時，可以回到：

$$
E(s_i)
$$

而不是重新掃描整個世界。

因此：

$$
\boxed{
Provenance
\rightarrow
TargetedReobservation
}
$$

是 APR 的關鍵工程連接點。

---

## 26. 世界狀態與任務狀態分離

Mimir 的近期設計顯示，world memory 與 task memory 分離具有實際價值。

APR-Runtime 同樣區分：

$$
W_t^{world}
$$

與：

$$
W_t^{task}
$$

其中：

### World State

保存：

- 外部物件；
- 屬性；
- 位置；
- 關係；
- 環境。

### Task State

保存：

- 目前目標；
- 完成步驟；
- 失敗；
- pending actions；
- constraints；
- required evidence。

因此：

$$
\mathcal S_t
=
(
W_t^{world},
W_t^{task},
...
)
$$

避免把：

> 世界是什麼

與：

> 我正在做什麼

混在一起。

---

## 27. Perceptual Need Graph

一個目標可能需要多個尚未確認的資訊。

定義：

$$
PNG_t
=
(V,E)
$$

其中每個 node 是：

$$
NeededFact_i
$$

例如：

```text
Goal: pick up correct medicine bottle

Needed facts:
- bottle_identity
- bottle_location
- label_text
- expiry_date
- graspability
```

每個 node 有：

$$
confidence,
risk,
VOI,
evidence
$$

Policy Controller 優先解決：

$$
i^*
=
\arg\max_i
\frac{
VOI_i
}{
Cost_i
}
$$

直到所有必要 facts 都達到：

$$
Confidence_i\ge\tau_i
$$

才進行 task action。

這使 perception 成為 planner 可以直接管理的 dependency graph。

---

## 28. 感知、推理與行動的共同停止條件

Agentic 系統的一大風險是永遠反思、永遠驗證、永遠重觀察。

因此定義：

$$
Stop
$$

條件：

$$
GoalEvidenceSufficient=1
$$

且：

$$
ExpectedGain(next\ step)
<
ExpectedCost(next\ step)
$$

且：

$$
RiskAcceptable=1
$$

即：

$$
\boxed{
SufficientEvidence
+
LowMarginalGain
+
AcceptableRisk
\Rightarrow
Stop
}
$$

停止可以代表：

- 回答；
- 採取任務動作；
- 回到 monitor mode；
- 等待新事件。

---

## 29. 感知失敗分類

本文提出六種 failure mode。

### F1：Miss

重要事件根本未觸發。

### F2：Misallocation

知道重要，但資源給錯地方。

### F3：Wrong Modality

使用錯誤資訊通道。

### F4：Wrong Reading Mode

例如需要 Track 卻只做 Glance。

### F5：Belief Drift

差分更新長期累積錯誤。

### F6：Perceptual Looping

無限重看或無限驗證。

這些 failure mode 比單純：

$$
AnswerWrong
$$

更適合診斷 Agentic Perception。

---

## 30. 安全與關鍵事件

效率最佳化不能凌駕於關鍵事件。

定義：

$$
CriticalStateSet
=
\mathcal C
$$

對：

$$
s_i\in\mathcal C
$$

要求：

$$
P(Miss(s_i))<\epsilon_i
$$

以及可能：

$$
N_{independent\ evidence}\ge2
$$

因此高風險 Agent 可以採：

$$
\boxed{
Risk-Adaptive Redundancy
}
$$

一般狀態：

$$
1\ evidence
$$

可能足夠。

關鍵狀態：

$$
2+\ modalities
$$

或 re-verification 才允許行動。

---

## 31. Privacy-aware Perception

Agentic Perception 還帶來另一個重要好處：

如果不需要看：

$$
DoNotObserve
$$

本身也可以是 privacy policy。

例如：

- 不持續 OCR 整個螢幕；
- 只對必要 ROI 做處理；
- 不保存無關聲音；
- 優先讀結構化狀態而非完整攝影機畫面；
- 任務結束後降低感知強度。

因此：

$$
\boxed{
SelectivePerception
}
$$

不只節省 compute，也可以減少不必要的資料取得面。

---

## 32. Perceptual Autonomy Level

為方便工程評估，本文提出六級感知自主性。

### P0：Passive Full Input

系統完全由外部決定輸入。

### P1：Static Selection

預定義 ROI / FPS / modality。

### P2：Adaptive Filtering

依輸入動態 pruning / resolution。

### P3：Goal-Conditioned Perception

依 query 選 frame、modality、ROI。

### P4：Stateful Agentic Perception

具有 persistent world state、memory 與 re-observation。

### P5：Active Epistemic Perception

可以為了取得資訊主動改變環境、視角或呼叫工具。

因此：

$$
\boxed{
P0
\rightarrow
P1
\rightarrow
P2
\rightarrow
P3
\rightarrow
P4
\rightarrow
P5
}
$$

並不代表必然的產品世代，而是一個 capability taxonomy。

---

## 33. APR-Runtime API

工程上可以形成：

```text
perceive(
    goal,
    required_facts,
    current_world_state,
    risk,
    budget,
    available_modalities,
    available_tools
)
```

Controller 回傳：

```text
decision:
  action: inspect
  modality: vision
  target: door_4
  region: [x1,y1,x2,y2]
  resolution: high
  temporal_window: current
  reasoning_depth: low
  reobserve: true
  epistemic_action: none
  expected_information_gain: 0.61
  estimated_cost: 44
```

若不值得感知：

```text
decision:
  action: no_observation
  reason: existing_state_sufficient
```

若需要改變視角：

```text
decision:
  action: epistemic_action
  tool: camera_pan
  direction: left
  then: inspect
```

---

## 34. Runtime 最小偽代碼

```text
while agent_active:

    state = read_world_state()

    goal = current_goal()
    uncertainty = estimate_uncertainty(state, goal)
    risk = estimate_risk(state, goal)

    delta = cheap_monitor()

    if state_is_sufficient(state, goal, risk):
        execute_or_wait()
        continue

    significance = lift_change(delta, goal, state)

    candidate_actions = propose_perceptual_actions(
        state,
        goal,
        uncertainty,
        risk,
        budget
    )

    action = choose_max_value_action(candidate_actions)

    if action == NO_OBSERVATION:
        continue

    evidence = execute_perceptual_action(action)

    update_evidence_store(evidence)

    state = revise_world_state(
        state,
        evidence
    )

    if contradiction_detected(state):
        schedule_targeted_reobservation()

    if task_action_ready(state, goal):
        execute_task_action()
```

此 runtime 不要求單一模型完成全部功能。

可以由：

- state machine；
- small models；
- VLM；
- LLM；
- detector；
- memory DB；
- sensor API；

共同實作。

---

## 35. 與既有 Agent 框架的差異

一般 Agent runtime 常見：

$$
Plan
\rightarrow
Tool
\rightarrow
Observe
\rightarrow
Plan
$$

APR-Runtime 則在 Observe 之前增加：

$$
\boxed{
PerceptualPolicy
}
$$

即：

$$
Plan
\rightarrow
\underbrace{
DecideWhetherAndHowToObserve
}_{APR}
\rightarrow
Observe
\rightarrow
BeliefRevision
\rightarrow
Plan
$$

因此 sensor / screenshot / browser / camera 不再只是 tool。

它們是：

$$
\boxed{
Controlled Information Channels
}
$$

---

## 36. 可驗證假說

### H1：Agentic Perception 優於固定感知

在長時間、部分可觀測、事件稀疏的環境：

$$
Utility_{APR}
>
Utility_{Fixed}
$$

在相同或更低平均成本下。

### H2：Persistent State 是主動感知的必要增益來源之一

若移除：

$$
W_t
$$

Agent 將重複取得已知資訊，導致：

$$
PerceptualCost\uparrow
$$

### H3：Epistemic Action 可以降低推理錯誤

允許：

$$
Move/Zoom/Open/Query
$$

等資訊導向行動的 Agent，應比只能被動觀察者在 occlusion / ambiguity 任務具有更高準確率。

### H4：No-observation action 能顯著降低穩態成本

在大量時間無重要變化的環境中：

$$
Cost_{with\ skip}
<
Cost_{always\ observe}
$$

### H5：Evidence provenance 提升衝突恢復

保留 evidence pointer 的系統應比只保存 state summary 的系統更容易修復錯誤 belief。

### H6：雙時間尺度優於 LLM-only perception

Fast monitor + slow cognition 應在即時任務中降低延遲與模型負載。

### H7：跨模態 VOI routing 降低無關模態激活

$$
UnnecessaryModalityActivation_{APR}
<
AllOn
$$

---

## 37. 系列統一 MVP

最終 APR MVP 可以是一個「持續桌面／房間 Agent」。

### 感知輸入

- RGB screen/camera；
- audio；
- DOM / accessibility；
- system events；
- structured state。

### World State

追蹤：

- active window；
- application state；
- visible entities；
- important values；
- task progress；
- alerts；
- uncertainties。

### 感知模式

支援：

$$
Monitor,
Glance,
Scan,
Track,
Inspect,
Deep,
Reobserve
$$

### 行動

- mouse；
- keyboard；
- camera control；
- API；
- state query。

### 事件

設計：

- 大像素變化、無狀態變化；
- 小像素變化、高重要性；
- audio-only event；
- visual/audio conflict；
- state stale；
- hidden detail requiring revisit；
- occlusion requiring camera movement。

---

## 38. Baselines

### A：Full Continuous

全畫面、固定 FPS、高解析。

### B：Static Adaptive

固定 heuristic：frame difference + ROI。

### C：Video Agent

主動 frame / clip selection，但無 persistent world-state policy。

### D：Memory Agent

有 memory，但無感知 budget / reading modes。

### E：APR-Runtime

完整：

$$
Delta
+
WorldState
+
ReadingModes
+
CrossModalRouting
+
Budget
+
Reobserve
+
EpistemicAction
$$

---

## 39. 評估指標

需要同時評估：

$$
TaskSuccess
$$

$$
StateAccuracy
$$

$$
StateFreshness
$$

$$
CriticalMissRate
$$

$$
VisualTokens
$$

$$
AudioTokens
$$

$$
ReasoningTokens
$$

$$
Latency
$$

$$
Energy
$$

$$
MemoryUsage
$$

$$
ReobserveCount
$$

$$
EpistemicActionCount
$$

$$
ConflictRecoveryRate
$$

$$
BeliefDrift
$$

$$
UnnecessaryObservationRate
$$

最後使用 Pareto frontier，而不是只報一個 Accuracy。

---

## 40. Agentic Perception Benchmark

可建立 APR-Bench，包含五大能力。

### A. Select

是否選對模態、區域與時間？

### B. Scale

是否配置適當解析度與推理深度？

### C. Maintain

是否持續維持正確世界狀態？

### D. Revisit

是否在必要時回到證據重新確認？

### E. Act-to-See

是否能為了取得資訊而採取合理 epistemic action？

最終評估：

$$
Score
=
f(
Success,
Cost,
Risk,
StateConsistency,
Recovery
)
$$

---

## 41. 訓練路徑

APR-Runtime 不一定要一開始端到端訓練。

可以分三階段。

### Stage 1：Heuristic Controller

人工規則：

$$
Delta
\rightarrow
Mode
$$

先證明架構。

### Stage 2：Supervised Perceptual Trajectories

收集：

$$
\mathcal T_P
$$

訓練：

$$
PolicyModel
$$

學習何時 scan / inspect / reobserve。

### Stage 3：RL / Constrained RL

Reward：

$$
r
=
TaskSuccess
-
\lambda Cost
-
\mu CriticalMiss
$$

使 Agent 學會 accuracy–cost–risk tradeoff。

LongVideo-R1、OmniAgent 等工作已顯示 SFT + RL 可有效訓練主動感知軌跡，因此此路徑具有現實可行性。

---

## 42. 理論上的 POMDP 表示

Agentic Perception 自然可表示成 POMDP：

$$
\mathcal P
=
(
S,A,O,T,Z,R,\gamma
)
$$

其中真實世界：

$$
s_t
$$

不可完整觀察。

Agent 維持 belief：

$$
b_t(s)
=
P(s_t=s|H_t)
$$

感知 action：

$$
a_t^P
$$

會改變可取得的 observation：

$$
o_{t+1}
\sim
Z(o|s,a_t^P)
$$

而 task action：

$$
a_t^T
$$

會改變世界：

$$
s_{t+1}
\sim
T(s'|s,a_t^T)
$$

因此 Agent 同時控制：

$$
\boxed{
\text{How the world changes}
}
$$

與：

$$
\boxed{
\text{How the world is observed}
}
$$

這正是 Agentic Perception 的決策本質。

---

## 43. 與 Active Inference / Active Vision 的關係

本文並不主張：

- active vision；
- active sensing；
- POMDP sensing；
- information-gain exploration；
- predictive processing；

為新的。

Agentic Perception 與上述研究存在明顯思想親緣。

但 APR 的工程焦點是當代多模態 Agent：

$$
\boxed{
MultimodalFoundationModels
+
PersistentWorldState
+
AdaptiveCompute
+
EvidenceTools
+
AgentRuntime
}
$$

即將傳統 active perception 問題重新放入：

- tokenized multimodal input；
- LLM/VLM reasoning；
- long-term memory；
- structured state；
- tool-use；
- resource cost；

的現代計算環境中。

---

## 44. 與目前 2026 前沿的邊界

本文不主張以下單項能力為新：

- active perception；
- active video navigation；
- observe–think–act loop；
- hierarchical multimodal memory；
- multimodal long-term memory；
- POMDP-based perception；
- world memory；
- evidence grounding；
- tool-based video inspection；
- multimodal world models。

OmniAgent 已使用 POMDP-based Observation–Thought–Action 主動 omni-modal perception；AOP-Agent 已做 observe–reflect–replan；VideoARM 已做 observe–think–act–memorize；LongVideo-R1 已做智能 clip navigation；WorldMemArena 已把 memory 放進 action–world interaction；Mimir 已顯式維護 world memory、task memory 與 perceptual evidence。

APR-07 的整合位置是：

$$
\boxed{
\text{Agentic Perception}
=
\text{Perceptual Policy Governance}
}
$$

它同時統一：

$$
Change
+
WorldState
+
Modality
+
ReadingMode
+
Budget
+
Memory
+
Evidence
+
Reobservation
+
EpistemicAction
$$

而不是只優化其中一項。

---

## 45. 限制

### 45.1 Controller 本身可能過度複雜

如果每一個 perception decision 都需要大型 LLM：

$$
C_{controller}
\gg C_{saved}
$$

整個架構失去效率。

因此必須分層與小模型化。

### 45.2 VOI 只能近似

Agent 無法在觀察前準確知道觀察結果。

因此：

$$
VOI
$$

本質上是估計。

### 45.3 World State schema 會演化

開放世界不能預先定義所有 object/state。

### 45.4 重觀察不保證解決矛盾

原始證據可能本身不足。

### 45.5 Epistemic action 可能改變世界

為了「看得更清楚」而移動物體，本身可能使場景改變，因此必須區分：

$$
ObservationIntervention
$$

與：

$$
TaskIntervention
$$

### 45.6 多模態同步仍然困難

不同資料流有 latency 與時間戳偏差。

### 45.7 Adaptive perception 可能形成注意盲區

如果 policy 長期錯估重要性，會持續忽略某些區域。

因此必須保留：

$$
ExplorationBudget
$$

與：

$$
PeriodicRefresh
$$

---

## 46. 討論：感知本身成為 Agent 的自治領域

當感知只是固定 pipeline 時：

$$
Developer
\rightarrow
SensorSettings
\rightarrow
Model
$$

但 Agentic Perception 中：

$$
AgentState
\rightarrow
PerceptualDecision
\rightarrow
Sensor/Tool
$$

這表示 Agent 的自治能力不只體現在：

> 自己決定做什麼。

還包括：

> 自己決定為了做好這件事，需要知道什麼，以及要付多少代價去知道。

因此：

$$
\boxed{
\text{Autonomy of Action}
}
$$

之前其實還有：

$$
\boxed{
\text{Autonomy of Information Acquisition}
}
$$

後者就是本文所謂 Agentic Perception。

---

## 47. 從注意力機制到注意力治理

Transformer attention 通常是：

$$
Attention(Q,K,V)
$$

但 APR 所談的「注意力」更高一層：

$$
\boxed{
\text{Which data should even reach expensive attention?}
}
$$

所以可以區分：

### Internal Attention

模型內部：

$$
Token\rightarrow Token
$$

### Perceptual Attention

模型外部／前端：

$$
World\rightarrow SelectedEvidence
$$

### Governance Attention

Agent 層：

$$
Goal+State+Risk+Budget
\rightarrow
PerceptualPolicy
$$

因此：

$$
\boxed{
AttentionMechanism
\subset
PerceptualAttention
\subset
AttentionGovernance
}
$$

這是 APR 系列最後可以留下的一個重要抽象。

---

## 48. 系列總命題

七篇文章最終可以壓縮成：

$$
\boxed{
\text{Intelligence does not require uniform processing of all available information.}
}
$$

更精確地：

$$
\boxed{
\text{Perception}
=
\text{Goal-conditioned, stateful, risk-aware, budgeted information acquisition}
}
$$

而 Agentic Perception 則是：

$$
\boxed{
\text{The autonomy to govern that acquisition process.}
}
$$

---

## 49. APR 七篇統一結構

### APR-01

$$
\boxed{
\text{Perception is Resource Allocation}
}
$$

### APR-02

$$
\boxed{
\text{Change Magnitude}\neq\text{Change Significance}
}
$$

### APR-03

$$
\boxed{
\text{Vision Has Multiple Reading Modes}
}
$$

### APR-04

$$
\boxed{
\text{Continuous Perception is Belief Maintenance}
}
$$

### APR-05

$$
\boxed{
\text{Compute Allocation is a Cognitive Action}
}
$$

### APR-06

$$
\boxed{
\text{Reading is Modality-General}
}
$$

### APR-07

$$
\boxed{
\text{Agentic Perception is Autonomous Perceptual Governance}
}
$$

整體：

$$
\boxed{
\text{Adaptive Perceptual Reading}
\rightarrow
\text{Agentic Perception}
}
$$

---

## 50. 結論

本文提出 Agentic Perception Runtime（APR-Runtime），完成 Adaptive Perceptual Reading 七篇系列的理論整合。

其核心 Agent state 為：

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

其核心感知 action 為：

$$
\boxed{
a_t
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

整體循環為：

$$
\boxed{
WorldState
\rightarrow
Prediction
\rightarrow
Monitor
\rightarrow
Difference
\rightarrow
Significance
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

本文因此得到五項最終原則：

$$
\boxed{
\text{Available Information}
\neq
\text{Information That Must Be Processed}
}
$$

$$
\boxed{
\text{Perception}
\neq
\text{Uniform Input Processing}
}
$$

$$
\boxed{
\text{Memory}
\neq
\text{Current World Belief}
}
$$

$$
\boxed{
\text{Action Can Serve Tasks or Acquire Information}
}
$$

以及：

$$
\boxed{
\text{A Mature Agent Should Govern Its Own Perceptual Activity}
}
$$

因此，未來多模態 Agent 的重要能力可能不只是擁有更長 context、更高解析度與更多 sensor，而是：

> **能在一個持續存在的世界裡，知道自己目前相信什麼、不知道什麼、需要知道什麼、應該去哪裡取得證據、要花多少資源確認，以及什麼時候已經知道得夠多。**

這就是本文對 Agentic Perception 的最終定義。

---

## 參考文獻

1. Xing, Z., Xu, R., Wang, Y., He, J., Ma, Z., Yang, Q., Chu, Y., Xu, J., Lin, J., Fu, C.-W., & Heng, P.-A. (2026). *Native Active Perception as Reasoning for Omni-Modal Understanding*. arXiv:2606.19341.
2. Xu, K., Wang, Y., Cheng, Z., Liu, H., Wang, Y., & Wang, Y. (2026). *Agentic Active Omni-Modal Perception for Multi-Hop Audio-Visual Reasoning*. arXiv:2605.28192.
3. Yin, Y., Meng, Q., Chen, M., Ding, J., Shao, Z., & Yu, Z. (2026). *VideoARM: Agentic Reasoning over Hierarchical Memory for Long-Form Video Understanding*. CVPR 2026.
4. Qiu, J., Xie, L., Huo, X., Tian, Q., & Ye, Q. (2026). *LongVideo-R1: Smart Navigation for Low-cost Long Video Understanding*. CVPR 2026.
5. Liu, C., Yang, Y., Pu, S. X., et al. (2026). *WorldMemArena: Evaluating Multimodal Agent Memory Through Action-World Interaction*. arXiv:2605.29341.
6. Xu, H., He, Z., Wang, H., Xu, J., & Dong, H. (2026). *Mimir: A Neuro-Symbolic Memory System with Dynamic Grounding for Embodied Agents in Interactive Environments*. arXiv:2608.04933.
7. Zhang, Z., Hou, Y., Cao, D., et al. (2026). *M4EI: A Hierarchical Multimodal Memory Framework for Embodied Intelligence with Causal-Driven Retrieval*. KSEM 2026.
8. Zhuang, X., Zhou, C., Feng, K., et al. (2026). *Embodied Science: Closing the Discovery Loop with Agentic Embodied AI*. arXiv:2603.19782.
9. Fung, P., Bachrach, Y., Celikyilmaz, A., et al. (2025). *Embodied AI Agents: Modeling the World*. arXiv:2506.22355.
10. Yang, Q., Kang, Y., Ren, G., Yang, Q., & Li, N. (2026). *Beyond Vision: Holistic World Models*. CVPR Workshops 2026.
11. Ren, H. (2026). *Research on embodied agent multimodal perception and real-time path planning algorithms for complex unstructured environments*. Frontiers in Neurorobotics, 20.
12. Ko, B. C. (2026). *Sensing the Action: Rethinking Sensor Modalities and Multi-Modal Fusion in Vision–Language–Action Models for Robotic Manipulation*. Sensors, 26(11), 3541.

---

## 系列封頂

APR-01：從均勻感知到自適應感知閱讀：多模態智能的感知資源配置理論  
APR-02：從像素差分到語義差分：連續多模態感知中的變化階層  
APR-03：視覺不是一種閱讀：多尺度視覺閱讀模式與重觀察理論  
APR-04：持續世界狀態與差分重觀察：從連續影片理解到持續感知智能  
APR-05：感知預算分配：從固定視覺 Token 到動態資訊獲益最大化  
APR-06：跨模態感知閱讀：文字、影像、影片與聲音的統一注意策略  
**APR-07：Agentic Perception：具備自主感知策略的多模態智能架構 ← 本文／系列封頂**
