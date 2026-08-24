from __future__ import annotations

import re
from collections.abc import Mapping
from itertools import product
from math import isfinite

CONTROL_ORDER = ("freshness", "uncertainty", "risk", "conflict", "budget", "goal")
CONTROL_VALUES = (
    ("fresh", "stale"),
    ("low", "high"),
    ("low", "high"),
    ("absent", "present"),
    ("available", "exhausted"),
    ("unresolved", "satisfied"),
)
PUBLIC_ROW_FIELDS = frozenset(
    {
        "scenario_key",
        "disposition",
        "reason_key",
        "effective_fact_status",
        "selected_channel",
        "expected_gain",
        "estimated_cost",
        "budget_before",
        "projected_budget_after",
        "affordable",
        "action_readiness",
        "facts_to_verify",
        "blocking_facts",
    }
)

DISPOSITION_VALUES = frozenset(
    {
        "no_observation",
        "monitor",
        "skim",
        "search",
        "track",
        "inspect",
        "deep",
        "revisit",
        "epistemic_action",
    }
)
REASON_VALUES = frozenset(
    {
        "fresh_fact_sufficient",
        "contradiction_revisit",
        "stale_fact_refresh",
        "fact_unknown_or_uncertain",
        "risk_reverification",
        "no_direct_modality",
    }
)
FACT_STATUS_VALUES = frozenset({"known", "unknown", "uncertain", "stale", "contradicted"})
CHANNEL_VALUES = frozenset({"text", "vision", "video", "audio", "structured", "sensor"})
READINESS_VALUES = frozenset({"allow", "verify", "block"})
DISPLAY_FIELDS = frozenset(
    {
        "disposition",
        "reason_key",
        "effective_fact_status",
        "selected_channel",
        "budget_before",
        "projected_budget_after",
        "affordable",
        "action_readiness",
    }
)
VALUE_LABEL_DOMAINS = {
    "disposition": DISPOSITION_VALUES,
    "reason_key": REASON_VALUES,
    "effective_fact_status": FACT_STATUS_VALUES,
    "selected_channel": CHANNEL_VALUES | {"none"},
    "affordable": frozenset({"true", "false"}),
    "action_readiness": READINESS_VALUES,
}

_EXPECTED_SCENARIO_KEYS = frozenset(":".join(values) for values in product(*CONTROL_VALUES))
_FORBIDDEN_TERMS = frozenset(
    {"id", "path", "pointer", "token", "credential", "private", "raw_response"}
)
_SIMPLE_PLURAL_TERMS = {
    "ids": "id",
    "paths": "path",
    "pointers": "pointer",
    "tokens": "token",
    "credentials": "credential",
    "responses": "response",
}


def _normalized_terms(value: str) -> set[str]:
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", normalized).strip("_").lower()
    parts = [_SIMPLE_PLURAL_TERMS.get(part, part) for part in normalized.split("_") if part]
    terms = set(parts)
    if any(
        left == "raw" and right == "response" for left, right in zip(parts, parts[1:], strict=False)
    ):
        terms.add("raw_response")
    return terms


def _reject_forbidden_content(value: object, location: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{location} contains a non-string field name")
            forbidden = _normalized_terms(key) & _FORBIDDEN_TERMS
            if forbidden:
                raise ValueError(f"{location} contains forbidden field name {key!r}")
            _reject_forbidden_content(nested, f"{location}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _reject_forbidden_content(nested, f"{location}[{index}]")
        return
    if isinstance(value, str):
        forbidden = _normalized_terms(value) & _FORBIDDEN_TERMS
        if forbidden:
            raise ValueError(f"{location} contains forbidden serialized content")


def _require_enum(row: Mapping[str, object], field: str, allowed: frozenset[str]) -> None:
    value = row[field]
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field} is outside the public value domain")


def _require_number(
    row: Mapping[str, object], field: str, *, maximum: float | None = None
) -> float:
    value = row[field]
    if type(value) not in (int, float) or not isfinite(value):
        raise ValueError(f"{field} must be a finite JSON number")
    number = float(value)
    if number < 0.0 or (maximum is not None and number > maximum):
        raise ValueError(f"{field} is outside the public numeric range")
    return number


def _require_fact_list(row: Mapping[str, object], field: str) -> None:
    value = row[field]
    if type(value) is not list or any(type(item) is not str or not item.strip() for item in value):
        raise ValueError(f"{field} must be a list of non-empty fact keys")


def _require_localized_mapping(value: object, expected_keys: frozenset[str], location: str) -> None:
    if type(value) is not dict or set(value) != expected_keys:
        raise ValueError(f"{location} must cover the exact public domain")
    if any(type(label) is not str or not label.strip() for label in value.values()):
        raise ValueError(f"{location} contains an empty or non-string label")


def _value_code(value: object) -> str:
    if value is None:
        return "none"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return value
    raise ValueError("displayed public value has no localization code")


def _validate_content_contract(
    *,
    scenarios: Mapping[str, Mapping[str, object]],
    locales: object,
    routes: object,
    pages: object,
    evidence: object,
    lab_ui: object,
) -> None:
    expected_locales = ("en", "zh-TW")
    expected_locale_set = frozenset(expected_locales)
    if locales != expected_locales:
        raise ValueError("public locales must be English and Traditional Chinese in order")
    if type(routes) is not tuple:
        raise ValueError("routes must be a declared ordered tuple")

    route_slugs: list[str] = []
    for route in routes:
        slug = getattr(route, "slug", None)
        if type(slug) is not str or slug in route_slugs:
            raise ValueError("route slugs must be unique strings")
        route_slugs.append(slug)
        for attribute in ("title", "description"):
            translations = getattr(route, attribute, None)
            _require_localized_mapping(
                translations,
                expected_locale_set,
                f"route {slug!r} {attribute}",
            )

    route_set = frozenset(route_slugs)
    if type(evidence) is not dict or any(
        type(evidence_id) is not str or not evidence_id or type(path) is not str or not path
        for evidence_id, path in evidence.items()
    ):
        raise ValueError("evidence must map stable identifiers to repository paths")
    if type(pages) is not dict or set(pages) != expected_locale_set:
        raise ValueError("page catalogs must cover both public locales")

    for locale in expected_locales:
        locale_pages = pages[locale]
        if type(locale_pages) is not dict or set(locale_pages) != route_set:
            raise ValueError(f"{locale} page routes drift from the declared route set")

    for slug in route_slugs:
        english_ids = pages["en"][slug].get("evidence_ids")
        chinese_ids = pages["zh-TW"][slug].get("evidence_ids")
        if (
            type(english_ids) is not tuple
            or type(chinese_ids) is not tuple
            or english_ids != chinese_ids
            or any(
                type(evidence_id) is not str or evidence_id not in evidence
                for evidence_id in english_ids
            )
        ):
            raise ValueError(f"route {slug!r} has bilingual evidence-ID drift")

    if type(lab_ui) is not dict or set(lab_ui) != expected_locale_set:
        raise ValueError("Lab UI must cover both public locales")
    expected_ui_keys = {
        "notice",
        "loading",
        "load_error",
        "missing_error",
        "controls",
        "fields",
        "value_labels",
    }
    for locale in expected_locales:
        ui = lab_ui[locale]
        if type(ui) is not dict or set(ui) != expected_ui_keys:
            raise ValueError(f"{locale} Lab UI shape is incomplete")
        for message in ("notice", "loading", "load_error", "missing_error"):
            if type(ui[message]) is not str or not ui[message].strip():
                raise ValueError(f"{locale} Lab UI has an invalid {message}")

        controls = ui["controls"]
        if type(controls) is not tuple or len(controls) != len(CONTROL_ORDER):
            raise ValueError(f"{locale} Lab controls do not match the public control order")
        for index, (expected_name, expected_values) in enumerate(
            zip(CONTROL_ORDER, CONTROL_VALUES, strict=True)
        ):
            control = controls[index]
            if type(control) is not tuple or len(control) != 3:
                raise ValueError(f"{locale} Lab control {expected_name!r} is malformed")
            name, legend, options = control
            if name != expected_name or type(legend) is not str or not legend.strip():
                raise ValueError(f"{locale} Lab control {expected_name!r} drifted")
            if (
                type(options) is not tuple
                or tuple(option[0] for option in options) != expected_values
            ):
                raise ValueError(f"{locale} Lab control {expected_name!r} values drifted")
            if any(
                type(option) is not tuple
                or len(option) != 2
                or type(option[1]) is not str
                or not option[1].strip()
                for option in options
            ):
                raise ValueError(f"{locale} Lab control {expected_name!r} labels are incomplete")

        _require_localized_mapping(ui["fields"], DISPLAY_FIELDS, f"{locale} field labels")
        value_labels = ui["value_labels"]
        if type(value_labels) is not dict or set(value_labels) != set(VALUE_LABEL_DOMAINS):
            raise ValueError(f"{locale} Lab value-label domains are incomplete")
        for field, expected_values in VALUE_LABEL_DOMAINS.items():
            _require_localized_mapping(
                value_labels[field], expected_values, f"{locale} value labels for {field}"
            )

    for key, row in scenarios.items():
        for field in VALUE_LABEL_DOMAINS:
            code = _value_code(row[field])
            for locale in expected_locales:
                if code not in lab_ui[locale]["value_labels"][field]:
                    raise ValueError(f"{locale} is missing {field} translation {code!r} in {key!r}")


def validate_scenarios(scenarios: Mapping[str, Mapping[str, object]]) -> None:
    """Validate the exported scenario matrix before public serialization."""

    if type(scenarios) is not dict:
        raise ValueError("scenarios must be a JSON object")
    if set(scenarios) != _EXPECTED_SCENARIO_KEYS:
        raise ValueError("scenario keys must be the exact 64-key control product")

    for key in sorted(scenarios):
        row = scenarios[key]
        if type(row) is not dict:
            raise ValueError(f"scenario {key!r} must be a JSON object")
        _reject_forbidden_content(row, f"scenarios.{key}")
        if set(row) != PUBLIC_ROW_FIELDS:
            raise ValueError(f"scenario {key!r} has an unapproved row shape")
        if row["scenario_key"] != key:
            raise ValueError(f"scenario {key!r} does not identify itself")

        _require_enum(row, "disposition", DISPOSITION_VALUES)
        _require_enum(row, "reason_key", REASON_VALUES)
        _require_enum(row, "effective_fact_status", FACT_STATUS_VALUES)
        selected_channel = row["selected_channel"]
        if selected_channel is not None and (
            type(selected_channel) is not str or selected_channel not in CHANNEL_VALUES
        ):
            raise ValueError("selected_channel is outside the public value domain")
        _require_enum(row, "action_readiness", READINESS_VALUES)
        if type(row["affordable"]) is not bool:
            raise ValueError("affordable must be a JSON boolean")

        _require_number(row, "expected_gain", maximum=1.0)
        _require_number(row, "estimated_cost")
        budget_before = _require_number(row, "budget_before")
        projected_budget_after = _require_number(row, "projected_budget_after")
        if projected_budget_after > budget_before:
            raise ValueError("projected_budget_after cannot exceed budget_before")

        _require_fact_list(row, "facts_to_verify")
        _require_fact_list(row, "blocking_facts")


def validate_publication(
    *,
    scenarios: Mapping[str, Mapping[str, object]],
    locales: object,
    routes: object,
    pages: object,
    evidence: object,
    lab_ui: object,
) -> None:
    """Validate all generated public data before an output tree is published."""

    validate_scenarios(scenarios)
    _validate_content_contract(
        scenarios=scenarios,
        locales=locales,
        routes=routes,
        pages=pages,
        evidence=evidence,
        lab_ui=lab_ui,
    )
