# 感知預算分配：從固定視覺 Token 到動態資訊獲益最大化

**英文題名：Perceptual Budget Allocation: From Fixed Visual Tokens to Dynamic Information-Gain Maximization**  
**系列：Adaptive Perceptual Reading（APR）／自適應感知閱讀理論，第 5 篇**  
**版本：v0.1（2026-08-07）**

---

## 摘要

多模態人工智慧的效率問題正由「如何壓縮視覺 token」逐步轉向「如何在不同輸入與任務之間動態配置有限計算資源」。2025–2026 年的研究已分別展示 context-aware resolution selection、per-frame visual budget allocation、query-aware long-video token routing、dynamic sparse attention，以及視覺 token 與 LLM compute 的聯合調度。這些成果共同說明：固定解析度、固定 token 數與固定推理成本並不是多模態推論的必要形式。

本文提出「感知預算經濟」（Perceptual Budget Economy, PBE）作為 Adaptive Perceptual Reading（APR）的第五層。本文將感知與推理資源表示成多維預算：

$$
\mathbf B_t
=
(
B^{tok}_t,
B^{flop}_t,
B^{lat}_t,
B^{mem}_t,
B^{eng}_t,
B^{io}_t
)
$$

並將智能體可分配的資源位置擴展到：

$$
\mathbf a_t
=
(
a^{mod},
a^{space},
a^{time},
a^{repr},
a^{reason},
a^{memory},
a^{reobs}
)
$$

分別對應模態選擇、空間解析度、時間解析度、表示 token、推理深度、記憶與重觀察。智能體的目標不再是單純最小化 token，而是在風險與可靠性約束下，最大化單位成本能取得的任務資訊與行動效用。

本文提出多資源約束優化、邊際資訊價值、影子價格、最小充分感知、預算彈性、風險保留預算、感知—推理耦合與停止規則，並把 APR-01 至 APR-04 的差分感知、觀看模式與 Persistent World State 納入同一個 constrained decision process。本文的核心命題為：

**有限資源下的多模態智能，不應問「每個輸入給多少固定 token」，而應持續問「下一單位計算資源現在花在哪裡最有價值」。**

**關鍵詞：** 感知預算、視覺 token、動態計算、資訊增益、資源配置、Adaptive Compute、Multimodal LLM、Active Perception、Persistent World State、Agentic Perception

---

## 1. 問題：Token 數不是唯一的成本

多模態模型經常用：

$$
N_{vision\ tokens}
$$

描述視覺成本。

這很重要，但不完整。

實際系統至少同時受到：

$$
\text{Token}
$$

$$
\text{FLOPs}
$$

$$
\text{Latency}
$$

$$
\text{Memory}
$$

$$
\text{Energy}
$$

$$
\text{I/O}
$$

等約束。

因此本文定義多維預算：

$$
\boxed{
\mathbf B_t
=
(
B^{tok}_t,
B^{flop}_t,
B^{lat}_t,
B^{mem}_t,
B^{eng}_t,
B^{io}_t
)
}
$$

在雲端離線影片分析中，主要瓶頸可能是：

$$
B^{tok},B^{flop}
$$

在即時機器人中，可能是：

$$
B^{lat},B^{eng}
$$

在邊緣裝置中，可能是：

$$
B^{mem},B^{eng}
$$

因此不存在一個普遍的：

$$
\text{Best Token Count}
$$

更合理的是：

$$
\boxed{
\text{Best Allocation Under Current Resource Constraints}
}
$$

---

## 2. 前沿研究已開始把「多少計算」變成決策

### 2.1 CARES：最小充分解析度

CARES 對 image–query pair 預測「最小充分輸入解析度」，而不是所有圖片一律以最高解析度送入 VLM。其核心思想可抽象為：

$$
\rho^*
=
\min_{\rho}
\{
\rho:
Perf(\rho,Q)\ge Perf_{target}
\}
$$

這已非常接近本文後面提出的：

$$
\text{Sufficient Perception}
$$

概念。

### 2.2 ResAdapt：每幀視覺預算

ResAdapt 在視覺 encoder 之前決定每個 frame 應接受多少 input-side visual budget，並將配置問題形式化為 contextual bandit。

因此：

$$
b^{frame}_i
\neq
b^{frame}_j
$$

可以依內容與任務動態變化。

### 2.3 Tempo：固定總預算下的動態時間頻寬

Tempo 對長影片使用 Adaptive Token Allocation，在嚴格總視覺 token 預算下，對 query-critical segments 給予較高 token 密度，對冗餘背景大幅壓縮。

這意味著：

$$
\sum_i b_i
\le
B
$$

但：

$$
b_i
$$

由資訊價值而不是固定 frame rate 決定。

### 2.4 Dynamic Sparse Attention：動態 attention 稀疏度

2026 年 Dynamic Sparse Attention 使用 entropy-conditioned predictor 產生 input-adaptive masks，把跨模態 attention computation 集中到較有訊號的 token pair。

所以可動態配置的不只是 input tokens，還包括：

$$
\text{Attention Edges}
$$

### 2.5 SmartVL：視覺 token 與模型計算聯合調度

SmartVL 進一步同時控制：

$$
N_{visual}
$$

與：

$$
C_{LLM}
$$

並使用共享 budget encoding 協調 vision-side token controller 與 LLM-side compute controller。

這是非常重要的轉變：

$$
\boxed{
\text{Perception Budget}
\leftrightarrow
\text{Reasoning Budget}
}
$$

已開始被當成同一個資源調度問題。

---

## 3. APR-05 的位置

上述工作已證明：

- 解析度可以動態；
- frame budget 可以動態；
- token 數可以動態；
- attention sparsity 可以動態；
- LLM compute 可以動態。

因此 APR-05 不主張：

> Dynamic token allocation 是新的。

本文要提出的是更高層的資源市場：

$$
\boxed{
\text{Perceptual Budget Economy}
}
$$

其中以下資源共同競爭有限預算：

$$
\{
\text{modality},
\text{space},
\text{time},
\text{representation},
\text{reasoning},
\text{memory},
\text{re-observation}
\}
$$

也就是：

$$
\mathbf a_t
=
(
a^{mod}_t,
a^{space}_t,
a^{time}_t,
a^{repr}_t,
a^{reason}_t,
a^{memory}_t,
a^{reobs}_t
)
$$

---

## 4. 從固定 Token 到資源配置向量

傳統配置可以近似為：

$$
b_i=b_0
\quad
\forall i
$$

例如每個 frame：

$$
256\ tokens
$$

或每秒：

$$
1\ FPS
$$

或每張圖：

$$
\rho=1024
$$

APR 則允許：

$$
b_i
=
f(
X_i,
G_t,
W_t,
U_t,
R_t,
B_t
)
$$

其中：

- $X_i$：候選輸入；
- $G_t$：目標；
- $W_t$：Persistent World State；
- $U_t$：不確定性；
- $R_t$：風險；
- $B_t$：剩餘預算。

所以同一影片中的不同時刻可有：

$$
b_1=1
$$

$$
b_2=1
$$

$$
b_3=16
$$

$$
b_4=0
$$

但更進一步，同一時刻還可以把資源分到不同維度：

$$
a_t^{space}=H
$$

$$
a_t^{time}=L
$$

$$
a_t^{reason}=M
$$

這比單一 token budget 更一般。

---

## 5. 感知資源項目

本文將可調整資源分成七大類。

### 5.1 模態預算

$$
a^{mod}
$$

決定：

- 看 RGB 嗎？
- 聽 audio 嗎？
- 讀 depth 嗎？
- 讀 DOM 嗎？
- 讀 LiDAR 嗎？
- 讀 sensor state 嗎？

如果 structured state 已足夠：

$$
VisualBudget\rightarrow0
$$

也是合法決策。

### 5.2 空間預算

$$
a^{space}
=
(
\rho^s,
\omega
)
$$

決定：

- 解析度；
- ROI 面積；
- tile 數；
- zoom level。

### 5.3 時間預算

$$
a^{time}
=
(
\rho^t,
h
)
$$

決定：

- frame rate；
- temporal window；
- history horizon；
- playback density。

### 5.4 表示預算

$$
a^{repr}
$$

決定：

- 保留多少 visual tokens；
- 哪些 tokens 被 merge/prune；
- attention sparsity；
- KV retention。

### 5.5 推理預算

$$
a^{reason}
$$

決定：

- LLM layers；
- reasoning tokens；
- tool calls；
- search depth；
- verification rounds。

### 5.6 記憶預算

$$
a^{memory}
$$

決定：

- 哪些狀態長期保存；
- 哪些證據留在 hot memory；
- compression ratio；
- cache size。

### 5.7 重觀察預算

$$
a^{reobs}
$$

決定：

- 是否回看；
- 回看哪裡；
- 回看多久；
- 用何解析度；
- 是否 full refresh。

---

## 6. 效用函數

本文令一次感知配置 $\mathbf a$ 的期望效用為：

$$
U(\mathbf a)
=
I(\mathbf a)
+
\alpha G(\mathbf a)
+
\beta R(\mathbf a)
+
\gamma S(\mathbf a)
-
C(\mathbf a)
$$

其中：

- $I$：Information Gain；
- $G$：Goal relevance；
- $R$：Risk coverage；
- $S$：World-state consistency gain；
- $C$：成本。

成本又可以表示為：

$$
C(\mathbf a)
=
\lambda_{tok}C_{tok}
+
\lambda_{flop}C_{flop}
+
\lambda_{lat}C_{lat}
+
\lambda_{mem}C_{mem}
+
\lambda_{eng}C_{eng}
+
\lambda_{io}C_{io}
$$

不同硬體與任務使用不同：

$$
\lambda
$$

例如手機端：

$$
\lambda_{eng}\uparrow
$$

即時控制：

$$
\lambda_{lat}\uparrow
$$

離線研究：

$$
\lambda_{lat}\downarrow
$$

---

## 7. 多資源約束問題

APR-PBE 的一般形式：

$$
\boxed{
\mathbf a_t^*
=
\arg\max_{\mathbf a}
\mathbb E[
U(\mathbf a)
]
}
$$

subject to：

$$
C_{tok}(\mathbf a)
\le
B^{tok}_t
$$

$$
C_{flop}(\mathbf a)
\le
B^{flop}_t
$$

$$
C_{lat}(\mathbf a)
\le
B^{lat}_t
$$

$$
C_{mem}(\mathbf a)
\le
B^{mem}_t
$$

$$
C_{eng}(\mathbf a)
\le
B^{eng}_t
$$

以及安全約束：

$$
P(
CriticalMiss
\mid
\mathbf a
)
\le
\epsilon
$$

因此最優解不是：

$$
\min Tokens
$$

而是：

$$
\boxed{
\max TaskUtility
\quad
\text{under bounded resources and bounded risk}
}
$$

---

## 8. 邊際資訊價值

假設資源類型為 $j$。

定義它的邊際價值：

$$
MV_j
=
\frac{
\partial \mathbb E[U]
}{
\partial b_j
}
$$

智能體應優先把下一單位資源配置到：

$$
j^*
=
\arg\max_j
\frac{
MV_j
}{
MC_j
}
$$

其中：

$$
MC_j
$$

為 marginal cost。

例如目前問題是讀小字。

增加：

$$
1\ unit\ spatial\ resolution
$$

的邊際價值可能很高：

$$
MV_{space}\gg MV_{reason}
$$

因此不應繼續增加 reasoning tokens。

相反地，如果影像已經非常清楚但問題需要多步因果推理：

$$
MV_{reason}\gg MV_{space}
$$

就應停止放大圖片，把資源轉給推理。

這正是 APR-03：

$$
\rho^s
\neq
\rho^t
\neq
\rho^r
$$

在資源經濟上的意義。

---

## 9. 感知與推理的替代與互補

感知與推理不是永遠可互相替代。

### 9.1 替代區

某些任務中：

$$
MorePerception
\leftrightarrow
MoreReasoning
$$

例如場景模糊時，多看幾個 frame 可能降低推理難度。

### 9.2 不可替代區

如果影像中的細字根本沒有被解析：

$$
Evidence=0
$$

則：

$$
Reasoning\rightarrow\infty
$$

也不能恢復不存在的證據。

因此：

$$
\boxed{
Reasoning\ cannot\ recover\ unavailable\ evidence
}
$$

反過來，如果證據已充分但問題需要邏輯推導：

$$
Perception\rightarrow\infty
$$

也不能替代必要推理。

所以兩者更接近互補投入：

$$
Performance
=
F(
P,
R
)
$$

其中：

$$
P=PerceptualInvestment
$$

$$
R=ReasoningInvestment
$$

其最優解要求動態平衡，而非固定比例。

---

## 10. 最小充分感知

CARES 已經明確使用 minimal sufficient resolution 的思想。

本文把它推廣成：

### Minimum Sufficient Perception

尋找：

$$
\mathbf a_{suff}
$$

使：

$$
P(
Success
\mid
\mathbf a_{suff}
)
\ge
1-\epsilon
$$

且：

$$
C(\mathbf a_{suff})
$$

最小。

形式上：

$$
\boxed{
\mathbf a_{suff}
=
\arg\min_{\mathbf a}
C(\mathbf a)
}
$$

subject to：

$$
P(
TaskSuccess|\mathbf a
)
\ge
\tau
$$

與：

$$
P(
CriticalMiss|\mathbf a
)
\le
\epsilon
$$

APR 的目標因此不是：

$$
\text{Minimal Perception}
$$

而是：

$$
\boxed{
\text{Minimal Sufficient Reliable Perception}
}
$$

---

## 11. 影子價格：不同資源在不同時刻的價值不同

多資源 constrained optimization 可以引入 Lagrangian：

$$
\mathcal L
=
-\mathbb E[U(\mathbf a)]
+
\sum_k
\lambda_k
(
C_k(\mathbf a)-B_k
)
$$

其中：

$$
\lambda_k
$$

可以解釋為資源 $k$ 的：

$$
\boxed{
ShadowPrice
}
$$

例如 GPU 接近滿載：

$$
\lambda_{flop}\uparrow
$$

電池不足：

$$
\lambda_{eng}\uparrow
$$

延遲快超時：

$$
\lambda_{lat}\uparrow
$$

此時同一任務的最優觀看方式會改變。

因此：

$$
\boxed{
\text{Perceptual Policy}
}
$$

不只依任務與場景，也依：

$$
\text{Current System Condition}
$$

---

## 12. 動態預算與預算彈性

令初始 budget：

$$
B_0
$$

智能體不一定必須一次決定全部消耗。

可以先投入：

$$
b_1
$$

觀察結果。

若：

$$
U_1\downarrow
$$

則追加：

$$
b_2
$$

形成：

$$
B
=
b_1+b_2+\cdots+b_n
$$

這可以稱為：

$$
\boxed{
Progressive Budget Commitment
}
$$

例如：

$$
Glance(cheap)
$$

若足夠：

$$
Stop
$$

否則：

$$
Scan
$$

仍不夠：

$$
Inspect
$$

再不夠：

$$
Deep/Reobserve
$$

因此 APR-03 的 mode transition 本質上也是：

$$
\boxed{
Budget Escalation Policy
}
$$

---

## 13. 預算升級條件

增加感知預算可由下列條件觸發。

### 不確定性

$$
U_t>\tau_U
$$

### 風險

$$
R_t>\tau_R
$$

### 新奇性

$$
Novelty_t>\tau_N
$$

### 任務相關性

$$
Rel_t>\tau_G
$$

### 狀態矛盾

$$
Conflict(W_t)>0
$$

### 預測誤差

$$
D(O_t,\hat O_t)>\tau_D
$$

因此：

$$
b_{t+1}
=
b_t
+
\Delta b(
U,R,N,G,D
)
$$

---

## 14. 停止規則

智能體也必須知道何時不再花錢。

若額外資源：

$$
\delta b
$$

帶來的預期增益：

$$
\Delta U
$$

小於成本：

$$
\Delta C
$$

則：

$$
\frac{\Delta U}{\Delta C}
<
\tau_{stop}
$$

應停止。

即：

$$
\boxed{
MarginalInformationGain
<
MarginalCost
\Rightarrow
Stop
}
$$

這可以防止：

- 無限 zoom；
- 無限回看；
- 無限 reasoning；
- 無限 tool call；
- 無限 verification。

---

## 15. 風險保留預算

若系統把所有預算都投入目前最相關區域，可能漏掉未知的重要事件。

因此定義：

$$
B_t
=
B_t^{task}
+
B_t^{safety}
+
B_t^{explore}
$$

### 任務預算

$$
B^{task}
$$

用於當前 goal。

### 安全預算

$$
B^{safety}
$$

保留給：

- 全局監視；
- 高風險區域；
- critical-state verification。

### 探索預算

$$
B^{explore}
$$

用於：

- 隨機抽查；
- 新奇事件；
- 避免 attention tunnel vision。

因此即使：

$$
Rel_G(region)=0
$$

某些區域仍可能獲得最低：

$$
b_{min}>0
$$

以避免純 exploitation。

---

## 16. Exploration–Exploitation in Perception

感知資源配置也具有：

$$
Exploration
\leftrightarrow
Exploitation
$$

問題。

Exploitation：

$$
\text{多看目前認為重要的地方}
$$

Exploration：

$$
\text{確認是不是漏掉其他重要東西}
$$

如果只做 exploitation：

$$
P(BlindSpot)\uparrow
$$

如果只做 exploration：

$$
Efficiency\downarrow
$$

所以可定義：

$$
a_t
=
\arg\max_a
[
ExpectedUtility(a)
+
\kappa UncertaintyReduction(a)
]
$$

其中：

$$
\kappa
$$

控制探索程度。

這使 active perception 與 contextual bandit 類方法自然進入 APR。

---

## 17. Persistent World State 對預算的影響

APR-04 提出：

$$
W_t
$$

作為持續世界狀態。

如果目前世界狀態高度可信：

$$
Confidence(W_t)\uparrow
$$

且新變化低：

$$
\Delta^{sig}\downarrow
$$

則：

$$
PerceptualBudget\downarrow
$$

反之：

$$
StateStaleness\uparrow
$$

$$
Conflict\uparrow
$$

$$
Uncertainty\uparrow
$$

則：

$$
ReobservationBudget\uparrow
$$

因此：

$$
\boxed{
Memory can save perception,
but stale memory should spend perception.
}
$$

Persistent state 不只是記憶機制，也會改變未來的資源分配。

---

## 18. State Value of Information

對某個世界狀態 $s_i$，定義重新確認它的 Value of Information：

$$
VOI(s_i)
=
\mathbb E[
U\mid Verify(s_i)
]
-
\mathbb E[
U\mid NoVerify(s_i)
]
$$

若：

$$
VOI(s_i)>Cost(Verify(s_i))
$$

則應重觀察。

例如：

$$
door.locked?
$$

若接下來機器人要高速通過該門：

$$
Risk\uparrow
$$

因此：

$$
VOI(door.state)\uparrow
$$

即使門的像素完全沒變，也值得重新看。

這與 APR-02：

$$
\Delta^{pix}
\neq
\Delta^{sig}
$$

完全一致。

---

## 19. Tokenization After Policy 的嚴格版本

APR-01 曾提出：

$$
TokenizationAfterAttention
$$

但嚴格而言，完全沒有低成本前置感知就不可能先知道哪裡重要。

APR-05 將其改寫成三段：

$$
\boxed{
CheapProbe
\rightarrow
BudgetDecision
\rightarrow
ExpensiveEncoding
}
$$

即：

$$
X
\xrightarrow{C_{cheap}}
z^{probe}
$$

$$
z^{probe},G,W,B
\rightarrow
\mathbf a
$$

$$
X
\xrightarrow[\mathbf a]{C_{expensive}}
Z
$$

所以最精確的命題是：

$$
\boxed{
\text{Expensive Tokenization Conditioned on Perceptual Policy}
}
$$

不是：

$$
\text{No Tokenization Before Attention}
$$

---

## 20. 預算市場

可把不同感知／推理模組想成競爭資源的 bidder。

令模組：

$$
j
\in
\{
Vision,
Audio,
Memory,
Reasoning,
Reobserve,
Safety
\}
$$

每個模組提交：

$$
Bid_j
=
(
ExpectedGain_j,
Cost_j,
Urgency_j,
Risk_j
)
$$

Budget Controller 選：

$$
A^*
=
\arg\max_A
\sum_{j\in A}
ExpectedGain_j
$$

subject to：

$$
\sum_{j\in A}Cost_j
\le
B
$$

這不一定要實作成真正拍賣。

「市場」只是功能類比：

> 多個認知操作競爭同一有限計算資源。

這使 APR 可與未來多 Agent / modular cognitive architectures 接合。

---

## 21. 時間價值

感知結果的價值也與時間相關。

若答案在：

$$
100ms
$$

後才有用，但模型需要：

$$
2s
$$

才能完成 deep perception：

$$
Utility\approx0
$$

因此加入 deadline：

$$
T_{deadline}
$$

有效效用：

$$
U_{eff}
=
U
\cdot
D(
Latency,T_{deadline}
)
$$

其中：

$$
D\rightarrow0
$$

當：

$$
Latency>T_{deadline}
$$

因此即時 Agent 應最大化：

$$
\boxed{
Timely Useful Information
}
$$

而不只是最終 accuracy。

---

## 22. 能源與邊緣裝置

動態稀疏與 edge multimodal research 已指出，動態策略必須同時考慮硬體友善性。

理論上：

$$
FLOPs\downarrow
$$

不一定代表：

$$
Latency\downarrow
$$

也不一定代表：

$$
Energy\downarrow
$$

若動態 routing 造成：

- irregular memory access；
- poor GPU utilization；
- branch overhead；
- kernel launch overhead；

則理論節省不一定成為實際節省。

因此：

$$
C(\mathbf a)
$$

應盡量使用：

$$
MeasuredRuntimeCost
$$

而不是只有：

$$
TheoreticalFLOPs
$$

SmartVL 使用 differentiable latency estimator 協調 joint scheduling，也正好說明這一點。

---

## 23. Perceptual Budget Controller

APR-05 的最小 Budget Controller 輸入：

$$
I_t
=
(
G_t,
W_t,
\Delta^{sig}_t,
U_t,
R_t,
\mathbf B_t,
HardwareState_t
)
$$

輸出：

$$
\mathbf a_t
=
(
modality,
ROI,
resolution,
fps,
tokens,
reasoning,
memory,
reobserve
)
$$

執行後觀察：

$$
Outcome_t
$$

再更新：

$$
\mathbf B_{t+1}
$$

與 policy。

形成：

$$
\boxed{
Observe
\rightarrow
Allocate
\rightarrow
Spend
\rightarrow
Measure
\rightarrow
Reallocate
}
$$

---

## 24. Constrained MDP 表示

可以進一步把 APR-PBE 表示為 constrained MDP。

狀態：

$$
s_t
=
(
W_t,
G_t,
U_t,
R_t,
B_t,
H_t
)
$$

動作：

$$
a_t
=
PerceptualAllocation
$$

轉移：

$$
P(s_{t+1}|s_t,a_t)
$$

reward：

$$
r_t
=
TaskGain_t
-
\lambda Cost_t
-
\mu Risk_t
$$

並要求：

$$
\mathbb E[
\sum_t Cost_t
]
\le
B
$$

與：

$$
P(CriticalFailure)\le\epsilon
$$

因此可以使用：

- contextual bandit；
- reinforcement learning；
- model predictive control；
- dynamic programming；
- heuristic controller；

等不同工程方法。

APR 是問題定義，不綁定單一 optimizer。

---

## 25. Pareto Frontier 而不是單一分數

多模態效率研究不應只報：

$$
Accuracy
$$

也不應只報：

$$
CompressionRatio
$$

而應觀察：

$$
\boxed{
Accuracy
\leftrightarrow
Cost
}
$$

甚至多維 Pareto：

$$
(
Accuracy,
Latency,
Energy,
Memory,
CriticalMiss
)
$$

一個模型 $A$ 若 token 少，但 latency 更高，不一定比模型 $B$ 有效。

因此 APR-05 要求至少報：

$$
TaskUtility
$$

$$
VisualTokens
$$

$$
ReasoningTokens
$$

$$
Latency
$$

$$
PeakMemory
$$

$$
Energy
$$

$$
CriticalMissRate
$$

與：

$$
ReobservationCost
$$

---

## 26. 可驗證假說

### H1：動態多維配置優於固定 Token

在混合任務集上：

$$
Pareto(PBE)
>
Pareto(FixedToken)
$$

即 PBE 應形成更優 accuracy–cost frontier。

### H2：聯合感知—推理分配優於單邊調整

若只調：

$$
VisualTokens
$$

而固定：

$$
ReasoningCompute
$$

應不如聯合調整：

$$
(
Visual,
Reasoning
)
$$

尤其在同時包含 perception-heavy 與 reasoning-heavy 的資料集上。

### H3：Progressive Commitment 優於一次性最大配置

先低成本 probe，再逐步升級：

$$
C_{progressive}
<
C_{max}
$$

而：

$$
Accuracy_{progressive}
\approx
Accuracy_{max}
$$

### H4：Persistent State 能降低未變世界的感知預算

在長時間穩態環境：

$$
Budget(W_t\text{-aware})
<
Budget(memoryless)
$$

### H5：Risk Reserve 能降低小變化關鍵事件漏失

具有：

$$
B^{safety}
$$

的系統，應在相近平均成本下具有更低：

$$
CriticalMissRate
$$

### H6：Measured Cost Optimization 優於 FLOP-only

在真實 GPU / edge hardware：

$$
Policy_{latency-aware}
$$

應比：

$$
Policy_{FLOP-only}
$$

具有更好的實際 deadline success rate。

---

## 27. MVP 設計

### 27.1 任務集合

建立四類任務：

#### Gist-heavy

低解析即可完成。

#### Detail-heavy

需要高空間解析度。

#### Temporal-heavy

需要高 frame rate 或長時間跨度。

#### Reasoning-heavy

視覺證據足夠，但需要多步 reasoning。

再加入：

#### Safety-critical micro-change

小視覺差異，但高風險。

### 27.2 系統

#### System A：Fixed High

$$
HighResolution
+
HighFPS
+
FixedReasoning
$$

#### System B：Fixed Low

$$
LowResolution
+
LowFPS
+
FixedReasoning
$$

#### System C：Adaptive Vision Only

只動態調 visual tokens / resolution。

#### System D：Joint Vision–Reasoning

聯合調整：

$$
visual+reasoning
$$

#### System E：APR-PBE

調整：

$$
\{
space,
time,
tokens,
reasoning,
memory,
reobserve,
safety
\}
$$

### 27.3 主要指標

$$
Accuracy
$$

$$
VisualTokenCost
$$

$$
ReasoningTokenCost
$$

$$
FLOPs
$$

$$
Latency
$$

$$
PeakMemory
$$

$$
Energy
$$

$$
CriticalMissRate
$$

$$
ReobserveCount
$$

$$
StateConsistency
$$

以及：

$$
\boxed{
UtilityPerCost
=
\frac{TaskUtility}{WeightedCost}
}
$$

---

## 28. 消融實驗

至少做以下 ablation。

### 移除 Persistent State

觀察：

$$
VisualCost\uparrow?
$$

### 移除 uncertainty

觀察：

$$
ReobserveQuality\downarrow?
$$

### 移除 safety reserve

觀察：

$$
CriticalMiss\uparrow?
$$

### 固定 reasoning budget

觀察：

$$
ReasoningHeavyAccuracy\downarrow?
$$

### 固定 visual budget

觀察：

$$
DetailHeavyAccuracy\downarrow?
$$

### 不允許 re-observe

觀察：

$$
InitialErrorRecovery\downarrow?
$$

這樣可以驗證 APR 各層是否真的提供獨立價值。

---

## 29. 與既有研究的邊界

本文不主張以下概念本身為新：

- adaptive resolution；
- token pruning；
- dynamic visual token allocation；
- dynamic sparse attention；
- budget-aware inference；
- contextual-bandit visual allocation；
- adaptive reasoning depth；
- joint token–compute scheduling；
- Pareto optimization。

CARES 已實作 minimal sufficient resolution；ResAdapt 已建立 input-side per-frame budget policy；Tempo 已進行 strict-budget adaptive token allocation；Dynamic Sparse Attention 已進行 input-dependent sparse computation；SmartVL 已進一步聯合調節視覺 token 與 LLM compute。

APR-05 的理論位置是：

$$
\boxed{
\text{Perceptual budgeting is broader than visual-token budgeting.}
}
$$

本文把：

$$
\text{Perception}
+
\text{Reasoning}
+
\text{Memory}
+
\text{Re-observation}
+
\text{Risk}
$$

放入同一個資源配置問題。

真正的 allocation target 不是：

$$
N_{vision}
$$

而是：

$$
\boxed{
\mathbf a_t
=
(
modality,
space,
time,
representation,
reasoning,
memory,
reobservation
)
}
$$

---

## 30. 限制

### 30.1 Utility 很難準確估計

智能體往往不知道：

$$
InformationGain
$$

直到真的花資源看完。

因此需要近似 predictor、bandit feedback 或 learned value model。

### 30.2 Controller 自己也花資源

若：

$$
C_{controller}
\gg
C_{saved}
$$

則 adaptive allocation 失去價值。

### 30.3 多維成本難以轉成單一價格

$$
Latency
$$

和：

$$
Energy
$$

不一定可以自然相加。

因此實際系統可能更適合 constrained Pareto optimization，而不是固定 scalar reward。

### 30.4 風險估計可能錯誤

如果系統錯誤認為某區域低風險：

$$
B^{safety}
$$

仍可能不足。

### 30.5 動態 routing 可能不硬體友善

理論上的 sparse compute 不一定帶來真實 latency 節省。

### 30.6 高動態世界可能真的值得高成本感知

APR 並不保證永遠節省大量資源。

若：

$$
InformationRate
\approx
RawDataRate
$$

合理 policy 本來就可能接近 full processing。

---

## 31. 討論：智能的一部分是會「花算力」

在傳統模型裡，計算量多由模型設計者預先決定：

$$
Architecture
\Rightarrow
Compute
$$

而自適應智能逐漸轉向：

$$
Situation
+
Goal
+
Risk
+
Budget
\Rightarrow
Compute
$$

這意味著：

$$
\boxed{
\text{Compute Allocation itself becomes a cognitive action.}
}
$$

智能體不只選擇：

> 我要回答什麼？

還會選擇：

> 這個問題值得花多少資源？

> 我要把資源花在「多看」還是「多想」？

> 我要回去確認證據，還是目前信念已足夠？

> 我現在還剩多少延遲與能量預算？

因此「注意力」最終可能不只是 Transformer 中的矩陣操作，而是一個更一般的資源治理概念。

---

## 32. 結論

本文提出 Perceptual Budget Economy（PBE），作為 APR 的第五層。

感知預算被表示為：

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

配置策略則為：

$$
\boxed{
\mathbf a_t
=
(
a^{mod},
a^{space},
a^{time},
a^{repr},
a^{reason},
a^{memory},
a^{reobs}
)
}
$$

智能體求解：

$$
\boxed{
\mathbf a_t^*
=
\arg\max_{\mathbf a}
\mathbb E[TaskUtility]
}
$$

subject to 多資源與風險約束。

本文因此建立四個核心原則：

$$
\boxed{
\text{Fixed Token Budget}
\rightarrow
\text{Dynamic Multi-Resource Budget}
}
$$

$$
\boxed{
\text{Maximum Perception}
\neq
\text{Optimal Perception}
}
$$

$$
\boxed{
\text{Perception Budget}
\leftrightarrow
\text{Reasoning Budget}
}
$$

以及：

$$
\boxed{
\text{Next Unit of Compute Should Go Where Its Marginal Value Is Highest}
}
$$

APR 前五篇至此形成：

$$
\text{APR-01：感知是一種資源配置}
$$

$$
\Downarrow
$$

$$
\text{APR-02：變化具有不同意義與重要性}
$$

$$
\Downarrow
$$

$$
\text{APR-03：觀看存在不同模式}
$$

$$
\Downarrow
$$

$$
\text{APR-04：觀看持續修正世界狀態}
$$

$$
\Downarrow
$$

$$
\text{APR-05：所有感知與推理操作共同競爭有限預算}
$$

下一篇 APR-06 將離開「視覺」本身，正式回答：

$$
\boxed{
\text{文字、影像、影片、音訊與其他感測資料，是否其實共享同一種 Perceptual Reading Policy？}
}
$$

---

## 參考文獻

1. Kimhi, M., Shabtay, N., Giryes, R., Baskin, C., & Schwartz, E. (2026). *CARES: Context-Aware Resolution Selector for VLMs*. Proceedings of ACL 2026, 2243–2256.
2. Liao, H., Jiang, Z., Hao, Y., Tan, Y., He, S., Wang, B., Zhao, J., Xu, K., & Liu, K. (2026). *ResAdapt: Adaptive Resolution for Efficient Multimodal Reasoning*. arXiv:2603.28610.
3. Fei, J., Chen, J., Liu, Z., et al. (2026). *Small Vision-Language Models are Smart Compressors for Long Video Understanding*. arXiv:2604.08120.
4. Wang, P., Wang, Z., Lee, J., Xu, Z., Xu, R., Bagchi, S., Li, Y., & Chaterji, S. (2026). *Look Less, Think Faster: Joint Token-Compute Adaptation for Multimodal LLMs*. arXiv:2607.20357. Accepted at ECCV 2026.
5. Tao, Z., Zhang, H., Kong, L., et al. (2026). *Dynamic Sparse Attention for Lightweight Multimodal Sensor Fusion on Edge Devices*. Scientific Reports, 16, 22023.
6. Chen, X., Tao, K., Shao, K., & Wang, H. (2026). *StreamingTOM: Streaming Token Compression for Efficient Video Understanding*. CVPR 2026.
7. Qiu, J., Xie, L., Huo, X., Tian, Q., & Ye, Q. (2026). *LongVideo-R1: Smart Navigation for Low-cost Long Video Understanding*. CVPR 2026.
8. Yin, Y., Meng, Q., Chen, M., Ding, J., Shao, Z., & Yu, Z. (2026). *VideoARM: Agentic Reasoning over Hierarchical Memory for Long-Form Video Understanding*. CVPR 2026.
9. Zhang, Y., Shi, C., & Yang, S. (2026). *WeaveTime: Streaming from Earlier Frames into Emergent Memory in VideoLLMs*. CVPR 2026.
10. Huang, X., Zhou, H., & Han, K. (2025). *PruneVid: Visual Token Pruning for Efficient Video Large Language Models*. Findings of ACL 2025.
11. Liao, C.-T., Xiao, X., Meng, C., et al. (2026). *SpaMEM: Benchmarking Dynamic Spatial Reasoning via Perception-Memory Integration in Embodied Environments*. arXiv:2604.22409.
12. Liu, C., Yang, Y., Pu, S. X., et al. (2026). *WorldMemArena: Evaluating Multimodal Agent Memory Through Action-World Interaction*. arXiv:2605.29341.

---

## 系列位置

APR-01：從均勻感知到自適應感知閱讀：多模態智能的感知資源配置理論  
APR-02：從像素差分到語義差分：連續多模態感知中的變化階層  
APR-03：視覺不是一種閱讀：多尺度視覺閱讀模式與重觀察理論  
APR-04：持續世界狀態與差分重觀察：從連續影片理解到持續感知智能  
**APR-05：感知預算分配：從固定視覺 Token 到動態資訊獲益最大化 ← 本文**  
APR-06：跨模態感知閱讀：文字、影像、影片與聲音的統一注意策略  
APR-07：Agentic Perception：具備自主觀看策略的多模態智能架構
