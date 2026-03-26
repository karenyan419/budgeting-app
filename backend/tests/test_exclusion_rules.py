import pytest
from services.exclusion_rules import should_exclude


class MockTransaction:
    """Mock transaction object for testing."""
    def __init__(self, description: str, amount: float):
        self.description = description
        self.amount = amount


class TestExclusionRules:
    def test_exclude_yonder_payment(self):
        tx = MockTransaction("Yonder", -481.27)
        assert should_exclude(tx, "monzo") is True

    def test_exclude_yonder_payment_any_amount(self):
        tx = MockTransaction("Yonder", -100.00)
        assert should_exclude(tx, "monzo") is True

    def test_yonder_not_excluded_from_yonder_account(self):
        tx = MockTransaction("Yonder", -100.00)
        assert should_exclude(tx, "yonder") is False

    def test_exclude_chloe_tong_500_only(self):
        tx_500 = MockTransaction("Chloe Tong", 500.00)
        tx_other = MockTransaction("Chloe Tong", 18.30)

        assert should_exclude(tx_500, "monzo") is True
        assert should_exclude(tx_other, "monzo") is False

    def test_exclude_kathy_yan_300_only(self):
        tx_300 = MockTransaction("Kathy Yan", -300.00)
        tx_other = MockTransaction("Kathy Yan", -84.00)

        assert should_exclude(tx_300, "monzo") is True
        assert should_exclude(tx_other, "monzo") is False

    def test_exclude_karen_yan_any_amount(self):
        tx = MockTransaction("Karen Yan", 1000.00)
        assert should_exclude(tx, "monzo") is True
        assert should_exclude(tx, "yonder") is True

    def test_exclude_k_yan_any_amount(self):
        tx = MockTransaction("K Yan", 3000.00)
        assert should_exclude(tx, "monzo") is True
        assert should_exclude(tx, "yonder") is True

    def test_exclude_investengine_any_amount(self):
        tx1 = MockTransaction("InvestEngine UK", -2000.00)
        tx2 = MockTransaction("InvestEngine UK", -3000.00)

        assert should_exclude(tx1, "monzo") is True
        assert should_exclude(tx2, "monzo") is True

    def test_case_insensitive_matching(self):
        tx_lower = MockTransaction("yonder", -100.00)
        tx_upper = MockTransaction("YONDER", -100.00)
        tx_mixed = MockTransaction("YoNdEr", -100.00)

        assert should_exclude(tx_lower, "monzo") is True
        assert should_exclude(tx_upper, "monzo") is True
        assert should_exclude(tx_mixed, "monzo") is True

    def test_partial_match(self):
        tx = MockTransaction("Payment to Yonder Credit", -100.00)
        assert should_exclude(tx, "monzo") is True

    def test_regular_transaction_not_excluded(self):
        tx = MockTransaction("Tesco", -50.00)
        assert should_exclude(tx, "monzo") is False

    def test_regular_transaction_not_excluded_yonder(self):
        tx = MockTransaction("TFL - Transport for London", -7.20)
        assert should_exclude(tx, "yonder") is False

    def test_dict_transaction(self):
        """Test that dict-style transactions also work."""
        tx = {"description": "Yonder", "amount": -100.00}
        assert should_exclude(tx, "monzo") is True

    def test_amount_tolerance(self):
        """Test that small floating point differences are handled."""
        tx = MockTransaction("Chloe Tong", 500.001)
        assert should_exclude(tx, "monzo") is True

        tx2 = MockTransaction("Chloe Tong", 499.999)
        assert should_exclude(tx2, "monzo") is True
