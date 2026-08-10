# 持續世界狀態與差分重觀察：從連續影片理解到持續感知智能

**英文題名：Persistent World State and Differential Re-observation: From Continuous Video Understanding to Persistent Perceptual Intelligence**  
**系列：Adaptive Perceptual Reading（APR）／自適應感知閱讀理論，第 4 篇**  
**版本：v0.1（2026-08-07）**

---

## 摘要

長影片理解、串流多模態模型與具身智能正在從「一次處理一段輸入」轉向「長時間持續存在於環境中」。然而，只增加上下文長度、儲存更多影格或建立更大的視覺記憶，並不等同於真正維持一個持續世界。持續感知智能的關鍵問題不是如何永久保存所有觀測，而是如何在局部、稀疏且可能互相衝突的新證據到來時，持續維護、修正與驗證對當前世界狀態的信念。

本文提出 Persistent World State（PWS，持續世界狀態）與 Differential Re-observation（DRO，差分重觀察）框架，作為 Adaptive Perceptual Reading（APR）的第四層。其核心表示為：

$$
W_t
=
\mathcal U(
W_{t-1},
\Delta_t,
E_t
)
$$

其中 $W_t$ 是當前世界狀態，$\Delta_t$ 是新觀測導出的狀態差分，$E_t$ 是支撐該更新的證據。系統不再要求每一時刻重新由完整視覺流重建世界，而是維持 persistent state，對局部變化進行 incremental update，並在不確定性、矛盾、狀態漂移、高風險事件或新問題出現時，選擇性回到原始影像、影片、感測器或其他模態進行重觀察。

本文進一步區分「歷史資料」、「記憶」、「世界狀態」與「信念」，提出狀態版本化、證據鏈、置信度、過期與失效、局部刷新與全局重建機制，並給出 Persistent State–Evidence Dual Layer、Belief Revision Loop、Drift Detection、State TTL 與 Re-observation Policy 等工程結構。本文的核心命題為：

**連續觀看不需要連續重建整個世界；持續智能應以可修正世界狀態為主工作層，以原始多模態資料為可按需重新觀察的證據層。**

**關鍵詞：** Persistent World State、持續感知、差分更新、重觀察、視覺記憶、具身智能、串流 Video-LLM、世界模型、信念修正、Agentic Perception

---

## 1. 從「看很久」到「持續存在」

長影片模型的第一個自然問題是：

> 模型可以看多久？

因此常見解法是提高：

$$
ContextLength
$$

或壓縮：

$$
VideoTokens
$$

或建立：

$$
MemoryBank
$$

然而，具身 Agent、桌面 Agent、機器人與全天候視覺系統面對的是另一個問題：

> 如果世界一直存在，智能體要如何一直知道「現在的世界是什麼」？

這與一次性的長影片 QA 不同。

長影片 QA 可以表示為：

$$
X_{0:T}
\xrightarrow{}
Answer(Q)
$$

持續 Agent 則更接近：

$$
W_0
\rightarrow
W_1
\rightarrow
W_2
\rightarrow
\cdots
\rightarrow
W_t
\rightarrow
\cdots
$$

其中每個 $W_t$ 都應代表智能體在當下對世界的最佳可用信念。

因此：

$$
\boxed{
\text{Long Context}
\neq
\text{Persistent World State}
}
$$

長 context 只是讓更多歷史資料可以被重新讀取；

Persistent World State 則要求：

$$
\boxed{
\text{The agent maintains what it currently believes the world is.}
}
$$

---

## 2. 前沿研究已開始從「影片記憶」走向「動態世界記憶」

近期研究已經逼近這個問題。

Embodied VideoAgent 使用 egocentric video、depth 與 camera pose 建立 persistent object memory，並在偵測到物件上的活動與互動後由 VLM 自動更新記憶。

3D-Mem 使用 memory snapshots 建立 compact 3D scene memory，以支援長時間 embodied exploration 與 reasoning。

M3-Agent 會持續處理即時視覺與音訊，建立並更新 episodic 與 semantic memories。

FlexMem 把 visual KV cache 當成記憶來源，允許模型持續觀看並在問題出現時召回相關片段。

CausalMem 在固定記憶預算下維護 streaming visual memory，利用 online semantic basis 保留影片流中的主要語義。

SelectStream 則把 streaming memory 明確描述為 budgeted online latent evidence allocation：模型需要決定何時寫、保留什麼、以及如何依 query 取回。

WorldMemArena 更進一步指出，多模態 Agent 的 memory 不只是 recall；它必須追蹤 evolving world、更新 stale states，並在行動決策時取出正確證據。

這些研究共同顯示：

$$
\text{Memory}
\rightarrow
\text{State Maintenance}
$$

正在成為多模態 Agent 的核心問題。

---

## 3. 四個容易混淆的概念

本文首先區分：

$$
\boxed{
History
\neq
Memory
\neq
WorldState
\neq
Belief
}
$$

### 3.1 歷史 History

歷史是曾經發生或曾經觀測到的資料：

$$
H_t
=
\{X_0,X_1,\ldots,X_t\}
$$

例如：

- 原始影片；
- 截圖；
- event stream；
- log；
- action trace；
- sensor readings。

歷史回答：

> 過去收到過什麼？

### 3.2 記憶 Memory

記憶是經過選擇、壓縮、索引或結構化後保留下來的歷史表示：

$$
M_t
=
\mathcal C(H_{0:t})
$$

它回答：

> 過去有哪些資訊值得保留與取回？

### 3.3 世界狀態 World State

世界狀態是智能體對「現在」的結構化表示：

$$
W_t
=
\{
entities,
properties,
relations,
events,
locations,
task\ states
\}
$$

它回答：

> 現在世界被認為是什麼樣子？

### 3.4 信念 Belief

由於感知不完美，世界狀態通常不是確定真值，而應帶有置信度：

$$
B_t(W)
=
P(W_t\mid E_{0:t})
$$

它回答：

> 我有多相信目前這個世界狀態？

因此：

$$
\boxed{
WorldState
=
\text{Current Structured Belief}
}
$$

而不是「全部歷史的摘要」。

---

## 4. Persistent World State

本文定義 Persistent World State：

$$
W_t
=
\{
e_i,
a_i,
r_{ij},
c_i,
\tau_i,
v_i
\}
$$

其中可包含：

- $e_i$：entity；
- $a_i$：attributes；
- $r_{ij}$：relations；
- $c_i$：confidence；
- $\tau_i$：最後驗證時間；
- $v_i$：版本或狀態版本號。

例如：

```text
entity: cup_03
location: kitchen_table
content: water
owner: unknown
confidence: 0.92
last_verified: 14:23:11
version: 17
evidence: frame_9281, depth_9281
```

下一個觀測可能只產生：

```text
entity: cup_03
location: unknown
change: disappeared_from_table
confidence: 0.81
```

系統不需要重新描述整個廚房。

而是：

$$
W_t
=
Update(
W_{t-1},
\Delta cup_{03}
)
$$

---

## 5. 差分世界更新

APR-02 已建立：

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

APR-04 將：

$$
\Delta^{state}
$$

真正寫入 persistent world。

定義：

$$
\Delta W_t
=
W_t\ominus W_{t-1}
$$

新觀測 $O_t$ 首先經過 APR-02 的 change lifting：

$$
O_t
\rightarrow
\widehat{\Delta W_t}
$$

再：

$$
W_t
=
\mathcal U(
W_{t-1},
\widehat{\Delta W_t}
)
$$

因此：

$$
\boxed{
\text{Continuous Perception}
=
\text{Persistent State}
+
\text{Incremental Revision}
}
$$

而不是：

$$
\boxed{
\text{Continuous Perception}
=
\text{Repeated Full Reconstruction}
}
$$

---

## 6. 世界狀態不是 append-only log

這一點非常重要。

如果系統只是不斷 append：

$$
cup\ on\ table
$$

$$
cup\ on\ table
$$

$$
cup\ moved
$$

$$
cup\ absent
$$

它擁有的是事件歷史，而不是清楚的當前狀態。

Persistent World State 應允許：

$$
state_{t-1}
\rightarrow
state_t
$$

例如：

$$
cup.location:
table
\rightarrow
sink
$$

但歷史證據不能被直接刪除。

因此需同時維持：

$$
\boxed{
CurrentState
+
StateHistory
}
$$

可表示：

$$
S_i
=
(
value,
valid\_from,
valid\_to,
confidence,
evidence
)
$$

這使：

> 杯子現在在哪裡？

和：

> 杯子半小時前在哪裡？

可以得到不同答案。

---

## 7. State–Evidence 雙層架構

本文提出：

$$
\boxed{
\text{State Layer}
+
\text{Evidence Layer}
}
$$

### State Layer

保存目前可操作的世界模型：

$$
W_t
$$

應盡量 compact、結構化、可快速查詢。

### Evidence Layer

保存支撐狀態的原始或近原始證據：

$$
E_t
=
\{
frames,
audio,
depth,
events,
logs,
DOM,
sensor
\}
$$

Evidence Layer 可以分級儲存：

$$
Raw
\rightarrow
Compressed
\rightarrow
Indexed
\rightarrow
Archive
$$

世界狀態中的每個重要事實都可以指向：

$$
EvidencePointer
$$

例如：

$$
door.state=open
$$

附帶：

$$
evidence=
\{frame_{1203},event_{804}\}
$$

這樣模型若之後懷疑：

> 我真的看對了嗎？

就能重新取回原始證據。

---

## 8. 為什麼摘要記憶不夠？

如果第一次觀察把影片摘要成：

> 有一個人走進房間，把東西放在桌上。

後來使用者問：

> 他放的是紅色鑰匙還是紅色 USB？

如果摘要中沒有保存這個細節：

$$
InformationLost=1
$$

單靠摘要：

$$
M_{summary}
$$

已無法恢復。

但若原始證據仍存在：

$$
E_{raw}
$$

便可：

$$
Reobserve(E_{raw},Q_{new})
$$

因此：

$$
\boxed{
\text{Memory Compression}
\neq
\text{Evidence Destruction}
}
$$

對可重觀察系統而言，壓縮記憶是主工作層，而原始資料是低頻回溯層。

---

## 9. Differential Re-observation

本文將差分重觀察定義為：

> 不重新全面感知整個歷史，而只針對產生不確定、矛盾或新任務需求的局部世界狀態，回到最相關的原始證據重新觀察。

令：

$$
Q_t
$$

為當前問題。

先從 world state：

$$
W_t
$$

得到候選答案。

若：

$$
U(W_t,Q_t)
<
\tau_U
$$

則直接回答或行動。

若：

$$
U(W_t,Q_t)
\ge
\tau_U
$$

則定位：

$$
AffectedStateSet
=
\{s_1,\ldots,s_k\}
$$

再尋找支撐證據：

$$
E^*
=
RetrieveEvidence(
AffectedStateSet,
Q_t
)
$$

最後：

$$
W_t'
=
ReobserveAndRevise(
W_t,E^*
)
$$

因此：

$$
\boxed{
Reobserve\ LocalEvidence
\ll
Reprocess\ FullHistory
}
$$

在大量任務中應可顯著降低成本。

---

## 10. 重觀察觸發條件

DRO 至少由六種情況觸發。

### 10.1 高不確定性

$$
Confidence(s_i)<\tau_C
$$

### 10.2 證據矛盾

$$
E_a
\Rightarrow
s_i=x
$$

但：

$$
E_b
\Rightarrow
s_i=y
$$

且：

$$
x\neq y
$$

### 10.3 狀態過期

若：

$$
t-\tau_i>TTL_i
$$

則目前狀態可能 stale。

### 10.4 高風險行動

若即將採取的行動 $a$：

$$
Risk(a)\gg0
$$

系統可要求：

$$
VerifyCriticalStates()
$$

### 10.5 新問題需要先前未保存的細節

$$
Q_{new}
\not\subset
Information(W_t)
$$

但：

$$
EvidenceExists(Q_{new})=1
$$

### 10.6 預測與觀測不一致

世界模型預測：

$$
\hat O_t
$$

實際觀測：

$$
O_t
$$

若：

$$
D(O_t,\hat O_t)>\tau_D
$$

則需重新確認相關區域與狀態。

---

## 11. State TTL：世界狀態有不同保鮮期

不是所有狀態都需要同樣頻率重新驗證。

例如：

$$
wall.location
$$

可能數月不變。

但：

$$
person.location
$$

可能幾秒就過期。

因此對每個狀態定義：

$$
TTL(s_i)
$$

甚至：

$$
TTL(s_i)
=
f(
volatility_i,
risk_i,
task_i,
history_i
)
$$

例如：

$$
TTL(wall)=High
$$

$$
TTL(door.state)=Medium
$$

$$
TTL(person.position)=Low
$$

當：

$$
Age(s_i)>TTL(s_i)
$$

狀態不一定立即刪除，而應降低：

$$
Confidence(s_i)
$$

可以寫成：

$$
c_i(t)
=
c_i(t_0)
e^{-\lambda_i(t-t_0)}
$$

其中：

$$
\lambda_i
$$

依狀態的自然變動速度設定。

---

## 12. Static / Dynamic State Decoupling

2026 年的 Mem4D 使用 Persistent Structure Memory 與 Transient Dynamics Memory 分離靜態結構與快速動態，提供一個值得借鑑的方向。

APR-04 可把世界狀態分成：

$$
W_t
=
W_t^{slow}
\cup
W_t^{fast}
$$

其中：

$$
W^{slow}
$$

包括：

- 房間結構；
- 固定家具；
- 長期物件 identity；
- 建築拓撲。

而：

$$
W^{fast}
$$

包括：

- 人的位置；
- 門的開關；
- 當前工具；
- 物體持有狀態；
- GUI 狀態；
- 暫時事件。

兩者使用不同：

$$
UpdateRate
$$

$$
TTL
$$

$$
MemoryBudget
$$

$$
VerificationPolicy
$$

這避免穩定背景與快速動態共享同一更新成本。

---

## 13. 世界狀態的局部可觀測性

具身智能永遠存在：

$$
PartialObservability
$$

智能體看不到世界全部區域。

因此：

$$
W_t
$$

不能被誤解成「真實世界完整狀態」。

更準確地：

$$
W_t
=
\text{Current Belief over a Partially Observed World}
$$

某個物件離開視野時：

$$
Visible(o)=0
$$

不代表：

$$
Exists(o)=0
$$

因此物件狀態可能成為：

$$
location=last\_seen(table)
$$

$$
visibility=unknown
$$

$$
confidence=0.63
$$

世界狀態應能顯式表示：

$$
\boxed{
Known,\;
Unknown,\;
Uncertain,\;
Stale,\;
Contradicted
}
$$

而不是只有 True / False。

---

## 14. Belief Revision

令狀態假說為：

$$
s_i=v
$$

舊信念：

$$
P_{t-1}(v)
$$

新證據：

$$
e_t
$$

更新：

$$
P_t(v)
\propto
P(e_t|v)P_{t-1}(v)
$$

APR 並不要求一定使用 Bayesian implementation，但需要具有同等功能：

> 新證據不是無條件覆蓋舊狀態，而是根據來源、時間、可靠性與衝突進行信念修正。

可定義：

$$
Score(e)
=
\alpha Reliability
+
\beta Recency
+
\gamma Directness
+
\delta CrossModalAgreement
$$

若兩個證據矛盾：

$$
e_a\perp e_b
$$

系統可以：

1. 保留兩者；
2. 降低狀態信心；
3. 觸發 Reobserve；
4. 等待第三證據；
5. 按 provenance 權重決定暫時狀態。

這比直接：

$$
LastWriteWins
$$

更適合持續感知。

---

## 15. 世界狀態漂移

差分更新的主要風險是：

$$
ErrorAccumulation
$$

如果：

$$
W_t
=
Update(W_{t-1},\Delta_t)
$$

而某一次：

$$
\Delta_k
$$

錯誤，後續世界狀態可能持續偏離現實。

定義 drift：

$$
D_t
=
D(
W_t,
\widehat W_t^{fresh}
)
$$

其中：

$$
\widehat W_t^{fresh}
$$

是由一次較完整重觀察得到的 fresh estimate。

當：

$$
D_t>\tau_D
$$

觸發：

$$
FullRefresh
$$

因此 APR 並不主張永不重建。

正確架構是：

$$
\boxed{
DifferentialUpdate
\leftrightarrow
SelectiveRefresh
\leftrightarrow
FullRefresh
}
$$

---

## 16. 三層刷新策略

### Level 1：Local Refresh

只重新看單一 entity 或 ROI：

$$
Refresh(e_i)
$$

例如重新確認門是否關閉。

### Level 2：Regional Refresh

重新掃描一個區域：

$$
Refresh(room_k)
$$

例如確認桌面上所有物品。

### Level 3：Global Refresh

重新建立較完整世界狀態：

$$
W_t
\leftarrow
Build(O_t^{global})
$$

只有在：

- 大幅環境切換；
- 定位失敗；
- 長時間離線；
- drift 過高；
- 安全需求；

時才執行。

因此更新成本呈現：

$$
C_{local}
<
C_{regional}
<
C_{global}
$$

---

## 17. 世界狀態與記憶預算

Persistent State 不代表無限增長。

世界狀態本身可以是有限：

$$
|W_t|\le B_W
$$

而 evidence archive：

$$
|E_{0:t}|
$$

可以透過：

- 壓縮；
- 分層儲存；
- 冷熱資料分級；
- retention policy；
- semantic indexing；

來管理。

CausalMem、SAVEMem、SelectStream 等工作都指出，在 streaming 模型中「保留什麼」比單純增加 memory bank 更重要。

本文進一步區分：

$$
B_W
$$

當前世界狀態預算；

$$
B_M
$$

主動記憶預算；

$$
B_E
$$

證據保存預算。

三者不應視為同一東西。

---

## 18. Query-time Re-observation

假設 Agent 已經看了一小時工廠影片。

世界狀態只保存：

```text
machine_7.state = running
machine_7.temperature = normal
operator_2.last_seen = station_B
warning_light = off
```

後來問：

> Operator 2 上一次離開 station B 時，有沒有拿走紅色扳手？

這個細節可能不存在於：

$$
W_t
$$

也不需要長期保存在 active world state。

系統可以：

$$
Q
\rightarrow
RelevantEntity(operator_2,wrench)
$$

$$
\rightarrow
RelevantTimeWindow
$$

$$
\rightarrow
RetrieveEvidence
$$

$$
\rightarrow
Reobserve
$$

$$
\rightarrow
Answer
$$

因此：

$$
\boxed{
PersistentState
\neq
StoreEverythingInState
}
$$

State Layer 只保存對持續行動有價值的結構。

低頻細節由 Evidence Layer 在 query time 回溯。

---

## 19. 行動也會更新世界

具身 Agent 不能只靠外部觀測更新世界。

如果 Agent 自己執行：

$$
Action_t
$$

例如：

$$
open(door_4)
$$

那麼在動作成功回饋後，可以先產生：

$$
\Delta W_t^{action}
$$

例如：

$$
door_4.state:
closed\rightarrow open
$$

因此：

$$
W_t
=
\mathcal U(
W_{t-1},
\Delta^{perception}_t,
\Delta^{action}_t
)
$$

這使：

$$
\boxed{
Perception
+
Action
\rightarrow
WorldState
}
$$

形成閉環。

WorldMemArena 將 memory 放入 Action–World Interaction Loop，也正是指出 memory 必須與世界變化及行動結果共同評估。

---

## 20. APR-01 到 APR-04 的完整閉環

APR-01：

$$
\text{How much perceptual resource?}
$$

APR-02：

$$
\text{What changed and how important is it?}
$$

APR-03：

$$
\text{How should the agent look?}
$$

APR-04：

$$
\text{How should what was seen alter the persistent world?}
$$

整合：

$$
W_{t-1}
$$

$$
\Downarrow
$$

$$
Predict/OngoingMonitor
$$

$$
\Downarrow
$$

$$
\Delta Detection
$$

$$
\Downarrow
$$

$$
\Delta^{sig}
$$

$$
\Downarrow
$$

$$
ChoosePerceptualMode
$$

$$
\Downarrow
$$

$$
Observe
$$

$$
\Downarrow
$$

$$
UpdateWorldState
$$

$$
\Downarrow
$$

$$
W_t
$$

若：

$$
U_t\uparrow
$$

則：

$$
ReobserveEvidence
$$

再回到：

$$
UpdateWorldState
$$

這形成：

$$
\boxed{
Persistent Perceptual Loop
}
$$

---

## 21. Persistent Perceptual Loop

本文定義最小迴圈：

$$
\boxed{
W_t
\rightarrow
Predict
\rightarrow
Monitor
\rightarrow
DetectDelta
\rightarrow
SelectMode
\rightarrow
Observe
\rightarrow
Revise
\rightarrow
W_{t+1}
}
$$

若觀測與世界模型一致：

$$
D(O_t,\hat O_t)<\tau
$$

只需：

$$
MinorUpdate
$$

甚至：

$$
NoUpdate
$$

若不一致：

$$
D(O_t,\hat O_t)\ge\tau
$$

則：

$$
Inspect/Reobserve
$$

並更新：

$$
W_{t+1}
$$

這使感知成本更接近：

$$
C_t
\propto
InformationNeededForStateRevision
$$

而不是：

$$
C_t
\propto
RawInputVolume
$$

---

## 22. World State Bus

工程上可以將 $W_t$ 實作為一個 World State Bus，供不同 Agent 或模組共享。

例如：

```text
WORLD_STATE
├── entities
│   ├── person_01
│   ├── cup_03
│   └── door_04
├── relations
│   ├── cup_03 ON table_02
│   └── person_01 NEAR door_04
├── environment
│   ├── room = kitchen
│   └── lighting = normal
├── task_state
│   └── cleaning_phase = 2
├── uncertainties
│   └── cup_03.location = stale
└── evidence_links
    ├── frame_9281
    └── event_441
```

Vision Agent、Audio Agent、Robot Controller、Planner 與 LLM 都不需要重新各自建立完整世界。

它們可以共同讀寫：

$$
W_t
$$

但每次 write 必須帶：

$$
source,
timestamp,
confidence,
evidence
$$

---

## 23. 跨模態狀態融合

世界狀態可能由不同模態共同支持。

例如：

視覺：

$$
door\ appears\ closed
$$

磁簧開關：

$$
door\ sensor=open
$$

音訊：

$$
door\ slam\ detected
$$

因此：

$$
W_t
=
Fuse(
E_t^{vision},
E_t^{audio},
E_t^{sensor},
E_t^{action}
)
$$

當模態互相矛盾時：

$$
Conflict=1
$$

可觸發：

$$
Reobserve
$$

例如：

$$
Vision says closed
$$

但：

$$
Sensor says open
$$

則應：

$$
InspectDoor()
$$

而不是任意選一個。

---

## 24. 可驗證假說

### H1：Persistent State 降低重複處理

在背景穩定、局部事件稀疏的長時間流中：

$$
Cost_{PWS}
<
Cost_{FullReconstruction}
$$

同時維持相近或更好的任務準確率。

### H2：State–Evidence 雙層優於摘要-only memory

在後續提出未預期細節問題時：

$$
Accuracy_{State+Evidence}
>
Accuracy_{SummaryOnly}
$$

### H3：差分重觀察優於全歷史重算

對局部不確定問題：

$$
Cost_{DRO}
\ll
Cost_{FullReplay}
$$

且：

$$
Accuracy_{DRO}
\approx
Accuracy_{FullReplay}
$$

### H4：TTL 能降低 stale-state error

具有狀態過期與置信度衰減機制的系統應比永久有效狀態模型更少出現 stale fact decision error。

### H5：局部刷新可以抑制 drift

週期性 local/regional refresh 應在明顯低於 full refresh 成本下，降低長時間 incremental update 的狀態漂移。

### H6：顯式 Unknown 優於錯誤確定

允許：

$$
Unknown/Uncertain/Stale
$$

狀態的系統，在 partial observability benchmark 中應比強迫每個狀態為確定值的系統具有更低的高信心錯誤率。

---

## 25. MVP 設計

### 25.1 測試世界

建立一個簡單桌面／房間場景：

- 5–10 個物件；
- 2 個可開關元件；
- 1 個移動人物；
- 固定攝影機或 robot camera；
- 可控制事件腳本。

### 25.2 事件

例如：

$$
cup:
table\rightarrow sink
$$

$$
door:
closed\rightarrow open
$$

$$
person:
room_A\rightarrow room_B
$$

$$
light:
off\rightarrow on
$$

並加入：

- camera motion；
- occlusion；
- short disappearance；
- conflicting sensor；
- unseen state change。

### 25.3 系統比較

#### System A：Full Reconstruction

每一輪：

$$
Frame_t\rightarrow VLM\rightarrow FullWorldDescription
$$

#### System B：Rolling Summary

維持文字摘要。

#### System C：Memory Retrieval

保留重要 frame/token 並 query-time retrieval。

#### System D：APR-PWS

$$
PersistentState
+
DifferentialUpdate
+
StateTTL
+
EvidenceLinks
+
SelectiveReobserve
$$

### 25.4 指標

$$
StateAccuracy
$$

$$
StateFreshness
$$

$$
ContradictionRate
$$

$$
StaleFactRate
$$

$$
VisualTokenCost
$$

$$
ReobserveCost
$$

$$
EvidenceRecoveryAccuracy
$$

$$
DriftOverTime
$$

$$
CriticalMissRate
$$

---

## 26. 與既有研究的邊界

本文不主張以下概念本身為新：

- visual memory；
- episodic memory；
- semantic memory；
- scene graph；
- object memory；
- long-video memory compression；
- streaming memory bank；
- active retrieval；
- persistent scene reconstruction；
- multimodal memory；
- world model。

Embodied VideoAgent、3D-Mem、M3-Agent、FlexMem、CausalMem、SAVEMem、SelectStream、Mem4D、SpaMEM 與 WorldMemArena 都已處理其中不同部分。

APR-04 的理論位置是：

$$
\boxed{
\text{Memory is not the final object;}
\quad
\text{maintaining a revisable current world state is.}
}
$$

以及：

$$
\boxed{
\text{Raw observations should remain re-observable evidence,}
\quad
\text{not necessarily active reasoning context.}
}
$$

本文將：

- 差分感知；
- persistent current state；
- evidence provenance；
- state freshness；
- belief revision；
- selective re-observation；

統合為一個持續感知循環。

---

## 27. 限制

### 27.1 世界狀態 schema 很難完整預先定義

開放世界中，新的 entity、property 與 relation 會持續出現，因此 $W_t$ 必須允許 schema evolution。

### 27.2 更新成本可能高於重新看

高度動態場景可能：

$$
|\Delta W_t|\approx|W_t|
$$

此時：

$$
FullRefresh
$$

可能更便宜。

### 27.3 原始證據儲存仍有成本

State–Evidence 雙層只是把 active compute 與 archival storage 分開，並不能讓儲存成本消失。

### 27.4 感知錯誤可能污染世界狀態

因此 provenance、confidence、contradiction 與 refresh 機制不是附加功能，而是必要結構。

### 27.5 世界狀態不是世界真相

在 partial observability 下：

$$
W_t
$$

永遠只是：

$$
Belief_t
$$

不能把未觀察區域錯誤地填成確定事實。

---

## 28. 討論：從「每次看世界」到「一直活在同一個世界裡」

今天大量多模態互動仍然具有：

$$
\text{Observe}
\rightarrow
\text{Answer}
\rightarrow
\text{Forget/Compress}
$$

的 session 性質。

真正持續 Agent 更像：

$$
\text{World Continues}
$$

$$
\Downarrow
$$

$$
\text{Agent Continues}
$$

$$
\Downarrow
$$

$$
\text{Belief Continues}
$$

因此每一輪感知不應從零開始問：

> 現在畫面裡有什麼？

而更接近：

> 我原本認為世界是 $W_{t-1}$。現在有什麼變了？我的哪些信念需要更新？哪些地方需要重新確認？

也就是：

$$
\boxed{
\text{Perception as Belief Maintenance}
}
$$

這可能比「Video Understanding」更接近長時間多模態智能真正需要的抽象層。

---

## 29. 結論

本文提出 Persistent World State（PWS）與 Differential Re-observation（DRO），作為 APR 的第四層。

核心公式為：

$$
\boxed{
W_t
=
\mathcal U(
W_{t-1},
\Delta_t,
E_t
)
}
$$

並提出：

$$
\boxed{
History
\neq
Memory
\neq
WorldState
\neq
Belief
}
$$

持續感知系統不必讓所有歷史資料永久存在 active context。

更有效的結構是：

$$
\boxed{
PersistentState
+
DifferentialUpdate
+
EvidenceArchive
+
SelectiveRe-observation
}
$$

其中：

- 世界狀態負責「現在是什麼」；
- 記憶負責「哪些過去值得保留」；
- 原始證據負責「必要時重新確認」；
- 差分感知負責「什麼真的變了」；
- 重觀察負責「當目前信念不夠可靠時再看」。

因此：

$$
\boxed{
\text{Continuous Watching}
\neq
\text{Continuous Full Reconstruction}
}
$$

而應逐步轉向：

$$
\boxed{
\text{Continuous Belief Maintenance}
}
$$

APR 前四篇至此形成：

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
\text{APR-03：觀看存在多種模式}
$$

$$
\Downarrow
$$

$$
\text{APR-04：觀看結果持續更新世界狀態}
$$

下一篇 APR-05 將把整套架構推入正式的資源最佳化問題：

$$
\boxed{
\text{Perceptual Budget Allocation}
}
$$

即在有限 token、GPU、記憶、時間與能量下，智能體應如何動態決定：

$$
\text{看多少、看哪裡、看多久、想多深、記多少、何時重看。}
$$

---

## 參考文獻

1. Fan, Y., Ma, X., Su, R., et al. (2025). *Embodied VideoAgent: Persistent Memory from Egocentric Videos and Embodied Sensors Enables Dynamic Scene Understanding*. ICCV 2025.
2. Yang, Y., Yang, H., Zhou, J., et al. (2025). *3D-Mem: 3D Scene Memory for Embodied Exploration and Reasoning*. CVPR 2025.
3. Long, L., He, Y., Ye, W., et al. (2026). *Seeing, Listening, Remembering, and Reasoning: A Multimodal Agent with Long-Term Memory*. ICLR 2026.
4. Chen, T., Zhang, K., Wu, Q., et al. (2026). *Scaling the Long Video Understanding of Multimodal Large Language Models via Visual Memory Mechanism*. CVPR 2026.
5. Song, B., Lin, Y., Wu, Q., et al. (2026). *Towards a Dynamic and Fixed-budget Memory Bank for Efficient Streaming Video Understanding*. arXiv:2606.25658.
6. Ge, H., Wang, Y., Wu, H., & Cai, Y. (2026). *What Should a Streaming Video Model Remember?* arXiv:2606.16353.
7. Wu, H., Mathews, S. M., Cai, Y., Yang, M.-H., & Wang, Y. (2026). *Semantic-Aware Adaptive Visual Memory for Streaming Video Understanding*. arXiv:2605.07897.
8. Liao, C.-T., Xiao, X., Meng, C., et al. (2026). *SpaMEM: Benchmarking Dynamic Spatial Reasoning via Perception-Memory Integration in Embodied Environments*. arXiv:2604.22409.
9. Liu, C., Yang, Y., Pu, S. X., et al. (2026). *WorldMemArena: Evaluating Multimodal Agent Memory Through Action-World Interaction*. arXiv:2605.29341.
10. Cai, X., Wang, S., Wang, P., et al. (2026). *Mem4D: Decoupling Static and Dynamic Memory for Dynamic Scene Reconstruction*. AAAI 2026.
11. Ge, Z., Jia, X., Wu, C., et al. (2026). *EvoMemNav: Efficient Self-Evolving Fine-Grained Memory for Zero-Shot Embodied Navigation*. arXiv:2606.03509.
12. Qian, J., Peng, Q., Panov, E., et al. (2026). *Expanding Spatial and Temporal Context for Robotic Imitation Learning With Scene Graphs*. arXiv:2606.01072.
13. Zhang, Z., Hou, Y., Cao, D., et al. (2026). *M4EI: A Hierarchical Multimodal Memory Framework for Embodied Intelligence with Causal-Driven Retrieval*. KSEM 2026.

---

## 系列位置

APR-01：從均勻感知到自適應感知閱讀：多模態智能的感知資源配置理論  
APR-02：從像素差分到語義差分：連續多模態感知中的變化階層  
APR-03：視覺不是一種閱讀：多尺度視覺閱讀模式與重觀察理論  
**APR-04：持續世界狀態與差分重觀察：從連續影片理解到持續感知智能 ← 本文**  
APR-05：感知預算分配：從固定視覺 Token 到動態資訊獲益最大化  
APR-06：跨模態感知閱讀：文字、影像、影片與聲音的統一注意策略  
APR-07：Agentic Perception：具備自主觀看策略的多模態智能架構
