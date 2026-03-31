from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import ExclusionRule
from schemas import ExclusionRuleCreate, ExclusionRuleUpdate, ExclusionRule as ExclusionRuleSchema

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
