# APR Runtime v0.4 — Historical Revisit + Browser Native State

**日期：2026-08-07**

## 1. v0.4 的兩個核心問題

### A. APR 能不能真的「回頭重讀」？

v0.3 已能保存：

```text
semantic fact
 -> evidence id
 -> SQLite row
 -> exact ROI PNG
```

v0.4 加上：

```text
Fact
 -> evidence IDs
 -> archived asset
 -> SemanticInspector
 -> new Evidence
 -> Belief Revision
```

因此：

$$
\boxed{
Revisit
}
$$

不再只是重新看「現在」。

它也可以是：

$$
\boxed{
HistoricalRevisit
}
$$

即重新解讀當時真正保存的證據。

### B. Browser Agent 是否一定要靠 screenshot？

不需要。

Chromium / Playwright / CDP 本身可提供：

```text
URL
title
DOM structure
ARIA/accessibility structure
active element
```

所以 v0.4 新增 Browser Native State。

---

## 2. Historical Revisit

### 現在重新觀察

回答：

> 世界現在是什麼？

### Historical Revisit

回答：

> 我當時看到的證據到底支持什麼？

兩者不可混淆：

$$
CurrentObservation
\neq
HistoricalEvidence
$$

例如：

```text
昨天 frame_102 的警告到底是 HIGH 還是 LOW？
```

如果今天畫面早已不存在，就不能重新看現在。

必須：

```text
Fact
 -> archived evidence
 -> archived ROI
 -> re-inspect
```

---

## 3. Revisit provenance

新 Evidence 會帶：

```text
historical_revisit = true
revisit_of = <old evidence id>
source_asset = <old ROI>
semantic_summary = ...
```

因此 evidence graph 可以形成：

```text
E_old
  ↓ revisit
E_new
```

而不是覆蓋舊證據。

---

## 4. Browser Native State

v0.4 新增：

```text
browser.url
browser.title
browser.aria.snapshot
browser.aria.digest
browser.dom.digest
browser.dom.element_count
browser.active_element
```

其中 fast loop 主要保存：

```text
url/title/digests/count/focus
```

完整 ARIA snapshot 只在明確 goal 查詢時由 adapter 讀取。

---

## 5. 為什麼不 dump 全 DOM？

Chrome DevTools Protocol 的 DOM domain 本身支持有限深度 node retrieval，
並提供 DOM mutation events；Accessibility domain 也提供 full / partial tree。

APR 的原則因此不是：

```text
每輪 get entire page tree
```

而是：

```text
bounded native state
 -> digest/change
 -> targeted deep read if necessary
```

---

## 6. Browser Fast Loop

```text
BrowserSnapshot_t
   │
   ├─ url/title
   ├─ aria digest
   ├─ dom digest
   └─ active element
   │
   ▼
compare with t-1
   │
   ├─ browser_navigation
   ├─ browser_aria_changed
   ├─ browser_dom_changed
   └─ browser_focus_changed
```

這些全都屬：

$$
\Delta^{struct}
$$

不是：

$$
\Delta^{pix}
$$

---

## 7. Playwright CDP source

可連既有 Chromium：

```python
PlaywrightCDPBrowserSource(
    "http://127.0.0.1:9222"
)
```

來源採：

```text
connect_over_cdp
```

並讀取現有：

```text
browser.contexts
page
```

注意：

CDP endpoint 具有很高瀏覽器權限，不應暴露到不可信網路。

---

## 8. bounded ARIA

現代 Playwright 提供：

```text
locator.aria_snapshot()
```

新版還可限制：

```text
depth
mode="ai"
```

v0.4 會使用這種 bounded representation。

若本地版本較舊，程式退回基本：

```text
aria_snapshot()
```

保持相容性。

---

## 9. bounded DOM digest

不下載整份 HTML。

Browser source 在頁面內只抽取最多：

```text
max_dom_elements
```

每個元素只保留有限：

```text
tag
id
role
aria-label
name
type
short text
```

然後 hash：

```text
DOM sample -> SHA256 digest
```

因此 Fast Loop 成本有上界。

---

## 10. Native state 優先

例如問題：

> 目前網址是什麼？

APR 使用：

```text
browser.url
```

而不是：

```text
screenshot
 -> locate address bar
 -> OCR
```

因此：

$$
\boxed{
NativeState
>
StructuralState
>
VisualEvidence
}
$$

在這類 task 中是直接工程優勢。

---

## 11. v0.4 完成後的 APR 記憶循環

現在已具備：

```text
Current world
 -> delta
 -> semantic evidence
 -> state
 -> archive
 -> later question
 -> historical evidence retrieval
 -> re-read
 -> belief revision
```

即：

$$
\boxed{
Perceive
\rightarrow
RememberEvidence
\rightarrow
Revisit
\rightarrow
Revise
}
$$

---

## 12. 下一版 v0.5

建議開始做：

### Event-Native + Targeted Subtree Runtime

1. Chrome DOM/CDP native mutation events；
2. Windows `SetWinEventHook`；
3. browser DOM/AX subtree targeted retrieval；
4. UIA subtree targeted retrieval；
5. persistent event ledger；
6. evidence retention / compaction；
7. current-vs-historical query distinction。

這會讓 APR 從：

```text
poll -> compare
```

進一步走到：

```text
native event -> targeted read
```
