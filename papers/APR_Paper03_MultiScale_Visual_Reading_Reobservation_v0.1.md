# 視覺不是一種閱讀：多尺度視覺閱讀模式與重觀察理論

**英文題名：Vision Has More Than One Reading Mode: Multi-Scale Visual Reading and Re-observation Theory**  
**系列：Adaptive Perceptual Reading（APR）／自適應感知閱讀理論，第 3 篇**  
**版本：v0.1（2026-08-07）**

## 摘要

當代多模態模型正在逐步突破固定解析度、固定影格率與固定視覺 token 預算：高解析影像可以先粗看，再定位任務相關區域並局部放大；長影片可以先低頻掃描，再對關鍵時間片段提高 frame rate、重新驗證甚至修正第一次選錯的位置。這些能力已分別出現在 region selection、query-aware zoom、temporal navigation、hierarchical memory 與 active tool use 等研究中。

本文提出「多尺度視覺閱讀模式」（Multi-Scale Visual Reading Modes, MVRM），作為 Adaptive Perceptual Reading（APR）的第三層。本文主張，「看」並非單一操作。正如文字存在掃讀、速讀、精讀、深讀與重讀，視覺智能也應具有監視、瞥視、掃視、追視、精視、深視與重觀察等不同模式。這些模式不是單純由解析度高低排列，而是由多個可獨立控制的感知自由度共同形成，包括空間解析度、時間解析度、視野覆蓋、推理深度、歷史跨度與重觀察能力。

本文形式化定義視覺閱讀狀態與模式轉移，提出「同一輸入、多種觀看」、「高解析度不等於深理解」、「重觀察是正常智能行為」等命題，並給出 MVP 與可驗證假說。其核心命題為：

**視覺輸入可以相同，但智能體的觀看行為不必相同；真正的視覺智能不只是看見，而是知道應該用什麼方式看。**

**關鍵詞：** 自適應視覺、視覺閱讀、主動視覺、粗到細感知、重觀察、視覺注意、影片理解、多模態智能、Agentic Perception

---

## 1. 問題：為什麼閱讀有很多種，但「看」常被當成一種？

人類對文字的處理從來不是單一模式。同一篇文章可以被掃讀、速讀、精讀、深讀、搜尋特定詞，或回頭重讀。因此：

$$
\text{Reading}\neq\text{Uniform Processing}
$$

文字內容沒有改變：

$$
X=X
$$

但在不同任務與閱讀策略下：

$$
R(X;G_1,M_1)\neq R(X;G_2,M_2)
$$

然而，在多模態人工智慧中，「看一張圖」常被簡化成：

$$
I\rightarrow VisionEncoder(I)\rightarrow Z
$$

「看一段影片」則常被表示為：

$$
F_1,F_2,\ldots,F_T\rightarrow VideoEncoder\rightarrow Z
$$

即使系統已使用 dynamic resolution、frame sampling 或 token pruning，概念上仍容易把「觀看」視為一種統一操作。

本文提出：

$$
\boxed{\text{Vision}\neq\text{One Perceptual Act}}
$$

更一般地：

$$
V_t=\mathcal O(X,G_t,M_t,A_t,\Theta_t)
$$

其中：

- $X$：原始視覺資料；
- $G_t$：任務；
- $M_t$：記憶；
- $A_t$：注意策略；
- $\Theta_t$：觀看模式參數。

因此即使：

$$
X_t=X_{t+1}
$$

仍可能：

$$
V_t\neq V_{t+1}
$$

因為新的問題可以讓同一張圖片產生不同的觀看行為。

---

## 2. 人類視覺本身就是非均勻感知系統

人類中央凹提供高解析視覺，而周邊視野較偏向粗略資訊，因此有效視覺更接近：

$$
\text{Global Low-Detail Field}
+
\text{Local High-Detail Sampling}
$$

而不是：

$$
\text{Uniform Maximum Resolution}
$$

更重要的是，人類會移動眼睛、頭部乃至身體以取得更有資訊量的視角。真實世界 3D 視覺搜尋研究顯示，受試者會主動選擇遮擋較少、資訊更充分的位置，而不是只被動接收固定視角。

task-dependent gaze 研究也長期指出：同一場景在不同任務指令下，可以產生不同 fixation 與掃視序列。

因此：

$$
\boxed{
\text{What is seen}
\neq
\text{What is physically available}
}
$$

而更接近：

$$
\text{What is seen}
=
f(
\text{scene},
\text{task},
\text{gaze},
\text{memory},
\text{budget}
)
$$

---

## 3. 近期 MLLM 已開始出現「不同看法」

### 3.1 空間 coarse-to-fine

PinPoint 先找出 instruction-relevant image regions，再對局部區域抽取細粒度視覺特徵。Q-Zoom 則先以 coarse global features 判斷是否需要高解析處理，必要時再定位 task-relevant ROI。

抽象為：

$$
I^{low}\rightarrow ROI\rightarrow I^{high}_{ROI}
$$

而不是：

$$
I^{high}_{all}\rightarrow FullProcessing
$$

### 3.2 時間 coarse-to-fine

Zoom-Zero 先定位與問題相關的時間區段，再對重要影格做 temporal zoom-in。VideoZoomer 從低 frame-rate 全局概覽開始，在推理途中自主提高特定時間區段的 frame rate。

因此：

$$
Video^{low\_fps}
\rightarrow
[t_a,t_b]
\rightarrow
Video^{high\_fps}_{[t_a,t_b]}
$$

### 3.3 主動導航與停止

LongVideo-R1 從高階影片摘要開始，逐步選擇最有資訊量的片段，並在資訊充分時停止探索。VideoARM 則建立 observe–think–act–memorize 迴圈，以工具與階層記憶進行 coarse-to-fine 理解。

因此模型逐漸具有兩種能力：

$$
\text{Where to look next?}
$$

與：

$$
\text{Have I seen enough?}
$$

### 3.4 歷史再展開

WeaveTime 在串流 Video-LLM 中使用不確定性觸發的 coarse-to-fine history retrieval，代表歷史視覺資訊不必永遠保持最高成本表示。

上述工作共同指出：

$$
\boxed{\text{Visual Processing Depth Can Be Conditional}}
$$

---

## 4. 多尺度視覺閱讀模式

本文定義觀看狀態：

$$
\Theta_t
=
(
\rho^s_t,
\rho^t_t,
\omega_t,
d_t,
h_t,
q_t
)
$$

其中：

- $\rho^s_t$：空間解析度；
- $\rho^t_t$：時間解析度；
- $\omega_t$：視野覆蓋比例；
- $d_t$：推理深度；
- $h_t$：歷史跨度；
- $q_t$：是否啟用重觀察。

因此：

$$
\boxed{
\text{Visual Depth}
\neq
\text{Image Resolution Alone}
}
$$

一個系統可以看得很廣但很粗、看得很窄但很細、看得很快但推理很淺，也可以在解析度不變時提高推理深度。

---

## 5. 模式 0：監視 Monitor

監視不是完全不看，而是保持最低成本的持續感知，回答：

> 是否發生值得升級感知的事情？

可使用：

- frame difference；
- event stream；
- low-resolution thumbnail；
- DOM/UI event；
- object tracker；
- lightweight encoder。

其輸出可簡化為：

$$
E_t=
\{
change,
confidence,
location
\}
$$

它相當於視覺系統的待機層。

---

## 6. 模式 1：瞥視 Glance

瞥視追求場景 gist：

> 大概是什麼？

典型配置：

$$
\rho^s=L,\quad
\rho^t=L,\quad
\omega=G,\quad
d=L
$$

它適合回答：

- 室內或室外；
- 是否有人；
- 畫面大致是文件、遊戲、簡報或監控；
- 影片大致在發生什麼。

瞥視主要建立初始 prior：

$$
P(S|X_{coarse})
$$

---

## 7. 模式 2：掃視 Scan

掃視的目的不是全面理解，而是搜尋特定目標、異常或證據。

令目標為 $g$：

$$
\pi_{scan}
=
\arg\max_{\pi}
P(
locate(g)\mid\pi
)
$$

subject to：

$$
Cost(\pi)\le B_{scan}
$$

例如：

- 找警告圖示；
- 找特定人物；
- 找某次事件；
- 找文件上的金額；
- 找畫面哪裡出現新物件。

因此其核心是：

$$
\boxed{\text{Locate Relevant Evidence}}
$$

可類比文字的：

$$
\boxed{Visual\ Ctrl+F}
$$

---

## 8. 模式 3：追視 Track

影片還需要另一種模式：找到重要物件後持續追蹤，而不是每一幀重新搜尋。

令目標為 $o_t$：

$$
P(o_t|o_{t-1},X_t)
$$

追視可處理：

- object tracking；
- speaker tracking；
- trajectory tracking；
- action continuation；
- GUI focus tracking；
- state-transition tracking。

典型情況可能是：

$$
\rho^s=M,\quad
\rho^t=H,\quad
\omega=L,\quad
d=L/M
$$

這說明：

$$
\boxed{
\text{High Temporal Attention}
\neq
\text{High Spatial Attention}
}
$$

快速手部動作可能只需要提高：

$$
\rho^t
$$

而不需要整個畫面都提高空間解析度。

---

## 9. 模式 4：精視 Inspect

精視處理：

> 已知要看哪裡，但需要確認細節。

例如：

- 數字是 $38.2$ 還是 $88.2$？
- 儀表指針在哪一格？
- 手中拿了什麼？
- 錯誤訊息小字寫什麼？

其形式是：

$$
ROI
\rightarrow
Crop
\rightarrow
HighResolution
\rightarrow
FineRecognition
$$

典型配置：

$$
\rho^s=H,\quad
\omega=L,\quad
d=M
$$

PinPoint、Q-Zoom、Zoom-Refine 都已提供這類局部高解析處理的技術例證。

但：

$$
\boxed{Inspect\neq Deep}
$$

精視代表感知精度增加，不表示推理深度必然增加。

---

## 10. 模式 5：深視 Deep Perception

深視不是單純把圖片放大，而是：

$$
d_t\uparrow
$$

包括：

- 多步推理；
- 跨影格比較；
- 查閱記憶；
- 建立因果假說；
- 比較替代解釋；
- 工具使用；
- 驗證初步答案。

有些任務不需要更高像素解析度，但需要：

$$
h_t\uparrow,\quad d_t\uparrow
$$

因此：

$$
\boxed{
\text{Fine Perception}
\neq
\text{Deep Perception}
}
$$

高解析圖片可以被淺層處理；低解析影片也可能需要深度推理。

---

## 11. 模式 6：重觀察 Re-observe

第一次觀察：

$$
X\xrightarrow{\Theta_1}Z_1
$$

之後出現新問題 $Q_2$、證據衝突或高不確定性：

$$
U\uparrow
$$

智能體可以重新設定：

$$
\Theta_2\neq\Theta_1
$$

再：

$$
X\xrightarrow{\Theta_2}Z_2
$$

即使：

$$
X=X
$$

也可以：

$$
Z_1\neq Z_2
$$

重觀察可以是：

- 看同一張圖的另一區；
- 放大；
- 回放影片；
- 提高 frame rate；
- 慢放；
- 讀取更早歷史；
- 換另一個視覺工具；
- 從原始資料重新建立證據。

Zoom-Refine 的初步回答→局部放大→重新修正，以及 VideoZoomer 在推理過程中修正初始 frame selection，都提供了這種能力的局部實例。

因此：

$$
\boxed{\text{Re-observation is not failure}}
$$

而是正常的 epistemic action。

---

## 12. 同一輸入，多種觀看

### 命題 1：觀看非唯一性

對同一視覺輸入 $X$：

$$
(G_1,M_1,U_1)
\neq
(G_2,M_2,U_2)
$$

則最優策略可不同：

$$
\Theta^*_1\neq\Theta^*_2
$$

因此：

$$
\mathcal O(X;\Theta^*_1)
\neq
\mathcal O(X;\Theta^*_2)
$$

例如同一張街景：

問題 A「有幾輛車？」需要：

$$
Scan(objects)
$$

問題 B「左側招牌寫什麼？」需要：

$$
Scan(sign)\rightarrow Inspect(sign)
$$

問題 C「是否存在交通危險？」則可能需要：

$$
Scan\rightarrow Track\rightarrow Deep
$$

輸入相同，但觀看路徑不同。

---

## 13. 三個核心解析度軸

### 13.1 空間解析度

$$
\rho^s
$$

控制每個空間位置看多細。

### 13.2 時間解析度

$$
\rho^t
$$

控制時間上看多密。

### 13.3 推理解析度／深度

$$
\rho^r\equiv d
$$

控制對已取得證據思考多深。

因此：

$$
\boxed{\rho^s,\rho^t,\rho^r}
$$

是三個可以獨立控制的軸。

例如：

$$
\rho^s=H,\quad
\rho^t=L,\quad
\rho^r=L
$$

可以是高解析 OCR；

$$
\rho^s=L,\quad
\rho^t=H,\quad
\rho^r=M
$$

可以是快速運動追蹤；

$$
\rho^s=M,\quad
\rho^t=M,\quad
\rho^r=H
$$

可以是一般畫質下的深度影片推理。

因此：

$$
\boxed{\text{More Vision}}
$$

並不是單一方向。

---

## 14. 視野覆蓋與歷史跨度

令：

$$
\omega_t\in[0,1]
$$

代表高成本處理的空間比例。

瞥視可能：

$$
\omega\approx1,\quad\rho^s=L
$$

精視可能：

$$
\omega\ll1,\quad\rho^s=H
$$

另令：

$$
h_t
$$

表示需要回看的歷史跨度。

即時控制可能：

$$
h_t\approx0
$$

而因果分析可能：

$$
h_t\gg0
$$

WeaveTime 的 uncertainty-triggered history expansion 說明 $h_t$ 也可以是動態參數。

---

## 15. 模式不是硬分類，而是策略空間中的典型區域

一般感知策略空間為：

$$
\mathcal P
=
\{
(\rho^s,\rho^t,\omega,d,h,q)
\}
$$

例如：

$$
Glance\approx(L,L,G,L,L,0)
$$

$$
Track\approx(M,H,L,L/M,M,0)
$$

$$
Inspect\approx(H,L/M,L,M,L/M,0)
$$

$$
Deep\approx(M,M,M,H,H,0/1)
$$

$$
Reobserve\approx(\ast,\ast,\ast,\ast,H,1)
$$

所以模式名稱的作用主要是：

> 為感知策略提供可解釋的控制語義。

實際模型仍可使用連續 policy。

---

## 16. 模式轉移

令：

$$
m_t\in
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

模式轉移為：

$$
m_{t+1}
=
T(
m_t,
\Delta^{sig}_t,
G_t,
U_t,
R_t,
B_t
)
$$

例如：

$$
Monitor\rightarrow Glance
\quad\text{if}\quad
Novelty>\tau_N
$$

$$
Glance\rightarrow Scan
\quad\text{if}\quad
GoalRequiresLocalization=1
$$

$$
Scan\rightarrow Inspect
\quad\text{if}\quad
TargetFound\land FineDetailNeeded
$$

$$
Scan\rightarrow Track
\quad\text{if}\quad
TemporalContinuityNeeded
$$

$$
Inspect\rightarrow Deep
\quad\text{if}\quad
ReasoningUnresolved
$$

任何模式都可：

$$
Any\rightarrow Reobserve
$$

若：

$$
U_t>\tau_U
$$

或：

$$
ContradictionDetected=1
$$

這形成一個：

$$
\boxed{Perceptual State Machine}
$$

---

## 17. APR-02 到 APR-03

APR-02 定義：

$$
\Delta^{sig}_t
$$

表示變化的重要性。

APR-03 則回答：

> 發現重要變化後，應該如何看？

因此：

$$
\Delta^{pix}
\rightarrow
\Delta^{feat}
\rightarrow
\Delta^{state}
\rightarrow
\Delta^{sig}
\rightarrow
m_t
\rightarrow
\Theta_t
$$

最後：

$$
Z_t=\mathcal O(X_t;\Theta_t)
$$

感知系統不再只有：

$$
Detected/NotDetected
$$

而可以選擇：

$$
\boxed{\text{How to Perceive}}
$$

---

## 18. 主動觀看與視角選擇

對具身 Agent，觀看還可以改變觀察位置 $Pose_t$：

- 攝影機轉向；
- 頭部轉動；
- 身體移動；
- 靠近物體；
- 改變角度；
- 移除遮擋。

因此可擴展：

$$
\Theta_t
=
(
\rho^s,
\rho^t,
\omega,
d,
h,
q,
Pose
)
$$

這使感知從：

$$
SelectData
$$

進一步成為：

$$
\boxed{ActToAcquireBetterData}
$$

如果機器人看不清楚一個物件，正確動作未必是：

$$
ReasonHarder
$$

而可能是：

$$
MoveCamera
$$

---

## 19. 觀看深度與計算預算

定義：

$$
C(\Theta)
=
C_s(\rho^s,\omega)
+
C_t(\rho^t,h)
+
C_r(d)
+
C_q(q)
$$

智能體選擇：

$$
\Theta_t^*
=
\arg\max_{\Theta}
\left[
\mathbb E[IG(\Theta)]
+
\alpha Rel_G(\Theta)
+
\beta RiskCov(\Theta)
-
\lambda C(\Theta)
\right]
$$

核心不是最大化解析度，而是：

$$
\boxed{
\text{Maximum Resolution}
\neq
\text{Optimal Perception}
}
$$

如果問題只需場景分類，高解析逐像素分析是浪費；如果需要細字辨識，再深的語言推理也無法彌補缺失的影像細節；如果需要捕捉短暫動作，高空間解析但低 frame rate 仍可能失敗。

---

## 20. 感知不足與感知過剩

### 20.1 感知不足

若：

$$
C(\Theta)<C_{required}
$$

導致：

$$
EvidenceInsufficient=1
$$

可能原因包括：

- 解析度不足；
- frame rate 太低；
- ROI 錯誤；
- 歷史跨度太短；
- 沒有重看。

### 20.2 感知過剩

若：

$$
C(\Theta)\gg C_{necessary}
$$

但：

$$
\frac{\partial Utility}{\partial C}\approx0
$$

則額外感知沒有邊際價值。

APR 要尋找的不是：

$$
MinimumPerception
$$

而是：

$$
\boxed{SufficientPerception}
$$

---

## 21. 重觀察觸發條件

重觀察至少可以由五類條件觸發：

### 不確定性

$$
U_t>\tau_U
$$

### 證據衝突

$$
Evidence_A\not\approx Evidence_B
$$

### 新問題

$$
G_{t+1}\neq G_t
$$

### 高風險低信心

$$
Risk_t\uparrow\land Confidence_t\downarrow
$$

### 世界模型與觀測不一致

$$
D(
\hat X_t(W_t),
X_t
)>\tau_D
$$

此時執行：

$$
Reobserve(region,time,resolution,modality)
$$

---

## 22. 感知閱讀軌跡

對完整任務可以記錄：

$$
\mathcal T_P
=
[
(m_1,\Theta_1),
(m_2,\Theta_2),
\ldots,
(m_n,\Theta_n)
]
$$

稱為：

**Perceptual Reading Trajectory／感知閱讀軌跡。**

例如：

$$
Glance
\rightarrow
Scan
\rightarrow
Inspect
\rightarrow
Reobserve
\rightarrow
Deep
\rightarrow
Stop
$$

或：

$$
Monitor
\rightarrow
Track
\rightarrow
Track
\rightarrow
Monitor
$$

此軌跡本身可以成為：

- 訓練資料；
- RL policy trajectory；
- 可解釋性紀錄；
- 成本分析資料；
- Agent debugging 資料。

未來 benchmark 不只問：

$$
AnswerCorrect?
$$

還可以問：

$$
\boxed{DidTheAgentLookEfficiently?}
$$

---

## 23. 可驗證假說

### H1：模式切換優於固定觀看

在包含 gist、search、fine-detail 與 temporal reasoning 的混合任務中，自適應模式切換應形成更好的 Accuracy–Cost Pareto frontier。

### H2：空間與時間解析度應分離控制

細字辨識中：

$$
\frac{\partial Acc}{\partial \rho^s}
>
\frac{\partial Acc}{\partial \rho^t}
$$

高速事件辨識中則應反向：

$$
\frac{\partial Acc}{\partial \rho^t}
>
\frac{\partial Acc}{\partial \rho^s}
$$

### H3：精視不等於深視

存在主要由視覺細節限制的任務 $Q_f$，以及主要由推理限制的任務 $Q_r$：

$$
\frac{\partial Acc(Q_f)}{\partial \rho^s}
>
\frac{\partial Acc(Q_f)}{\partial d}
$$

而：

$$
\frac{\partial Acc(Q_r)}{\partial d}
>
\frac{\partial Acc(Q_r)}{\partial \rho^s}
$$

### H4：重觀察能修復第一次選擇錯誤

允許 Reobserve 的模型，應在 initial ROI error、frame sampling miss 與 ambiguous OCR 任務中降低不可恢復錯誤。

### H5：任務條件觀看軌跡不同

同一影片不同問題：

$$
G_1\neq G_2
$$

應產生：

$$
\mathcal T_P(G_1)\neq\mathcal T_P(G_2)
$$

且差異應與任務效能相關。

---

## 24. MVP 實驗

建立四類任務：

### A. Gist

> 這是哪一類場景？

預期：

$$
Glance
$$

### B. Search

> 警告圖示在哪裡？

預期：

$$
Glance\rightarrow Scan
$$

### C. Fine-detail

> 儀表數值是多少？

預期：

$$
Scan\rightarrow Inspect
$$

### D. Temporal reasoning

> 他在打開抽屜之前做了什麼？

預期：

$$
Glance
\rightarrow
TemporalScan
\rightarrow
Track/Reobserve
\rightarrow
Deep
$$

比較：

- System A：Uniform High；
- System B：Uniform Low；
- System C：Static Coarse-to-Fine；
- System D：MVRM Agent。

量測：

$$
Accuracy
$$

$$
VisualTokens
$$

$$
FramesRead
$$

$$
HighResArea
$$

$$
ReasoningTokens
$$

$$
Latency
$$

$$
ReobserveCount
$$

$$
InitialErrorRecoveryRate
$$

以及：

$$
\boxed{PerceptualUtilityPerCost}
$$

---

## 25. 與既有研究的邊界

本文不主張以下能力本身為新：

- foveated vision；
- saliency；
- active vision；
- region proposal；
- image zoom；
- dynamic resolution；
- temporal zoom；
- frame selection；
- video navigation；
- coarse-to-fine reasoning；
- visual tool use；
- history retrieval。

PinPoint、Q-Zoom、Zoom-Zero、VideoZoomer、LongVideo-R1、VideoARM 與 WeaveTime 已分別展示其中若干能力。

本文提出的是統一描述：

$$
\boxed{
\text{Visual Perception}
=
\text{Mode Selection}
+
\text{Multi-Axis Resource Allocation}
+
\text{Optional Re-observation}
}
$$

也就是：

> zoom、scan、track、deep reasoning、history retrieval 與 re-observation，可以被視為同一個 Perceptual Reading Policy 下的不同視覺行為。

---

## 26. 限制

第一，模式名稱具有人工語義。模型不必內部真的維持七個離散神經模組；MVRM 可以是：

$$
\Theta_t\in\mathbb R^n
$$

的連續 policy。

第二，模式切換本身有成本。若：

$$
C_{routing}>C_{saved}
$$

則自適應控制失去意義，因此 controller 必須保持輕量。

第三，粗略觀看可能漏掉小但重要的訊號，因此需要 minimum coverage、random rescan、risk-sensitive sampling 與 periodic refresh。

第四，高風險領域不能只以平均成本最佳化，而必須約束：

$$
P(CriticalMiss)<\epsilon
$$

第五，並非所有影片都高度冗餘；高動態影片可能自然使最優策略接近 full processing。

---

## 27. 討論：從視覺吞吐轉向視覺閱讀

如果系統的基本邏輯是：

$$
InputArrives
\Rightarrow
ProcessEverything
$$

那麼長時間多模態智能會持續遭遇：

$$
InputBandwidth
\rightarrow
TokenExplosion
\rightarrow
MemoryExplosion
$$

MVRM 提出的另一種邏輯是：

$$
InputArrives
\Rightarrow
ChooseHowToReadIt
$$

真正成熟的感知能力因此不只是：

$$
CanReadImages
$$

而是：

$$
\boxed{
CanChooseHowToReadImages
}
$$

智能不是永遠看最細，而是知道：

- 什麼只需要瞥一眼；
- 什麼需要搜尋；
- 什麼值得持續追蹤；
- 什麼必須放大；
- 什麼需要深度推理；
- 什麼應該回頭再看。

---

## 28. 結論

本文提出多尺度視覺閱讀模式 MVRM，將觀看表示為：

$$
\boxed{
\Theta_t
=
(
\rho^s_t,
\rho^t_t,
\omega_t,
d_t,
h_t,
q_t
)
}
$$

並提出七種功能性典型模式：

$$
\boxed{
Monitor,\;
Glance,\;
Scan,\;
Track,\;
Inspect,\;
Deep,\;
Reobserve
}
$$

它們不是固定線性流程，而是可依目標、不確定性、風險與資源任意轉移的感知狀態。

APR-03 建立三個核心區分：

$$
\boxed{
\text{High Spatial Resolution}
\neq
\text{High Temporal Resolution}
\neq
\text{Deep Reasoning}
}
$$

以及：

$$
\boxed{
\text{Same Input}
\not\Rightarrow
\text{Same Perceptual Act}
}
$$

最後：

$$
\boxed{
\text{Re-observation}
\neq
\text{Failure}
}
$$

而是正常的 epistemic action。

至此：

$$
\text{APR-01: Why allocate perception?}
$$

$$
\Downarrow
$$

$$
\text{APR-02: What change deserves attention?}
$$

$$
\Downarrow
$$

$$
\text{APR-03: How should the agent look?}
$$

下一篇 APR-04 將把上述三層接到：

$$
\boxed{
PersistentWorldState
+
DifferentialUpdate
+
SelectiveRe-observation
}
$$

以回答：

**連續觀看是否真的需要連續重建整個世界？**

---

## 參考文獻

1. Kwon, M., Lee, M., Choi, S., et al. (2026). *Focus, Don't Prune: Identifying Instruction-Relevant Regions for Information-Rich Image Understanding*. CVPR 2026.
2. Shi, Y., Pei, X., Wen, L., Dong, M., & Xu, C. (2026). *Q-Zoom: Query-Aware Adaptive Perception for Efficient Multimodal Large Language Models*. arXiv:2604.06912.
3. Shen, X., Chen, M.-H., Wang, Y.-C. F., Elhoseiny, M., & Hachiuma, R. (2026). *Zoom-Zero: Reinforced Coarse-to-Fine Video Understanding via Temporal Zoom-in*. ICLR Workshop 2026.
4. Ding, Y., Zhang, Y., Lai, X., Chu, R., & Yang, Y. (2025/2026). *VideoZoomer: Reinforcement-Learned Temporal Focusing for Long Video Reasoning*. arXiv:2512.22315.
5. Qiu, J., Xie, L., Huo, X., Tian, Q., & Ye, Q. (2026). *LongVideo-R1: Smart Navigation for Low-cost Long Video Understanding*. CVPR 2026.
6. Yin, Y., Meng, Q., Chen, M., Ding, J., Shao, Z., & Yu, Z. (2026). *VideoARM: Agentic Reasoning over Hierarchical Memory for Long-Form Video Understanding*. CVPR 2026.
7. Zhang, Y., Shi, C., & Yang, S. (2026). *WeaveTime: Streaming from Earlier Frames into Emergent Memory in VideoLLMs*. CVPR 2026.
8. Yu, X., Guan, D., Yang, M. Y., & Gu, Y. (2025). *Zoom-Refine: Boosting High-Resolution Multimodal Understanding via Localized Zoom and Self-Refinement*. arXiv:2506.01663.
9. Greenwood, J. A., Kyprianou, M., & Dekker, T. M. (2026). *The development of visual acuity and crowding reveals the slow fine-tuning of foveal vision*. Scientific Reports, 16, 3234.
10. Wu, et al. (2025). *Real-world visual search goes beyond eye movements: Active searchers select 3D scene viewpoints too*. PMID: 40638606.
11. Tatler, B. W., et al. (2010). *Modelling the role of task in the control of gaze*. PMC2856937.
12. Xu, Z.-X., & DeAngelis, G. C. (2025). *Seeing a Three-Dimensional World in Motion: How the Brain Computes Object Motion and Depth During Self-Motion*. Annual Review of Vision Science, 11, 423–446.

---

## 系列位置

APR-01：從均勻感知到自適應感知閱讀：多模態智能的感知資源配置理論  
APR-02：從像素差分到語義差分：連續多模態感知中的變化階層  
**APR-03：視覺不是一種閱讀：多尺度視覺閱讀模式與重觀察理論 ← 本文**  
APR-04：持續世界狀態與差分重觀察：從連續影片理解到持續感知智能  
APR-05：感知預算分配：從固定視覺 Token 到動態資訊獲益最大化  
APR-06：跨模態感知閱讀：文字、影像、影片與聲音的統一注意策略  
APR-07：Agentic Perception：具備自主觀看策略的多模態智能架構
