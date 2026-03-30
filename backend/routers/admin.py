from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from dateutil.relativedelta import relativedelta

from database import get_db
from models import Transaction, Category, Account, RecurringRule

router = APIRouter()


@router.get("/data-coverage")
def data_coverage(db: Session = Depends(get_db)):
    """
    Show which time periods have data and identify gaps.
    Helps you know which statements you need to upload.
    """
    accounts = db.query(Account).all()

    if not accounts:
        return {
            "message": "No accounts found. Create accounts first.",
            "accounts": []
        }

    result = []

    for account in accounts:
        # Get date range for this account
        stats = db.query(
            func.min(Transaction.date).label("earliest"),
            func.max(Transaction.date).label("latest"),
            func.count(Transaction.id).label("count")
        ).filter(Transaction.account_id == account.id).first()

        if not stats.earliest:
            result.append({
                "account_id": account.id,
                "account_name": account.name,
                "bank": account.bank.value,
                "status": "no_data",
                "message": "No transactions uploaded yet",
                "transactions": 0,
                "covered_months": [],
                "missing_months": []
            })
            continue

        # Find which months have data
        months_with_data = db.query(
            func.strftime("%Y-%m", Transaction.date).label("month")
        ).filter(
            Transaction.account_id == account.id
        ).distinct().all()

        covered_months = sorted([m.month for m in months_with_data])

        # Find gaps between earliest and latest
        missing_months = []
        current = date(stats.earliest.year, stats.earliest.month, 1)
        end = date(stats.latest.year, stats.latest.month, 1)

        while current <= end:
            month_str = current.strftime("%Y-%m")
            if month_str not in covered_months:
                missing_months.append(month_str)
            current += relativedelta(months=1)

        # Check if we're missing recent months (up to current month)
        today = date.today()
        current_month = date(today.year, today.month, 1)
        latest_month = date(stats.latest.year, stats.latest.month, 1)

        months_behind = []
        check = latest_month + relativedelta(months=1)
        while check <= current_month:
            months_behind.append(check.strftime("%Y-%m"))
            check += relativedelta(months=1)

        result.append({
            "account_id": account.id,
            "account_name": account.name,
            "bank": account.bank.value,
            "status": "has_data",
            "transactions": stats.count,
            "date_range": {
                "earliest": str(stats.earliest),
                "latest": str(stats.latest)
            },
            "covered_months": covered_months,
            "missing_months": missing_months,
            "months_to_upload": months_behind
        })

    return {
        "message": "Data coverage by account",
        "accounts": result
    }


@router.post("/clear-database")
def clear_database(db: Session = Depends(get_db)):
    """
    Clear all data from the database.
    WARNING: This deletes all transactions, categories, accounts, and rules.
    """
    # Delete in order to respect foreign key constraints
    deleted_transactions = db.query(Transaction).delete()
    deleted_rules = db.query(RecurringRule).delete()
    deleted_categories = db.query(Category).delete()
    deleted_accounts = db.query(Account).delete()

    db.commit()

    return {
        "message": "Database cleared",
        "deleted": {
            "transactions": deleted_transactions,
            "recurring_rules": deleted_rules,
            "categories": deleted_categories,
            "accounts": deleted_accounts,
        }
    }
