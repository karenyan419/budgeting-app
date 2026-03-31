"""
Exclusion Rules Service

Checks transactions against exclusion rules stored in the database.
Excluded transactions are marked but still stored - they just don't appear in reports.
"""
from sqlalchemy.orm import Session
from models import ExclusionRule


def should_exclude(transaction, account_bank: str, db: Session) -> bool:
    """
    Check if a transaction should be excluded from spending reports.

    Args:
        transaction: Transaction dict with 'description' and 'amount'
        account_bank: The bank type ('monzo' or 'yonder')
        db: Database session to query exclusion rules

    Returns:
        True if transaction should be excluded
    """
    description = transaction.get('description', '').lower()
    amount = abs(transaction.get('amount', 0))

    # Get all exclusion rules from database
    rules = db.query(ExclusionRule).all()

    for rule in rules:
        # Check bank match (None means any bank)
        if rule.bank is not None and rule.bank.value != account_bank:
            continue

        # Check description pattern match
        if rule.description_pattern.lower() not in description:
            continue

        # Check amount match (None means any amount)
        if rule.amount is not None and abs(amount - rule.amount) >= 0.01:
            continue

        return True

    return False
