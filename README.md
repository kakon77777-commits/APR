# APR — Adaptive Perceptual Reading / Agentic Perception Runtime

[![CI](https://github.com/kakon77777-commits/APR/actions/workflows/ci.yml/badge.svg)](https://github.com/kakon77777-commits/APR/actions/workflows/ci.yml)

APR 是一套「讓智能決定何時看、看哪裡、看多深、何時重看，以及何時停止看」的研究框架與可執行 Python MVP。它把感知視為受任務、風險、不確定性、證據品質與資源預算共同約束的治理行為，而不是永遠全量處理所有可用輸入。

This repository contains the theory corpus, the cumulative v0.10 runtime, examples, tests, and an explicit plugin boundary for downstream research projects.

> 目前定位是研究基礎設施與工程收斂候選版，不是已完成 benchmark 驗證的理論結論，也不是可直接用於高風險自主操作的 production agent。

## ACR 與 APR 的關係

- **ACR（Adaptive Cognitive Runtime）**：處理「一個問題值得投入多少認知／推理深度」。
- **APR（Adaptive Perceptual Reading）**：把相同的比例性原則落到感知，處理「需要取得哪些資訊、採用何種讀法、投入多少資源」。
- APR 不是把 ACR 改名；本儲存庫保留 ACR 理論根源，並以 APR runtime 作為獨立、可引用的感知基礎設施。

## 核心閉環

```text
Perceive
  → Maintain Belief
  → Determine Need
  → Gate Action
  → Execute
  → Observe Outcome
  → Verify
  → Recover
```

核心原則包括：

- 可用資訊不等於必須處理的資訊；
- event、evidence、current belief 三者分離；
- fresh state 可以合法導向 `NO_OBSERVATION`；
- 不確定、過期、衝突或高風險狀態觸發 targeted read／revisit；
- 行動前要通過 evidence preconditions，行動後要以新證據驗證 outcome；
- rollback 是明確的 compensating action，不是假設時間倒轉；
- retry、補償與不可逆行動都有顯式政策與 trace。

## 已整合內容

| 路徑 | 內容 |
| --- | --- |
| `apr_runtime/` | v0.1–v0.10 累積 runtime 與插件 registry |
| `tests/` | 世界狀態、事件、證據、action gate、outcome、recovery、插件與輸入不變量測試 |
| `examples/` | 合成串流、hosted vision、browser state、need graph、action readiness、closed-loop recovery 等示例 |
| `papers/` | APR-01 至 APR-07 理論系列 |
| `docs/theory/` | APR 統一白皮書與 ACR 理論根源 |
| `docs/runtime/` | 架構、協議、保留政策與各版 smoke-test 記錄 |
| `docs/releases/` | v0.2–v0.10 工程筆記與 0.x 收斂報告 |
| `docs/provenance/` | 原始壓縮包與來源文件的 SHA-256 清單 |
| `site/` | 雙語靜態研究網站、離線 Lab、機器探索檔案與 Cloudflare Static Assets 封裝 |

完整索引見 [`docs/README.md`](docs/README.md)。

## 公開靜態網站

`site/build.py` 只使用儲存庫內的 APR 內容與確定性固定案例，產生英文、繁體中文、
離線 Lab、`llms.txt`、`ai/site.json`、sitemap、robots、雙語 404 與靜態安全標頭。
瀏覽器端不呼叫模型 Provider、API、localhost、桌面 adapter 或未實作的 MCP 服務。

從儲存庫根目錄進行本機驗證與靜態預覽：

```powershell
Push-Location site
npm ci
npm run validate
npm run deploy:dry
Pop-Location
python -m http.server 8000 --directory site/dist
```

`npm run deploy:dry` 只執行 Wrangler dry-run。`npm run deploy` 是另外保留的正式發布入口；
production deployment 必須另行取得明確授權，並不屬於本機驗證流程。

## 快速開始

需要 Python 3.10 或更新版本。核心 runtime 沒有強制第三方依賴。

```powershell
git clone https://github.com/kakon77777-commits/APR.git
cd APR
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m unittest discover -s tests -v
python examples/run_demo.py
```

選用整合：

```powershell
python -m pip install -e ".[desktop]"
python -m pip install -e ".[browser]"
playwright install chromium
```

Desktop／browser 範例會接觸真實畫面或瀏覽器狀態；先閱讀相應腳本與 [`SECURITY.md`](SECURITY.md)，不要直接連接高風險操作環境。

## 最小使用例

```python
from apr_runtime import (
    APRRuntime,
    Budget,
    ChannelProfile,
    EvidenceStore,
    Goal,
    Modality,
    ObservationSpec,
    PolicyController,
    SimulatorAdapter,
    WorldState,
)

evidence = EvidenceStore()
world = WorldState(evidence)
policy = PolicyController(
    {
        Modality.STRUCTURED: ChannelProfile(
            Modality.STRUCTURED,
            reliability=0.98,
            cost=0.5,
            directness=1.0,
        )
    }
)
adapter = SimulatorAdapter(
    Modality.STRUCTURED,
    source="demo-state",
    world={"door.state": ObservationSpec("closed")},
    reliability=1.0,
    base_cost=0.5,
)
runtime = APRRuntime(
    world,
    evidence,
    policy,
    Budget(10),
    {Modality.STRUCTURED: adapter},
)

action, observation = runtime.step(Goal("door.state"))
```

## 插件介面

外部專案可以註冊 adapter、source、inspector、policy 或自訂 component factory，而不必修改 APR core：

```python
from apr_runtime import PluginRegistry

registry = PluginRegistry()
registry.register_component("adapter", "my_adapter", MyAdapter)
adapter = registry.create_component("adapter", "my_adapter", config=my_config)
```

APR 不會自動執行第三方插件。Python entry point 載入必須由呼叫端顯式觸發，且應只載入可信任的程式碼。完整契約與打包範例見 [`docs/PLUGIN_API.md`](docs/PLUGIN_API.md)。

內建的 hosted semantic plugin 可把 OpenAI Responses 或 Anthropic Messages 視覺輸出轉成相同的 APR `SemanticResult`，但只有在呼叫 `inspect()` 時才會連線：

```python
from apr_runtime import HostedSemanticInspectorsPlugin, PluginRegistry

registry = PluginRegistry()
registry.install(HostedSemanticInspectorsPlugin())
openai_inspector = registry.create_component("semantic_inspector", "openai")
```

憑證只從 `OPENAI_API_KEY`／`ANTHROPIC_API_KEY` 環境變數讀取。低成本雙供應商實測方式與限制見 [`docs/experiments/HOSTED_SEMANTIC_SMOKE_2026-08-10.md`](docs/experiments/HOSTED_SEMANTIC_SMOKE_2026-08-10.md)。

Google Vertex 插件提供真正的文字轉影像輸出，同時保持網路與認證為顯式、延遲發生的操作：

```python
from apr_runtime import GoogleVertexImageGenerationPlugin, PluginRegistry

registry = PluginRegistry()
registry.install(GoogleVertexImageGenerationPlugin())
generator = registry.create_component(
    "image_generator",
    "google_vertex",
    project_id="your-project-id",
)
result = generator.generate("one quiet observatory instrument", output_path="output.png")
```

先安裝 `pip install -e ".[vertex]"`，並以 Application Default Credentials 或
`GOOGLE_APPLICATION_CREDENTIALS` 提供 Google 認證。預設值為 `global`、
`gemini-3.1-flash-lite-image`、一張 1K 圖、無自動重試；插件會按實際 MIME 保存 PNG 或
JPEG，而不偽造副檔名。實測圖片、踩坑、成本與限制見
[`docs/experiments/GOOGLE_VERTEX_IMAGE_GENERATION_SMOKE_2026-08-10.md`](docs/experiments/GOOGLE_VERTEX_IMAGE_GENERATION_SMOKE_2026-08-10.md)。

## 驗證

```powershell
python -m unittest discover -s tests -v
python -m pytest
ruff format --check apr_runtime tests examples
ruff check apr_runtime tests examples
python -m build
```

目前離線整合驗證為 **149/149 Python tests**，另有 **6/6 dependency-free Node client
tests**。本機候選接受紀錄（含 scoped Ruff、靜態產物、Wrangler dry-run 與本機瀏覽器
證據）見 [`docs/experiments/APR_PUBLIC_SITE_ACCEPTANCE_2026-08-24.md`](docs/experiments/APR_PUBLIC_SITE_ACCEPTANCE_2026-08-24.md)；它記錄的是尚未合併、尚未上線的 locally accepted release candidate。歷史上另有 OpenAI／Anthropic 受控合成視覺 smoke test，以及 Google Vertex
的真實 1K 影像生成與人工視覺驗證。這仍不等同真實
桌面、Chromium CDP、廣泛 VLM／影像生成 benchmark 或長時間可靠性驗證。

## 引用

GitHub 可直接讀取 [`CITATION.cff`](CITATION.cff) 產生引用格式。理論內容若需精確引用，請同時標示所引用的 APR 論文編號或 ACR／APR 白皮書檔名與版本。

## 授權狀態

本儲存庫目前尚未選定開源授權。對外發布、再散布或第三方重用前，應由儲存庫擁有者補上明確 `LICENSE`；這不影響擁有者在自己的其他專案中引用此基礎設施。
