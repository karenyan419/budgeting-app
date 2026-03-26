import pytest


class TestAccountsAPI:
    def test_create_account(self, client):
        response = client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Monzo"
        assert data["bank"] == "monzo"
        assert data["type"] == "current_account"
        assert "id" in data

    def test_list_accounts(self, client):
        # Create an account first
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        response = client.get("/accounts/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Monzo"

    def test_get_account(self, client):
        # Create an account first
        create_response = client.post("/accounts/", json={
            "name": "Yonder",
            "bank": "yonder",
            "type": "credit_card"
        })
        account_id = create_response.json()["id"]

        response = client.get(f"/accounts/{account_id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Yonder"

    def test_get_nonexistent_account(self, client):
        response = client.get("/accounts/999")
        assert response.status_code == 404

    def test_update_account(self, client):
        # Create an account first
        create_response = client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })
        account_id = create_response.json()["id"]

        response = client.patch(f"/accounts/{account_id}", json={
            "name": "Monzo Main"
        })

        assert response.status_code == 200
        assert response.json()["name"] == "Monzo Main"

    def test_delete_account(self, client):
        # Create an account first
        create_response = client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })
        account_id = create_response.json()["id"]

        response = client.delete(f"/accounts/{account_id}")
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/accounts/{account_id}")
        assert get_response.status_code == 404


class TestCategoriesAPI:
    def test_create_category(self, client):
        response = client.post("/categories/", json={
            "name": "Groceries",
            "monthly_budget": 300.00
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Groceries"
        assert data["monthly_budget"] == 300.00

    def test_create_category_without_budget(self, client):
        response = client.post("/categories/", json={
            "name": "Entertainment"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Entertainment"
        assert data["monthly_budget"] is None

    def test_create_duplicate_category(self, client):
        client.post("/categories/", json={"name": "Food"})
        response = client.post("/categories/", json={"name": "Food"})

        assert response.status_code == 400

    def test_list_categories(self, client):
        client.post("/categories/", json={"name": "Transport"})
        client.post("/categories/", json={"name": "Bills"})

        response = client.get("/categories/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_update_category_budget(self, client):
        create_response = client.post("/categories/", json={
            "name": "Food",
            "monthly_budget": 200.00
        })
        category_id = create_response.json()["id"]

        response = client.patch(f"/categories/{category_id}", json={
            "monthly_budget": 250.00
        })

        assert response.status_code == 200
        assert response.json()["monthly_budget"] == 250.00


class TestTransactionsAPI:
    def test_upload_monzo_csv(self, client):
        # Create account first
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP
tx_002,21/02/2026,14:00:00,Card payment,TFL,,Transport,-5.00,GBP"""

        response = client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 2

    def test_upload_skips_duplicates(self, client):
        # Create account first
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        # Upload once
        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        # Upload again - should skip
        response = client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["imported"] == 0
        assert data["skipped"] == 1

    def test_list_transactions(self, client):
        # Create account and upload
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

        response = client.get("/transactions/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "Tesco"

    def test_filter_transactions_by_month(self, client):
        # Create account and upload
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Feb Transaction,,Groceries,-25.50,GBP
tx_002,20/03/2026,10:30:00,Card payment,Mar Transaction,,Groceries,-30.00,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        response = client.get("/transactions/?month=3&year=2026")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["description"] == "Mar Transaction"

    def test_update_transaction_category(self, client):
        # Create account, category, and upload
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })
        cat_response = client.post("/categories/", json={"name": "Food"})
        category_id = cat_response.json()["id"]

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,20/02/2026,10:30:00,Card payment,Tesco,,Groceries,-25.50,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        # Get transaction ID
        transactions = client.get("/transactions/").json()
        tx_id = transactions[0]["id"]

        # Update category
        response = client.patch(f"/transactions/{tx_id}", json={
            "category_id": category_id
        })

        assert response.status_code == 200
        assert response.json()["category_id"] == category_id

    def test_upload_marks_excluded_transactions(self, client):
        # Create account
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        # Include a transaction that should be excluded (Yonder payment)
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


class TestReportsAPI:
    def test_monthly_report(self, client):
        # Setup: account, category, transactions
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })
        client.post("/categories/", json={
            "name": "Groceries",
            "monthly_budget": 300.00
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Tesco,,Groceries,-50.00,GBP
tx_002,16/03/2026,11:00:00,Card payment,Asda,,Groceries,-30.00,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        response = client.get("/reports/monthly?month=3&year=2026")

        assert response.status_code == 200
        data = response.json()
        assert data["month"] == 3
        assert data["year"] == 2026
        assert data["total_spent"] == 80.00

    def test_monthly_report_excludes_excluded_transactions(self, client):
        # Setup: account with excluded transaction
        client.post("/accounts/", json={
            "name": "Monzo",
            "bank": "monzo",
            "type": "current_account"
        })

        csv_content = """Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
tx_001,15/03/2026,10:30:00,Card payment,Yonder,,Bills,-100.00,GBP
tx_002,16/03/2026,11:00:00,Card payment,Tesco,,Groceries,-30.00,GBP"""

        client.post(
            "/transactions/upload/1",
            files={"file": ("test.csv", csv_content, "text/csv")}
        )

        response = client.get("/reports/monthly?month=3&year=2026")

        assert response.status_code == 200
        data = response.json()
        # Should only include Tesco (30), not Yonder (100)
        assert data["total_spent"] == 30.00
