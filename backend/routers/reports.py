from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date

from database import get_db
from models import Transaction, Category, Account
from schemas import MonthlyReport, CategorySpending

router = APIRouter()


@router.get("/monthly", response_model=MonthlyReport)
def monthly_report(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2000),
    db: Session = Depends(get_db)
):
    """
    Get monthly spending report.
    Returns total spent (net of refunds), spending by category with budget comparison,
    and alerts for categories over budget.

    Note: Transactions with excluded=True are not included.
    """
    # Calculate date range
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    # Get all categories
    categories = db.query(Category).all()

    # Get net spending by category (expenses + refunds, not excluded)
    spending_query = (
        db.query(
            Transaction.category_id,
            func.sum(Transaction.amount).label("total")
        )
        .filter(
            Transaction.date >= start_date,
            Transaction.date < end_date,
            Transaction.excluded == False
        )
        .group_by(Transaction.category_id)
        .all()
    )

    # Build spending map (abs of net negative amounts; if net positive, treat as 0 spent)
    spending_map = {}
    for row in spending_query:
        net = row.total
        spending_map[row.category_id] = abs(net) if net < 0 else 0

    # Get uncategorized spending
    uncategorized_spent = spending_map.get(None, 0)

    # Build category spending list
    category_spending = []

    for cat in categories:
        spent = spending_map.get(cat.id, 0)
        budget = cat.monthly_budget

        percentage_used = None
        over_budget = False

        if budget and budget > 0:
            percentage_used = round((spent / budget) * 100, 1)
            over_budget = spent > budget

        category_spending.append(CategorySpending(
            category_id=cat.id,
            category_name=cat.name,
            spent=round(spent, 2),
            budget=budget,
            percentage_used=percentage_used,
            over_budget=over_budget,
        ))

    # Add uncategorized if there's spending
    if uncategorized_spent > 0:
        category_spending.append(CategorySpending(
            category_id=0,
            category_name="Uncategorized",
            spent=round(uncategorized_spent, 2),
            budget=None,
            percentage_used=None,
            over_budget=False,
        ))

    # Calculate total spent
    total_spent = sum(cs.spent for cs in category_spending)

    return MonthlyReport(
        month=month,
        year=year,
        total_spent=round(total_spent, 2),
        categories=category_spending,
    )


@router.get("/trends")
def spending_trends(
    months: int = Query(6, ge=1, le=24),
    db: Session = Depends(get_db)
):
    """
    Get spending trends over the last N months.

    Note: Transactions with excluded=True are not included.
    """
    from datetime import datetime
    from dateutil.relativedelta import relativedelta

    today = datetime.now().date()
    trends = []

    for i in range(months - 1, -1, -1):
        target_date = today - relativedelta(months=i)
        month = target_date.month
        year = target_date.year

        # Calculate date range
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        # Get net spending for month (not excluded)
        result = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.date >= start_date,
                Transaction.date < end_date,
                Transaction.excluded == False
            )
            .scalar()
        )

        total = abs(result) if result and result < 0 else 0

        # Get net spending by account
        account_results = (
            db.query(Account.name, func.sum(Transaction.amount))
            .join(Transaction)
            .filter(
                Transaction.date >= start_date,
                Transaction.date < end_date,
                Transaction.excluded == False
            )
            .group_by(Account.name)
            .all()
        )
        by_account = {name: round(abs(spent), 2) for name, spent in account_results if spent < 0}

        # Get net spending by category
        category_results = (
            db.query(Category.name, func.sum(Transaction.amount))
            .join(Transaction, Transaction.category_id == Category.id)
            .filter(
                Transaction.date >= start_date,
                Transaction.date < end_date,
                Transaction.excluded == False
            )
            .group_by(Category.name)
            .all()
        )
        by_category = {name: round(abs(spent), 2) for name, spent in category_results if spent < 0}

        # Add uncategorized
        uncategorized = (
            db.query(func.sum(Transaction.amount))
            .filter(
                Transaction.date >= start_date,
                Transaction.date < end_date,
                Transaction.excluded == False,
                Transaction.category_id == None
            )
            .scalar()
        )
        if uncategorized and uncategorized < 0:
            by_category["Uncategorized"] = round(abs(uncategorized), 2)

        trends.append({
            "month": month,
            "year": year,
            "total_spent": round(total, 2),
            "by_account": by_account,
            "by_category": by_category,
        })

    return trends
