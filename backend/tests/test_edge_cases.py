"""Edge case tests for error handling and boundary conditions."""
import pytest


class TestMalformedCSVs:
    """Test handling of malformed CSV files."""

    def test_empty_file(self, client):
        """Test uploading an empty file."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("empty.csv", "", "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 0

    def test_header_only_csv(self, client):
        """Test CSV with only headers, no data rows."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = "Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency"

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("headers.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 0

    def test_missing_required_columns(self, client):
        """Test CSV missing required columns."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        # Missing Date column
        csv_content = """Transaction ID,Name,Amount
tx_001,Tesco,-25.50"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("bad.csv", csv_content, "text/csv")}
        )

        # Should handle gracefully - either 400 or 200 with 0 imported
        assert response.status_code in [200, 400]

    def test_invalid_date_format(self, client):
        """Test CSV with invalid date format."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,invalid-date,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("bad_date.csv", csv_content, "text/csv")}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_invalid_amount_format(self, client):
        """Test CSV with non-numeric amount."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,not-a-number,GBP"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("bad_amount.csv", csv_content, "text/csv")}
        )

        # Should handle gracefully
        assert response.status_code in [200, 400, 422]

    def test_extra_columns_ignored(self, client):
        """Test that extra columns in CSV are ignored."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency,ExtraCol1,ExtraCol2
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP,extra1,extra2"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("extra_cols.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        assert response.json()["imported"] == 1


class TestYonderCSVEdgeCases:
    """Edge cases specific to Yonder CSV format."""

    def test_yonder_empty_file(self, client):
        """Test uploading empty Yonder file."""
        client.post("/accounts/", json={
            "name": "Yonder",
            "bank": "yonder",
            "type": "credit_card"
        })

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("empty.csv", "", "text/csv")}
        )

        assert response.status_code == 200
        assert response.json()["imported"] == 0

    def test_yonder_credit_transaction(self, client):
        """Test Yonder CSV with credit (refund) transaction."""
        client.post("/accounts/", json={
            "name": "Yonder",
            "bank": "yonder",
            "type": "credit_card"
        })

        # Use correct Yonder format with Credit type
        csv_content = """"Date/Time of transaction","Description","Amount (GBP)","Amount (in Charged Currency)","Currency","Category","Debit or Credit","Country"
"2026-03-15T13:55:20.413736","REFUND","50.00","50.00","GBP","General","Credit","GBR\""""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("yonder.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 1

        # Credit should be positive (not negated)
        transactions = client.get("/transactions/").json()
        assert len(transactions) == 1
        assert transactions[0]["amount"] == 50.00


class TestAccountEdgeCases:
    """Edge cases for account operations."""

    def test_upload_to_nonexistent_account(self, client):
        """Test uploading to account that doesn't exist."""
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        response = client.post(
            "/transactions/upload/999",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 404

    def test_delete_account_with_transactions(self, client):
        """Test deleting account that has transactions."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        # Try to delete account - should either cascade or fail gracefully
        response = client.delete("/accounts/1")
        # Depends on implementation - either success with cascade or error
        assert response.status_code in [200, 400, 409]


class TestCategoryEdgeCases:
    """Edge cases for category operations."""

    def test_delete_category_with_transactions(self, client):
        """Test deleting category that has assigned transactions."""
        # Create account and category
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })
        cat_response = client.post("/categories/", json={"name": "Food"})
        category_id = cat_response.json()["id"]

        # Upload and assign category
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        # Assign category to transaction
        transactions = client.get("/transactions/").json()
        client.patch(f"/transactions/{transactions[0]['id']}", json={
            "category_id": category_id
        })

        # Try to delete category
        response = client.delete(f"/categories/{category_id}")
        # Should either cascade (set to null) or fail gracefully
        assert response.status_code in [200, 400, 409]

    def test_category_name_with_special_characters(self, client):
        """Test category name with special characters."""
        response = client.post("/categories/", json={
            "name": "Food & Drink (Restaurants)",
            "monthly_budget": 200.00
        })

        assert response.status_code == 200
        assert response.json()["name"] == "Food & Drink (Restaurants)"

    def test_category_with_zero_budget(self, client):
        """Test creating category with zero budget."""
        response = client.post("/categories/", json={
            "name": "Miscellaneous",
            "monthly_budget": 0
        })

        assert response.status_code == 200
        assert response.json()["monthly_budget"] == 0


class TestTransactionEdgeCases:
    """Edge cases for transaction operations."""

    def test_transaction_with_zero_amount(self, client):
        """Test handling transaction with zero amount."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Zero Amount,,Test,0.00,GBP"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        # Zero amount transactions might be filtered or included
        data = response.json()
        assert data["imported"] >= 0

    def test_transaction_with_positive_amount(self, client):
        """Test handling income/refund with positive amount."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Salary,,Income,2500.00,GBP"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        assert response.json()["imported"] == 1

        transactions = client.get("/transactions/").json()
        assert transactions[0]["amount"] == 2500.00

    def test_update_nonexistent_transaction(self, client):
        """Test updating transaction that doesn't exist."""
        response = client.patch("/transactions/999", json={
            "category_id": 1
        })

        assert response.status_code == 404

    def test_filter_by_invalid_month(self, client):
        """Test filtering transactions by invalid month."""
        response = client.get("/transactions/?month=13&year=2026")
        # Should either return 422 validation error or empty list
        assert response.status_code in [200, 422]

    def test_filter_by_future_year(self, client):
        """Test filtering transactions by far future year."""
        response = client.get("/transactions/?month=1&year=3000")
        assert response.status_code == 200
        assert response.json() == []


class TestReportEdgeCases:
    """Edge cases for reporting endpoints."""

    def test_monthly_report_no_transactions(self, client):
        """Test monthly report when no transactions exist."""
        response = client.get("/reports/monthly?month=1&year=2026")

        assert response.status_code == 200
        data = response.json()
        assert data["total_spent"] == 0
        assert data["categories"] == []

    def test_monthly_report_invalid_month(self, client):
        """Test monthly report with invalid month."""
        response = client.get("/reports/monthly?month=0&year=2026")
        assert response.status_code == 422  # Validation error

        response = client.get("/reports/monthly?month=13&year=2026")
        assert response.status_code == 422

    def test_monthly_report_with_over_budget_category(self, client):
        """Test report correctly identifies over-budget categories."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })
        client.post("/categories/", json={
            "name": "Coffee",
            "monthly_budget": 20.00
        })

        # Spend more than budget
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Costa,,Coffee,-15.00,GBP
tx_002,16/03/2026,10:30:00,Card payment,Starbucks,,Coffee,-15.00,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        # Assign transactions to Coffee category
        transactions = client.get("/transactions/").json()
        for tx in transactions:
            client.patch(f"/transactions/{tx['id']}", json={"category_id": 1})

        report = client.get("/reports/monthly?month=3&year=2026").json()

        coffee_category = next(
            (c for c in report["categories"] if c["category_name"] == "Coffee"),
            None
        )
        assert coffee_category is not None
        assert coffee_category["spent"] == 30.00
        assert coffee_category["budget"] == 20.00
        assert coffee_category["over_budget"] is True
        assert coffee_category["percentage_used"] == 150.0


class TestLargeDataSets:
    """Tests for handling larger amounts of data."""

    def test_upload_many_transactions(self, client):
        """Test uploading many transactions at once."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        # Generate 100 transactions
        lines = ["Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency"]
        for i in range(100):
            day = (i % 28) + 1
            lines.append(f"tx_{i:03d},{day:02d}/03/2026,10:30:00,Card payment,Shop{i},,Misc,-{i+1}.00,GBP")

        csv_content = "\n".join(lines)

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("large.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        assert response.json()["imported"] == 100

        # Verify all transactions stored
        transactions = client.get("/transactions/").json()
        assert len(transactions) == 100

    def test_many_categories_in_report(self, client):
        """Test report with many categories."""
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        # Create 20 categories
        for i in range(20):
            client.post("/categories/", json={
                "name": f"Category{i}",
                "monthly_budget": 100.00
            })

        # Upload a transaction
        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Test,,Misc,-50.00,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        response = client.get("/reports/monthly?month=3&year=2026")
        assert response.status_code == 200
        data = response.json()
        # Should have all 20 categories plus uncategorized
        assert len(data["categories"]) == 21
