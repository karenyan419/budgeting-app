from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import ExclusionRule, Transaction, Account
from schemas import ExclusionRuleCreate, ExclusionRuleUpdate, ExclusionRule as ExclusionRuleSchema
from services.exclusion_rules import should_exclude

router = APIRouter()


@router.post("/", response_model=ExclusionRuleSchema)
def create_exclusion_rule(rule: ExclusionRuleCreate, db: Session = Depends(get_db)):
    """Create a new exclusion rule."""
    db_rule = ExclusionRule(
        description_pattern=rule.description_pattern,
        bank=rule.bank,
        amount=rule.amount,
        notes=rule.notes
    )
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.get("/", response_model=List[ExclusionRuleSchema])
def list_exclusion_rules(db: Session = Depends(get_db)):
    """List all exclusion rules."""
    return db.query(ExclusionRule).all()


@router.get("/{rule_id}", response_model=ExclusionRuleSchema)
def get_exclusion_rule(rule_id: int, db: Session = Depends(get_db)):
    """Get a specific exclusion rule."""
    rule = db.query(ExclusionRule).filter(ExclusionRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Exclusion rule not found")
    return rule


@router.patch("/{rule_id}", response_model=ExclusionRuleSchema)
def update_exclusion_rule(rule_id: int, rule_update: ExclusionRuleUpdate, db: Session = Depends(get_db)):
    """Update an exclusion rule."""
    db_rule = db.query(ExclusionRule).filter(ExclusionRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Exclusion rule not found")

    update_data = rule_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_rule, field, value)

    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/{rule_id}")
def delete_exclusion_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete an exclusion rule."""
    db_rule = db.query(ExclusionRule).filter(ExclusionRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Exclusion rule not found")

    db.delete(db_rule)
    db.commit()
    return {"message": "Exclusion rule deleted"}


@router.post("/apply-all")
def apply_all_exclusion_rules(db: Session = Depends(get_db)):
    """Re-apply all exclusion rules to every transaction. Resets excluded flag first."""
    transactions = db.query(Transaction).all()
    accounts = {a.id: a for a in db.query(Account).all()}

    excluded_count = 0
    for tx in transactions:
        account = accounts.get(tx.account_id)
        bank = account.bank.value if account else ""
        tx_data = {"description": tx.description, "amount": tx.amount}
        tx.excluded = should_exclude(tx_data, bank, db)
        if tx.excluded:
            excluded_count += 1

    db.commit()
    return {
        "message": f"Applied rules to {len(transactions)} transactions",
        "total": len(transactions),
        "excluded": excluded_count,
    }


@router.post("/reset")
def reset_exclusions(db: Session = Depends(get_db)):
    """Clear all excluded flags on every transaction."""
    count = db.query(Transaction).filter(Transaction.excluded == True).update(
        {Transaction.excluded: False}, synchronize_session="fetch"
    )
    db.commit()
    return {"message": f"Reset {count} transactions to not excluded", "reset": count}
