# APR Runtime v0.3 — Semantic Evidence Layer

**日期：2026-08-07**

## 1. v0.2 → v0.3

v0.2 能回答：

> 哪裡變了？

以：

```text
frame delta
foreground change
UIA structural change
```

產生低成本事件。

v0.3 新增：

> 這個變化在語義上代表什麼？

流程：

$$
\boxed{
\Delta^{pix}
\rightarrow
ROI
\rightarrow
SemanticInspect
\rightarrow
EvidenceContract
\rightarrow
\Delta^{sem/state}
\rightarrow
W_t
}
$$

## 2. 本版核心模組

### `image_ops.py`

- bbox clamp/padding；
- BGRA ROI crop；
- stdlib PNG encoder。

不強迫 Pillow/OpenCV 成為 core dependency。

### `archive.py`

SQLite metadata + 外部資產檔：

```text
runtime_data/
├─ evidence.sqlite3
└─ assets/
   └─ screen-roi-....png
```

### `semantic.py`

提供：

```text
SemanticInspector
CallableSemanticInspector
CommandSemanticInspector
RuleSemanticInspector
```

### `semantic_pipeline.py`

把：

```text
StreamEvent + latest frame
```

升級成：

```text
ROI PNG
SemanticResult
Evidence[]
WorldState revision
```

### `semantic_stream.py`

建立 Fast/Slow loop：

```text
RealStreamMonitor
   ↓
high-significance screen event only
   ↓
SemanticEvidencePipeline
```

因此不是每一個 frame 都進 VLM。

## 3. Evidence Archive

v0.3 首次讓 APR 的 `Evidence Layer` 變成真正持久儲存。

SQLite 保存：

```text
claim
value
modality
source
confidence
cost
timestamp
pointer
asset_path
metadata
```

而 ROI PNG 保存在外部資產目錄。

之後：

```text
REVISIT
```

可以重新讀取原先的 crop，而不必重放全部螢幕歷史。

## 4. Semantic Inspector 為什麼不綁 SDK

APR Runtime 的研究目標是控制面。

因此 v0.3 的 VLM 邊界是：

```text
image + prompt + context
 -> SemanticResult
```

而不是：

```text
APR core -> vendor-specific API
```

本地模型、雲端模型都可用：

```text
CallableSemanticInspector
```

或：

```text
CommandSemanticInspector
```

接入。

## 5. 語義狀態

Semantic Inspector 回傳 fact：

```text
desktop.warning.visible = true
confidence = 0.96
volatile = true
ttl = 5s
```

Pipeline 會：

1. 設定 World State schema；
2. 產生 Vision Evidence；
3. 保存 provenance；
4. 寫 SQLite；
5. 指向實際 ROI PNG；
6. 更新 World State。

所以現在：

$$
W_t
$$

中的 semantic fact 已能追溯到：

$$
E_t
$$

與：

$$
ROI_t
$$

## 6. 真正的「重看」

v0.1 的 REVISIT 是控制邏輯。

v0.3 之後開始具備真正的材料：

```text
Fact
 -> evidence_id
 -> archive row
 -> ROI PNG
 -> semantic inspector
```

所以後續 v0.4 可以正式實作：

```text
targeted historical REVISIT
```

而不是只對現在重新觀察。

## 7. 安全邊界

低階 pixel delta 不直接被當成 semantic delta。

只有 Semantic Inspector 產生的 Evidence 才能建立：

```text
desktop.warning.visible
desktop.dialog.type
desktop.download.failed
...
```

這保持：

$$
\Delta^{pix}
\neq
\Delta^{sem}
$$

## 8. 下一版建議：v0.4

下一步應做：

### Historical Revisit + Browser Native State

1. `EvidenceArchive` query / historical replay；
2. fact → evidence → image targeted revisit；
3. Browser/CDP DOM adapter；
4. UIA subtree targeted inspect；
5. conflict resolution using archived evidence；
6. native WinEvent source（可選）。

這會把：

```text
current semantic inspection
```

推進到：

```text
persistent evidence memory + historical re-observation
```
