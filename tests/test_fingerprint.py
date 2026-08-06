from datetime import date
from decimal import Decimal

from app.services.classifier.normalizer import make_fingerprint


def test_fingerprint_deterministic():
    fp1 = make_fingerprint("amex", date(2026, 6, 1), Decimal("100.00"), "GBP", "google ads")
    fp2 = make_fingerprint("amex", date(2026, 6, 1), Decimal("100.00"), "GBP", "google ads")
    assert fp1 == fp2
    assert len(fp1) == 64


def test_fingerprint_differs_by_bank():
    fp1 = make_fingerprint("amex", date(2026, 6, 1), Decimal("100.00"), "GBP", "google ads")
    fp2 = make_fingerprint("hsbc", date(2026, 6, 1), Decimal("100.00"), "GBP", "google ads")
    assert fp1 != fp2


def test_fingerprint_differs_by_amount():
    fp1 = make_fingerprint("amex", date(2026, 6, 1), Decimal("100.00"), "GBP", "google ads")
    fp2 = make_fingerprint("amex", date(2026, 6, 1), Decimal("200.00"), "GBP", "google ads")
    assert fp1 != fp2
