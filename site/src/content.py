from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

LOCALES = ("en", "zh-TW")
SITE = {
    "origin": "https://apr.evemisslab.com",
    "name": "APR",
    "version": "0.10.0",
    "source_ref": "d1722eca845353acd3ce1f7241283bfa16263e93",
    "release_status": "candidate",
}

EVIDENCE = {
    "runtime_architecture": "docs/runtime/ARCHITECTURE.md",
    "event_runtime": "docs/runtime/EVENT_NATIVE_RUNTIME.md",
    "need_graph": "docs/runtime/PERCEPTUAL_NEED_GRAPH.md",
    "budget": "apr_runtime/budget.py",
    "action_gate": "docs/runtime/ACTION_READINESS_GATES.md",
    "outcome": "docs/runtime/ACTION_OUTCOME_VERIFICATION.md",
    "recovery": "docs/runtime/CLOSED_LOOP_RECOVERY.md",
    "lab_runtime": "apr_runtime/runtime.py",
    "apr_01": "papers/APR_Paper01_Adaptive_Perceptual_Reading_v0.1.md",
    "apr_02": "papers/APR_Paper02_Hierarchical_Differential_Perception_v0.1.md",
    "apr_03": "papers/APR_Paper03_MultiScale_Visual_Reading_Reobservation_v0.1.md",
    "apr_04": "papers/APR_Paper04_Persistent_World_State_Differential_Reobservation_v0.1.md",
    "apr_05": "papers/APR_Paper05_Perceptual_Budget_Allocation_v0.1.md",
    "apr_06": "papers/APR_Paper06_CrossModal_Perceptual_Reading_v0.1.md",
    "apr_07": "papers/APR_Paper07_Agentic_Perception_Runtime_v0.1.md",
    "whitepaper": "docs/theory/WHITEPAPER_APR_Runtime_v1.0.md",
    "acr_specification": "docs/theory/acr/ACR_MVP_Runtime_規格_v0.1.md",
    "acr_engineering": "docs/theory/acr/ACR_工程白皮書_v0.1.md",
    "acr_moderate_cognition": (
        "docs/theory/acr/適度認知論_智能為什麼不應對每一個問題都使用最大思考深度_v0.1.md"
    ),
    "mcp_boundary": "docs/theory/acr/ACR_工程白皮書_v0.1.md",
    "security": "SECURITY.md",
    "status": "STATUS.md",
    "smoke_v010": "docs/runtime/SMOKE_TEST_v0.10.txt",
    "source_manifest": "docs/provenance/SOURCE_MANIFEST.md",
}

LAB_UI = {
    "en": {
        "notice": "Educational projection only — no policy execution or service contact.",
        "loading": "Loading bounded fixture…",
        "load_error": (
            "The educational projection is unavailable because its local fixture could not "
            "be validated."
        ),
        "missing_error": "No bounded fixture matches this control state.",
        "controls": (
            ("freshness", "Evidence freshness", (("fresh", "Fresh"), ("stale", "Stale"))),
            ("uncertainty", "Uncertainty", (("low", "Low"), ("high", "High"))),
            ("risk", "Action risk", (("low", "Low"), ("high", "High"))),
            (
                "conflict",
                "Evidence conflict",
                (("absent", "Absent"), ("present", "Present")),
            ),
            (
                "budget",
                "Observation budget",
                (("available", "Available"), ("exhausted", "Exhausted")),
            ),
            (
                "goal",
                "Goal evidence",
                (("unresolved", "Unresolved"), ("satisfied", "Satisfied")),
            ),
        ),
        "fields": {
            "disposition": "Observation disposition",
            "reason_key": "Reason",
            "effective_fact_status": "Effective fact status",
            "selected_channel": "Selected channel",
            "budget_before": "Budget before",
            "projected_budget_after": "Projected budget after",
            "affordable": "Affordable",
            "action_readiness": "Action readiness",
        },
        "value_labels": {
            "disposition": {
                "no_observation": "No observation",
                "monitor": "Monitor",
                "skim": "Skim",
                "search": "Search",
                "track": "Track",
                "inspect": "Inspect",
                "deep": "Deep read",
                "revisit": "Revisit",
                "epistemic_action": "Epistemic action",
            },
            "reason_key": {
                "fresh_fact_sufficient": "Fresh fact is sufficient",
                "contradiction_revisit": "Contradiction requires re-observation",
                "stale_fact_refresh": "Stale fact requires refresh",
                "fact_unknown_or_uncertain": "Fact is unknown or uncertain",
                "risk_reverification": "Risk requires re-verification",
                "no_direct_modality": "No direct observation channel",
            },
            "effective_fact_status": {
                "known": "Known",
                "unknown": "Unknown",
                "uncertain": "Uncertain",
                "stale": "Stale",
                "contradicted": "Contradicted",
            },
            "selected_channel": {
                "text": "Text",
                "vision": "Vision",
                "video": "Video",
                "audio": "Audio",
                "structured": "Structured data",
                "sensor": "Sensor",
                "none": "No channel selected",
            },
            "affordable": {"true": "Yes", "false": "No"},
            "action_readiness": {
                "allow": "Allow",
                "verify": "Verify first",
                "block": "Block",
            },
        },
    },
    "zh-TW": {
        "notice": "僅供教育投影 — 不執行政策，也不聯絡任何服務。",
        "loading": "正在載入有界固定案例…",
        "load_error": "本機固定案例無法通過驗證，因此教育投影目前不可用。",
        "missing_error": "沒有符合此控制狀態的有界固定案例。",
        "controls": (
            ("freshness", "證據新鮮度", (("fresh", "新鮮"), ("stale", "過期"))),
            ("uncertainty", "不確定性", (("low", "低"), ("high", "高"))),
            ("risk", "行動風險", (("low", "低"), ("high", "高"))),
            ("conflict", "證據衝突", (("absent", "無"), ("present", "有"))),
            ("budget", "觀察預算", (("available", "可用"), ("exhausted", "耗盡"))),
            ("goal", "目標證據", (("unresolved", "未解決"), ("satisfied", "已滿足"))),
        ),
        "fields": {
            "disposition": "觀察處置",
            "reason_key": "理由",
            "effective_fact_status": "有效事實狀態",
            "selected_channel": "所選通道",
            "budget_before": "預算前值",
            "projected_budget_after": "預估預算後值",
            "affordable": "可負擔性",
            "action_readiness": "行動就緒狀態",
        },
        "value_labels": {
            "disposition": {
                "no_observation": "不觀察",
                "monitor": "監看",
                "skim": "略讀",
                "search": "搜尋",
                "track": "追蹤",
                "inspect": "檢視",
                "deep": "深度閱讀",
                "revisit": "重新觀察",
                "epistemic_action": "認知行動",
            },
            "reason_key": {
                "fresh_fact_sufficient": "新鮮事實已足夠",
                "contradiction_revisit": "矛盾需要重新觀察",
                "stale_fact_refresh": "過期事實需要更新",
                "fact_unknown_or_uncertain": "事實未知或不確定",
                "risk_reverification": "風險要求再次驗證",
                "no_direct_modality": "沒有直接觀察通道",
            },
            "effective_fact_status": {
                "known": "已知",
                "unknown": "未知",
                "uncertain": "不確定",
                "stale": "過期",
                "contradicted": "相互矛盾",
            },
            "selected_channel": {
                "text": "文字",
                "vision": "視覺",
                "video": "影片",
                "audio": "音訊",
                "structured": "結構化資料",
                "sensor": "感測器",
                "none": "未選擇通道",
            },
            "affordable": {"true": "可負擔", "false": "不可負擔"},
            "action_readiness": {
                "allow": "允許",
                "verify": "先驗證",
                "block": "阻擋",
            },
        },
    },
}


@dataclass(frozen=True)
class Route:
    slug: str
    title: Mapping[str, str]
    description: Mapping[str, str]


ROUTES = (
    Route(
        "",
        {"en": "APR", "zh-TW": "APR"},
        {"en": "Adaptive Perceptual Reading", "zh-TW": "自適應感知閱讀"},
    ),
    Route(
        "runtime",
        {"en": "Runtime", "zh-TW": "Runtime"},
        {"en": "APR runtime architecture", "zh-TW": "APR Runtime 架構"},
    ),
    Route(
        "lab",
        {"en": "Lab", "zh-TW": "實驗室"},
        {"en": "Offline APR decision lab", "zh-TW": "離線 APR 決策實驗室"},
    ),
    Route(
        "papers",
        {"en": "Papers", "zh-TW": "論文"},
        {"en": "APR theory index", "zh-TW": "APR 理論索引"},
    ),
    Route(
        "mcp",
        {"en": "Local MCP", "zh-TW": "本機 MCP"},
        {"en": "Local-only architecture", "zh-TW": "僅限本機的架構"},
    ),
    Route(
        "status",
        {"en": "Status", "zh-TW": "狀態"},
        {"en": "Evidence and boundaries", "zh-TW": "證據與邊界"},
    ),
)


def _page(
    kicker: str,
    heading: str,
    summary: str,
    status_label: str,
    status_tone: str,
    status_text: str,
    evidence_ids: tuple[str, ...],
    sections: tuple[dict[str, object], ...],
) -> dict[str, object]:
    return {
        "kicker": kicker,
        "heading": heading,
        "summary": summary,
        "status_label": status_label,
        "status_tone": status_tone,
        "status_text": status_text,
        "evidence_ids": evidence_ids,
        "sections": sections,
    }


PAPER_EVIDENCE = (
    "apr_01",
    "apr_02",
    "apr_03",
    "apr_04",
    "apr_05",
    "apr_06",
    "apr_07",
    "whitepaper",
    "acr_specification",
    "acr_engineering",
    "acr_moderate_cognition",
)

PAGES = {
    "en": {
        "": _page(
            "Adaptive Perceptual Reading",
            "Read what changed. Verify what matters.",
            "APR is a research architecture for deciding when an agent should observe, what it should read, how deeply it should read, and when fresh evidence is sufficient to stop.",
            "Research status",
            "uncertain",
            "v0.10 release candidate — public research infrastructure",
            ("runtime_architecture", "whitepaper", "recovery"),
            (
                {
                    "title": "Perceive → Verify → Recover",
                    "body": "APR maintains a closed loop: perceive evidence, update bounded belief, identify unmet needs, gate action, observe the outcome, verify it, and recover when reality disagrees.",
                    "items": (
                        ("Observe", "Acquire only the evidence a live need justifies.", "observe"),
                        (
                            "Budget",
                            "Spend finite attention where information gain matters.",
                            "budget",
                        ),
                        (
                            "Verify",
                            "Require post-action evidence before declaring success.",
                            "verified",
                        ),
                        (
                            "Recover",
                            "Retry, replan, compensate, or stop under explicit policy.",
                            "danger",
                        ),
                    ),
                },
                {
                    "title": "Current boundary",
                    "body": "The repository is a research MVP. This static site explains evidence already present in the repository; it does not host an agent, call a model Provider, or expose desktop control.",
                },
                {
                    "title": "Start with evidence",
                    "body": "Explore the runtime guide, inspect the bounded offline lab, or read the papers. Every technical page links to an immutable candidate source reference.",
                },
            ),
        ),
        "runtime": _page(
            "Runtime architecture",
            "Evidence stays separate from events and belief.",
            "APR turns observations into provenance-bearing evidence, routes unmet perceptual needs through a finite budget, and blocks action until explicit gates are met.",
            "Runtime line",
            "observe",
            "Evidence → Need → Gate → Outcome → Recovery",
            (
                "runtime_architecture",
                "event_runtime",
                "need_graph",
                "budget",
                "action_gate",
                "outcome",
                "recovery",
            ),
            (
                {
                    "title": "Evidence, event, belief",
                    "body": "An event says something may have changed. Evidence records what was observed and where it came from. Belief is the runtime's current bounded world state. APR does not silently collapse these layers.",
                },
                {
                    "title": "Need graph and perceptual budget",
                    "body": "Unknown, stale, conflicting, or action-critical facts become explicit needs. Dependencies determine what can be observed next; budget is spent only when an observation is made.",
                    "items": (
                        ("Unknown", "Request evidence for an unresolved fact.", "uncertain"),
                        (
                            "Budgeted",
                            "Choose depth and channel within available attention.",
                            "budget",
                        ),
                        ("Observed", "Preserve source, confidence, age, and cost.", "observe"),
                    ),
                },
                {
                    "title": "Action, outcome, recovery",
                    "body": "The action gate checks freshness, contradiction, independence, risk, and semantic preconditions. Execution creates a receipt, not a success claim. Fresh post-action evidence drives verification and bounded recovery.",
                },
            ),
        ),
        "lab": _page(
            "Offline decision lab",
            "Inspect a bounded educational projection.",
            "The finite scenario matrix is generated from deterministic APR fixtures; local lookup controls are available below. This page remains a static educational projection; it does not execute policy or contact a service.",
            "Lab notice",
            "budget",
            "Educational projection — bounded, deterministic, offline",
            ("lab_runtime", "action_gate", "recovery"),
            (
                {
                    "title": "Scenario controls",
                    "body": "Each control is discrete and text-labelled; colour is supplemental.",
                    "items": (
                        ("Evidence freshness", "Fresh / stale", "observe"),
                        ("Uncertainty", "Low / high", "uncertain"),
                        ("Risk", "Low / high", "danger"),
                        ("Evidence conflict", "Absent / present", "danger"),
                        ("Observation budget", "Available / exhausted", "budget"),
                        ("Goal satisfaction", "Unresolved / satisfied", "verified"),
                    ),
                },
                {
                    "title": "Projected output",
                    "body": "The exported scenario matrix reports disposition, reason, effective fact status, unmet evidence needs, selected channel, budget before and projected after, affordability, and action-gate state; the local interface renders disposition, reason, effective fact status, selected channel, budget before and projected after, affordability, and action-gate state below.",
                },
                {
                    "title": "Interpretation boundary",
                    "body": "A projected result teaches how bounded fixtures map to APR concepts. It is not a benchmark, a live runtime decision, or evidence about arbitrary agents.",
                },
            ),
        ),
        "papers": _page(
            "Theory and roots",
            "APR-01 through APR-07, unified.",
            "The paper series develops adaptive reading, change hierarchies, re-observation, persistent world state, budget allocation, cross-modal attention, and agentic perception.",
            "Corpus",
            "verified",
            "7 APR papers · 1 unified whitepaper · 3 ACR roots",
            PAPER_EVIDENCE,
            (
                {
                    "title": "APR series",
                    "body": "Seven papers form the conceptual path into the runtime.",
                    "items": (
                        (
                            "APR-01",
                            "Adaptive perceptual reading and resource allocation.",
                            "observe",
                        ),
                        ("APR-02", "From pixel difference to semantic difference.", "observe"),
                        ("APR-03", "Multi-scale visual reading and re-observation.", "observe"),
                        (
                            "APR-04",
                            "Persistent world state and differential re-observation.",
                            "observe",
                        ),
                        ("APR-05", "Perceptual budgets and information-gain allocation.", "budget"),
                        ("APR-06", "Cross-modal perceptual reading.", "uncertain"),
                        (
                            "APR-07",
                            "Agentic perception and active evidence acquisition.",
                            "verified",
                        ),
                    ),
                },
                {
                    "title": "Unified whitepaper",
                    "body": "The v1.0 whitepaper connects the series to a stateful, budgeted, cross-modal runtime architecture.",
                },
                {
                    "title": "ACR roots",
                    "body": "The ACR specification, engineering whitepaper, and moderate-cognition document provide adjacent runtime and bounded-reasoning roots.",
                },
            ),
        ),
        "mcp": _page(
            "Local capability boundary",
            "Local MCP is planned and not implemented.",
            "Transport details will be documented with accepted MCP evidence. The public website cannot grant authority to or stand in for a local server.",
            "Implementation status",
            "uncertain",
            "not_implemented",
            ("mcp_boundary", "security"),
            (
                {
                    "title": "Deferred MCP documentation",
                    "body": "Transport details will be documented when accepted MCP evidence is available. This page does not describe an available local service.",
                },
                {
                    "title": "Human authority",
                    "body": "A human-controlled allowlist defines which local capabilities may be used. Discovery is not execution authority, and the website cannot expand the allowlist.",
                },
                {
                    "title": "Deferred implementation",
                    "body": "The local MCP server requires a separate specification, implementation, acceptance record, and user authorization. This page documents a boundary, not an available service.",
                },
            ),
        ),
        "status": _page(
            "Evidence and limitations",
            "v0.10 is a research release candidate.",
            f"This site is pinned to candidate commit {SITE['source_ref']}. The immutable source links below describe the evidence available at that exact revision.",
            "Release truth",
            "uncertain",
            "Release candidate · Draft PR content is not presented as merged",
            ("status", "smoke_v010", "source_manifest"),
            (
                {
                    "title": "Measured evidence",
                    "body": "The repository status, v0.10 smoke record, and source manifest are linked as bounded records. Historical checks do not become a current production claim.",
                },
                {
                    "title": "Licence status",
                    "body": "No repository licence is currently specified. Public visibility does not grant reuse, redistribution, or modification rights.",
                },
                {
                    "title": "Non-claims",
                    "body": "APR does not claim broad benchmark validation, arbitrary multimodal-agent coverage, high-risk autonomy, hosted runtime availability, or implemented MCP access.",
                },
            ),
        ),
    },
    "zh-TW": {
        "": _page(
            "自適應感知閱讀",
            "閱讀變化，驗證關鍵。",
            "APR 是一套研究型架構，用來決定代理何時應觀察、該讀什麼、讀多深，以及新鮮證據何時已足以停止閱讀。",
            "研究狀態",
            "uncertain",
            "v0.10 發布候選版 — 公開研究基礎設施",
            ("runtime_architecture", "whitepaper", "recovery"),
            (
                {
                    "title": "感知 → 驗證 → 復原",
                    "body": "APR 維持閉環：感知證據、更新有界信念、找出未滿足需求、為行動設閘、觀察並驗證結果，且在現實與預期不一致時復原。",
                    "items": (
                        ("觀察", "只取得當前需求所能證成的證據。", "observe"),
                        ("預算", "把有限注意力花在資訊增益重要之處。", "budget"),
                        ("驗證", "宣告成功前要求行動後證據。", "verified"),
                        ("復原", "依明確政策重試、重規劃、補償或停止。", "danger"),
                    ),
                },
                {
                    "title": "目前邊界",
                    "body": "此儲存庫是研究型 MVP。靜態網站解釋既有證據；它不託管代理、不呼叫模型 Provider，也不開放桌面控制。",
                },
                {
                    "title": "從證據開始",
                    "body": "可探索 Runtime 指南、查看有界離線實驗室，或閱讀論文。每個技術頁面都連回不可變的候選來源版本。",
                },
            ),
        ),
        "runtime": _page(
            "Runtime 架構",
            "證據、事件與信念彼此分離。",
            "APR 將觀察轉為帶有出處的證據，讓未滿足的感知需求通過有限預算，並在明確閘門未滿足前阻擋行動。",
            "Runtime 路徑",
            "observe",
            "證據 → 需求 → 閘門 → 結果 → 復原",
            (
                "runtime_architecture",
                "event_runtime",
                "need_graph",
                "budget",
                "action_gate",
                "outcome",
                "recovery",
            ),
            (
                {
                    "title": "證據、事件、信念",
                    "body": "事件表示某事可能已改變；證據記錄觀察內容與來源；信念是 Runtime 當下有界的世界狀態。APR 不會默默合併這三層。",
                },
                {
                    "title": "需求圖與感知預算",
                    "body": "未知、過期、衝突或與行動關鍵相關的事實會成為明確需求。依賴關係決定下一個可觀察項目；只有實際觀察時才花費預算。",
                    "items": (
                        ("未知", "為未解決事實請求證據。", "uncertain"),
                        ("有預算", "在可用注意力內選擇深度與通道。", "budget"),
                        ("已觀察", "保存來源、信心、時間與成本。", "observe"),
                    ),
                },
                {
                    "title": "行動、結果、復原",
                    "body": "行動閘門檢查新鮮度、矛盾、獨立性、風險與語義前置條件。執行只建立收據，不等於成功；新鮮的行動後證據驅動驗證與有界復原。",
                },
            ),
        ),
        "lab": _page(
            "離線決策實驗室",
            "檢視有界的教育投影。",
            "有限情境矩陣已由確定性的 APR 固定案例產生；本機查表控制項已在下方提供。此頁目前仍是靜態教育投影；它不執行政策，也不聯絡任何服務。",
            "實驗室聲明",
            "budget",
            "教育投影 — 有界、確定性、離線",
            ("lab_runtime", "action_gate", "recovery"),
            (
                {
                    "title": "情境控制項",
                    "body": "每個控制項都有離散文字標籤；顏色只作為輔助。",
                    "items": (
                        ("證據新鮮度", "新鮮／過期", "observe"),
                        ("不確定性", "低／高", "uncertain"),
                        ("風險", "低／高", "danger"),
                        ("證據衝突", "無／有", "danger"),
                        ("觀察預算", "可用／耗盡", "budget"),
                        ("目標滿足", "未解決／已滿足", "verified"),
                    ),
                },
                {
                    "title": "投影輸出",
                    "body": "匯出的情境矩陣列出處置、理由、有效事實狀態、未滿足的證據需求、所選通道、預算前值與預估後值、可負擔性，以及行動閘門狀態；本機介面在下方呈現處置、理由、有效事實狀態、所選通道、預算前值與預估後值、可負擔性，以及行動閘門狀態。",
                },
                {
                    "title": "詮釋邊界",
                    "body": "投影結果用來解釋有界固定案例如何映射到 APR 概念。它不是基準測試、即時 Runtime 決策或任意代理的證據。",
                },
            ),
        ),
        "papers": _page(
            "理論與根源",
            "統合 APR-01 至 APR-07。",
            "論文系列發展自適應閱讀、變化階層、重觀察、持續世界狀態、預算分配、跨模態注意力與 Agentic Perception。",
            "文獻集",
            "verified",
            "7 篇 APR 論文 · 1 份統一白皮書 · 3 份 ACR 根文件",
            PAPER_EVIDENCE,
            (
                {
                    "title": "APR 系列",
                    "body": "七篇論文構成通往 Runtime 的概念路徑。",
                    "items": (
                        ("APR-01", "自適應感知閱讀與資源配置。", "observe"),
                        ("APR-02", "從像素差分到語義差分。", "observe"),
                        ("APR-03", "多尺度視覺閱讀與重觀察。", "observe"),
                        ("APR-04", "持續世界狀態與差分重觀察。", "observe"),
                        ("APR-05", "感知預算與資訊增益配置。", "budget"),
                        ("APR-06", "跨模態感知閱讀。", "uncertain"),
                        ("APR-07", "Agentic Perception 與主動取得證據。", "verified"),
                    ),
                },
                {
                    "title": "統一白皮書",
                    "body": "v1.0 白皮書把系列連接到具狀態、預算與跨模態能力的 Runtime 架構。",
                },
                {
                    "title": "ACR 根文件",
                    "body": "ACR 規格、工程白皮書與適度認知論文件提供相鄰的 Runtime 與有界推理根源。",
                },
            ),
        ),
        "mcp": _page(
            "本機能力邊界",
            "本機 MCP 規劃中且尚未實作。",
            "傳輸細節將隨已接受的 MCP 證據一併記錄。公開網站不能授權，也不能取代本機伺服器。",
            "實作狀態",
            "uncertain",
            "not_implemented",
            ("mcp_boundary", "security"),
            (
                {
                    "title": "延後的 MCP 文件",
                    "body": "待有已接受的 MCP 證據後，才會記錄傳輸細節。此頁不描述可用的本機服務。",
                },
                {
                    "title": "人類權限",
                    "body": "由人類控制的允許清單定義哪些本機能力可使用。發現不等於執行權限，網站也不能擴張允許清單。",
                },
                {
                    "title": "延後實作",
                    "body": "本機 MCP 伺服器需要獨立規格、實作、驗收記錄與使用者授權。此頁記錄的是邊界，不是可用服務。",
                },
            ),
        ),
        "status": _page(
            "證據與限制",
            "v0.10 是研究型發布候選版。",
            f"此網站固定於候選 commit {SITE['source_ref']}。下方不可變來源連結描述該精確版本所具有的證據。",
            "發布事實",
            "uncertain",
            "發布候選版 · Draft PR 內容不表示已合併",
            ("status", "smoke_v010", "source_manifest"),
            (
                {
                    "title": "量測證據",
                    "body": "儲存庫狀態、v0.10 smoke 記錄與來源清單在下方作為有界記錄連結。歷史檢查不會自動成為目前的生產宣稱。",
                },
                {
                    "title": "授權狀態",
                    "body": "儲存庫目前沒有指定授權條款。公開可見不授予重用、散布或修改權利。",
                },
                {
                    "title": "不宣稱事項",
                    "body": "APR 不宣稱廣泛基準驗證、任意多模態代理涵蓋、高風險自主、託管 Runtime 可用性或 MCP 已實作。",
                },
            ),
        ),
    },
}
