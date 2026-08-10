# Adaptive Cognitive Runtime（ACR）工程白皮書
## 從認知比例性到可自適應配置的 AI Runtime

**版本：** v0.1  
**日期：** 2026-08-02  
**定位：** 工程白皮書

---

## 0. 摘要

Adaptive Cognitive Runtime（ACR，自適應認知運行時）是一個位於使用者請求與模型／Agent 執行之間的元控制層。

它解決的不是「模型能不能推理」，而是：

> **這一次究竟值得使用多少推理、多少上下文、多少記憶、多少工具、多少驗證，以及何時需要升級或降級？**

ACR 的核心流程：

\[
\boxed{
\text{Request}
\rightarrow
\text{Task Map}
\rightarrow
\text{Cognitive Profile}
\rightarrow
\text{Regime}
\rightarrow
\text{Resource Gating}
\rightarrow
\text{Execution}
\rightarrow
\text{Adaptive Supervision}
}
\]

它是《適度認知論》中「認知比例性」原則的工程實作層，也是《反身狀態閘控論》的弱形式、當代可實作版本。

完整 RSG 假設未來智能可以主動封印內部認知狀態；ACR v0.1 不要求這種能力，只控制目前工程上已可外顯調度的資源：

- 推理預算；
- context 範圍；
- memory retrieval；
- web / code / tool 權限；
- verifier 強度；
- model / endpoint（可選）；
- 回答長度；
- Agent autonomy。

近年研究已逐步把這些控制面變成可學習決策。Rational Metareasoning for LLMs 顯示，選擇性使用推理可降低不必要計算；2026 adaptive test-time compute 工作直接學習「哪些輸入值得更多 compute」；Agentic Memory 與 Memory-R1 讓模型主動決定 memory 的 store／retrieve／update／discard；Context as a Tool 則把 context 壓縮本身變成 Agent 可調用動作。這些工作共同支持 ACR 的工程方向：**認知資源本身應成為 policy 的一部分，而不是固定常數。**

---

# 1. 問題定義

目前 AI Runtime 常見兩種極端：

## 1.1 固定快速模式

所有問題：

\[
R=R_{\mathrm{low}}.
\]

優點：

- 快；
- 便宜。

缺點：

- 複雜問題 underthinking；
- 高風險問題驗證不足。

## 1.2 固定深度模式

所有問題：

\[
R=R_{\mathrm{high}}.
\]

優點：

- 充分推理。

缺點：

- 簡單問題 overthinking；
- 成本、延遲增加；
- 上下文污染；
- 不必要的工具呼叫；
- 長答案干擾使用者。

ACR 改成：

\[
\boxed{
R_t
=
f(T,U,H,E_t)
}
\]

其中：

- \(T\)：任務結構；
- \(U\)：使用者需求；
- \(H\)：必要歷史；
- \(E_t\)：執行途中取得的新證據。

---

# 2. 設計原則

## P1 — Coarse First

先建立低解析度全局圖，不先完整解題。

\[
\text{overview before expansion}.
\]

目標是判斷「要不要展開」，不是先把所有分支都算完。

---

## P2 — Minimum Sufficient Cognition

選擇能可靠完成任務的最低充分認知配置：

\[
\boxed{
r^*
=
\arg\min_r C(r)
\quad
\text{s.t.}
\quad
Q(r)\ge Q_{\min}.
}
\]

---

## P3 — Escalation Before Failure

Runtime 應在偵測到：

- confidence 下降；
- contradiction；
- evidence gap；
- tool failure；
- risk increase；

時主動升級，而不是等最終答案失敗後才重做。

---

## P4 — De-escalation Is First-Class

如果：

- 高信心；
- 問題已解；
- 邊際資訊收益下降；

應允許：

\[
\text{deep}\rightarrow\text{shallow}\rightarrow\text{stop}.
\]

---

## P5 — User Intent Overrides Default

使用者明確指定：

- 「只給答案」；
- 「深入分析」；
- 「嚴格驗證」；
- 「不要用我的歷史」；

時，Runtime 將其視為高權重約束。

---

## P6 — Architecture Before Training

v0.x 不需要重新訓練模型。

先以：

- classifier；
- heuristic；
- prompt planner；
- policy rules；

建立外部 Runtime。

收集 traces 後，再決定是否訓練 router / controller。

---

# 3. 系統總覽

```text
User / API
    │
    ▼
┌────────────────────────────┐
│ 1. Request Normalizer      │
└─────────────┬──────────────┘
              ▼
┌────────────────────────────┐
│ 2. Global Task Mapper      │
│ low-resolution task graph  │
└─────────────┬──────────────┘
              ▼
┌────────────────────────────┐
│ 3. Cognitive Profiler      │
│ difficulty / uncertainty   │
│ risk / evidence / action   │
└─────────────┬──────────────┘
              ▼
┌────────────────────────────┐
│ 4. Regime Router           │
│ DIRECT / EXPLAIN / REASON  │
│ RESEARCH / VERIFY / FORMAL │
└─────────────┬──────────────┘
              ▼
┌────────────────────────────┐
│ 5. Resource Gating Layer   │
│ compute / context / memory │
│ tools / verifier / model   │
└─────────────┬──────────────┘
              ▼
┌────────────────────────────┐
│ 6. Execution Runtime       │
└─────────────┬──────────────┘
              ▼
┌────────────────────────────┐
│ 7. Adaptive Supervisor     │
│ confidence / error / cost  │
│ escalate / de-escalate     │
└─────────────┬──────────────┘
              ▼
         Final Output
```

---

# 4. Global Task Mapper

Global Task Mapper 不負責完整解題。

輸出：

\[
G_T=(V,E,M)
\]

其中：

- \(V\)：主要子任務；
- \(E\)：依賴；
- \(M\)：metadata。

例如：

```json
{
  "goal": "answer simple arithmetic",
  "subtasks": ["calculate"],
  "needs_current_data": false,
  "needs_tools": false,
  "needs_formal_proof": false,
  "action_side_effects": false
}
```

對研究任務則可能：

```json
{
  "goal": "evaluate a new mathematical conjecture",
  "subtasks": [
    "formalize claim",
    "search related work",
    "test examples",
    "search counterexamples",
    "assess salvageable structure"
  ],
  "needs_current_data": true,
  "needs_tools": true,
  "needs_formal_proof": "possible",
  "action_side_effects": false
}
```

Task Map 必須：

- 小；
- cheap；
- 可重新生成；
- 不包含完整 chain-of-thought。

---

# 5. Cognitive Profiler

MVP 使用七維：

\[
z_T=
(D,U,R,N,L,E,A)
\]

### D — Difficulty
估計推理複雜度。

### U — Uncertainty
模型／系統對輸入、知識或答案的不確定性。

### R — Risk
錯誤後果。

### N — Novelty
是否偏離常規 pattern。

### L — Dependency Depth
子任務與依賴深度。

### E — Evidence Requirement
是否需要外部證據、引用、驗證。

### A — Action Consequence
是否有外部 side effect。

每項先離散為：

```text
0 = low
1 = medium
2 = high
```

MVP 不追求精確心理量表。

目標只是：

\[
\boxed{
\text{route well enough}.
}
\]

---

# 6. Cognitive Regimes

ACR v0.1 定義七種 regime：

## DIRECT
單步、低風險、低不確定。

## EXPLAIN
需要基本說明，但不需要長鏈推理。

## REASON
多步推理、內部分析。

## RESEARCH
需要外部資料與證據。

## VERIFY
答案已有候選，但需要高強度查錯／反例。

## FORMAL
需要形式推導、程式驗證、定理證明等。

## EXECUTE
需要外部工具產生 side effects。

Regime 不是模型人格。

它是：

\[
\boxed{
\text{runtime policy profile}.
}
\]

---

# 7. Resource Gating

每個 regime 對應：

\[
\rho=
(B_r,B_c,M,T,V,A_u)
\]

其中：

- \(B_r\)：reasoning budget；
- \(B_c\)：context budget；
- \(M\)：memory scope；
- \(T\)：tools；
- \(V\)：verification strength；
- \(A_u\)：autonomy level。

範例：

| Regime | Reasoning | Context | Memory | Tools | Verify | Autonomy |
|---|---|---|---|---|---|---|
| DIRECT | low | local | none/min | off | low | answer |
| EXPLAIN | low-med | local | optional | off | low | answer |
| REASON | med-high | task | task | optional | med | answer |
| RESEARCH | high | expanded | relevant | web/search | med-high | research |
| VERIFY | high | evidence | relevant | verifier | very high | audit |
| FORMAL | high | formal | task | code/prover | very high | formalize |
| EXECUTE | task | task | relevant | allowlist | high | action |

---

# 8. Memory 與 Context

ACR 將：

\[
\text{memory available}
\]

與：

\[
\text{memory loaded}
\]

分離。

2026 的 AgeMem 已把 store、retrieve、update、summarize、discard 直接作為 Agent action；Memory-R1 亦學習 ADD、UPDATE、DELETE、NOOP 等操作。這支持「memory selection 是 policy」而不是固定 RAG 管線的方向。

ACR v0.1 採：

```text
memory_scope =
  none
  current_turn
  task_session
  relevant_long_term
  full_allowed
```

Context 同理：

```text
context_scope =
  minimal
  local
  task
  expanded
```

Context as a Tool 已證明，在長期 SWE Agent 中，主動壓縮與管理 context 可以優於 append-only / 靜態壓縮方式。

---

# 9. Tools

工具不是預設全部開放。

每次 task profile 產生：

```text
tool_allowlist
```

例如：

```json
{
  "web_search": true,
  "python": false,
  "filesystem_write": false,
  "email_send": false
}
```

若途中需要新工具：

\[
T_{\mathrm{off}}
\rightarrow
T_{\mathrm{request}}
\rightarrow
T_{\mathrm{on}}
\]

必須經 supervisor / policy gate。

這是 RSG「權限封印」的現代工程版本。

---

# 10. Model Routing 是可選項，不是核心

RouteLLM 與後續 dynamic routing 研究顯示，根據 query characteristics 在強／弱模型間 routing 可以改善成本效益。

但 ACR v0.1 建議：

\[
\boxed{
\text{single-model-first}.
}
\]

原因：

- 減少行為不一致；
- 避免不同模型記憶／工具協議差異；
- 更容易評估 Runtime 本身；
- 不把「模型能力差」誤認成「認知配置差」。

之後再增加：

```text
model_tier =
  fast
  standard
  frontier
  specialist
  local_private
```

---

# 11. Adaptive Supervisor

Supervisor 在執行途中監控：

\[
S_t=
(C_f,X_c,E_g,F_r,K_c)
\]

其中：

- \(C_f\)：confidence；
- \(X_c\)：contradiction；
- \(E_g\)：evidence gap；
- \(F_r\)：failure rate；
- \(K_c\)：cost consumed。

### Escalation Trigger

例如：

\[
C_f<\theta_c
\]

或：

\[
X_c=1
\]

或：

\[
E_g>\theta_e.
\]

則：

\[
r_t\rightarrow r_{t+1}^{+}.
\]

### De-escalation / Stop

若：

\[
C_f>\theta_h
\]

且：

\[
\Delta I_{\mathrm{next}}<\theta_I,
\]

則：

\[
\operatorname{Stop}.
\]

CoRefine 類工作已證明 confidence dynamics 可以成為 halt／re-examine／alternate approach 的控制訊號；VLA-ATTC 甚至把 uncertainty-triggered escalation 稱為「cognitive clutch」。

---

# 12. 使用者 Cognitive Interaction Mode

ACR 支援：

```text
AUTO
DIRECT
DEEP
AUDIT
CREATIVE
BLIND
FORMAL
EXECUTE
```

### AUTO
Runtime 自行判斷。

### DIRECT
最短充分答案；除非偵測高風險／歧義才升級。

### DEEP
允許高 reasoning/context 預算。

### AUDIT
偏重反證、驗證、來源。

### CREATIVE
延遲過早 closure，擴張候選。

### BLIND
限制 personalization/history 對核心判斷的影響。

### FORMAL
偏重形式化、程式／證明驗證。

### EXECUTE
允許進入工具行動流程。

User mode 是約束：

\[
r\in\mathcal R_U,
\]

不是硬編碼答案。

---

# 13. 可觀測性

每次執行記錄：

```json
{
  "task_profile": {},
  "initial_regime": "DIRECT",
  "regime_transitions": [],
  "reasoning_budget": {},
  "memory_scope": "none",
  "tools_used": [],
  "verification_level": "low",
  "latency_ms": 0,
  "token_cost": 0,
  "final_quality": null
}
```

不保存模型私密 chain-of-thought。

保存的是：

\[
\boxed{
\text{runtime decisions}.
}
\]

---

# 14. 評估

至少四條曲線：

## Quality
任務品質。

## Cost
token / API / compute。

## Latency
互動時間。

## Cognitive Mismatch
錯誤 regime 比率。

定義：

\[
CMR
=
P(
r_{\mathrm{selected}}
\neq
r_{\mathrm{oracle}}
).
\]

再分：

\[
UR
=
P(\text{underthink})
\]

與：

\[
OR
=
P(\text{overthink}).
\]

---

# 15. 核心 Benchmark

建立混合任務集：

- 30% trivial；
- 25% explain；
- 20% multi-step；
- 10% research；
- 10% verification；
- 5% action/high-risk。

比較：

### Baseline A
全部 DIRECT。

### Baseline B
全部 DEEP。

### Baseline C
固定 heuristic。

### ACR
adaptive。

若 ACR 成立，目標不是每題最高分，而是：

\[
\boxed{
\max
\frac{\text{quality}}
{\text{cost}+\text{latency}}
}
\]

並維持高風險任務品質下限。

---

# 16. 與《反身狀態閘控論》的關係

RSG：

\[
X
\rightarrow
X^{(g)}.
\]

ACR v0.1：

\[
\boxed{
X_{\mathrm{external}}
\rightarrow
X_{\mathrm{external}}^{(g)}.
}
\]

也就是目前只能 gate：

- context；
- memory；
- tools；
- reasoning budget；
- model；
- verifier。

未來若模型暴露更多可控制內部狀態，ACR 可以逐步往 RSG 發展。

---

# 17. 路線圖

## v0.1
規則式 profiler + regime router。

## v0.2
加入 execution feedback escalation。

## v0.3
加入 memory/context gating。

## v0.4
加入 tool permissions / verifier。

## v0.5
以 trace 訓練 lightweight router。

## v1.0
完整 adaptive cognitive runtime。

未來：

\[
\text{ACR}
\rightarrow
\text{RSG-capable Runtime}.
\]

---

# 18. 結論

ACR 的核心不是讓 AI 少想。

而是：

\[
\boxed{
\text{讓 AI 把思考本身視為需要管理的資源。}
}
\]

傳統：

\[
\text{question}\rightarrow\text{answer}.
\]

Reasoning model：

\[
\text{question}\rightarrow\text{reason}\rightarrow\text{answer}.
\]

ACR：

\[
\boxed{
\text{question}
\rightarrow
\text{assess}
\rightarrow
\text{configure}
\rightarrow
\text{reason}
\rightarrow
\text{reassess}
\rightarrow
\text{answer}.
}
\]

因此最簡單的工程原則仍然是：

\[
\boxed{
\text{不是讓 AI 永遠想得更深，}
}
\]

\[
\boxed{
\text{而是讓它知道何時值得想得更深。}
\]

---

## 參考資料

- De Sabbata, C. N., Sumers, T. R., & Griffiths, T. L. (2024). *Rational Metareasoning for Large Language Models*.
- Ong, I. et al. (2024). *RouteLLM: Learning to Route LLMs with Preference Data*.
- Yu, Y. et al. (2026). *Agentic Memory: Learning Unified Long-Term and Short-Term Memory Management for Large Language Model Agents*. ACL 2026.
- Yan, S. et al. (2026). *Memory-R1: Enhancing Large Language Model Agents to Manage and Utilize Memories via Reinforcement Learning*. ACL 2026.
- Liu, S. et al. (2026). *Context as a Tool: Context Management for Long-Horizon SWE-Agents*. Findings of ACL 2026.
- Jin, C. et al. (2026). *CoRefine: Confidence-Guided Self-Refinement for Adaptive Test-Time Compute*.
- Zhai, Z. et al. (2026). *Adaptive Test-Time Compute Allocation for Reasoning LLMs via Constrained Policy Optimization*.
- Li, W. et al. (2026). *VLA-ATTC: Adaptive Test-Time Compute for VLA Models with Relative Action Critic Model*.
