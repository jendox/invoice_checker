from dataclasses import dataclass
from typing import Protocol

from app.services.parser.bank_presets import LEGACY_BANK_KEYS, PRESETS


class _KeyedDisplay(Protocol):
    key: str
    display_name: str


@dataclass(frozen=True)
class FilterOption:
    key: str
    label: str


# Parser preset keys used in transactions may differ from bank catalog keys.
BANK_CATALOG_KEY_CANDIDATES: dict[str, tuple[str, ...]] = {
    "amex": ("amex", "amex_gbp"),
    "hsbc": ("hsbc", "hsbc_gbp"),
}


STATUS_LABELS: dict[str, str] = {
    "new": "New",
    "confirmed": "Confirmed",
    "needs_review": "Needs review",
    "resolved": "Resolved",
}

STATUS_FILTER_OPTIONS: list[FilterOption] = [
    FilterOption(key=key, label=label) for key, label in STATUS_LABELS.items()
]


def fallback_label(key: str) -> str:
    return key.replace("_", " ").title()


def label_for_key(key: str, catalog: dict[str, str]) -> str:
    return catalog.get(key, fallback_label(key))


def build_key_label_options(
    used_keys: list[str],
    catalog_items: list[_KeyedDisplay],
    active: str | None = None,
) -> list[FilterOption]:
    labels = {item.key: item.display_name for item in catalog_items}
    return _build_filter_options(used_keys, labels, active)


def build_bank_label_lookup(catalog_items: list[_KeyedDisplay]) -> dict[str, str]:
    by_key = {item.key: item.display_name for item in catalog_items}
    labels = dict(by_key)

    for parser_key in PRESETS:
        if parser_key in labels:
            continue
        candidates = BANK_CATALOG_KEY_CANDIDATES.get(parser_key, (parser_key,))
        for catalog_key in candidates:
            if catalog_key in by_key:
                labels[parser_key] = by_key[catalog_key]
                break

    for legacy_key, parser_key in LEGACY_BANK_KEYS.items():
        if parser_key in labels:
            labels.setdefault(legacy_key, labels[parser_key])
        elif legacy_key in by_key:
            labels.setdefault(parser_key, by_key[legacy_key])

    return labels


def build_bank_filter_options(
    used_keys: list[str],
    catalog_items: list[_KeyedDisplay],
    active: str | None = None,
) -> list[FilterOption]:
    return _build_filter_options(used_keys, build_bank_label_lookup(catalog_items), active)


def _build_filter_options(
    used_keys: list[str],
    labels: dict[str, str],
    active: str | None,
) -> list[FilterOption]:
    keys = {key for key in used_keys if key}
    if active:
        keys.add(active)
    return [
        FilterOption(key=key, label=label_for_key(key, labels))
        for key in sorted(keys, key=lambda value: label_for_key(value, labels).lower())
    ]


def status_label(status: str) -> str:
    return STATUS_LABELS.get(status, fallback_label(status))
