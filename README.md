# Budgeting App

A personal budgeting app to track monthly expenses from Monzo and Yonder. Import transactions via CSV/PDF, categorize spending, set budgets, and get alerts when overspending.

## Features

- Import Monzo CSV and Yonder CSV exports
- Create spending categories with monthly budgets
- Auto-categorize transactions using pattern matching rules
- Monthly spending reports with budget tracking
- Duplicate detection on re-import

## Setup

### Prerequisites

- Python 3.9+

### Installation

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Run the Server

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

The API will be available at http://localhost:8000

Interactive docs at http://localhost:8000/docs

## Usage

### 1. Create Accounts

```bash
# Monzo (current account)
curl -X POST http://localhost:8000/accounts/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Monzo", "bank": "monzo", "type": "current_account"}'

# Yonder (credit card)
curl -X POST http://localhost:8000/accounts/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Yonder", "bank": "yonder", "type": "credit_card"}'
```

### 2. Create Categories

```bash
curl -X POST http://localhost:8000/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Transport", "monthly_budget": 150}'

curl -X POST http://localhost:8000/categories/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Groceries", "monthly_budget": 300}'
```

### 3. Create Auto-Categorization Rules (Optional)

```bash
# Auto-categorize TFL transactions as Transport
curl -X POST http://localhost:8000/rules/ \
  -H "Content-Type: application/json" \
  -d '{"description_pattern": "TFL", "category_id": 1, "mark_recurring": false}'
```

### 4. Upload Statements

```bash
# Upload Monzo CSV (account_id = 1)
curl -X POST http://localhost:8000/transactions/upload/1 \
  -F "file=@path/to/monzo-export.csv"

# Upload Yonder CSV (account_id = 2)
curl -X POST http://localhost:8000/transactions/upload/2 \
  -F "file=@path/to/yonder-export.csv"
```

### 5. View Transactions

```bash
# All transactions
curl http://localhost:8000/transactions/

# Filter by month
curl "http://localhost:8000/transactions/?month=3&year=2026"

# Filter by account
curl "http://localhost:8000/transactions/?account_id=1"
```

### 6. Update Transaction Category

```bash
curl -X PATCH http://localhost:8000/transactions/1 \
  -H "Content-Type: application/json" \
  -d '{"category_id": 2}'
```

### 7. Get Monthly Report

```bash
curl "http://localhost:8000/reports/monthly?month=3&year=2026"
```

Response:
```json
{
  "month": 3,
  "year": 2026,
  "total_spent": 450.00,
  "categories": [
    {
      "category_name": "Transport",
      "spent": 85.50,
      "budget": 150.00,
      "percentage_used": 57.0,
      "over_budget": false
    }
  ]
}
```

## API Endpoints

### Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/accounts/` | Create account |
| GET | `/accounts/` | List all accounts |
| GET | `/accounts/{id}` | Get account by ID |
| PATCH | `/accounts/{id}` | Update account |
| DELETE | `/accounts/{id}` | Delete account |

### Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/categories/` | Create category |
| GET | `/categories/` | List all categories |
| GET | `/categories/{id}` | Get category by ID |
| PATCH | `/categories/{id}` | Update category |
| DELETE | `/categories/{id}` | Delete category |

### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/transactions/upload/{account_id}` | Upload statement (CSV) |
| GET | `/transactions/` | List transactions |
| GET | `/transactions/{id}` | Get transaction by ID |
| PATCH | `/transactions/{id}` | Update transaction |
| DELETE | `/transactions/{id}` | Delete transaction |

**Query parameters for `GET /transactions/`:**
- `month` (int): Filter by month (1-12)
- `year` (int): Filter by year
- `account_id` (int): Filter by account
- `category_id` (int): Filter by category

### Recurring Rules

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rules/` | Create auto-categorization rule |
| GET | `/rules/` | List all rules |
| GET | `/rules/{id}` | Get rule by ID |
| DELETE | `/rules/{id}` | Delete rule |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/monthly?month={m}&year={y}` | Monthly spending report |
| GET | `/reports/trends?months={n}` | Spending trends (last n months) |

### Admin

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/clear-database` | Delete all data |

## Supported Banks

| Bank | Format | Categories Included |
|------|--------|---------------------|
| Monzo | CSV | Yes (in `source_category`) |
| Yonder | CSV | Yes (in `source_category`) |
