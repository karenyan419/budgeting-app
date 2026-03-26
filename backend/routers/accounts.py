from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Account
from schemas import AccountCreate, AccountUpdate, Account as AccountSchema

router = APIRouter()


@router.post("/", response_model=AccountSchema)
def create_account(account: AccountCreate, db: Session = Depends(get_db)):
    db_account = Account(**account.model_dump())
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account


@router.get("/", response_model=list[AccountSchema])
def list_accounts(db: Session = Depends(get_db)):
    return db.query(Account).all()


@router.get("/{account_id}", response_model=AccountSchema)
def get_account(account_id: int, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.patch("/{account_id}", response_model=AccountSchema)
def update_account(account_id: int, account: AccountUpdate, db: Session = Depends(get_db)):
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    update_data = account.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_account, key, value)

    db.commit()
    db.refresh(db_account)
    return db_account


@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    db_account = db.query(Account).filter(Account.id == account_id).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")

    db.delete(db_account)
    db.commit()
    return {"message": "Account deleted"}
