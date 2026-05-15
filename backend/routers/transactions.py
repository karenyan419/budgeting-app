from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from datetime import date

from database import get_db
from models import Transaction, Account, RecurringRule, Category, BankType
from schemas import TransactionUpdate, Transaction as TransactionSchema
from services.monzo_parser import parse_monzo_csv
from services.yonder_parser import parse_yonder_csv
from services.categorizer import apply_rules
from services.exclusion_rules import should_exclude

router = APIRouter()


@router.get("/latest-dates")
def get_latest_dates(db: Session = Depends(get_db)):
    """Get the most recent transaction date per account."""
    results = (
        db.query(Account.id, Account.name, Account.bank, func.max(Transaction.date))
        .outerjoin(Transaction)
        .group_by(Account.id)
        .all()
    )
    return {
        row[1]: row[3].isoformat() if row[3] else None
        for row in results
    }


@router.post("/upload/{account_id}")
async def upload_statement(
    account_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a bank statement (CSV for Monzo, PDF for Yonder)."""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    content = await file.read()

    # Parse based on bank type
    if account.bank == BankType.monzo:
        transactions = parse_monzo_csv(content.decode("utf-8"))
    elif account.bank == BankType.yonder:
        transactions = parse_yonder_csv(content.decode("utf-8"))
    else:
        raise HTTPException(status_code=400, detail="Unsupported bank type")

    # Map source_category text to category_id where possible
    categories = db.query(Category).all()
    category_name_map = {cat.name.lower(): cat.id for cat in categories}
    for tx_data in transactions:
        if not tx_data.get("category_id") and tx_data.get("source_category"):
            matched_id = category_name_map.get(tx_data["source_category"].lower())
            if matched_id:
                tx_data["category_id"] = matched_id

    # Get all rules for auto-categorization (overrides source_category if matched)
    rules = db.query(RecurringRule).all()
    transactions = apply_rules(transactions, rules)

    # Insert transactions, skipping duplicates
    imported = 0
    skipped = 0
    excluded_count = 0

    for tx_data in transactions:
        # Check if transaction should be excluded from reports
        is_excluded = should_exclude(tx_data, account.bank.value, db)
        if is_excluded:
            excluded_count += 1

        tx = Transaction(
            account_id=account_id,
            date=tx_data["date"],
            description=tx_data["description"],
            amount=tx_data["amount"],
            source_category=tx_data.get("source_category"),
            hash=tx_data.get("hash"),
            category_id=tx_data.get("category_id"),
            is_recurring=tx_data.get("is_recurring", False),
            excluded=is_excluded,
        )
        db.add(tx)

        try:
            db.flush()
            imported += 1
        except IntegrityError:
            db.rollback()
            skipped += 1

    db.commit()

    return {
        "message": f"Imported {imported} transactions ({excluded_count} excluded from reports)",
        "imported": imported,
        "skipped": skipped,
        "excluded": excluded_count,
    }


@router.get("/")
def list_transactions(
    month: Optional[int] = Query(None, ge=1, le=12),
    year: Optional[int] = Query(None, ge=2000),
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    excluded: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """List transactions with optional filters."""
    query = db.query(Transaction)

    if month and year:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        query = query.filter(Transaction.date >= start_date, Transaction.date < end_date)

    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    if excluded is not None:
        query = query.filter(Transaction.excluded == excluded)

    rows = query.order_by(Transaction.date.desc()).all()

    # Attach category_name and account_name for convenience
    results = []
    for tx in rows:
        data = TransactionSchema.model_validate(tx).model_dump()
        data["category_name"] = tx.category.name if tx.category else None
        data["account_name"] = tx.account.name if tx.account else None
        results.append(data)

    return results


@router.get("/{transaction_id}", response_model=TransactionSchema)
def get_transaction(transaction_id: int, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx


@router.patch("/{transaction_id}", response_model=TransactionSchema)
def update_transaction(
    transaction_id: int,
    transaction: TransactionUpdate,
    db: Session = Depends(get_db)
):
    """Update transaction (change category, mark recurring, add notes)."""
    db_tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    update_data = transaction.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_tx, key, value)

    db.commit()
    db.refresh(db_tx)
    return db_tx


@router.delete("/{transaction_id}")
def delete_transaction(transaction_id: int, db: Session = Depends(get_db)):
    db_tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not db_tx:
        raise HTTPException(status_code=404, detail="Transaction not found")

    db.delete(db_tx)
    db.commit()
    return {"message": "Transaction deleted"}
