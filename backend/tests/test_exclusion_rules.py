"""Tests for database-driven exclusion rules."""
import pytest
from services.exclusion_rules import should_exclude


class TestExclusionRulesAPI:
    """Tests for the exclusion rules CRUD API."""

    def test_create_exclusion_rule(self, client):
        """Test creating an exclusion rule."""
        response = client.post("/exclusions/", json={
            "description_pattern": "yonder",
            "bank": "monzo",
            "amount": None,
            "notes": "Credit card payments"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["description_pattern"] == "yonder"
        assert data["bank"] == "monzo"
        assert data["amount"] is None

    def test_create_exclusion_rule_any_bank(self, client):
        """Test creating a rule that applies to any bank."""
        response = client.post("/exclusions/", json={
            "description_pattern": "self transfer",
            "notes": "Transfers between own accounts"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["bank"] is None

    def test_list_exclusion_rules(self, client):
        """Test listing all exclusion rules."""
        client.post("/exclusions/", json={"description_pattern": "rule1"})
        client.post("/exclusions/", json={"description_pattern": "rule2"})

        response = client.get("/exclusions/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_exclusion_rule(self, client):
        """Test getting a specific rule."""
        create_response = client.post("/exclusions/", json={
            "description_pattern": "test pattern"
        })
        rule_id = create_response.json()["id"]

        response = client.get(f"/exclusions/{rule_id}")
        assert response.status_code == 200
        assert response.json()["description_pattern"] == "test pattern"

    def test_update_exclusion_rule(self, client):
        """Test updating an exclusion rule."""
        create_response = client.post("/exclusions/", json={
            "description_pattern": "old pattern"
        })
        rule_id = create_response.json()["id"]

        response = client.patch(f"/exclusions/{rule_id}", json={
            "description_pattern": "new pattern",
            "amount": 100.00
        })

        assert response.status_code == 200
        assert response.json()["description_pattern"] == "new pattern"
        assert response.json()["amount"] == 100.00

    def test_delete_exclusion_rule(self, client):
        """Test deleting an exclusion rule."""
        create_response = client.post("/exclusions/", json={
            "description_pattern": "to delete"
        })
        rule_id = create_response.json()["id"]

        response = client.delete(f"/exclusions/{rule_id}")
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/exclusions/{rule_id}")
        assert get_response.status_code == 404


class TestExclusionRulesService:
    """Tests for the exclusion rules matching logic."""

    def test_exclude_by_description(self, client, db_session):
        """Test exclusion by description pattern."""
        # Create exclusion rule
        client.post("/exclusions/", json={
            "description_pattern": "yonder",
            "bank": "monzo"
        })

        tx = {"description": "Yonder Payment", "amount": -100.00}
        assert should_exclude(tx, "monzo", db_session) is True

    def test_exclude_case_insensitive(self, client, db_session):
        """Test that matching is case insensitive."""
        client.post("/exclusions/", json={
            "description_pattern": "YONDER"
        })

        tx = {"description": "yonder payment", "amount": -100.00}
        assert should_exclude(tx, "monzo", db_session) is True

    def test_exclude_with_specific_amount(self, client, db_session):
        """Test exclusion with specific amount."""
        client.post("/exclusions/", json={
            "description_pattern": "rent",
            "bank": "monzo",
            "amount": 500.00
        })

        tx_match = {"description": "Rent Payment", "amount": 500.00}
        tx_no_match = {"description": "Rent Payment", "amount": 18.30}

        assert should_exclude(tx_match, "monzo", db_session) is True
        assert should_exclude(tx_no_match, "monzo", db_session) is False

    def test_exclude_bank_specific(self, client, db_session):
        """Test that bank-specific rules only apply to that bank."""
        client.post("/exclusions/", json={
            "description_pattern": "yonder",
            "bank": "monzo"
        })

        tx = {"description": "Yonder", "amount": -100.00}
        assert should_exclude(tx, "monzo", db_session) is True
        assert should_exclude(tx, "yonder", db_session) is False

    def test_exclude_any_bank(self, client, db_session):
        """Test that rules without bank apply to all banks."""
        client.post("/exclusions/", json={
            "description_pattern": "self transfer"
        })

        tx = {"description": "Self Transfer", "amount": -100.00}
        assert should_exclude(tx, "monzo", db_session) is True
        assert should_exclude(tx, "yonder", db_session) is True

    def test_no_exclusion_when_no_rules(self, client, db_session):
        """Test that nothing is excluded when no rules exist."""
        tx = {"description": "Tesco", "amount": -50.00}
        assert should_exclude(tx, "monzo", db_session) is False

    def test_regular_transaction_not_excluded(self, client, db_session):
        """Test that normal transactions aren't excluded."""
        client.post("/exclusions/", json={
            "description_pattern": "yonder"
        })

        tx = {"description": "Tesco Groceries", "amount": -50.00}
        assert should_exclude(tx, "monzo", db_session) is False


class TestExclusionWithTransactions:
    """Integration tests for exclusions with transaction upload."""

    def test_upload_applies_exclusion_rules(self, client):
        """Test that exclusion rules are applied during upload."""
        # Create account
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        # Create exclusion rule
        client.post("/exclusions/", json={
            "description_pattern": "yonder",
            "bank": "monzo"
        })

        # Upload transactions
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Yonder,,Bills,-100.00,GBP
tx_002,20/02/2026,11:00:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 2
        assert data["excluded"] == 1

        # Verify the Yonder transaction is marked as excluded
        transactions = client.get("/transactions/").json()
        yonder_tx = next(tx for tx in transactions if tx["description"] == "Yonder")
        tesco_tx = next(tx for tx in transactions if tx["description"] == "Tesco")

        assert yonder_tx["excluded"] is True
        assert tesco_tx["excluded"] is False
