# Budgeting App

Personal budgeting app to track spending across Monzo (current account) and Yonder (credit card).

## Tech Stack

- **Backend:** Python 3.9, FastAPI, SQLAlchemy, SQLite
- **Testing:** pytest + pytest-cov (96 tests, 97% coverage)

## Project Structure

```
backend/
├── main.py              # FastAPI entry point
├── database.py          # SQLite connection (budgeting.db)
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── routers/
│   ├── accounts.py      # Bank account CRUD
│   ├── categories.py    # Spending category CRUD
│   ├── transactions.py  # Upload CSVs, list/update transactions
│   ├── recurring_rules.py # Auto-categorization rules
│   ├── exclusion_rules.py # Exclusion rules CRUD
│   ├── reports.py       # Monthly reports & trends
│   └── admin.py         # Clear DB, data coverage
├── services/
│   ├── monzo_parser.py  # Parse Monzo CSV
│   ├── yonder_parser.py # Parse Yonder CSV
│   ├── categorizer.py   # Apply auto-categorization rules
│   └── exclusion_rules.py # Check exclusions from database
└── tests/               # 96 tests
```

## Commands

```bash
# Run server
cd backend && source venv/bin/activate
uvicorn main:app --reload

# Run tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=term-missing

# Query database
sqlite3 budgeting.db
```

## Key Concepts

### Transaction Flow
1. Upload CSV → Parser extracts transactions
2. Exclusion rules (from DB) mark internal transfers (`excluded=True`)
3. Hash generated for duplicate detection (SHA256, 16 chars)
4. RecurringRules auto-categorize by description pattern

### Exclusion Rules (Database-driven)
Managed via `/exclusions/` API. Each rule has:
- `description_pattern` - text to match (case-insensitive)
- `bank` - optional, limit to specific bank (monzo/yonder)
- `amount` - optional, match specific amount only
- `notes` - description of why excluded

### Bank Statement Formats

**Monzo CSV:**
```
Transaction ID,Date,Time,Type,Name,Emoji,Category,Amount,Currency
```

**Yonder CSV:**
```
Date/Time of transaction,Description,Amount (GBP),Amount (in Charged Currency),Currency,Category,Debit or Credit,Country
```

## Database

SQLite file at `backend/budgeting.db`. Tables:
- `accounts` - bank accounts (monzo/yonder)
- `categories` - spending categories with monthly budgets
- `transactions` - all transactions with `excluded` flag and `hash` for dedup
- `recurring_rules` - pattern-matching auto-categorization
- `exclusion_rules` - patterns to exclude from reports

## API Endpoints

| Prefix | Endpoints |
|--------|-----------|
| `/accounts` | CRUD for bank accounts |
| `/categories` | CRUD for categories with budgets |
| `/transactions` | `POST /upload/{id}`, list/filter/update |
| `/rules` | Auto-categorization rules |
| `/exclusions` | Exclusion rules CRUD |
| `/reports` | `GET /monthly`, `GET /trends` |
| `/admin` | `POST /clear-database`, `GET /data-coverage` |

## Python Version

Using Python 3.9 - use `Optional[type]` instead of `type | None` syntax.
