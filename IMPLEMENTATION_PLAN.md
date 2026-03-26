# Budgeting App - Implementation Plan

## Overview

A personal budgeting web app to track monthly expenses from your credit card and current account. Import transactions via CSV, categorize spending, set budgets, and get alerts when overspending.

**Tech Stack:**
- Backend: Python + FastAPI + SQLAlchemy + SQLite
- Frontend: React + Recharts
- PDF Parsing: pdfplumber (for Yonder statements)

---

## Product Plan: MVP Scope & Priorities

### MVP (Must-Have)

Core features required for a functional budgeting app:

| Priority | Feature | Description |
|----------|---------|-------------|
| P0 | CSV Import | Import transactions from bank CSV exports |
| P0 | Transaction List | View and filter imported transactions |
| P0 | Categories | Create spending categories and assign transactions |
| P0 | Monthly Report | See spending totals by category for a given month |
| P1 | Budget Limits | Set monthly budget per category |
| P1 | Overspend Alerts | Visual warnings when nearing/exceeding budget |
| P1 | Multiple Accounts | Support credit card + current account with different CSV formats |

### Post-MVP (Nice-to-Have)

Features to add after core functionality is stable:

| Priority | Feature | Description |
|----------|---------|-------------|
| P2 | Recurring Rules | Auto-categorize transactions based on description patterns |
| P2 | LLM Categorization | Use AI to auto-categorize transactions that don't match rules |
| P2 | Spending Trends | Charts showing spending over multiple months |
| P2 | Recurring Flags | Mark and track recurring expenses (subscriptions, bills) |
| P3 | Manual Transactions | Add transactions without CSV import |
| P3 | Export Reports | Download spending reports as PDF/CSV |
| P3 | Dark Mode | Theme toggle for UI |

### MVP Definition of Done

The MVP is complete when a user can:
1. Set up Monzo (current account) and Yonder (credit card) accounts
2. Upload a Monzo CSV or Yonder PDF and see transactions imported
3. Create categories (Food, Bills, Transport, etc.)
4. Assign categories to transactions
5. View a monthly breakdown showing spend per category vs budget
6. See a warning if any category exceeds its budget

---

## Bank Statement Formats

### Monzo (Current Account) - CSV

**Filename pattern:** `Monzo Data Export - CSV (Sunday, 22 March 2026).csv`

| Column | Index | Example |
|--------|-------|---------|
| Date | 1 | `02/02/2026` |
| Name | 4 | `Octopus Energy` |
| Category | 6 | `Bills` |
| Amount | 7 | `-101.99` (negative = expense) |
| Money Out | 16 | `-101.99` |
| Money In | 17 | `14.30` |

- Date format: `%d/%m/%Y`
- Already includes Monzo's own categories
- Negative amounts = expenses, positive = income

### Yonder (Credit Card) - PDF

**Filename pattern:** `2026-03-Yonder-Bill.pdf`

PDF contains a transactions table with 3 columns:

| Column | Description |
|--------|-------------|
| Date | `DD/MM/YYYY` format |
| Description | Merchant name |
| Amount (£) | Always positive (all are expenses) |

- Requires PDF parsing with `pdfplumber`
- No categories provided - must be assigned manually or via rules
- Statement period spans ~1 month

---

## Phase 1: Backend Foundation

### 1.1 Project Setup

**File: `backend/requirements.txt`**

Dependencies needed:
- `fastapi` - Web framework for building the REST API
- `uvicorn` - ASGI server to run the app
- `sqlalchemy` - ORM for database operations
- `pydantic` - Data validation (bundled with FastAPI)
- `python-multipart` - Required for file uploads
- `pdfplumber` - PDF parsing for Yonder statements
- `anthropic` - Claude API for LLM-based categorization (post-MVP)

**How to run:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

---

### 1.2 Database Setup

**File: `backend/database.py`**

Purpose: Configure SQLite database connection and session management.

Contents:
- `DATABASE_URL` - Points to local SQLite file `budget.db`
- `engine` - SQLAlchemy engine for database connection
- `SessionLocal` - Session factory for creating database sessions
- `Base` - Declarative base for model definitions
- `get_db()` - Dependency function that provides a database session to route handlers and ensures cleanup

---

### 1.3 Database Models

**File: `backend/models.py`**

Four tables representing the core data:

#### Table: `accounts`
Represents your payment sources (Monzo current account, Yonder credit card).

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Display name (e.g., "Monzo", "Yonder") |
| bank | Enum | `monzo` or `yonder` (determines parser) |
| type | Enum | `credit_card` or `current_account` |

The `bank` field determines which parser to use:
- `monzo` → CSV parser with Monzo column layout
- `yonder` → PDF parser extracting transaction tables

#### Table: `categories`
Spending categories with budget limits.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| name | String | Category name (e.g., "Food", "Bills") |
| monthly_budget | Float | Maximum monthly spend for this category |

#### Table: `transactions`
Individual expenses imported from CSV or added manually.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| account_id | Integer | Foreign key to accounts |
| category_id | Integer | Foreign key to categories (nullable) |
| amount | Float | Transaction amount (positive = expense) |
| date | Date | Transaction date |
| description | String | Transaction description from bank |
| is_recurring | Boolean | Whether this is a recurring expense |

#### Table: `recurring_rules`
Patterns to auto-categorize and flag recurring transactions.

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| description_pattern | String | Text pattern to match (e.g., "NETFLIX") |
| category_id | Integer | Auto-assign this category when matched |
| mark_recurring | Boolean | Auto-flag as recurring when matched |

---

### 1.4 Pydantic Schemas

**File: `backend/schemas.py`**

Request/response validation models for each entity:

- `AccountCreate`, `AccountUpdate`, `Account` - For account CRUD
- `CategoryCreate`, `CategoryUpdate`, `Category` - For category CRUD
- `TransactionCreate`, `TransactionUpdate`, `Transaction` - For transaction CRUD
- `RecurringRuleCreate`, `RecurringRule` - For rule management
- `CategorySpending`, `MonthlyReport` - For report responses

---

### 1.5 Main Application

**File: `backend/main.py`**

Purpose: FastAPI application entry point.

Contents:
- Create FastAPI app instance
- Configure CORS middleware (allow frontend to call API)
- Include all routers
- Create database tables on startup

---

## Phase 2: Statement Import

### 2.1 Statement Parser Services

**File: `backend/services/monzo_parser.py`**

Purpose: Parse Monzo CSV exports.

```python
def parse_monzo_csv(file) -> list[dict]:
    # Column mappings (fixed for Monzo):
    # - Date: index 1, format %d/%m/%Y
    # - Name: index 4
    # - Category: index 6 (Monzo's own categories)
    # - Amount: index 7
    # Returns list of transaction dicts with date, description, amount, source_category
```

**File: `backend/services/yonder_parser.py`**

Purpose: Parse Yonder PDF statements using pdfplumber.

```python
def parse_yonder_pdf(file) -> list[dict]:
    # Extract tables from PDF
    # Parse 3-column format: Date | Description | Amount (£)
    # Date format: %d/%m/%Y
    # All amounts are expenses (convert to negative)
    # Returns list of transaction dicts with date, description, amount
```

### 2.2 Transactions Router

**File: `backend/routers/transactions.py`**

Endpoints:
- `POST /transactions/upload/{account_id}` - Upload statement file
  - Accepts CSV (Monzo) or PDF (Yonder) based on account type
  - Routes to appropriate parser based on `account.bank` field
  - Applies recurring rules for auto-categorization
  - Saves transactions to database
  - Returns count of imported transactions

- `GET /transactions` - List transactions with filters
  - Query params: `month`, `year`, `account_id`, `category_id`

- `PATCH /transactions/{id}` - Update transaction (change category, mark recurring)

- `DELETE /transactions/{id}` - Delete a transaction

---

## Phase 3: Categories & Budgets

**File: `backend/routers/categories.py`**

Endpoints:
- `POST /categories` - Create a new category with budget
- `GET /categories` - List all categories
- `PATCH /categories/{id}` - Update category name or budget
- `DELETE /categories/{id}` - Delete category (nullifies transactions' category_id)

---

## Phase 4: Accounts Management

**File: `backend/routers/accounts.py`**

Endpoints:
- `POST /accounts` - Create account with CSV column mapping
- `GET /accounts` - List all accounts
- `PATCH /accounts/{id}` - Update account settings
- `DELETE /accounts/{id}` - Delete account and its transactions

---

## Phase 5: Reports & Alerts

**File: `backend/routers/reports.py`**

Endpoints:
- `GET /reports/monthly?month=3&year=2026` - Monthly spending report
  - Returns:
    - Total spent
    - Spending by category with budget comparison
    - Percentage of budget used per category
    - Alerts for categories over 80% or 100% of budget

- `GET /reports/trends?months=6` - Spending trends over time
  - Returns monthly totals for charting

---

## Phase 6: Recurring Rules

**File: `backend/services/categorizer.py`**

Purpose: Apply rules to auto-categorize transactions on import.

Function:
- `apply_rules(transactions, rules)` - For each transaction:
  - Check if description matches any rule pattern
  - If matched, set category_id and is_recurring flag

**File: `backend/routers/recurring_rules.py`**

Endpoints:
- `POST /rules` - Create a new rule
- `GET /rules` - List all rules
- `DELETE /rules/{id}` - Delete a rule

---

## Phase 6.5: LLM Categorization

**File: `backend/services/llm_categorizer.py`**

Purpose: Use Claude API to categorize transactions that don't match any rules.

### Hybrid Approach

1. **Rules first** (instant, free) - Check recurring rules for pattern matches
2. **LLM fallback** - Send unmatched transactions to Claude for categorization
3. **Auto-create rules** (optional) - Offer to create rules from LLM decisions

### Implementation

```python
from anthropic import Anthropic

async def categorize_with_llm(transactions: list[dict], categories: list[str]) -> list[dict]:
    """
    Send uncategorized transactions to Claude for categorization.
    Batches transactions to minimize API calls.
    """
    client = Anthropic()

    prompt = f"""Categorize these transactions into one of: {', '.join(categories)}

Transactions:
{format_transactions(transactions)}

Return JSON array with transaction index and category."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}]
    )

    return parse_categorization_response(response)
```

### Configuration

**Environment variable:** `ANTHROPIC_API_KEY`

**Settings in `backend/config.py`:**
- `LLM_ENABLED` - Toggle LLM categorization on/off
- `LLM_BATCH_SIZE` - Max transactions per API call (default: 20)
- `LLM_AUTO_CREATE_RULES` - Auto-create rules from LLM decisions

### API Changes

- `POST /transactions/upload/{account_id}` - Add `use_llm=true` query param
- `POST /transactions/categorize` - Manually trigger LLM categorization for selected transactions

### Cost Estimate

~$0.003-0.01 per batch of 20 transactions (using Claude Sonnet)

---

## Phase 7: React Frontend

### 7.1 Project Setup

```bash
cd frontend
npm create vite@latest . -- --template react
npm install axios recharts react-router-dom
```

### 7.2 Components

| Component | Purpose |
|-----------|---------|
| `App.jsx` | Main layout with navigation |
| `Dashboard.jsx` | Overview with charts and alerts |
| `StatementUpload.jsx` | File upload for CSV (Monzo) or PDF (Yonder) |
| `TransactionList.jsx` | Table of transactions with filtering |
| `CategoryManager.jsx` | CRUD interface for categories |
| `BudgetChart.jsx` | Bar/pie charts for spending vs budget |
| `Alerts.jsx` | Warning banners for overspending |

### 7.3 API Client

**File: `frontend/src/services/api.js`**

Axios instance configured with base URL pointing to FastAPI backend.
Export functions for each API call.

---

## Implementation Order

### MVP Implementation (Priority P0-P1)

| Step | Task | Priority | Files |
|------|------|----------|-------|
| 1 | Backend setup & database | P0 | `requirements.txt`, `database.py`, `models.py`, `schemas.py`, `main.py` |
| 2 | Accounts CRUD | P1 | `routers/accounts.py` |
| 3 | Categories CRUD | P0 | `routers/categories.py` |
| 4 | Statement parsers (Monzo CSV + Yonder PDF) | P0 | `services/monzo_parser.py`, `services/yonder_parser.py` |
| 5 | Transactions CRUD + upload | P0 | `routers/transactions.py` |
| 6 | Monthly reports + alerts | P0/P1 | `routers/reports.py` |
| 7 | Frontend setup | P0 | `package.json`, `App.jsx`, `api.js` |
| 8 | Core frontend components | P0 | `Dashboard.jsx`, `TransactionList.jsx`, `CSVUpload.jsx`, `CategoryManager.jsx` |
| 9 | Budget UI + alerts | P1 | `BudgetChart.jsx`, `Alerts.jsx` |

### Post-MVP Implementation (Priority P2-P3)

| Step | Task | Priority | Files |
|------|------|----------|-------|
| 10 | Recurring rules | P2 | `services/categorizer.py`, `routers/recurring_rules.py` |
| 11 | LLM categorization | P2 | `services/llm_categorizer.py`, `config.py` |
| 12 | Spending trends | P2 | `routers/reports.py` (extend), `TrendsChart.jsx` |
| 13 | Manual transaction entry | P3 | `TransactionForm.jsx` |
| 14 | Export functionality | P3 | `services/export.py`, `routers/export.py` |
| 15 | Refactor parsers (SOLID) | P3 | `services/base_parser.py`, `services/monzo_parser.py`, `services/yonder_parser.py` |
| 16 | Refactor exclusion rules | P3 | `models.py`, `routers/exclusion_rules.py` - store in DB with API |

---

## API Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/accounts` | Create account |
| GET | `/accounts` | List accounts |
| PATCH | `/accounts/{id}` | Update account |
| DELETE | `/accounts/{id}` | Delete account |
| POST | `/categories` | Create category |
| GET | `/categories` | List categories |
| PATCH | `/categories/{id}` | Update category |
| DELETE | `/categories/{id}` | Delete category |
| POST | `/transactions/upload/{account_id}` | Import statement (CSV/PDF) |
| GET | `/transactions` | List transactions |
| PATCH | `/transactions/{id}` | Update transaction |
| DELETE | `/transactions/{id}` | Delete transaction |
| POST | `/rules` | Create recurring rule |
| GET | `/rules` | List rules |
| DELETE | `/rules/{id}` | Delete rule |
| POST | `/transactions/categorize` | LLM categorize selected transactions |
| GET | `/reports/monthly` | Monthly report |
| GET | `/reports/trends` | Spending trends |

---

## Next Steps

Once you approve this plan, I'll implement the MVP first (steps 1-9), then iterate on post-MVP features. Let me know if you'd like to:

1. Adjust MVP scope (move features between MVP/post-MVP)
2. Change feature priorities
3. Modify tech stack or architecture
4. Proceed with MVP implementation
