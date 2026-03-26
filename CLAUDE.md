# Budgeting App

Personal budgeting app to track spending across Monzo (current account) and Yonder (credit card).

## Tech Stack

- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **Frontend:** React (not yet built)
- **PDF Parsing:** pdfplumber

## Project Structure

```
backend/
├── main.py              # FastAPI entry point
├── database.py          # SQLite connection
├── models.py            # SQLAlchemy models (Account, Category, Transaction, RecurringRule)
├── schemas.py           # Pydantic schemas
├── routers/             # API endpoints
│   ├── accounts.py
│   ├── categories.py
│   ├── transactions.py  # Includes file upload
│   ├── reports.py
│   └── recurring_rules.py
└── services/
    ├── monzo_parser.py  # Parse Monzo CSV exports
    ├── yonder_parser.py # Parse Yonder PDF statements
    └── categorizer.py   # Apply auto-categorization rules
```

## Running the Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload
```

API docs at http://localhost:8000/docs

## Key Concepts

- **Accounts:** Monzo (CSV import) or Yonder (PDF import)
- **Categories:** User-defined spending categories with optional monthly budgets
- **Transactions:** Imported from bank statements, linked to accounts and categories
- **Recurring Rules:** Pattern matching on descriptions to auto-categorize transactions

## Bank Statement Formats

### Monzo CSV
- Columns: Date (1), Name (4), Category (6), Amount (7)
- Includes Monzo's own categories in `source_category`

### Yonder PDF
- 3-column table: Date, Description, Amount
- No categories provided - needs manual or rule-based categorization

## Database

SQLite file at `backend/budget.db`. Key tables:
- `accounts` - bank accounts
- `categories` - spending categories with budgets
- `transactions` - all transactions with hash for duplicate detection
- `recurring_rules` - auto-categorization patterns

## Python Version

Using Python 3.9 - use `Optional[type]` instead of `type | None` syntax.
