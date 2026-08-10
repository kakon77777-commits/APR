# Adaptive Cognitive Runtime（ACR）MVP Runtime 規格
## v0.1 — Single-Model Adaptive Cognition Controller

**版本：** MVP v0.1  
**日期：** 2026-08-02  
**目標：** 以最小工程成本驗證「先判斷認知需求，再自適應配置」是否比固定深度更有效。

---

# 1. MVP 範圍

ACR MVP **不做**：

- 模型權重修改；
- 真正內部 cognition sealing；
- RL training；
- 多 Agent swarm；
- 自主長期學習；
- 複雜多模型 router。

ACR MVP **只做**：

1. 任務低解析度分類；
2. 認知需求評分；
3. Regime 選擇；
4. reasoning/context/memory/tool/verification 配置；
5. 執行途中最多兩次升級；
6. trace 記錄；
7. 固定 baseline 比較。

目標：

\[
\boxed{
\text{Proof of Runtime Possibility}
}
\]

而不是最佳化產品。

---

# 2. Runtime Pipeline

```text
POST /run
   │
   ▼
Normalize Request
   │
   ▼
Task Mapper
   │
   ▼
Cognitive Profiler
   │
   ▼
Regime Router
   │
   ▼
Resource Policy
   │
   ▼
Model Call
   │
   ├── confidence OK ───────► Finish
   │
   └── uncertainty/error
            │
            ▼
       Escalate Regime
            │
            ▼
         Model Call
            │
            ▼
           Finish
```

---

# 3. Regime Enum

```python
class Regime(str, Enum):
    DIRECT = "direct"
    EXPLAIN = "explain"
    REASON = "reason"
    RESEARCH = "research"
    VERIFY = "verify"
    FORMAL = "formal"
```

MVP 暫不做 EXECUTE side effects。

---

# 4. Request Schema

```json
{
  "message": "使用者輸入",
  "mode": "auto",
  "session_id": "optional",
  "preferences": {
    "verbosity": "auto",
    "latency_priority": "balanced",
    "cost_priority": "balanced",
    "allow_web": true,
    "allow_code": true,
    "use_long_term_memory": true
  }
}
```

---

# 5. TaskMap Schema

```json
{
  "goal": "string",
  "task_type": "fact|explain|reason|research|verify|formal|other",
  "subtasks": ["string"],
  "requires_current_info": false,
  "requires_external_evidence": false,
  "requires_code": false,
  "requires_formalization": false,
  "has_external_side_effect": false
}
```

Task Mapper 要求：

- 最大 200–400 output tokens；
- 不解題；
- 不產生完整推理；
- JSON-only。

---

# 6. CognitiveProfile Schema

```json
{
  "difficulty": 0,
  "uncertainty": 0,
  "risk": 0,
  "novelty": 0,
  "dependency_depth": 0,
  "evidence_requirement": 0,
  "action_consequence": 0,
  "confidence": 0.95
}
```

每個離散值：

```text
0 low
1 medium
2 high
```

confidence：

\[
[0,1].
\]

---

# 7. Initial Router v0.1

規則：

```python
def route(task, profile, mode):
    if mode != "auto":
        return mode_to_regime(mode)

    if task.requires_formalization:
        return FORMAL

    if task.requires_current_info or profile.evidence_requirement == 2:
        return RESEARCH

    if profile.risk == 2:
        return VERIFY

    score = (
        profile.difficulty
        + profile.uncertainty
        + profile.novelty
        + profile.dependency_depth
    )

    if score <= 1:
        return DIRECT
    if score <= 3:
        return EXPLAIN
    return REASON
```

這只是 baseline。

---

# 8. ResourcePolicy

```json
{
  "regime": "reason",
  "reasoning_budget": "medium",
  "context_scope": "task",
  "memory_scope": "task_session",
  "web": false,
  "code": false,
  "verification": "medium",
  "max_output_tokens": 1600
}
```

---

# 9. Regime Presets

## DIRECT

```json
{
  "reasoning_budget": "minimal",
  "context_scope": "minimal",
  "memory_scope": "none",
  "verification": "low",
  "max_output_tokens": 400
}
```

## EXPLAIN

```json
{
  "reasoning_budget": "low",
  "context_scope": "local",
  "memory_scope": "current_turn",
  "verification": "low",
  "max_output_tokens": 900
}
```

## REASON

```json
{
  "reasoning_budget": "medium",
  "context_scope": "task",
  "memory_scope": "task_session",
  "verification": "medium",
  "max_output_tokens": 1800
}
```

## RESEARCH

```json
{
  "reasoning_budget": "high",
  "context_scope": "expanded",
  "memory_scope": "relevant_long_term",
  "web": true,
  "verification": "high",
  "max_output_tokens": 2600
}
```

## VERIFY

```json
{
  "reasoning_budget": "high",
  "context_scope": "evidence",
  "memory_scope": "task_session",
  "verification": "very_high",
  "max_output_tokens": 2200
}
```

## FORMAL

```json
{
  "reasoning_budget": "high",
  "context_scope": "task",
  "memory_scope": "task_session",
  "code": true,
  "verification": "very_high",
  "max_output_tokens": 3000
}
```

---

# 10. Context Builder

```python
def build_context(request, policy, memory_store):
    context = [request.current_message]

    if policy.context_scope in ("local", "task", "expanded"):
        context += get_recent_turns()

    if policy.context_scope in ("task", "expanded"):
        context += get_task_summary()

    if policy.memory_scope == "relevant_long_term":
        context += retrieve_memory(query=request.message, top_k=5)

    return fit_to_budget(context, policy)
```

核心：

\[
\boxed{
\text{available memory}
\neq
\text{loaded memory}.
}
\]

---

# 11. Memory Store v0.1

最簡版 SQLite / JSONL。

Memory item：

```json
{
  "id": "uuid",
  "session_id": "string",
  "kind": "fact|preference|task_state|summary",
  "content": "string",
  "embedding": null,
  "created_at": "timestamp",
  "confidence": 0.9
}
```

MVP 先做到：

- write summary；
- semantic retrieval；
- no automatic delete。

Memory-R1 / AgeMem 類 learned operations 留到 v0.3+。

---

# 12. Execution Result Schema

```json
{
  "answer": "...",
  "self_check": {
    "confidence": 0.86,
    "contradiction_detected": false,
    "evidence_gap": false,
    "tool_failure": false,
    "needs_escalation": false,
    "suggested_regime": null
  }
}
```

self_check 不要求模型暴露 chain-of-thought。

只要求：

\[
\boxed{
\text{control signals}.
}
\]

---

# 13. Escalation Rules

```python
ORDER = [
    DIRECT,
    EXPLAIN,
    REASON,
    RESEARCH,
    VERIFY
]
```

FORMAL 由 task requirement 特殊進入。

觸發：

```python
if confidence < 0.65:
    escalate()

if contradiction_detected:
    escalate()

if evidence_gap and web_allowed:
    switch_to(RESEARCH)

if high_risk and verification != "very_high":
    switch_to(VERIFY)
```

最大 escalation：

```text
2 transitions / request
```

避免無限 meta-loop。

---

# 14. De-Escalation / Early Stop

若第一輪已：

```text
confidence >= 0.90
contradiction = false
evidence_gap = false
```

直接停止。

若進入高 regime 後 verifier 判定：

```text
sufficient = true
```

不再繼續展開。

---

# 15. User Mode Mapping

```python
MODE_MAP = {
    "direct": DIRECT,
    "deep": REASON,
    "audit": VERIFY,
    "formal": FORMAL
}
```

特殊：

## BLIND

不是 regime。

它是 flag：

```json
{
  "use_long_term_memory": false,
  "identity_context": false
}
```

## CREATIVE

MVP 可映射：

```json
{
  "regime": "reason",
  "verification": "delayed",
  "candidate_count": 3
}
```

---

# 16. API

## POST /run

request：

```json
{
  "message": "1+1等於多少？",
  "mode": "auto"
}
```

response：

```json
{
  "answer": "2。",
  "runtime": {
    "task_type": "fact",
    "regime_initial": "direct",
    "regime_final": "direct",
    "escalations": 0
  }
}
```

另一案例：

```json
{
  "message": "請從 Peano 公理推導 1+1=2",
  "mode": "auto"
}
```

可能：

```json
{
  "runtime": {
    "task_type": "formal",
    "regime_initial": "formal",
    "regime_final": "formal"
  }
}
```

---

# 17. Trace Schema

```json
{
  "trace_id": "uuid",
  "request_hash": "...",
  "task_map": {},
  "profile": {},
  "initial_policy": {},
  "events": [
    {
      "type": "model_call",
      "regime": "direct",
      "tokens": 42,
      "latency_ms": 210
    }
  ],
  "final_regime": "direct",
  "total_tokens": 42,
  "total_latency_ms": 210,
  "quality_score": null
}
```

禁止 trace：

- hidden chain-of-thought；
- 私密模型內部推理文本。

---

# 18. MVP Storage

```text
acr/
├── app.py
├── schemas.py
├── mapper.py
├── profiler.py
├── router.py
├── policies.py
├── executor.py
├── supervisor.py
├── memory.py
├── tracing.py
├── eval/
│   ├── dataset.jsonl
│   └── evaluate.py
└── tests/
```

---

# 19. Technology Stack

建議最小：

```text
Python 3.12
FastAPI
Pydantic
SQLite
HTTP client / provider adapter
optional embeddings
pytest
```

不需要：

- Kubernetes；
- vector DB；
- event bus；
- distributed agents。

---

# 20. Provider Adapter

所有模型統一：

```python
class ModelAdapter:
    async def generate(
        self,
        messages,
        reasoning_budget=None,
        max_tokens=None,
        tools=None
    ) -> ModelResult:
        ...
```

若 provider 不支援 reasoning budget：

- 用不同 system instruction；
- 不同 model endpoint；
- 或忽略該欄位。

Runtime 不依賴單一供應商。

---

# 21. Evaluation Dataset

至少 200 題。

```text
40 trivial
40 factual/explain
40 reasoning
30 research/current
30 verification
20 formal/code
```

每題標：

```json
{
  "oracle_min_regime": "direct",
  "acceptable_regimes": ["direct", "explain"],
  "requires_web": false,
  "risk": 0
}
```

---

# 22. Baselines

## B0 — Fast Only
全部 DIRECT。

## B1 — Deep Only
全部 REASON。

## B2 — Prompt Classifier Only
初始 routing，但不 escalation。

## ACR
routing + adaptive supervisor。

---

# 23. Metrics

### Accuracy / Quality

人工或 judge score。

### Token Cost

\[
TC=\sum\text{tokens}.
\]

### Latency

\[
L.
\]

### Overthinking Rate

\[
OR
=
P(r>r^*).
\]

### Underthinking Rate

\[
UR
=
P(r<r^*).
\]

### Escalation Precision

\[
EP
=
P(\text{escalation useful}\mid\text{escalated}).
\]

### Escalation Recall

\[
ER
=
P(\text{escalated}\mid\text{needed}).
\]

### Utility

可用：

\[
\boxed{
U
=
Q
-
\lambda TC
-
\mu L
-
\nu RiskFailure.
}
\]

---

# 24. MVP Success Criteria

v0.1 成功不要求 SOTA。

只要求同一模型下，相對 B0 / B1：

1. trivial 任務 token 顯著下降；
2. complex 任務品質不低於 deep baseline 的可接受範圍；
3. high-risk / research 任務能正確升級；
4. overall utility 提升；
5. router 可解釋且 trace 可審核。

最重要判準：

\[
\boxed{
Q_{\mathrm{ACR}}
\approx
Q_{\mathrm{Deep}}
}
\]

同時：

\[
\boxed{
Cost_{\mathrm{ACR}}
<
Cost_{\mathrm{Deep}}.
}
\]

---

# 25. 下一版本

## v0.2
學習式 task profiler。

## v0.3
Agentic memory operations。

## v0.4
multi-model routing。

## v0.5
learned supervisor / confidence model。

## v0.6
task graph dynamic expansion。

## v1.0
完整 Cognitive Runtime。

---

# 26. 一句話 MVP

ACR v0.1 就是：

\[
\boxed{
\text{先用很少的成本判斷「這題值不值得深想」，}
}
\]

\[
\boxed{
\text{再只給它足夠的認知資源，}
}
\]

\[
\boxed{
\text{如果途中發現想少了，再升級。}
}
\]

它不需要 AGI。

不需要修改模型。

甚至不需要多模型。

它只需要把原本固定的：

\[
\boxed{
\text{Reasoning / Context / Memory / Tool Policy}
}
\]

改成：

\[
\boxed{
\text{Task-Conditioned Adaptive Policy}.
}
\]

這就是 MVP。
