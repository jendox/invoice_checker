from app.services.classifier.normalizer import normalize_description


def test_normalize_lowercase_and_spaces():
    assert normalize_description("  AMAZON   MARKETPLACE  ") == "amazon marketplace"


def test_normalize_removes_transaction_ids():
    result = normalize_description("PAYMENT AT261530099000010000049 amazon")
    assert "at261530099000010000049" not in result
    assert "amazon" in result


def test_normalize_strips_special_chars():
    result = normalize_description("GOOGLE*ADS7924609133    DUBLIN")
    assert "google" in result
    assert "7924609133" in result or "ads" in result
