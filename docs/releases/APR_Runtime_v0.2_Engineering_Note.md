# APR Runtime v0.2 工程增補：Real Stream

**版本：v0.2**  
**日期：2026-08-07**

## 1. 本版回答的問題

v0.1 證明 APR 控制層可以在模擬世界中運作：

```text
Unknown -> Observe -> Known -> No Observation
Stale -> Inspect
Contradicted -> Revisit
```

v0.2 進一步問：

> 這套控制層能不能真的接到持續存在的電腦桌面，而不是只有 simulator？

本版答案是：可以，並先從低成本的 Fast Loop 開始。

## 2. Real Stream 架構

```text
Windows Desktop
├─ Screen Frame
│   └─ sampled frame delta
├─ Foreground Window
│   └─ HWND / title / PID
└─ UI Automation
    └─ bounded accessibility snapshot
             │
             ▼
       RealStreamMonitor
             │
             ├─ screen_change
             ├─ foreground_changed
             └─ uia_changed
             │
             ▼
     Persistent World State
             │
             ▼
      APR Slow-loop Escalation
```

## 3. 重要工程修正：volatile state

v0.1 的 conflict 模型假定兩個高可信 evidence 對同一 fact 給不同值時，
應標記為 `CONTRADICTED`。

這對：

```text
door.identity
medicine.label
invoice.total
```

是合理的。

但對：

```text
foreground_window
cursor_position
person_position
screen_change_ratio
```

則不合理，因為它們本來就會變。

因此 v0.2 加入：

```text
FactState.volatile
```

動態狀態使用：

```text
latest valid observation -> replace current value
```

非動態 claim 仍保留：

```text
strong disagreement -> CONTRADICTED -> REVISIT
```

這是 Persistent World State 從靜態 MVP 走向真實流所必須補上的語義。

## 4. Screen Fast Loop

本版不讓 VLM 每次看全畫面。

而是：

$$
F_{t-1},F_t
\rightarrow
SampledDelta
$$

輸出：

$$
(
mean\_abs\_delta,
changed\_ratio,
bbox
)
$$

只有：

$$
changed\_ratio>\tau
$$

才發出 `screen_change` event。

這是 APR-02 的低階：

$$
\Delta^{pix}
$$

並不把它錯稱為：

$$
\Delta^{sem}
$$

## 5. Structured UI Fast Loop

Windows UI Automation 本身提供可編程的 UI 元素樹。

v0.2 不每輪 dump 全樹，而只取得 bounded snapshot：

```text
max_elements = N
```

再計算：

```text
digest(snapshot)
```

若 digest 未變：

```text
NO STRUCTURAL EVENT
```

若變：

```text
uia_changed
```

之後 Slow Loop 才有理由 inspect selected subtree。

## 6. Structured state 優先於視覺

若目標是：

```text
desktop.foreground.title
```

v0.2 可直接透過 Win32 讀取。

流程：

```text
Goal
 -> STRUCTURED modality
 -> Win32ForegroundWindowSource
 -> Evidence
 -> World State
```

而不是：

```text
Screenshot
 -> OCR
 -> Guess title
```

因此此版本開始真正落實：

$$
\boxed{
NativeState
>
Event
>
StructuralDelta
>
VisualDelta
>
FullVision
}
$$

這裡的 `>` 表示資訊效率優先序，而非能力高低。

## 7. Native events 的位置

Windows 的 UI Automation 與 WinEvents 都支援事件通知。

v0.2 尚未直接掛 `SetWinEventHook`；目前先用 snapshot polling 轉成
event stream，因為可測、容易 debug，且已能驗證 APR 的 Fast/Slow
loop 邊界。

未來只需替換 Source：

```text
PollingSource
-> NativeWinEventSource
```

不需要重寫 World State、Evidence 或 Policy。

## 8. 本版完成標準

v0.2 視為完成，若：

1. synthetic stream tests 全過；
2. frame delta 可辨識變化區；
3. foreground/UIA 變化不被誤判為 contradiction；
4. structured desktop adapter 可直接回答真實桌面 fact；
5. Windows demo 可以在無 VLM 條件下持續跑 Fast Loop；
6. 所有真實感知來源仍可替換。

## 9. 下一版

v0.3 建議正式進入：

```text
Fast Loop event
 -> ROI / evidence pointer
 -> VLM Inspect Adapter
 -> semantic evidence
 -> world-state revision
```

也就是第一次把：

$$
\Delta^{pix/struct}
$$

升級成：

$$
\Delta^{sem}
$$

並建立可保存與重看的 Evidence Archive。
