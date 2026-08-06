from types import SimpleNamespace

from app.utils.filter_labels import (
    FilterOption,
    STATUS_FILTER_OPTIONS,
    build_bank_filter_options,
    build_key_label_options,
    status_label,
)


def test_build_key_label_options_uses_catalog_labels():
    catalog = [
        SimpleNamespace(key="hipcrate", display_name="Hipcrate"),
        SimpleNamespace(key="paypal", display_name="PayPal"),
    ]
    options = build_key_label_options(["hipcrate", "paypal"], catalog)
    assert options == [
        FilterOption(key="hipcrate", label="Hipcrate"),
        FilterOption(key="paypal", label="PayPal"),
    ]


def test_build_key_label_options_fallback_for_unknown_key():
    options = build_key_label_options(["revolut_savings"], [])
    assert options[0].key == "revolut_savings"
    assert options[0].label == "Revolut Savings"


def test_build_bank_filter_options_maps_parser_keys_to_catalog():
    catalog = [
        SimpleNamespace(key="amex", display_name="Amex"),
        SimpleNamespace(key="hsbc", display_name="HSBC"),
        SimpleNamespace(key="paypal", display_name="PayPal"),
    ]
    options = build_bank_filter_options(["amex", "hsbc", "paypal"], catalog)
    assert options == [
        FilterOption(key="amex", label="Amex"),
        FilterOption(key="hsbc", label="HSBC"),
        FilterOption(key="paypal", label="PayPal"),
    ]


def test_build_bank_filter_options_supports_legacy_transaction_keys():
    catalog = [
        SimpleNamespace(key="amex", display_name="Amex"),
        SimpleNamespace(key="hsbc", display_name="HSBC"),
    ]
    options = build_bank_filter_options(["amex_gbp", "hsbc_usd"], catalog)
    assert options[0].label == "Amex"
    assert options[1].label == "HSBC"


def test_build_bank_filter_options_supports_legacy_catalog_keys():
    catalog = [
        SimpleNamespace(key="amex_gbp", display_name="Amex"),
        SimpleNamespace(key="hsbc", display_name="HSBC"),
    ]
    options = build_bank_filter_options(["amex", "hsbc"], catalog)
    assert options[0].label == "Amex"
    assert options[1].label == "HSBC"


def test_status_label():
    assert status_label("needs_review") == "Needs review"
    assert STATUS_FILTER_OPTIONS[2].label == "Needs review"
