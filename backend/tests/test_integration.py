"""Integration tests for full application flows."""
import pytest


class TestFullUploadToReportFlow:
    """Test complete flows from upload through to reporting."""

    def test_upload_categorize_report_flow(self, client):
        """Test: upload transactions → apply rules → get monthly report."""
        # 1. Create account
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        # 2. Create categories
        client.post("/categories/", json={
            "name": "Transport",
            "monthly_budget": 100.00
        })
        client.post("/categories/", json={
            "name": "Groceries",
            "monthly_budget": 300.00
        })

        # 3. Create auto-categorization rule
        client.post("/rules/", json={
            "description_pattern": "TFL",
            "category_id": 1,
            "mark_recurring": True
        })

        # 4. Upload transactions
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,TFL,,Transport,-5.00,GBP
tx_002,16/03/2026,11:00:00,Card payment,Tesco,,Groceries,-45.00,GBP
tx_003,17/03/2026,12:00:00,Card payment,TFL,,Transport,-5.00,GBP"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )
        assert response.status_code == 200
        assert response.json()["imported"] == 3

        # 5. Verify transactions were categorized by rule
        transactions = client.get("/transactions/").json()
        tfl_txs = [tx for tx in transactions if "TFL" in tx["description"]]
        assert all(tx["category_id"] == 1 for tx in tfl_txs)
        assert all(tx["is_recurring"] for tx in tfl_txs)

        # 6. Get monthly report
        report = client.get("/reports/monthly?month=3&year=2026").json()
        assert report["total_spent"] == 55.00
        assert report["month"] == 3
        assert report["year"] == 2026

    def test_multi_account_flow(self, client):
        """Test managing transactions across multiple accounts."""
        # Create two accounts
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })
        client.post("/accounts/", json={
            "name": "Yonder",
            "bank": "yonder",
            "type": "credit_card"
        })

        # Upload to Monzo
        monzo_csv = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Coffee Shop,,Eating out,-4.50,GBP"""
        client.post(
            "/transactions/upload/1",
            files={"file": ("monzo.csv", monzo_csv, "text/csv")}
        )

        # Upload to Yonder (correct format)
        yonder_csv = """"Date/Time of transaction","Description","Amount (GBP)","Amount (in Charged Currency)","Currency","Category","Debit or Credit","Country"
"2026-03-15T12:00:00.000000","RESTAURANT","25.00","25.00","GBP","Eating Out","Debit","GBR\""""
        client.post(
            "/transactions/upload/2",
            files={"file": ("yonder.csv", yonder_csv, "text/csv")}
        )

        # Filter by account
        monzo_txs = client.get("/transactions/?account_id=1").json()
        yonder_txs = client.get("/transactions/?account_id=2").json()

        assert len(monzo_txs) == 1
        assert len(yonder_txs) == 1
        assert monzo_txs[0]["description"] == "Coffee Shop"
        assert yonder_txs[0]["description"] == "RESTAURANT"

    def test_exclusion_flow_with_reporting(self, client):
        """Test that excluded transactions don't appear in reports."""
        # Create Monzo account
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        # Create exclusion rules
        client.post("/exclusions/", json={
            "description_pattern": "yonder",
            "bank": "monzo"
        })
        client.post("/exclusions/", json={
            "description_pattern": "investengine"
        })

        # Upload transactions including ones that should be excluded
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Yonder,,Bills,-500.00,GBP
tx_002,15/03/2026,11:00:00,Card payment,InvestEngine,,Savings,-200.00,GBP
tx_003,15/03/2026,12:00:00,Card payment,Actual Purchase,,Shopping,-50.00,GBP"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        # Verify exclusions were applied
        data = response.json()
        assert data["imported"] == 3
        assert data["excluded"] == 2  # Yonder and InvestEngine

        # Get report - should only include non-excluded
        report = client.get("/reports/monthly?month=3&year=2026").json()
        assert report["total_spent"] == 50.00  # Only "Actual Purchase"


class TestAdminEndpoints:
    """Tests for admin router endpoints."""

    def test_clear_database(self, client):
        """Test clearing all data from database."""
        # Create some data
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })
        client.post("/categories/", json={"name": "Food"})

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Test,,Food,-10.00,GBP"""
        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        # Verify data exists
        assert len(client.get("/accounts/").json()) == 1
        assert len(client.get("/categories/").json()) == 1
        assert len(client.get("/transactions/").json()) == 1

        # Clear database
        response = client.post("/admin/clear-database")
        assert response.status_code == 200
        data = response.json()
        assert data["deleted"]["accounts"] == 1
        assert data["deleted"]["categories"] == 1
        assert data["deleted"]["transactions"] == 1

        # Verify all data gone
        assert len(client.get("/accounts/").json()) == 0
        assert len(client.get("/categories/").json()) == 0
        assert len(client.get("/transactions/").json()) == 0

    def test_data_coverage_no_accounts(self, client):
        """Test data coverage with no accounts."""
        response = client.get("/admin/data-coverage")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "No accounts found. Create accounts first."
        assert data["accounts"] == []

    def test_data_coverage_no_transactions(self, client):
        """Test data coverage with account but no transactions."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        response = client.get("/admin/data-coverage")
        assert response.status_code == 200
        data = response.json()
        assert len(data["accounts"]) == 1
        assert data["accounts"][0]["status"] == "no_data"
        assert data["accounts"][0]["transactions"] == 0

    def test_data_coverage_with_transactions(self, client):
        """Test data coverage shows correct months."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/01/2026,10:30:00,Card payment,Test1,,Food,-10.00,GBP
tx_002,15/03/2026,10:30:00,Card payment,Test2,,Food,-10.00,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        response = client.get("/admin/data-coverage")
        assert response.status_code == 200
        data = response.json()

        account_data = data["accounts"][0]
        assert account_data["status"] == "has_data"
        assert account_data["transactions"] == 2
        assert "2026-01" in account_data["covered_months"]
        assert "2026-03" in account_data["covered_months"]
        # February is missing
        assert "2026-02" in account_data["missing_months"]


class TestRecurringRulesAPI:
    """Tests for recurring rules endpoints."""

    def test_create_rule(self, client):
        """Test creating a categorization rule."""
        # Create category first
        client.post("/categories/", json={"name": "Transport"})

        response = client.post("/rules/", json={
            "description_pattern": "TFL",
            "category_id": 1,
            "mark_recurring": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["description_pattern"] == "TFL"
        assert data["category_id"] == 1
        assert data["mark_recurring"] is True

    def test_create_rule_nonexistent_category(self, client):
        """Test creating rule with nonexistent category fails."""
        response = client.post("/rules/", json={
            "description_pattern": "TFL",
            "category_id": 999,
            "mark_recurring": False
        })

        assert response.status_code == 404
        assert "Category not found" in response.json()["detail"]

    def test_list_rules(self, client):
        """Test listing all rules."""
        client.post("/categories/", json={"name": "Transport"})
        client.post("/rules/", json={
            "description_pattern": "TFL",
            "category_id": 1,
            "mark_recurring": True
        })
        client.post("/rules/", json={
            "description_pattern": "UBER",
            "category_id": 1,
            "mark_recurring": False
        })

        response = client.get("/rules/")
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_rule(self, client):
        """Test getting a specific rule."""
        client.post("/categories/", json={"name": "Transport"})
        create_response = client.post("/rules/", json={
            "description_pattern": "TFL",
            "category_id": 1,
            "mark_recurring": True
        })
        rule_id = create_response.json()["id"]

        response = client.get(f"/rules/{rule_id}")
        assert response.status_code == 200
        assert response.json()["description_pattern"] == "TFL"

    def test_get_nonexistent_rule(self, client):
        """Test getting nonexistent rule returns 404."""
        response = client.get("/rules/999")
        assert response.status_code == 404

    def test_delete_rule(self, client):
        """Test deleting a rule."""
        client.post("/categories/", json={"name": "Transport"})
        create_response = client.post("/rules/", json={
            "description_pattern": "TFL",
            "category_id": 1,
            "mark_recurring": True
        })
        rule_id = create_response.json()["id"]

        response = client.delete(f"/rules/{rule_id}")
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/rules/{rule_id}")
        assert get_response.status_code == 404


class TestTrendsEndpoint:
    """Tests for spending trends endpoint."""

    def test_trends_empty(self, client):
        """Test trends with no data."""
        response = client.get("/reports/trends?months=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(item["total_spent"] == 0 for item in data)

    def test_trends_with_data(self, client):
        """Test trends with transaction data."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        # Upload transactions for March 2026
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Test,,Food,-100.00,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        response = client.get("/reports/trends?months=6")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 6

        # Find March 2026 in the results
        march_data = next((item for item in data if item["month"] == 3 and item["year"] == 2026), None)
        if march_data:
            assert march_data["total_spent"] == 100.00

    def test_trends_excludes_excluded_transactions(self, client):
        """Test that excluded transactions don't appear in trends."""
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

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Yonder,,Bills,-500.00,GBP
tx_002,15/03/2026,11:00:00,Card payment,Regular Purchase,,Shopping,-50.00,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        response = client.get("/reports/trends?months=6")
        data = response.json()

        march_data = next((item for item in data if item["month"] == 3 and item["year"] == 2026), None)
        if march_data:
            # Should only be 50, not 550 (Yonder payment excluded)
            assert march_data["total_spent"] == 50.00
