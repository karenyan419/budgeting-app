from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import RecurringRule, Category
from schemas import RecurringRuleCreate, RecurringRule as RecurringRuleSchema

router = APIRouter()


@router.post("/", response_model=RecurringRuleSchema)
def create_rule(rule: RecurringRuleCreate, db: Session = Depends(get_db)):
    """Create a new recurring rule for auto-categorization."""
    # Verify category exists
    category = db.query(Category).filter(Category.id == rule.category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    db_rule = RecurringRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.get("/", response_model=list[RecurringRuleSchema])
def list_rules(db: Session = Depends(get_db)):
    """List all recurring rules."""
    return db.query(RecurringRule).all()


@router.get("/{rule_id}", response_model=RecurringRuleSchema)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(RecurringRule).filter(RecurringRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    return rule


@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    """Delete a recurring rule."""
    db_rule = db.query(RecurringRule).filter(RecurringRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    db.delete(db_rule)
    db.commit()
    return {"message": "Rule deleted"}
