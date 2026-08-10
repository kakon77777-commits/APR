# 從均勻感知到自適應感知閱讀：多模態智能的感知資源配置理論

**英文題名：From Uniform Perception to Adaptive Perceptual Reading: A Resource-Allocation Theory for Multimodal Intelligence**  
**系列：Adaptive Perceptual Reading（APR）／自適應感知閱讀理論，第 1 篇**  
**版本：v0.1（2026-08-02）**

---

## 摘要

當代多模態人工智慧已能處理文字、影像、音訊與影片，並逐步進入長影片理解、串流視覺與具身智能。然而，許多系統仍隱含一項值得重新檢討的假設：只要某段感知輸入被送入模型，它便應以相對固定的空間解析度、時間採樣率、視覺 token 預算與推理深度進行處理。這種「均勻感知」假設在工程上簡單，卻未必符合有限計算資源下的智能行為。

人類閱讀文字時會在掃讀、速讀、一般閱讀、精讀、深讀與重讀之間切換；人類視覺亦呈現明顯的任務依賴性，觀看位置、凝視時間與掃視模式會因目標、知識與任務而改變。近年的 Video-LLM 研究也開始分別探索視覺 token 壓縮、相鄰影格變化選擇、主動片段導航、階層式記憶與不確定性觸發的歷史重取樣。這些成果共同指出：感知不必等同於對所有可用資料做同等深度的完整處理。

本文提出「自適應感知閱讀」（Adaptive Perceptual Reading, APR）作為較高階的統一理論框架。APR 將感知視為一個受目標、記憶、不確定性、風險與計算預算共同約束的資源配置過程。智能體不只回答「輸入是什麼」，還必須決定「是否需要看、看哪個模態、看哪裡、多久看一次、看多細、推理多深，以及是否需要重看」。本文形式化定義感知策略、提出資源配置目標函數與六類感知行為，並給出可驗證假說、系統架構與實驗設計。本文不主張視覺 token pruning、動態解析度、主動影片導航或階層記憶本身為新技術；其理論貢獻在於將這些局部技術提升為同一個一般命題：**感知不是固定的輸入操作，而是智能體對有限計算資源進行動態分配的決策過程。**

**關鍵詞：** 多模態智能、自適應感知、主動視覺、視覺注意力、Video-LLM、感知資源配置、動態 token、長影片理解、Agentic Perception、重觀察

---

## 1. 問題背景：為何「看」會被默認成一種操作？

多模態模型的快速發展，使「模型能不能看懂影像」逐漸轉化成另一個更重要的問題：**模型應該如何看？**

在最簡化的多模態管線中，感知常被表示為：

$$
X_t \rightarrow E(X_t) \rightarrow Z_t \rightarrow \text{Reasoning}
$$

其中 $X_t$ 是輸入，$E$ 是視覺、音訊或其他感知編碼器，$Z_t$ 是送入後續模型的表示。此表示方式容易產生一個工程上的默認：只要輸入存在，就應按照預先設定的方式進行感知編碼。

然而，這與人類處理資訊的方式並不一致。

面對同一篇文章，人可以先掃讀標題，再精讀某一段，搜尋特定詞彙，回頭重讀先前內容，或在確認問題已解決後停止閱讀。面對同一張圖，人也可能先取得場景大意，再搜尋特定物體，最後只對一個局部區域進行細查。人類眼動研究長期顯示，視線配置並非單純由低階顯著性決定；任務、知識、期待與目標會改變凝視位置、凝視時間與掃視模式。不同任務甚至能使觀察者對同一幅作品採用不同的觀看策略。

因此，本文提出第一個基本命題：

> **感知方式本身也是智能決策的一部分。**

換言之：

$$
\text{Perception} \neq f(X)
$$

而應更接近：

$$
\text{Perception}_t
=
f(X_t,G_t,M_t,U_t,R_t,B_t)
$$

其中：

- $X_t$：當前可取得的外部感知資料；
- $G_t$：當前任務與目標；
- $M_t$：既有記憶；
- $U_t$：對目前理解的不確定性；
- $R_t$：錯過資訊的風險或重要性；
- $B_t$：可用的計算、延遲、能量與 token 預算。

感知因此不是被動資料入口，而是有限資源條件下的主動選擇。

---

## 2. 現有研究正在逼近同一個問題

本文並非主張現有多模態系統仍完全採用逐幀、全局、等量處理。相反地，2025–2026 年的研究已明顯開始攻擊視覺冗餘與長序列成本，只是多半從不同局部切入。

### 2.1 串流影片中的變化與 token 選擇

StreamingTOM 在串流 Video-LLM 中提出因果式 temporal reduction，依據相鄰影格變化與 token saliency，在固定每幀預算下選擇較少的視覺 token，並配合量化線上記憶，使串流過程中的 active KV cache 維持有界。這證明「每一幀都保留同樣多的視覺資訊」並非必要，也顯示相鄰時間差異本身可以成為感知資源配置訊號。

### 2.2 主動導航取代窮舉觀看

LongVideo-R1 將長影片理解改寫為主動導航問題：模型先讀取高階視覺摘要，再推斷下一個最值得觀察的影片片段，獲得足夠資訊後立即停止探索。這已經不只是 token pruning，而是把「下一步看哪裡」本身變成推理決策。

### 2.3 Observe–Think–Act–Memorize

VideoARM 進一步使用 observe、think、act、memorize 的循環，在長影片中自主呼叫工具，以 coarse-to-fine 方式建構階層式多模態記憶，而不是事先對整段影片做靜態且窮舉的預處理。

### 2.4 不確定性觸發的重新展開

WeaveTime 針對串流 Video-LLM 的時間順序與歷史—現在區分問題，引入 Past-Current Dynamic Focus Cache，並以不確定性觸發 coarse-to-fine 的歷史取回：當目前資訊足夠時不必展開大量過去；需要時才進一步讀取。

這些研究共同揭示了一個正在形成、但尚未完全統一的趨勢：

$$
\text{Exhaustive Perception}
\rightarrow
\text{Selective Perception}
$$

然而，目前常見方法分別優化 frame、token、cache、memory、clip navigation 或 tool use。本文關心的是更高一層的問題：**這些是否其實都是同一種一般智能機制的不同實例？**

本文的回答是肯定的。

---

## 3. 自適應感知閱讀（APR）

本文定義自適應感知閱讀為：

> **智能體依據當前任務、內部狀態、既有記憶、不確定性、風險與可用資源，自主選擇感知模態、區域、時間、解析度、計算深度與重觀察策略的過程。**

令感知策略為：

$$
\Pi_P:
(S_t,M_t,G_t,U_t,R_t,B_t)
\rightarrow a_t^P
$$

其中感知動作 $a_t^P$ 可寫成：

$$
a_t^P=
(m_t,\Omega_t,\rho_t,\nu_t,d_t,q_t)
$$

各變數分別表示：

- $m_t$：選擇哪一個模態，例如文字、影像、音訊、深度、GUI state；
- $\Omega_t$：選擇哪個空間區域、物件或時間區段；
- $\rho_t$：解析度或表示精細程度；
- $\nu_t$：時間採樣頻率或讀取速率；
- $d_t$：後續推理深度；
- $q_t$：是否重看、回放、放大或取回歷史。

外界原始資料並不必然全部進入高成本多模態模型，而是先由低成本感知控制器產生策略：

$$
a_t^P=\Pi_P(S_t,M_t,G_t,U_t,R_t,B_t)
$$

再執行真正的觀察：

$$
Z_t=\mathcal O(X_t;a_t^P)
$$

最後更新智能體狀態：

$$
S_{t+1}=\mathcal U(S_t,Z_t)
$$

因此，感知的核心不再只是：

$$
X_t\rightarrow Z_t
$$

而是：

$$
\boxed{
\text{State}
\rightarrow
\text{Perceptual Policy}
\rightarrow
\text{Selective Observation}
\rightarrow
\text{State Update}
}
$$

---

## 4. 均勻感知與自適應感知的區別

令完整感知輸入被分割為 $n$ 個候選單元：

$$
X=\{x_1,x_2,\ldots,x_n\}
$$

均勻感知可近似表示為對所有單元配置相同計算量：

$$
b_i=\frac{B}{n}
$$

其中 $B$ 為總感知預算。

但如果不同單元對任務的價值 $v_i$ 不同，則一般而言：

$$
v_i\neq v_j
$$

此時固定配置會將資源浪費在低價值區域，也可能使高價值區域得不到足夠解析度。

APR 改為求取：

$$
\mathbf b^*
=
\arg\max_{\mathbf b}
\sum_{i=1}^{n}V_i(b_i\mid G,M,U,R)
$$

subject to：

$$
\sum_{i=1}^{n}b_i\le B
$$

其中 $V_i$ 並非單純像素量，而是該感知單元在目前任務下能帶來的預期價值。

更一般地，可將單次感知策略定義為：

$$
\pi_t^*
=
\arg\max_{\pi\in\Pi}
\left[
\mathbb E[IG(\pi)]
+\alpha\,Rel_G(\pi)
+\beta\,RiskCov(\pi)
-\lambda\,Cost(\pi)
\right]
$$

其中：

- $IG(\pi)$：預期資訊增益；
- $Rel_G(\pi)$：與當前目標的相關性；
- $RiskCov(\pi)$：對高風險資訊的覆蓋能力；
- $Cost(\pi)$：計算、token、能量與延遲成本；
- $\alpha,\beta,\lambda$：不同任務下的權重。

並可加入安全約束：

$$
P(\text{miss critical information}\mid\pi)\le\epsilon
$$

這使「看更多」與「看得更有效」成為兩個不同問題。

---

## 5. 感知閱讀模式

APR 不假設智能體只有「看」與「不看」兩種狀態，而是允許感知深度形成階梯。

本文先定義六種一般模式：

### 5.1 跳過／監控（Skip / Monitor）

當環境高度穩定、既有狀態可信且風險低時，只維持低成本變化監控：

$$
\mathcal P_0=\text{Monitor}
$$

### 5.2 瞥視（Glance）

以低解析度與低推理深度快速取得場景大意：

$$
\mathcal P_1=\text{Glance}
$$

### 5.3 掃視（Scan）

快速搜尋目標、異常、顯著變化或任務相關區域：

$$
\mathcal P_2=\text{Scan}
$$

### 5.4 精視（Inspect）

對特定區域提高空間、時間或語義解析度：

$$
\mathcal P_3=\text{Inspect}
$$

### 5.5 深視（Deep Perception）

不一定提高原始影像解析度，而是增加多步推理、跨模態比對與世界模型參與程度：

$$
\mathcal P_4=\text{Deep}
$$

### 5.6 重觀察（Re-observe）

當問題、任務或不確定性改變時，重新檢視先前已觀察資料：

$$
\mathcal P_5=\text{Reobserve}
$$

重要的是，同一份輸入 $X$ 不保證產生同一個感知結果：

$$
X=X
$$

但：

$$
\mathcal O(X;\pi_1)\neq\mathcal O(X;\pi_2)
$$

因為新的問題、記憶與注意策略可能使智能體取得不同資訊。

這與文字閱讀完全類似：同一篇論文在第一次掃讀、第二次尋找證據、第三次檢查矛盾時，實際被處理的資訊並不相同。

---

## 6. 「Tokenization After Attention」需要重新定義

一個容易被誤解的口號是：

$$
\text{Tokenization After Attention}
$$

嚴格而言，完全沒有任何前置處理就決定「哪裡值得看」是不可能的。注意力控制本身也需要輸入資訊。因此 APR 並不主張零成本地先知道重要區域，而是主張**感知應具有成本分層**。

可將整個流程表示為：

$$
X_t
\xrightarrow{C_{cheap}}
\tilde Z_t
\xrightarrow{\Pi_P}
\Omega_t
\xrightarrow{C_{expensive}}
Z_t
$$

其中：

- $C_{cheap}$ 是低成本的變化檢測、低解析度摘要、事件流、結構化 state delta 或輕量 encoder；
- $\Pi_P$ 根據粗略資訊決定資源配置；
- $C_{expensive}$ 才是高解析度視覺編碼、大型多模態推理或深度重觀察。

因此更準確的表述是：

$$
\boxed{
\text{Expensive Tokenization Conditioned on Perceptual Policy}
}
$$

也就是：高成本 token 應在知道任務與感知策略之後才被大量生成，而不是對所有輸入一律預先支付同樣成本。

---

## 7. 感知資源配置命題

### 命題 1：非均勻價值命題

若不同輸入單元對任務的邊際資訊價值不同，且總感知預算有限，則均勻配置通常不會是最優解。

形式上，若存在 $i,j$ 使：

$$
\frac{\partial V_i}{\partial b_i}
\neq
\frac{\partial V_j}{\partial b_j}
$$

則在最優配置中通常不應要求：

$$
b_i=b_j
$$

這是 APR 最基本的資源配置理由。

### 命題 2：任務條件感知命題

同一份感知資料在不同目標下，其最優感知策略可以不同：

$$
G_1\neq G_2
\Rightarrow
\pi^*(X,G_1)\neq\pi^*(X,G_2)
$$

這與人類眼動的任務依賴性一致。

### 命題 3：可重觀察命題

新的問題或不確定性可以改變既有資料的價值，因此歷史輸入不應被視為「讀過一次即永久完成」：

$$
Q_{t+1}\neq Q_t
\Rightarrow
V(X_{past}\mid Q_{t+1})
eq V(X_{past}\mid Q_t)
$$

因此重看不是系統失敗，而是正常的智能行為。

### 命題 4：停止感知命題

當額外感知的預期邊際價值低於成本時，智能體應能停止：

$$
\Delta \mathbb E[Utility_{perception}]
<
\Delta Cost
\Rightarrow
Stop
$$

Long-video navigation 中「取得足夠知識後停止探索」已提供這類策略的實際例子。

---

## 8. APR 系統架構

一個最小 APR Runtime 可包含以下七個模組：

1. **Persistent State Store**：維持目前世界狀態；
2. **Low-Cost Monitor**：負責低成本變化與事件偵測；
3. **Goal Relevance Estimator**：估計資訊與目前任務的相關性；
4. **Uncertainty Estimator**：判斷目前理解是否足夠；
5. **Risk Estimator**：避免忽略低像素差但高重要性的事件；
6. **Budget Controller**：管理 token、GPU 時間、延遲與能量；
7. **Perceptual Policy Controller**：輸出真正的觀看策略。

其循環為：

$$
S_t
\rightarrow
\text{Monitor}
\rightarrow
\text{Estimate}(G,U,R,B)
\rightarrow
\Pi_P
\rightarrow
\mathcal O_{\pi_t}
\rightarrow
S_{t+1}
$$

若不確定性升高：

$$
U_t\uparrow
\Rightarrow
\rho_t\uparrow
\lor
\nu_t\uparrow
\lor
 d_t\uparrow
\lor
q_t=1
$$

若環境穩定且任務相關性低：

$$
U_t\downarrow,
\quad Rel_t\downarrow,
\quad R_t\downarrow
\Rightarrow
Cost_t\downarrow
$$

這使感知成本隨資訊需求而變，而不是單純隨原始資料量線性增長。

---

## 9. 可驗證假說

APR 若要成為科學理論，而非純粹設計哲學，必須能被實驗否證。本文提出五項直接可測假說。

### H1：成本—準確率 Pareto 優勢

在長影片、GUI 或連續攝影機任務中，自適應感知策略應比固定採樣率與固定 token 預算取得更好的 accuracy–cost Pareto frontier。

### H2：任務條件配置優勢

對同一份影片，不同問題若允許產生不同感知策略，應比所有問題共用同一組影格與 token 配置更有效率。

### H3：不確定性觸發重看優勢

允許模型在低信心時主動放大、回放或重新取樣，應降低細粒度時間定位與小區域辨識的錯誤率。

### H4：歷史重觀察優勢

當後續問題改變時，允許重新取回原始歷史資料應優於只依賴第一次觀看後生成的固定摘要。

### H5：跨模態一般性

若 APR 是一般感知原理，類似的資源配置機制應同時適用於文字、影像、影片與音訊，而非只能在 Video-LLM 中成立。

---

## 10. 最小實驗設計

本文建議以三組系統進行初始驗證。

### Baseline A：Uniform Full Processing

固定影格率、固定解析度、固定每幀 token：

$$
\rho_t=\rho_0,
\quad
\nu_t=\nu_0,
\quad
b_t=b_0
$$

### Baseline B：Static Pruning

使用既有 frame selection 或 token pruning，但不允許任務中途改變感知策略。

### System C：APR Agent

允許模型動態決定：

$$
\{skip,glance,scan,inspect,deep,reobserve\}
$$

並根據問題、不確定性與預算調整：

$$
(\Omega_t,\rho_t,\nu_t,d_t,q_t)
$$

主要量測：

$$
\text{Accuracy}
$$

$$
\text{Visual Tokens}
$$

$$
\text{GPU Time}
$$

$$
\text{Latency}
$$

$$
\text{Peak Memory}
$$

$$
\text{Critical Miss Rate}
$$

$$
\text{Re-observation Count}
$$

最重要的評估不是只追求最低 token，而是比較：

$$
\frac{Task\ Utility}{Perceptual\ Cost}
$$

並繪製完整 Pareto frontier。

---

## 11. 與既有工作的邊界

APR 不應被描述為以下技術的重新命名：

- key-frame selection；
- visual token pruning；
- dynamic resolution；
- video memory compression；
- event camera；
- active video navigation；
- coarse-to-fine visual reasoning。

這些工作各自已經有豐富研究。

APR 的理論位置是將它們視為同一個更一般決策問題的不同投影：

$$
\boxed{
\text{Adaptive Allocation of Perceptual Computation}
}
$$

例如：

- token pruning 是「保留多少表示」；
- frame selection 是「何時看」；
- region selection 是「看哪裡」；
- dynamic resolution 是「看多細」；
- active navigation 是「下一步去哪裡看」；
- memory retrieval 是「是否重新讀歷史」；
- tool use 是「用什麼方式看」。

APR 將上述決策統一寫入感知策略：

$$
\Pi_P
\rightarrow
(m,\Omega,\rho,\nu,d,q)
$$

因此本文的核心貢獻不是某一項局部壓縮技巧，而是提出一個可以容納這些技巧的感知控制層。

---

## 12. 限制與風險

### 12.1 感知控制器也有成本

APR 並不能消除資訊處理成本。若要決定「哪裡重要」，系統仍需要某種低成本前置感知。因此 APR 的目標是形成成本階梯，而不是得到免費注意力。

### 12.2 小變化不等於小意義

單純依賴像素變化會漏掉：

$$
99\rightarrow999
$$

或：

$$
OFF\rightarrow ON
$$

等低像素差、高語義差事件。因此真正的感知策略必須結合風險、目標與語義模型。

### 12.3 錯誤信心可能造成感知不足

若模型錯誤地認為自己已理解環境，便可能停止觀察並累積錯誤。因此不確定性估計本身會成為 APR 的核心瓶頸。

### 12.4 對抗性注意力操縱

攻擊者可能刻意把重要資訊放置在模型低頻監控區、低解析區或看似無關的位置。因此 APR 必須保留隨機抽查、風險掃描或最低覆蓋率。

### 12.5 缺乏專門 benchmark

目前多數 benchmark 衡量回答正確率，而不是「模型是否以合理感知成本取得答案」。APR 需要新的 benchmark 同時測量任務效用、觀看路徑、token 消耗、重新觀察行為與漏失風險。

---

## 13. 討論：從模型會看，到模型知道怎麼看

多模態人工智慧的第一階段問題是：

> 模型能否理解圖片、聲音與影片？

第二階段問題正在變成：

> 模型能否在長時間、連續、多來源的資訊流中維持理解？

本文認為第三階段必須進一步詢問：

> **模型是否知道自己應該如何取得資訊？**

真正長時間運作的智能體不可能永久對所有感測器維持最大解析度、最高採樣率與最深推理。如果感知成本與原始資料流永遠近似線性成長：

$$
C_{perception}\propto |X|
$$

那麼全天候視覺、機器人、智慧眼鏡、桌面 Agent 與長時間影片理解都會持續受限於計算與記憶成本。

APR 希望將此關係改寫為：

$$
C_{perception}
\propto
\text{Required Information Acquisition}
$$

更理想地：

$$
C_t
=
f(
Novelty_t,
Uncertainty_t,
GoalRelevance_t,
Risk_t
)
$$

而不是只由當前輸入資料量決定。

這不表示智能體應盡可能少看，而是表示：

> **智能的其中一部分，就是知道什麼值得花昂貴的感知資源。**

---

## 14. 結論

本文提出自適應感知閱讀（Adaptive Perceptual Reading, APR），將多模態感知重新定義為有限資源條件下的動態資源配置問題。

其核心公式可濃縮為：

$$
\boxed{
\Pi_P:
(S,M,G,U,R,B)
\rightarrow
(m,\Omega,\rho,\nu,d,q)
}
$$

智能體不是被動接受固定格式的感知輸入，而是持續決定：

$$
\boxed{
\text{是否看}
+
\text{看什麼}
+
\text{何時看}
+
\text{看多細}
+
\text{想多深}
+
\text{是否重看}
}
$$

因此：

$$
\boxed{
\text{Perception is not merely an input operation;}
\quad
\text{it is an adaptive resource-allocation policy.}
}
$$

這一觀點與人類任務依賴視覺、近期串流 Video-LLM token 壓縮、主動長影片導航、階層式記憶與不確定性觸發取回等成果具有一致方向，但將其提升為跨模態的一般感知理論。

下一篇將進一步處理本系列的第二個核心問題：**「變化」究竟是什麼？** 我們將區分像素差分、特徵差分、物件差分、世界狀態差分與語義重要性差分，建立從資料變化到智能意義變化的階層模型。

---

## 參考文獻

1. Sharvashidze, N., & Schütz, A. C. (2020). *Task-Dependent Eye-Movement Patterns in Viewing Art*. Journal of Eye Movement Research, 13(2). DOI: 10.16910/jemr.13.2.12.
2. Chen, X., Tao, K., Shao, K., & Wang, H. (2026). *StreamingTOM: Streaming Token Compression for Efficient Video Understanding*. Proceedings of CVPR 2026, 24675–24685.
3. Qiu, J., Xie, L., Huo, X., Tian, Q., & Ye, Q. (2026). *LongVideo-R1: Smart Navigation for Low-cost Long Video Understanding*. Proceedings of CVPR 2026, 40505–40515.
4. Yin, Y., Meng, Q., Chen, M., Ding, J., Shao, Z., & Yu, Z. (2026). *VideoARM: Agentic Reasoning over Hierarchical Memory for Long-Form Video Understanding*. Proceedings of CVPR 2026, 24042–24051.
5. Zhang, Y., Shi, C., & Yang, S. (2026). *WeaveTime: Streaming from Earlier Frames into Emergent Memory in VideoLLMs*. Proceedings of CVPR 2026, 16920–16932.
6. Martinson, E., Fishta, I., & Butani, D. (2026). *Integrating foundation models with change detection to identify tasking for service robots*. Frontiers in Robotics and AI, 13. DOI: 10.3389/frobt.2026.1772005.
7. Schütz, A. C., Braun, D. I., & Gegenfurtner, K. R. (2011). *Eye movements and perception: A selective review*. Journal of Vision, 11(5).
8. Tatler, B. W., Hayhoe, M. M., Land, M. F., & Ballard, D. H. (2011). *Eye guidance in natural vision: Reinterpreting salience*. Journal of Vision, 11(5).

---

## 系列位置

**APR-01：從均勻感知到自適應感知閱讀：多模態智能的感知資源配置理論** ← 本文  
APR-02：從像素差分到語義差分：連續多模態感知中的變化階層  
APR-03：視覺不是一種閱讀：多尺度視覺閱讀模式與重觀察理論  
APR-04：持續世界狀態與差分重觀察：從連續影片理解到持續感知智能  
APR-05：感知預算分配：從固定視覺 Token 到動態資訊獲益最大化  
APR-06：跨模態感知閱讀：文字、影像、影片與聲音的統一注意策略  
APR-07：Agentic Perception：具備自主觀看策略的多模態智能架構
