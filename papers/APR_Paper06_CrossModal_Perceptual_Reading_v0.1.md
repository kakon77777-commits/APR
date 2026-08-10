# 跨模態感知閱讀：文字、影像、影片與聲音的統一注意策略

**英文題名：Cross-Modal Perceptual Reading: A Unified Attention Policy for Text, Images, Video, Audio, and Sensor Streams**  
**系列：Adaptive Perceptual Reading（APR）／自適應感知閱讀理論，第 6 篇**  
**版本：v0.1（2026-08-07）**

---

## 摘要

文字、影像、影片、聲音與感測器資料具有不同的物理形式、編碼方式與時間結構，但智能體面對它們時，都必須回答相似的資源配置問題：是否需要讀取、讀取哪一部分、以何種解析度、在什麼時間尺度、推理多深、是否需要回到歷史資料重讀，以及何時停止。2025–2026 年的研究已分別出現文字 token-level dynamic early exit、audio token pruning、query-conditioned modality routing、audio-guided video compression、active omni-modal perception 與 multimodal long-term memory，顯示「不同模態使用不同處理強度」正在由局部效率技巧逐步成為跨模態智能的共同問題。

本文提出 Cross-Modal Perceptual Reading Policy（CMPRP，跨模態感知閱讀政策），作為 Adaptive Perceptual Reading（APR）的第六層。本文不主張所有模態共享相同 encoder，而是提出它們可共享更高階的感知控制語義：

$$
\Pi_t^{read}:
(
G_t,
W_t,
U_t,
R_t,
\mathbf B_t
)
\rightarrow
(
m_t,
\Omega_t,
\rho_t,
\nu_t,
d_t,
h_t,
q_t
)
$$

其中智能體先選擇模態 $m_t$，再決定資料區域／時間區間 $\Omega_t$、解析度 $\rho_t$、讀取速率 $\nu_t$、推理深度 $d_t$、歷史跨度 $h_t$ 與是否重讀 $q_t$。本文將文字的掃讀／精讀／重讀、影像的瞥視／掃視／精視、影片的取樣／追視／回放、音訊的監聽／聚焦／重播，以及 GUI／感測器的事件監控／狀態查詢統一為若干共同操作原語。

本文進一步提出「模態不是必須被同等啟用」、「可直接讀狀態時不必重新視覺化」、「跨模態冗餘可以替代而非累加」、「模態衝突應觸發跨模態重讀」等命題，並建立跨模態路由、證據互補、模態替代、同步窗口與 modality value-of-information 的形式化描述。核心命題為：

**閱讀不是文字專屬行為；它可以被抽象為智能體對任何可感知資訊流進行選擇性取得、分辨率配置、推理與重取證據的一般政策。**

**關鍵詞：** 跨模態感知、多模態路由、感知閱讀、Audio-Visual Reasoning、Omni-modal LLM、動態注意力、模態選擇、Active Perception、Adaptive Compute、Agentic Perception

---

## 1. 問題：不同模態真的需要不同「智能原理」嗎？

文字、影像、聲音與影片的底層表示差異巨大。

文字通常是離散序列：

$$
x_1,x_2,\ldots,x_n
$$

影像是空間場：

$$
I(x,y)
$$

聲音是時間訊號：

$$
A(t)
$$

影片則同時具有空間與時間：

$$
V(x,y,t)
$$

從 encoder 層看，它們確實需要不同處理方法。

然而從智能體層看，它們都會遇到同樣問題：

1. 現在需要使用這個模態嗎？
2. 哪一部分資訊與任務最有關？
3. 需要多高的解析程度？
4. 需要處理多久的歷史？
5. 需要快速掃過還是深入分析？
6. 若目前證據不足，應該重讀哪一段？
7. 是否可以改用另一個模態取得相同狀態？
8. 何時資訊已充分，可以停止？

因此本文區分：

$$
\boxed{
\text{Modality-Specific Encoding}
}
$$

與：

$$
\boxed{
\text{Modality-General Perceptual Control}
}
$$

前者可以不同；

後者可能共享同一高階政策。

---

## 2. 前沿研究已開始出現跨模態動態路由

Omni-modal 模型的發展使這個問題變得直接。

OmniSelect 針對 audio-video OmniLLM，不再假設不同 query 對音訊與影像的重要性相同，而先估計 cross-modal relevance，再把輸入分成 Audio-Centric、Video-Centric 與 Uniform 等不同 pruning regime，並進一步動態配置各時間群組的 token pruning 比例。

這意味著：

$$
\boxed{
m_t^{important}
=
f(Q,X_{audio},X_{video})
}
$$

而不是：

$$
audio=video
$$

永遠同權。

OmniZip 則反過來使用 salient audio tokens 與 audio retention score 指導 video token compression，使音訊成為「何時值得多看影片」的控制訊號。

因此：

$$
AudioEvidence
\rightarrow
VisualBudget
$$

已經具有實際技術形式。

AOP-Agent 更進一步把長時間 audio-visual multi-hop reasoning 寫成 active omni-modal perception，透過 hierarchical omni-modal memory 與 observe–reflect–replan loop 主動取得跨模態證據。

所以：

$$
\boxed{
\text{Cross-modal perception}
}
$$

正開始從「一次融合」轉向「持續選擇下一個該取得的證據」。

---

## 3. 「不用這個模態」本身也是感知行動

Router-Suggest 在 visually grounded dialogue 中動態選擇：

$$
TextModel
$$

或：

$$
VisionLanguageModel
$$

也就是當視覺上下文對當前輸入沒有足夠價值時，不必每次都支付 VLM 成本。

這可抽象為：

$$
m_t
\in
\{
text,
vision,
audio,
video,
state,
sensor,
\varnothing
\}
$$

其中：

$$
m_t=\varnothing
$$

代表：

> 目前不需要額外感知。

因此：

$$
\boxed{
\text{Modality Activation}
}
$$

本身就是 APR 的一部分。

這尤其適合桌面 Agent。

如果問題是：

> 目前瀏覽器 URL 是什麼？

若可以直接取得：

$$
BrowserState.url
$$

則不必：

$$
Screenshot
\rightarrow
OCR
\rightarrow
URL
$$

也就是：

$$
\boxed{
\text{Prefer direct state when state is available and trustworthy.}
}
$$

---

## 4. 文字其實也存在「視覺式」動態閱讀

文字常被誤解為：

> Token 都已經進 context，所以模型就是全部一起讀。

但計算層仍可以不同。

2026 年 ADEPT 使用 adaptive token-level early exit，讓不同 token 依複雜度經過不同 Transformer 深度。

可以抽象為：

$$
d_i
=
f(
x_i,
context,
difficulty
)
$$

而不是：

$$
d_i=D_{max}
\quad
\forall i
$$

ACL 2026 的 Adaptive Layer Selection 則會依 attention rank variance 等訊號，動態決定 layer-wise KV token selection 發生在哪一層，以在不同任務難度下取得速度—準確率平衡。

因此：

$$
\boxed{
\text{Text Already Tokenized}
\not\Rightarrow
\text{Text Must Receive Uniform Compute}
}
$$

文字中的「速讀／精讀」可以在人工模型中表現為：

- token selection；
- retrieval；
- early exit；
- variable reasoning depth；
- selective rereading；
- query-conditioned context expansion。

所以「閱讀模式」不是只存在於人類主觀描述中。

---

## 5. 音訊也有不同讀法

音訊序列具有非常高的時間冗餘。

一段長時間聲音可能包含：

- 靜音；
- 穩態背景噪聲；
- 重複音樂；
- 固定 speaker；
- 關鍵詞；
- 非語音事件；
- 語調與情緒；
- 瞬態警報。

HeadRouter 顯示，大型音訊語言模型中的 attention heads 對不同 acoustic / semantic task 具有不同重要性；它根據任務動態選擇適合的 head importance 進行 audio token pruning。

因此：

$$
\boxed{
\text{Audio Reading}
\neq
\text{Uniform Time-Series Processing}
}
$$

同一段錄音可以被：

- Monitor：只監聽是否有事件；
- Speech Scan：搜尋特定字詞；
- Acoustic Inspect：分析非語音聲響；
- Speaker Track：追蹤說話者；
- Semantic Listen：理解語義；
- Deep Listen：結合長上下文推理；
- Replay：回放關鍵時間段。

這與 APR-03 的視覺閱讀模式具有直接結構對應。

---

## 6. 跨模態感知閱讀政策

本文定義：

$$
\boxed{
\Pi_t^{read}:
(
G_t,
W_t,
U_t,
R_t,
\mathbf B_t
)
\rightarrow
\Theta_t^{cross}
}
$$

其中：

$$
\Theta_t^{cross}
=
(
m_t,
\Omega_t,
\rho_t,
\nu_t,
d_t,
h_t,
q_t
)
$$

各項含義：

- $m_t$：啟用哪個模態；
- $\Omega_t$：空間區域、文本區段或時間窗口；
- $\rho_t$：解析度／表示精度；
- $\nu_t$：採樣或閱讀速率；
- $d_t$：推理深度；
- $h_t$：回顧歷史跨度；
- $q_t$：是否重新取得證據。

不同模態只需各自實作：

$$
Execute_m(\Theta_t^{cross})
$$

例如：

$$
Execute_{text}
$$

可能是 retrieval + deep reread；

$$
Execute_{image}
$$

可能是 crop + high-resolution inspection；

$$
Execute_{audio}
$$

可能是 temporal replay + acoustic model；

$$
Execute_{GUI}
$$

可能直接 query DOM state。

因此高階政策可以共享，而低階執行可以保持 modality-specific。

---

## 7. 統一的感知操作原語

本文提出七個跨模態操作原語。

### 7.1 Monitor

低成本監控：

$$
\mathcal R_0=Monitor
$$

文字：

> 是否有新訊息？

影像：

> 是否有變化？

音訊：

> 是否有人開始說話／有警報聲？

感測器：

> 是否超過閾值？

### 7.2 Glance / Skim

快速取得 gist：

$$
\mathcal R_1=Skim
$$

文字是掃讀摘要；

圖片是場景瞥視；

影片是低 FPS overview；

音訊是低密度摘要或 speech activity overview。

### 7.3 Search / Scan

尋找特定證據：

$$
\mathcal R_2=Search
$$

文字：

$$
Ctrl+F
$$

影像：

$$
VisualSearch
$$

音訊：

$$
Keyword/EventSearch
$$

影片：

$$
TemporalLocalization
$$

### 7.4 Track

維持時間連續性：

$$
\mathcal R_3=Track
$$

文字中可以是追蹤某個概念或 entity；

影片中追蹤人物／物件；

聲音中追蹤 speaker；

感測器中追蹤變量趨勢。

### 7.5 Inspect

提高資料精度：

$$
\mathcal R_4=Inspect
$$

文字：

> 逐字精讀條款。

影像：

> zoom OCR。

音訊：

> 高解析分析短聲音。

感測器：

> 讀取 raw waveform 而非平均值。

### 7.6 Deep Read

提高推理深度：

$$
\mathcal R_5=Deep
$$

可以跨多模態建立：

- 因果推理；
- 矛盾檢查；
- 多步證據鏈；
- 世界模型修正。

### 7.7 Re-read / Re-observe

重新取得過去證據：

$$
\mathcal R_6=Revisit
$$

文字：

> 回頭重讀上一章。

影片：

> 回放。

音訊：

> replay。

GUI：

> 重新截圖／重新讀 DOM。

感測器：

> 查閱歷史 raw log。

因此：

$$
\boxed{
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
}
$$

可以作為 modality-independent 的感知動作語彙。

---

## 8. 「讀法相同」不等於「資料處理相同」

本文並不是說：

$$
Text=Image=Audio
$$

也不是說所有模態都應轉成文字。

更精確地：

$$
\boxed{
\text{Control Semantics can be shared even when representations differ.}
}
$$

例如：

$$
Inspect(text)
$$

可能是提高 contextual reasoning；

$$
Inspect(image)
$$

可能是提高 spatial resolution；

$$
Inspect(audio)
$$

可能是提高 temporal / spectral precision。

它們底層不同，但高階共同意義都是：

> 已定位相關證據，現在增加局部辨識精度。

這就像：

$$
Read(file)
$$

可以對不同檔案格式有不同 parser，但高階 API 仍叫：

$$
Read
$$

---

## 9. Modality Value of Information

對每個候選模態：

$$
m
\in
\mathcal M
$$

定義：

$$
VOI(m)
=
\mathbb E[
U\mid Observe(m)
]
-
\mathbb E[
U\mid NoObserve(m)
]
$$

再考慮成本：

$$
Score(m)
=
VOI(m)-\lambda C(m)
$$

選擇：

$$
m_t^*
=
\arg\max_m Score(m)
$$

例如：

> 「門目前開著嗎？」

若視覺不確定但 door sensor 可用：

$$
VOI(sensor)\gg VOI(vision)
$$

則應直接查 sensor。

如果 sensor 疑似故障：

$$
Reliability(sensor)\downarrow
$$

則：

$$
VOI(vision)\uparrow
$$

因此模態選擇應依：

$$
\boxed{
Relevance
+
Reliability
+
Cost
+
Risk
}
$$

共同決定。

---

## 10. 模態替代

不同模態有時可以提供相同世界狀態。

令欲估計狀態：

$$
s
$$

可由：

$$
Vision\rightarrow s
$$

或：

$$
Audio\rightarrow s
$$

或：

$$
Sensor\rightarrow s
$$

取得。

若：

$$
P(s|m_1)
\approx
P(s|m_2)
$$

但：

$$
C(m_1)\ll C(m_2)
$$

則優先：

$$
m_1
$$

因此：

$$
\boxed{
\text{Multimodality does not imply always using all modalities.}
}
$$

多模態能力的價值之一反而是：

> 有更多可替代的取證路徑。

---

## 11. 模態互補

另一類情況不能替代。

例如：

視覺看到：

$$
person\ speaking
$$

音訊知道：

$$
what\ was\ said
$$

文字字幕提供：

$$
exact\ wording
$$

三者共同形成：

$$
E=
E_v\cup E_a\cup E_t
$$

且：

$$
I(E_v,E_a,E_t)
>
\max(
I(E_v),
I(E_a),
I(E_t)
)
$$

這是：

$$
\boxed{
Complementary Evidence
}
$$

所以感知路由不是永遠只選一個 modality。

它可以選：

$$
M_t^*
\subseteq
\mathcal M
$$

並求：

$$
M_t^*
=
\arg\max_{M}
[
VOI(M)-C(M)
]
$$

---

## 12. 模態冗餘

很多時候多個模態只是重複同一資訊。

例如：

影片中有人說：

> 「門打開了。」

同時畫面也看見門開。

字幕又顯示：

> Door is open.

則：

$$
Redundancy(E_v,E_a,E_t)\uparrow
$$

如果目前只需要知道：

$$
door.state
$$

不必永久以最高精度處理三條證據。

因此：

$$
\boxed{
\text{Cross-modal redundancy should be compressed, not automatically accumulated.}
}
$$

OmniZip 使用音訊 salient event 指導 video compression，就是一個低階實例：

$$
Audio
\rightarrow
ReduceRedundantVideo
$$

---

## 13. 跨模態時間同步

音訊與影片往往共享時間軸。

令：

$$
E_a(t)
$$

為音訊事件；

$$
E_v(t)
$$

為視覺事件。

若音訊偵測：

$$
glass\ breaking
$$

發生在：

$$
t=t_0
$$

則可以提升：

$$
VisualBudget(t_0-\delta,t_0+\delta)
$$

因此：

$$
\boxed{
\text{One modality can act as temporal attention for another modality.}
}
$$

同理：

視覺看到有人張嘴：

$$
\rightarrow
AudioSpeakerFocus
$$

GUI 出現通知：

$$
\rightarrow
AudioMonitoring\downarrow
$$

或 sensor temperature spike：

$$
\rightarrow
CameraInspect(machine)
$$

這使跨模態政策成為真正互相調度的系統。

---

## 14. 跨模態空間對齊

對具身系統，模態還可能共享空間：

$$
Vision(x,y,z)
$$

$$
AudioDirection(\theta,\phi)
$$

$$
LiDAR(x,y,z)
$$

$$
Thermal(x,y)
$$

如果麥克風陣列判斷聲音來自：

$$
Direction=d
$$

視覺可以：

$$
TurnCamera(d)
$$

如果 thermal sensor 指出：

$$
hotspot(x,y)
$$

RGB camera 可以：

$$
Inspect(x,y)
$$

因此：

$$
\boxed{
\text{Cross-modal attention can be spatial routing.}
}
$$

而不只是 token fusion。

---

## 15. 模態衝突

多模態不是永遠互相證明。

可能：

$$
Vision:
door=closed
$$

但：

$$
Sensor:
door=open
$$

或者：

$$
Audio:
person\ says\ ``red''
$$

但：

$$
VisualObject=blue
$$

因此定義：

$$
Conflict(m_i,m_j)
$$

若：

$$
Conflict>\tau_C
$$

不應簡單 averaging。

而應觸發：

$$
\boxed{
CrossModalReRead
}
$$

例如：

1. 提高影像解析度；
2. 重新聽原始 audio；
3. 查 sensor provenance；
4. 對齊 timestamp；
5. 檢查是否不同 entity；
6. 更新世界狀態置信度。

---

## 16. Reliability-aware Modality Routing

令：

$$
r_m
=
Reliability(m)
$$

例如：

- camera 被遮擋；
- microphone 有雜訊；
- sensor 失準；
- OCR confidence 低；
- ASR confidence 低。

則：

$$
Score(m)
=
VOI(m)
\cdot
r_m
-
\lambda C(m)
$$

A2MAML 類工作已展示 uncertainty-aware modality-level selection：不同 agent–modality pair 可依不確定性被抑制或提高權重。

因此：

$$
\boxed{
\text{More modalities}
\neq
\text{more reliable perception}
}
$$

如果多個低品質模態一起輸入，反而可能提高噪音。

---

## 17. Modality State Machine

定義 active modality set：

$$
M_t
\subseteq
\{
Text,
Vision,
Video,
Audio,
GUI,
Depth,
Sensor
\}
$$

狀態轉移：

$$
M_{t+1}
=
T(
M_t,
G_t,
W_t,
U_t,
R_t,
B_t
)
$$

例如：

### Text → Text + Vision

若：

$$
TextEvidenceInsufficient=1
$$

且：

$$
VisualContextAvailable=1
$$

### Vision → Vision + Audio

若：

$$
TemporalEventDetected
$$

且語義需 audio 補充。

### Audio → Sensor

若：

$$
machine\ anomaly
$$

需要確認實際物理狀態。

### Any → State-only

若：

$$
PersistentWorldState
$$

已足以回答。

因此跨模態 perception 不是：

$$
AllModalitiesAlwaysOn
$$

而是：

$$
\boxed{
Dynamic Modality Activation
}
$$

---

## 18. Cross-Modal Reading Trajectory

APR-03 提出：

$$
\mathcal T_P
$$

感知閱讀軌跡。

跨模態版可寫成：

$$
\mathcal T_C
=
[
(m_1,r_1,\Theta_1),
(m_2,r_2,\Theta_2),
\ldots
]
$$

其中：

- $m_i$：模態；
- $r_i$：閱讀模式；
- $\Theta_i$：具體解析度與預算。

例如處理會議影片：

$$
(Audio,Monitor)
$$

$$
\rightarrow
(Audio,TrackSpeaker)
$$

$$
\rightarrow
(Video,ScanSlide)
$$

$$
\rightarrow
(Image,InspectText)
$$

$$
\rightarrow
(Text,DeepRead)
$$

$$
\rightarrow
(Video,Revisit)
$$

這就是一條：

$$
\boxed{
CrossModalPerceptualTrajectory
}
$$

---

## 19. 文字作為壓縮模態，而不是最高模態

多模態系統常把影像、聲音最後轉成文字。

這很實用，但不能假設：

$$
Text
=
LosslessSemanticRepresentation
$$

例如音訊中的：

- 情緒；
- 音高；
- 節奏；
- speaker identity；
- 非語音聲響；

或影像中的：

- 幾何；
- 細部空間關係；
- 顏色；
- 紋理；

可能在 caption 中丟失。

因此：

$$
\boxed{
Text Summary
=
Useful Compression,
\quad
not Universal Lossless Representation.
}
$$

APR-04 的 Evidence Layer 因此仍需要保留原始模態證據。

---

## 20. 直接狀態模態

除了人類常說的文字、聲音與影像，Agent 還有一類非常重要的「模態」：

$$
\boxed{
StructuredState
}
$$

例如：

- DOM；
- Accessibility Tree；
- game state；
- robot joint state；
- GPS；
- database；
- system event；
- API response。

它們可能不是傳統感官，但對智能體而言都是資訊取得通道。

若：

$$
StateChannel
$$

比視覺更直接，則：

$$
Cost(State)
<
Cost(Vision)
$$

且：

$$
Reliability(State)
\ge
Reliability(Vision)
$$

時，應優先 State。

因此 APR 的「跨模態」應比傳統：

$$
Vision+Audio+Text
$$

更寬。

---

## 21. Perceptual Reading API

工程上可定義一個統一控制 API：

```text
read(
    target,
    modality = auto,
    mode = auto,
    region = auto,
    time_range = auto,
    resolution = auto,
    reasoning_depth = auto,
    history = auto,
    budget = current
)
```

高階 planner 可以提出：

```text
read(
    target="warning_state",
    modality="auto",
    mode="inspect",
    budget="low_latency"
)
```

Policy Controller 再決定：

```text
sensor -> confirm threshold
vision -> inspect warning light ROI
audio -> skip
```

這個 API 不要求底層模型統一，只統一：

$$
\boxed{
\text{Perceptual Intent Interface}
}
$$

---

## 22. 統一成本模型

對模態 $m$、模式 $r$ 與參數 $\Theta$：

$$
C(m,r,\Theta)
$$

總效用：

$$
U(m,r,\Theta)
=
IG
+
\alpha Rel
+
\beta RiskCov
+
\gamma StateConsistency
-
C
$$

因此：

$$
(m^*,r^*,\Theta^*)
=
\arg\max
U(m,r,\Theta)
$$

subject to APR-05 的：

$$
\mathbf C
\le
\mathbf B
$$

與：

$$
P(CriticalMiss)<\epsilon
$$

所以 APR-06 並不是獨立於 APR-05。

它把 APR-05 的 resource allocation action space 從：

$$
VisualResources
$$

擴張成：

$$
\boxed{
CrossModalResources
}
$$

---

## 23. 跨模態停止條件

若目前 active modalities 已使：

$$
Confidence(W_t,Q)\ge\tau
$$

且：

$$
ExpectedVOI(m_{new})
<
Cost(m_{new})
$$

則：

$$
DoNotActivate(m_{new})
$$

例如文字已清楚指出：

> 系統時間為 10:32。

若來源可信且問題只是問時間，沒有必要：

$$
Screenshot\rightarrow OCR
$$

做第二次驗證。

但如果這是高風險操作：

$$
Risk\uparrow
$$

則：

$$
VOI(second\ modality)\uparrow
$$

因此 cross-modal verification 應任務依賴。

---

## 24. 跨模態閱讀與 Persistent World State

APR-04 的：

$$
W_t
$$

是不同模態共同寫入的共享狀態。

因此：

$$
W_t
=
Fuse(
\Delta W_t^{text},
\Delta W_t^{vision},
\Delta W_t^{audio},
\Delta W_t^{sensor},
\Delta W_t^{action}
)
$$

但：

$$
W_t
$$

不應要求保存所有模態完整內容。

State Layer 只保存：

$$
\text{current belief}
$$

而 Evidence Layer 保存：

$$
\text{modality-specific provenance}
$$

例如：

```text
door_4.state = open
confidence = 0.97
evidence:
  - door_sensor_221
  - frame_9921
last_verified = 16:42:08
```

若之後有矛盾，可以針對：

$$
door_4
$$

進行：

$$
CrossModalReobserve
$$

---

## 25. 可驗證假說

### H1：動態模態啟用優於全模態常開

在模態相關性隨 query 改變的 benchmark：

$$
Cost_{dynamic}
<
Cost_{all-on}
$$

且：

$$
Accuracy_{dynamic}
\approx
Accuracy_{all-on}
$$

或更高。

### H2：跨模態政策優於各模態獨立 policy

若 audio、video、text 各自只做本模態 pruning，而不交換 relevance signal，應不如：

$$
CrossModalRouting
$$

尤其在一個 modality 可指出另一 modality 關鍵時間／區域的任務中。

### H3：模態替代可以降低成本

若兩個模態估計相同 state，dynamic selector 應偏好：

$$
\frac{Reliability}{Cost}
$$

較高者。

### H4：模態互補應觸發聯合閱讀

對 genuinely complementary evidence：

$$
Perf(m_i+m_j)
>
\max(
Perf(m_i),
Perf(m_j)
)
$$

Policy 應學會同時啟用兩者。

### H5：衝突觸發重讀優於直接融合

當模態互相矛盾時：

$$
Reobserve
$$

應比：

$$
StaticWeightedAverage
$$

具有較低高信心錯誤率。

### H6：文字也具有自適應閱讀收益

在 text-only long-context 任務中，adaptive retrieval / early exit / selective rereading 應形成與視覺 APR 類似的 accuracy–cost Pareto 優勢。

---

## 26. MVP

建立一個同步多模態測試環境：

- 影片；
- 原始音訊；
- 字幕；
- GUI state；
- structured event log。

設計五類問題。

### Audio-centric

例如：

> 誰先說出某個詞？

### Vision-centric

例如：

> 誰拿走了紅色物件？

### Text-centric

例如：

> 投影片上列出的第三項條款是什麼？

### State-centric

例如：

> 現在程式是否完成下載？

可直接讀 progress state。

### Cross-modal

例如：

> 說「關掉它」的人指的是畫面中的哪台設備，設備之後真的關閉了嗎？

需要：

$$
Audio
+
Vision
+
StateTransition
$$

---

## 27. 系統比較

### System A：All Modalities Full

所有模態全程高成本。

### System B：Single Best Modality

人工指定單一模態。

### System C：Independent Adaptive

每個模態各自 pruning，但沒有 cross-modal policy。

### System D：Dynamic Modality Router

動態選模態，但沒有 APR reading modes。

### System E：APR-CMPRP

可以同時決定：

$$
modality
+
mode
+
region
+
time
+
resolution
+
reasoning
+
revisit
$$

---

## 28. 評估指標

$$
TaskAccuracy
$$

$$
ModalityActivationRate
$$

$$
AudioTokens
$$

$$
VisualTokens
$$

$$
TextTokens
$$

$$
SensorQueries
$$

$$
Latency
$$

$$
Energy
$$

$$
CrossModalConflictRate
$$

$$
ConflictRecoveryRate
$$

$$
RevisitCount
$$

以及：

$$
\boxed{
UsefulInformationPerCost
}
$$

特別加入：

$$
UnnecessaryModalityActivation
$$

衡量系統是否總是「有模態就全部打開」。

---

## 29. 與既有研究的邊界

本文不主張以下能力本身為新：

- modality routing；
- multimodal fusion；
- token pruning；
- audio-guided visual compression；
- audio token pruning；
- early exit；
- multimodal memory；
- active audio-visual reasoning；
- mixture-of-experts modality routing。

OmniSelect 已做 query-dependent modality-aware compression；OmniZip 已做 audio-guided audiovisual compression；HeadRouter 已做 task-adaptive audio token pruning；ADEPT 已做 token-level adaptive early exit；Router-Suggest 已在 text model / VLM 之間做動態 routing；AOP-Agent 已提出 active omni-modal perception。

APR-06 的位置是：

$$
\boxed{
\text{All of these can be interpreted as instances of a common perceptual reading policy.}
}
$$

其共同控制語義為：

$$
\boxed{
\text{Which channel?}
+
\text{Which evidence?}
+
\text{How much detail?}
+
\text{How much reasoning?}
+
\text{When to revisit?}
}
$$

---

## 30. 限制

### 30.1 不同模態未必可以完全共享 policy representation

文字與 event camera 的統計結構差異極大，因此 modality-general controller 仍可能需要 modality-specific features。

### 30.2 Cross-modal router 本身可能成為瓶頸

若每次選模態都需要大型 omni-model：

$$
C_{router}
$$

可能過高。

### 30.3 低成本模態不一定更可信

structured state 可能被 API bug 污染；字幕也可能 ASR 錯誤。

所以：

$$
Cheap
\neq
Reliable
$$

### 30.4 同步問題很難

audio、video、sensor、GUI event 的 timestamp 可能有不同 latency 與 clock drift。

### 30.5 模態缺失與退化

真實世界中：

$$
m_t
$$

可能暫時不可用。

Policy 必須支援：

$$
GracefulFallback
$$

### 30.6 語義對齊並不自動產生

不同模態 token 進同一 Transformer，不代表它們已經建立可靠的 cross-modal causal alignment。

---

## 31. 討論：閱讀是一種一般資訊行為

「閱讀」這個詞通常被限制於文字。

但如果抽象掉人類媒介，其結構其實是：

$$
\boxed{
\text{Selective acquisition of information under a purpose}
}
$$

人類讀書時不會每頁每句永遠使用完全相同注意力。

看電影時不會每個像素永遠同樣重要。

聽演講時不會把冷氣背景聲與關鍵論點賦予同等處理。

操作電腦時也不會每毫秒重新理解整個桌面。

因此：

$$
\boxed{
Reading
}
$$

可以從一個語言行為提升成：

$$
\boxed{
Perceptual Information Acquisition Policy
}
$$

它回答的不是：

> 這是不是文字？

而是：

> 在目前目標與資源下，我應該如何取得足夠且可靠的資訊？

---

## 32. 結論

本文提出 Cross-Modal Perceptual Reading Policy（CMPRP），將 APR 從視覺推廣到文字、影片、音訊、GUI 與感測器。

高階政策表示為：

$$
\boxed{
\Pi_t^{read}:
(
G_t,
W_t,
U_t,
R_t,
\mathbf B_t
)
\rightarrow
(
m_t,
\Omega_t,
\rho_t,
\nu_t,
d_t,
h_t,
q_t
)
}
$$

不同模態保留自己的 encoder 與執行工具，但共享：

$$
\boxed{
Monitor,
Skim,
Search,
Track,
Inspect,
Deep,
Revisit
}
$$

等一般感知操作語義。

本文建立五項核心原則：

$$
\boxed{
\text{Multimodal}
\neq
\text{All Modalities Always On}
}
$$

$$
\boxed{
\text{Same State Can Have Multiple Evidence Channels}
}
$$

$$
\boxed{
\text{Different Modalities Can Substitute or Complement Each Other}
}
$$

$$
\boxed{
\text{One Modality Can Allocate Attention to Another}
}
$$

以及：

$$
\boxed{
\text{Reading Is a Modality-General Information Acquisition Policy}
}
$$

APR 前六篇至此形成：

$$
\text{APR-01：感知是一種資源配置}
$$

$$
\Downarrow
$$

$$
\text{APR-02：變化具有階層與重要性}
$$

$$
\Downarrow
$$

$$
\text{APR-03：觀看具有不同閱讀模式}
$$

$$
\Downarrow
$$

$$
\text{APR-04：感知持續修正世界狀態}
$$

$$
\Downarrow
$$

$$
\text{APR-05：感知、推理與記憶共同競爭預算}
$$

$$
\Downarrow
$$

$$
\boxed{
\text{APR-06：上述政策可跨文字、影像、影片、音訊與狀態通道統一}
}
$$

下一篇 APR-07 將完成系列整合：

$$
\boxed{
\text{Agentic Perception}
}
$$

即建立一個能自主決定：

$$
\text{看不看、看什麼、看哪裡、聽什麼、讀什麼、記什麼、何時重看、何時停止}
$$

的完整多模態智能架構。

---

## 參考文獻

1. Yang, M., Xu, R., Li, L., et al. (2026). *OmniSelect: Dynamic Modality-Aware Token Compression for Efficient Omni-modal Large Language Models*. arXiv:2605.18041.
2. Tao, K., Shao, K., Yu, B., Wang, W., Liu, J., & Wang, H. (2026). *OmniZip: Audio-Guided Dynamic Token Compression for Fast Omnimodal Large Language Models*. CVPR 2026, 17682–17692.
3. Xu, K., Wang, Y., Cheng, Z., et al. (2026). *Agentic Active Omni-Modal Perception for Multi-Hop Audio-Visual Reasoning*. arXiv:2605.28192.
4. He, P., Luo, Y., Liu, X., et al. (2026). *HeadRouter: Dynamic Head-Weight Routing for Task-Adaptive Audio Token Pruning in Large Audio Language Models*. arXiv:2604.23717.
5. Yoo, S., Malla, S., Choi, C., Lu, W. D., & Choi, J. H. (2026). *ADEPT: Adaptive Dynamic Early-Exit Process for Transformers*. arXiv:2601.03700.
6. Taniguchi, R., Dong, Y., Onizuka, M., & Xiao, C. (2026). *Adaptive Layer Selection for Layer-Wise Token Pruning in LLM Inference*. Findings of ACL 2026, 967–986.
7. Mishra, S., Budagam, D., Mandal, A., et al. (2026). *Router-Suggest: Dynamic Routing for Multimodal Auto-Completion in Visually-Grounded Dialogs*. EACL 2026 Industry Track, 145–156.
8. Long, L., He, Y., Ye, W., et al. (2026). *Seeing, Listening, Remembering, and Reasoning: A Multimodal Agent with Long-Term Memory*. ICLR 2026.
9. Lou, Y., Yang, K., & You, Y. (2026). *MoST: Mixing Speech and Text with Modality-Aware Mixture of Experts*. arXiv:2601.10272.
10. Liu, R., Tokekar, P., & Lin, M. (2026). *Active Asymmetric Multi-Agent Multimodal Learning under Uncertainty*. arXiv:2602.04763.
11. Zuo, C., Zhu, Y., Xu, M., et al. (2026). *AMR: Adaptive Modality Routing for Multimodal Polyglot Speaker Identification*. arXiv:2606.29335.
12. Zhang, H., Mengsi, L., He, C., Ao, Y., & Lin, Y. (2026). *TrimTokenator: Towards Adaptive Visual Token Pruning for Large Multimodal Models*. Findings of ACL 2026.
13. Lee, J., Xuan, K., Ekbote, C., et al. (2025). *TAMP: Token-Adaptive Layerwise Pruning in Multimodal Large Language Models*. Findings of ACL 2025.
14. Guo, H., Wang, S., Ma, R., et al. (2025). *OmniVLA: Unifying Multi-Sensor Perception for Physically-Grounded Multimodal VLA*. arXiv:2511.01210.

---

## 系列位置

APR-01：從均勻感知到自適應感知閱讀：多模態智能的感知資源配置理論  
APR-02：從像素差分到語義差分：連續多模態感知中的變化階層  
APR-03：視覺不是一種閱讀：多尺度視覺閱讀模式與重觀察理論  
APR-04：持續世界狀態與差分重觀察：從連續影片理解到持續感知智能  
APR-05：感知預算分配：從固定視覺 Token 到動態資訊獲益最大化  
**APR-06：跨模態感知閱讀：文字、影像、影片與聲音的統一注意策略 ← 本文**  
APR-07：Agentic Perception：具備自主觀看策略的多模態智能架構
