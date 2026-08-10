# 從像素差分到語義差分：連續多模態感知中的變化階層

**英文題名：From Pixel Difference to Semantic Difference: A Hierarchy of Change in Continuous Multimodal Perception**  
**系列：Adaptive Perceptual Reading（APR）／自適應感知閱讀理論，第 2 篇**  
**版本：v0.1（2026-08-02）**

---

## 摘要

連續多模態系統若以固定影格率、固定解析度與固定視覺 token 預算反覆處理完整輸入，會大量重複計算沒有新增任務資訊的內容。影片編碼、事件相機與近期 Video-LLM token pruning 研究均已證明時間冗餘可以被利用；語義變化偵測與 object state change 研究則進一步顯示，真正重要的變化並不等同於像素差異。然而，現有方法多半分別處理訊號冗餘、特徵冗餘、場景變化、物件狀態或特定任務相關性，尚缺乏一個直接服務於持續多模態智能體的統一變化階層。

本文提出「階層差分感知」（Hierarchical Differential Perception, HDP）作為自適應感知閱讀理論的第二層。本文將連續感知中的變化分解為六個層次：

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

它們分別表示像素／訊號差分、特徵差分、物件差分、世界狀態差分、語義差分與任務重要性差分。本文主張，高階智能體不應把「變了多少」與「變得多重要」視為同一問題；大量像素改變可能只是鏡頭移動或光照變化，而少量像素改變也可能對世界狀態、風險或決策造成巨大影響。

本文進一步提出變化提升算子、干擾不變性、重要性函數、差分不對稱性、狀態更新規則與感知升級機制，並給出可驗證假說及 MVP 實驗架構。其核心命題為：

**連續智能的有效感知單位不應只是「新影格」，而應逐步轉向「具有任務意義的狀態變化」。**

**關鍵詞：** 差分感知、語義變化、狀態變化、Video-LLM、事件視覺、場景變化偵測、物件狀態、視覺 token、持續感知、Agentic Perception

---

## 1. 問題：畫面變化不等於世界變化

對兩個相鄰影格 $F_{t-1}$ 與 $F_t$，最直接的變化可以寫成：

$$
\Delta^{pix}_t = D(F_t,F_{t-1})
$$

其中 $D$ 可以是逐像素差、絕對差、結構相似度差異或其他低階距離。

然而，對智能體而言，真正重要的通常不是：

> 有多少像素不同？

而是：

> 世界發生了什麼變化？

考慮兩種極端情形。

### 1.1 大像素差，小世界差

攝影機向右平移時，幾乎所有像素都可能改變：

$$
\lVert\Delta^{pix}_t\rVert \gg 0
$$

但如果場景中的桌子、門、人物與物件關係都沒有真正改變，則：

$$
\lVert\Delta^{state}_t\rVert \approx 0
$$

### 1.2 小像素差，大世界差

控制介面上的文字由：

$$
\text{OFF}\rightarrow\text{ON}
$$

或價格由：

$$
99.9\rightarrow999
$$

只改變很小區域，甚至只改變少量字元與像素：

$$
\lVert\Delta^{pix}_t\rVert \approx 0
$$

但若該訊號代表設備啟動、交易價格改變或安全狀態切換，則：

$$
\lVert\Delta^{sig}_t\rVert \gg 0
$$

因此本文區分兩個問題：

$$
\text{Change Magnitude}
$$

與：

$$
\text{Change Significance}
$$

兩者不能互相替代。

---

## 2. 既有技術已證明「重複世界」可以被利用

本文並不主張時間差分本身是新的。

### 2.1 影片編碼：先利用訊號冗餘

現代影片編碼長期透過 inter prediction、motion vector prediction、reference picture、residual coding 等技術避免完整重複編碼相鄰畫面。H.266/VVC 仍包含 temporal motion vector prediction、subblock-based temporal motion vector prediction、motion-vector difference 與多種 residual coding 工具。

其抽象形式可寫為：

$$
F_t
=
\widehat F_t(F_{t-k},M_t)
+
R_t
$$

其中 $M_t$ 是運動／預測資訊，$R_t$ 是預測殘差。

影片編碼因此首先證明：

$$
\text{Raw Video Volume}
\neq
\text{New Information Volume}
$$

但 codec 的目標主要是重建訊號，而不是判斷事件對智能體任務的意義。

### 2.2 Event Camera：沒有低階變化就沒有事件

事件相機不以固定 FPS 傳送完整影格，而是讓每個像素在亮度變化超過門檻時非同步產生事件。若沒有足夠的亮度變化，便不產生對應資料。

可簡化為：

$$
|\Delta\log I(x,y,t)|>\theta
\Rightarrow
e=(x,y,t,p)
$$

否則：

$$
\text{No Event}
$$

這從感測器層直接展示：

$$
\text{No Change}
\Rightarrow
\text{No Full Re-observation Required}
$$

然而，事件視覺主要解決的是低階亮度變化；「哪個 event 對目前任務重要」仍是另一層問題。

### 2.3 Video-LLM：開始利用時間 token 冗餘

ResidualViT 利用連續影格間大量時間冗餘，以 residual connections 與 token reduction 降低高時間解析度影片特徵抽取成本。

PruneVid 會合併 temporally static 與 spatially similar tokens，並依查詢去除不相關視覺 token。

StreamingTOM 更直接依據相鄰影格變化與 token saliency 在串流影片中進行固定預算的 token 選擇。

ForestPrune 則把影片 token 組織為具有語義、空間與時間限制的森林，對高度冗餘的影片 token 進行大比例壓縮。

這些研究共同支持：

$$
\text{Adjacent Frames}
\not\Rightarrow
\text{Equal New Information}
$$

---

## 3. 但「變化」本身不是單一層級

本文提出六層差分階梯：

$$
\boxed{
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
}
$$

此箭頭不是表示每個系統都必須嚴格逐層運算，而是表示從低階訊號變化向高階智能意義提升的概念關係。

---

## 4. 第一層：像素／訊號差分

定義：

$$
\Delta^{pix}_t
=
D_{pix}(X_t,X_{t-1})
$$

對影像而言，它可以是 RGB、亮度、深度、事件流或其他感測訊號的局部改變。

優點是：

- 成本低；
- 可以高頻運行；
- 適合產生 early warning；
- 適合快速篩除完全靜態區域。

但其主要問題是對 nuisance variation 過度敏感。

令：

$$
N_t
=
\{
\text{camera motion},
\text{illumination},
\text{noise},
\text{compression artifact},
\text{viewpoint}
\}
$$

則可能發生：

$$
\Delta^{pix}_t
=
\Delta^{world}_t
+
\Delta^{nuisance}_t
$$

而：

$$
|\Delta^{nuisance}_t|
>
|\Delta^{world}_t|
$$

因此低階差分只能作為候選訊號，不能直接等同於「世界變了」。

---

## 5. 第二層：特徵差分

將原始輸入映射到特徵空間：

$$
z_t=\phi(X_t)
$$

則：

$$
\Delta^{feat}_t
=
D_f(z_t,z_{t-1})
$$

其中 $\phi$ 可以是 CNN、ViT、VLM encoder 或其他 latent representation。

特徵差分的目標是：

$$
\Delta^{feat}
\approx
\Delta^{task\text{-}relevant\ structure}
$$

而降低對部分低階干擾的敏感度。

近期 visual token pruning 大量採用 token similarity、跨幀特徵相似性、saliency 或 query relevance，本質上都在嘗試回答：

> 哪些 latent representation 沒有提供足夠的新資訊？

但特徵差分仍可能存在模型依賴。

同一個視覺變化：

$$
X_{t-1}\rightarrow X_t
$$

在不同 encoder 下可能得到：

$$
\Delta^{feat}_{A}
\neq
\Delta^{feat}_{B}
$$

所以「特徵差分」還不是客觀世界狀態本身。

---

## 6. 第三層：物件差分

令場景中的物件集合為：

$$
O_t
=
\{o_t^1,o_t^2,\ldots,o_t^n\}
$$

則物件差分不再關心每個 patch 是否變動，而關心：

- 哪個物件出現？
- 哪個物件消失？
- 哪個物件移動？
- 哪個物件被遮擋？
- 哪個物件被替換？
- 哪個物件本身改變？

可表示為：

$$
\Delta^{obj}_t
=
\{
O_t^{+},
O_t^{-},
O_t^{move},
O_t^{transform}
\}
$$

例如攝影機平移造成大量像素變化，但若 object correspondence 成功建立：

$$
o_t^i
\equiv
o_{t-1}^i
$$

則可判定：

$$
\Delta^{obj}\approx0
$$

反之，如果畫面中突然多出一把工具：

$$
O_t^{+}
=
\{\text{tool}\}
$$

即使其面積很小，也可得到明確的物件層變化。

2025–2026 的 scene change detection 已開始大量研究如何從二元 change map 走向 semantic change；UniChange 進一步使用多模態大型模型統一 binary change detection 與 semantic change detection，而 LangSCD 則利用語言描述與幾何—語義匹配提高 changed-object 的辨識能力。

這表示研究前沿已逐漸從：

$$
\text{Where changed?}
$$

走向：

$$
\text{What changed?}
$$

---

## 7. 第四層：世界狀態差分

物件存在不代表物件狀態不變。

令世界狀態為：

$$
S_t
=
\{
s_t^1,s_t^2,\ldots,s_t^m
\}
$$

其中狀態可以包括：

- 位置；
- 開／關；
- 完整／損壞；
- 空／滿；
- 生／熟；
- 鎖定／解鎖；
- 正常／警報；
- 持有者；
- 物件關係；
- 任務階段。

則：

$$
\Delta^{state}_t
=
S_t\ominus S_{t-1}
$$

這裡的 $\ominus$ 不是單純數值相減，而是結構化狀態差運算。

例如：

$$
door.state:
closed\rightarrow open
$$

$$
cup.content:
empty\rightarrow full
$$

$$
robot.grasp:
none\rightarrow wrench
$$

近期 object state change 研究顯示，這一層仍是多模態模型的重要難題。ObjChangeVR 專門研究連續第一人稱視角中、甚至缺乏直接動作提示的背景物件狀態變化；OSCBench 也指出，現代影片模型即使能維持整體場景與語義對齊，對細緻、連續且可組合的 object state change 仍然不穩定。

因此：

$$
\text{Scene Understanding}
\neq
\text{State Transition Understanding}
$$

---

## 8. 第五層：語義差分

世界狀態變化之後，仍需判斷「這個變化意味著什麼」。

本文定義語義差分：

$$
\Delta^{sem}_t
=
\Psi(
S_{t-1},
S_t,
C_t,
G_t
)
$$

其中：

- $C_t$：上下文；
- $G_t$：任務目標。

例如：

$$
door:
closed\rightarrow open
$$

本身是狀態差分。

但在不同上下文中可以代表：

1. 有人進入；
2. 緊急出口被打開；
3. 機器人已完成開門步驟；
4. 安全區域失去隔離；
5. 只是風把門吹開。

因此：

$$
\Delta^{state}
\not\Rightarrow
\text{unique }\Delta^{sem}
$$

語義差分必須結合上下文、時間序列、因果假說與任務。

這也是為什麼單純 change mask 不足以支撐高階智能體。

---

## 9. 第六層：重要性差分

即使兩個事件在語義上都能被理解，它們也不一定值得投入相同感知資源。

本文定義重要性差分：

$$
\Delta^{sig}_t
=
\Gamma(
\Delta^{sem}_t,
G_t,
R_t,
U_t,
K_t,
H_t
)
$$

其中：

- $G_t$：目標相關性；
- $R_t$：風險；
- $U_t$：不確定性；
- $K_t$：因果後果或可達範圍；
- $H_t$：歷史與記憶脈絡。

可進一步寫成：

$$
Sig_t
=
\alpha Rel_t
+
\beta Risk_t
+
\gamma Novelty_t
+
\delta CausalReach_t
+
\eta Irreversibility_t
+
\mu Uncertainty_t
$$

此函數不要求固定線性形式；其目的只是說明「重要性」由多項因素共同決定。

因此：

$$
|\Delta^{pix}_a|
>
|\Delta^{pix}_b|
$$

不代表：

$$
Sig(a)>Sig(b)
$$

甚至可能完全相反。

---

## 10. 差分不對稱性

本文提出 APR 系列中的一項重要原則：

### 差分不對稱原則

在一般智能任務中：

$$
\boxed{
\text{Physical Magnitude of Change}
\not\propto
\text{Decision Significance of Change}
}
$$

也就是：

$$
\frac{
\Delta^{sig}
}{
\Delta^{pix}
}
$$

可以非常大，也可以非常小。

### 例 1：攝影機快速平移

$$
\Delta^{pix}\gg0
$$

但：

$$
\Delta^{sig}\approx0
$$

### 例 2：一個警告 icon 出現

$$
\Delta^{pix}\ll1
$$

但：

$$
\Delta^{sig}\gg0
$$

### 例 3：背景人群持續移動

$$
\Delta^{obj}>0
$$

但若任務是讀取前景儀表：

$$
Rel_G\approx0
$$

因此：

$$
\Delta^{sig}\approx0
$$

### 例 4：價格最後一位數改變

同樣的像素差大小，在一般瀏覽中可能不重要，但在高頻交易監控中：

$$
Rel_G\uparrow
\Rightarrow
\Delta^{sig}\uparrow
$$

所以重要性不是輸入本身的固定屬性。

---

## 11. 變化提升算子

本文將從低階變化到高階變化的過程稱為：

**Change Lifting／變化提升**

令：

$$
L_k:
\Delta^{(k)}
\rightarrow
\Delta^{(k+1)}
$$

則：

$$
L_{pix\rightarrow feat}
$$

把訊號差異提升為表示差異；

$$
L_{feat\rightarrow obj}
$$

把局部特徵差異聚合為物件變化；

$$
L_{obj\rightarrow state}
$$

辨識物件狀態轉移；

$$
L_{state\rightarrow sem}
$$

結合上下文解釋狀態意義；

$$
L_{sem\rightarrow sig}
$$

依任務、風險與不確定性評估重要性。

整體：

$$
\Delta^{sig}
=
L_{sem\rightarrow sig}
\circ
L_{state\rightarrow sem}
\circ
L_{obj\rightarrow state}
\circ
L_{feat\rightarrow obj}
\circ
L_{pix\rightarrow feat}
(
\Delta^{pix}
)
$$

但實際系統不必每次完整走完所有層。

可以採 early exit。

若：

$$
\Delta^{pix}\approx0
$$

且風險低，可直接停止。

若低階差異高但被判定為 camera motion：

$$
\Delta^{feat}_{world}\approx0
$$

可在中間停止。

只有當候選變化可能影響世界狀態時，才升級到高成本語義推理。

---

## 12. 干擾不變性與「假變化」

真正的差分感知必須處理大量假變化：

$$
\mathcal N
=
\{
illumination,
viewpoint,
camera\ motion,
compression,
sensor\ noise,
occlusion
\}
$$

理想的高階變化算子希望滿足近似不變性：

$$
\Delta^{state}
(
T_n(X_{t-1}),
T_n(X_t)
)
\approx
\Delta^{state}
(
X_{t-1},X_t
)
$$

其中 $T_n$ 是不影響真實世界狀態的 nuisance transform。

這一點對持續 Agent 尤其重要。

如果機器人走動本身造成的視覺變化每次都被當成世界劇烈改變，感知系統將持續錯誤升級到高成本模式。

因此應區分：

$$
\Delta^{ego}
$$

智能體自身運動造成的觀測變化；

以及：

$$
\Delta^{exo}
$$

外部世界真正發生的變化。

目標是估計：

$$
\Delta^{world}
\approx
\Delta^{obs}
\ominus
\Delta^{ego}
$$

---

## 13. 從差分偵測到差分狀態更新

本文的目標不是只建立 change detector，而是讓變化成為持續世界狀態更新的基本輸入。

令：

$$
W_{t-1}
$$

為智能體已持有的世界模型。

傳統完整重建可近似為：

$$
W_t
=
Build(X_t)
$$

每次都重新從輸入推定當前世界。

APR/HDP 改為：

$$
W_t
=
Update(
W_{t-1},
\Delta^{state}_t
)
$$

如果只改變一個局部狀態：

$$
\Delta^{state}_t
=
\{
door_4: closed\rightarrow open
\}
$$

則沒有必要重新建構：

$$
\{
room,
walls,
tables,
chairs,
windows,
door_1,
door_2,
door_3,
...
\}
$$

這將連續感知從：

$$
\text{Repeated Reconstruction}
$$

轉換成：

$$
\text{Persistent State + Differential Update}
$$

---

## 14. 感知升級機制

HDP 應與 APR-01 的 Perceptual Reading Policy 連接。

低成本監控器首先估計：

$$
c_t
=
(
\Delta^{pix},
\Delta^{feat}
)
$$

再計算候選重要性：

$$
\widehat{Sig}_t
=
g(c_t,G_t,R_t,U_t)
$$

當：

$$
\widehat{Sig}_t<\tau_1
$$

採：

$$
skip/monitor
$$

當：

$$
\tau_1
\le
\widehat{Sig}_t
<
\tau_2
$$

採：

$$
glance/scan
$$

當：

$$
\tau_2
\le
\widehat{Sig}_t
<
\tau_3
$$

採：

$$
inspect
$$

當：

$$
\widehat{Sig}_t\ge\tau_3
$$

或：

$$
U_t\gg0
$$

採：

$$
deep/reobserve
$$

因此：

$$
\boxed{
Change
\rightarrow
Significance
\rightarrow
Perceptual Budget
}
$$

而不是：

$$
\boxed{
New Frame
\rightarrow
Full Vision
}
$$

---

## 15. 差分事件封包

為工程化本文概念，可以定義一個抽象的 Differential Perceptual Event：

$$
E_t
=
(
t,
source,
region,
\Delta^{pix},
\Delta^{feat},
entity,
\Delta^{state},
\Delta^{sem},
Sig,
confidence
)
$$

例如：

```text
time: 21:08:13.412
source: desktop.window.4
region: [842, 121, 1034, 184]
entity: payment_total
state_before: 99.90
state_after: 999.00
semantic_change: price_increase
significance: 0.93
confidence: 0.98
```

後續大型模型未必需要重新接收整張螢幕。

只需要在必要時讀取：

$$
E_t
$$

並在信心不足時要求：

$$
Reobserve(region,t)
$$

這提供一條從低階視覺到 Agent state bus 的工程路徑。

---

## 16. 跨模態推廣

本文雖以視覺為主，但差分階層並非視覺專屬。

### 16.1 音訊

低階：

$$
\Delta^{wave}
$$

頻譜：

$$
\Delta^{spec}
$$

聲學事件：

$$
\Delta^{event}
$$

狀態：

$$
fan:on\rightarrow off
$$

語義：

$$
machine\ stopped
$$

重要性：

$$
production\ interruption
$$

### 16.2 文字

字元差：

$$
\Delta^{char}
$$

token 差：

$$
\Delta^{token}
$$

命題差：

$$
\Delta^{prop}
$$

狀態差：

$$
contract.version:
v3\rightarrow v4
$$

語義／重要性差：

$$
payment\ term:
30\ days\rightarrow90\ days
$$

即使整份文件只有一行改動，任務影響仍可能非常大。

### 16.3 GUI / Computer Use

GUI 特別適合 HDP，因為系統可同時取得：

$$
DOM\ Delta,
Accessibility\ Delta,
Event\ Delta,
Framebuffer\ Delta
$$

因此可優先使用結構化差分，而只在必要時重新啟動完整視覺模型。

---

## 17. 可驗證假說

### H1：階層差分優於像素差分

在存在 camera motion、光照變化與背景動態的影片中，加入 feature/object/state lifting 的系統應比單純 pixel threshold 更能保持低 false-positive rate。

### H2：重要性與像素幅度低相關

在人為設計的小變化高風險資料集中：

$$
Corr(
|\Delta^{pix}|,
Sig
)
$$

應顯著低於：

$$
Corr(
|\Delta^{state/sem}|,
Sig
)
$$

若結果相反，本文的重要性階層假說將受到挑戰。

### H3：差分狀態更新可降低重複 token

對固定背景、局部變化的長影片或 GUI 任務：

$$
C_{HDP}
<
C_{Full}
$$

並應在保持任務準確率的同時顯著降低：

- visual tokens；
- prefill cost；
- KV cache；
- GPU time。

### H4：語義差分可降低關鍵事件漏失

如果只有低階 token pruning，微小但關鍵的文字、圖示或狀態切換可能被刪除。加入 state/semantic significance routing 後，Critical Miss Rate 應下降。

### H5：重觀察可以修復 lifting error

若前置差分模型對某一事件信心不足：

$$
U_t>\tau_U
$$

允許高解析度 re-observation 的系統應比「一次 pruning 後不可回頭」系統更穩健。

---

## 18. MVP 實驗設計

### 18.1 三類場景

#### A. 靜態背景＋局部 UI 改變

例如：

- 數字更新；
- 警告燈；
- 按鈕狀態；
- 游標移動；
- 文字出現。

#### B. 高像素變化＋低世界變化

例如：

- camera pan；
- zoom；
- 曝光變化；
- 視角改變。

#### C. 低像素變化＋高任務重要性

例如：

- OFF→ON；
- 99→999；
- access denied→granted；
- safe→warning。

### 18.2 比較系統

#### System A：Full Frame

$$
F_t\rightarrow VLM
$$

#### System B：Pixel Difference

$$
\Delta^{pix}
\rightarrow ROI
\rightarrow VLM
$$

#### System C：Feature/Token Difference

$$
\Delta^{feat}
\rightarrow TokenSelection
\rightarrow VLM
$$

#### System D：HDP

$$
\Delta^{pix}
\rightarrow
\Delta^{feat}
\rightarrow
\Delta^{obj/state}
\rightarrow
Sig
\rightarrow
Adaptive\ Observation
$$

### 18.3 指標

$$
TokenCost
$$

$$
GPUTime
$$

$$
Latency
$$

$$
ChangeRecall
$$

$$
SemanticChangeAccuracy
$$

$$
CriticalMissRate
$$

$$
FalseEscalationRate
$$

$$
StateConsistency
$$

其中最關鍵的是：

$$
\text{Critical Miss Rate}
$$

因為一個效率系統如果靠忽略重要的小變化省 token，工程上沒有意義。

---

## 19. 與既有研究的邊界

本文不主張以下技術為新的：

- inter-frame prediction；
- residual coding；
- event-based sensing；
- scene change detection；
- semantic change detection；
- object state change recognition；
- visual token pruning；
- temporal redundancy compression；
- query-guided change detection。

本文提出的理論位置是：

> 將這些不同層次的「change」重新排列為持續多模態 Agent 可操作的變化階層，並把最高層的 task significance 直接連接到感知預算配置與 persistent world-state update。

換句話說：

$$
\text{Compression}
$$

問的是：

> 哪些資訊可以少表示？

$$
\text{Change Detection}
$$

問的是：

> 哪裡／什麼發生了變化？

而 HDP 進一步問：

> **哪一層發生了什麼變化？這個變化對目前智能體意味著什麼？值得投入多少新的感知計算？**

---

## 20. 理論限制

### 20.1 層級不是完全離散

真實模型可能沒有明確的 pixel、feature、object、state 分界，而是在共享 latent space 中聯合完成多層推理。

因此本文的六層首先是一個可分析的功能分解，而非神經網路必須遵守的硬體分層。

### 20.2 高階差分可能比完整重算更昂貴

在高度動態、全局變化的場景：

$$
|\Delta^{state}|\approx|S|
$$

此時維持複雜差分追蹤可能不如直接重建划算。

所以 APR 應允許：

$$
DifferentialMode
\leftrightarrow
FullRefresh
$$

動態切換。

### 20.3 世界模型錯誤會累積

若：

$$
W_t
=
Update(W_{t-1},\Delta_t)
$$

中的早期 $\Delta_t$ 判斷錯誤，誤差可能持續累積。

因此系統需要週期性或事件觸發的 full refresh：

$$
W_t
\leftarrow
Rebuild(X_t)
$$

### 20.4 重要性具有任務依賴性

不存在唯一客觀的：

$$
Sig(\Delta)
$$

因為不同任務可能給同一事件完全不同的權重。

APR/HDP 必須明確把：

$$
G_t
$$

放在重要性函數中。

---

## 21. 討論：從「幀」轉向「事件與狀態」

影格是一種非常成功的攝影與計算表示。

但它不一定是持續智能的最佳基本單位。

對影片播放器而言：

$$
Frame
$$

是自然的。

對 codec 而言：

$$
Prediction+Residual
$$

已經更自然。

對 event camera 而言：

$$
BrightnessChangeEvent
$$

更自然。

對持續多模態智能體而言，本文主張最終更自然的單位可能是：

$$
\boxed{
Meaningful State Transition
}
$$

也就是：

$$
S_{t-1}
\xrightarrow{\Delta^{sig}}
S_t
$$

此時影片不再只是：

$$
F_1,F_2,\ldots,F_T
$$

而可以被理解為：

$$
S_0,
E_1,
E_2,
\ldots,
E_k
$$

其中：

$$
k\ll T
$$

在大量穩態場景中甚至可能：

$$
k\ll\ll T
$$

這不表示原始影格可以全部丟棄；它們仍然是可回溯證據。

真正的改變是：

> 原始資料成為可按需重觀察的證據層，而「狀態變化」成為持續推理的主工作層。

---

## 22. 結論

本文提出階層差分感知 HDP，作為 Adaptive Perceptual Reading 的第二層理論。

核心區分為：

$$
\boxed{
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
}
$$

它們描述的是不同問題：

- 像素差：畫面哪裡不同？
- 特徵差：表示哪裡產生新資訊？
- 物件差：什麼東西改變？
- 狀態差：世界的哪個屬性改變？
- 語義差：這個改變代表什麼？
- 重要性差：這個改變值得多少注意與計算？

因此：

$$
\boxed{
\text{Change Magnitude}
\neq
\text{Change Meaning}
\neq
\text{Change Significance}
}
$$

持續多模態智能的理想流程應從：

$$
NewFrame
\rightarrow
FullProcessing
$$

轉向：

$$
\boxed{
ChangeDetection
\rightarrow
ChangeLifting
\rightarrow
SignificanceEstimation
\rightarrow
AdaptivePerception
\rightarrow
StateUpdate
}
$$

而當不確定性、風險或重要性升高時，系統仍可回到原始資料進行高解析度重觀察。

本文因此將 APR-01 的「感知資源配置」補上了第一個核心訊號：

$$
\boxed{
\text{不是所有變化都值得相同的注意；
不是所有重要變化都具有大的表面差異。}
}
$$

下一篇 APR-03 將處理另一半問題：

**即使知道哪裡值得注意，智能體究竟可以用哪些不同方式「看」？**

也就是正式建立瞥視、掃視、精視、深視與重觀察等多尺度 Visual Reading Modes。

---

## 參考文獻

1. ITU-T. *Recommendation H.266 (V4): Versatile Video Coding*. January 2026.
2. Adra, M., Melcarne, S., Mirabet-Herranz, N., & Dugelay, J.-L. (2025). *Event-based solutions for human-centered applications: a comprehensive review*. Frontiers in Signal Processing, 5.
3. Soldan, M., Caba Heilbron, F., Ghanem, B., Sivic, J., & Russell, B. (2025). *ResidualViT for Efficient Temporally Dense Video Encoding*. ICCV 2025, 22305–22315.
4. Huang, X., Zhou, H., & Han, K. (2025). *PruneVid: Visual Token Pruning for Efficient Video Large Language Models*. Findings of ACL 2025.
5. Chen, X., Tao, K., Shao, K., & Wang, H. (2026). *StreamingTOM: Streaming Token Compression for Efficient Video Understanding*. CVPR 2026, 24675–24685.
6. Ju, S., Song, B., Chen, T., et al. (2026). *ForestPrune: High-ratio Visual Token Compression for Video Multimodal Large Language Models via Spatial-Temporal Forest Modeling*. arXiv:2603.22911.
7. Zhang, X., Li, D., Dong, X., et al. (2026). *UniChange: Unifying Change Detection with Multimodal Large Language Model*. CVPR 2026, 42169–42179.
8. Sheng, D., Gohil, V., Gaba, S., et al. (2026). *Scene Change Detection with Vision-Language Representation Learning*. arXiv:2604.11402.
9. Galappaththige, C. J., Lai, J., Windrim, L., et al. (2026). *Changes in Real Time: Online Scene Change Detection with Multi-View Fusion*. CVPR 2026, 32246–32256.
10. Ding, S., Wu, S., & Chen, Y. (2026). *ObjChangeVR: Object State Change Reasoning from Continuous Egocentric Views in VR Environments*. EACL 2026.
11. Han, X., Zhu, B., Hu, S., et al. (2026). *OSCBench: Benchmarking Object State Change in Text-to-Video Generation*. ACL 2026.
12. Nguyen, N., Bi, J., Vosoughi, A., et al. (2024). *OSCaR: Object State Captioning and State Change Representation*. arXiv:2402.17128.

---

## 系列位置

APR-01：從均勻感知到自適應感知閱讀：多模態智能的感知資源配置理論  
**APR-02：從像素差分到語義差分：連續多模態感知中的變化階層 ← 本文**  
APR-03：視覺不是一種閱讀：多尺度視覺閱讀模式與重觀察理論  
APR-04：持續世界狀態與差分重觀察：從連續影片理解到持續感知智能  
APR-05：感知預算分配：從固定視覺 Token 到動態資訊獲益最大化  
APR-06：跨模態感知閱讀：文字、影像、影片與聲音的統一注意策略  
APR-07：Agentic Perception：具備自主觀看策略的多模態智能架構
