"""Tests for the categorizer service."""
import pytest
from services.categorizer import apply_rules
from models import RecurringRule


class MockRule:
    """Mock RecurringRule for testing."""
    def __init__(self, description_pattern: str, category_id: int, mark_recurring: bool = False):
        self.description_pattern = description_pattern
        self.category_id = category_id
        self.mark_recurring = mark_recurring


class TestApplyRules:
    """Tests for the apply_rules function."""

    def test_no_rules(self):
        """Test with no rules - transactions unchanged."""
        transactions = [
            {"description": "TFL", "amount": -5.00},
            {"description": "Tesco", "amount": -25.00},
        ]

        result = apply_rules(transactions, [])

        assert len(result) == 2
        assert "category_id" not in result[0]
        assert "category_id" not in result[1]

    def test_no_transactions(self):
        """Test with no transactions."""
        rules = [MockRule("TFL", 1)]

        result = apply_rules([], rules)

        assert result == []

    def test_single_rule_match(self):
        """Test single rule matching a transaction."""
        transactions = [
            {"description": "TFL Travel", "amount": -5.00},
            {"description": "Tesco", "amount": -25.00},
        ]
        rules = [MockRule("TFL", 1)]

        result = apply_rules(transactions, rules)

        assert result[0]["category_id"] == 1
        assert "category_id" not in result[1]

    def test_case_insensitive_matching(self):
        """Test that pattern matching is case insensitive."""
        transactions = [
            {"description": "tfl travel", "amount": -5.00},
            {"description": "TFL TRAVEL", "amount": -5.00},
            {"description": "Tfl Travel", "amount": -5.00},
        ]
        rules = [MockRule("TFL", 1)]

        result = apply_rules(transactions, rules)

        assert all(tx["category_id"] == 1 for tx in result)

    def test_mark_recurring_flag(self):
        """Test that mark_recurring flag is applied."""
        transactions = [
            {"description": "Netflix", "amount": -10.00},
        ]
        rules = [MockRule("Netflix", 1, mark_recurring=True)]

        result = apply_rules(transactions, rules)

        assert result[0]["category_id"] == 1
        assert result[0]["is_recurring"] is True

    def test_mark_recurring_false(self):
        """Test that mark_recurring=False doesn't set flag."""
        transactions = [
            {"description": "Netflix", "amount": -10.00},
        ]
        rules = [MockRule("Netflix", 1, mark_recurring=False)]

        result = apply_rules(transactions, rules)

        assert result[0]["category_id"] == 1
        assert "is_recurring" not in result[0]

    def test_first_rule_wins(self):
        """Test that first matching rule is applied."""
        transactions = [
            {"description": "TFL Bus", "amount": -2.00},
        ]
        rules = [
            MockRule("TFL", 1),  # Should match first
            MockRule("Bus", 2),  # Should not override
        ]

        result = apply_rules(transactions, rules)

        assert result[0]["category_id"] == 1

    def test_multiple_transactions_multiple_rules(self):
        """Test multiple transactions with multiple rules."""
        transactions = [
            {"description": "TFL Travel", "amount": -5.00},
            {"description": "Tesco Groceries", "amount": -50.00},
            {"description": "Spotify", "amount": -10.00},
            {"description": "Random Shop", "amount": -20.00},
        ]
        rules = [
            MockRule("TFL", 1, mark_recurring=True),
            MockRule("Tesco", 2),
            MockRule("Spotify", 3, mark_recurring=True),
        ]

        result = apply_rules(transactions, rules)

        assert result[0]["category_id"] == 1
        assert result[0]["is_recurring"] is True

        assert result[1]["category_id"] == 2
        assert "is_recurring" not in result[1]

        assert result[2]["category_id"] == 3
        assert result[2]["is_recurring"] is True

        # Random Shop should be unchanged
        assert "category_id" not in result[3]

    def test_partial_match(self):
        """Test that partial string match works."""
        transactions = [
            {"description": "PAYPAL *NETFLIX", "amount": -10.00},
        ]
        rules = [MockRule("NETFLIX", 1)]

        result = apply_rules(transactions, rules)

        assert result[0]["category_id"] == 1

    def test_empty_description(self):
        """Test handling transaction with empty description."""
        transactions = [
            {"description": "", "amount": -5.00},
        ]
        rules = [MockRule("TFL", 1)]

        result = apply_rules(transactions, rules)

        assert "category_id" not in result[0]

    def test_missing_description(self):
        """Test handling transaction without description key."""
        transactions = [
            {"amount": -5.00},
        ]
        rules = [MockRule("TFL", 1)]

        result = apply_rules(transactions, rules)

        assert "category_id" not in result[0]

    def test_preserves_existing_fields(self):
        """Test that existing transaction fields are preserved."""
        transactions = [
            {
                "description": "TFL",
                "amount": -5.00,
                "date": "2026-03-15",
                "hash": "abc123",
                "notes": "Test note",
            },
        ]
        rules = [MockRule("TFL", 1)]

        result = apply_rules(transactions, rules)

        assert result[0]["description"] == "TFL"
        assert result[0]["amount"] == -5.00
        assert result[0]["date"] == "2026-03-15"
        assert result[0]["hash"] == "abc123"
        assert result[0]["notes"] == "Test note"
        assert result[0]["category_id"] == 1
