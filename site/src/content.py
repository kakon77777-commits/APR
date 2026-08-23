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
