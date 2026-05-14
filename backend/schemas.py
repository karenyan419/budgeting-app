from __future__ import annotations
from pydantic import BaseModel
from datetime import date, datetime
from enum import Enum
from typing import Optional, List


class BankType(str, Enum):
    monzo = "monzo"
    yonder = "yonder"


class AccountType(str, Enum):
    current_account = "current_account"
    credit_card = "credit_card"


# Account schemas
class AccountCreate(BaseModel):
    name: str
    bank: BankType
    type: AccountType


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    bank: Optional[BankType] = None
    type: Optional[AccountType] = None


class Account(BaseModel):
    id: int
    name: str
    bank: BankType
    type: AccountType

    model_config = {"from_attributes": True}


# Category schemas
class CategoryCreate(BaseModel):
    name: str
    monthly_budget: Optional[float] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    monthly_budget: Optional[float] = None


class Category(BaseModel):
    id: int
    name: str
    monthly_budget: Optional[float] = None

    model_config = {"from_attributes": True}


# Transaction schemas
class TransactionCreate(BaseModel):
    account_id: int
    category_id: Optional[int] = None
    amount: float
    date: date
    description: str
    is_recurring: bool = False
    source_category: Optional[str] = None
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    category_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    notes: Optional[str] = None
    excluded: Optional[bool] = None


class Transaction(BaseModel):
    id: int
    account_id: int
    category_id: Optional[int] = None
    amount: float
    date: date
    description: str
    is_recurring: bool
    source_category: Optional[str] = None
    hash: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    excluded: bool = False

    model_config = {"from_attributes": True}


# Recurring rule schemas
class RecurringRuleCreate(BaseModel):
    description_pattern: str
    category_id: int
    mark_recurring: bool = False


class RecurringRule(BaseModel):
    id: int
    description_pattern: str
    category_id: int
    mark_recurring: bool

    model_config = {"from_attributes": True}


# Report schemas
class CategorySpending(BaseModel):
    category_id: int
    category_name: str
    spent: float
    budget: Optional[float] = None
    percentage_used: Optional[float] = None
    over_budget: bool = False


class MonthlyReport(BaseModel):
    month: int
    year: int
    total_spent: float
    categories: List[CategorySpending]


# Exclusion rule schemas
# Auth schemas
class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# Exclusion rule schemas
class ExclusionRuleCreate(BaseModel):
    description_pattern: str
    bank: Optional[BankType] = None
    amount: Optional[float] = None
    notes: Optional[str] = None


class ExclusionRuleUpdate(BaseModel):
    description_pattern: Optional[str] = None
    bank: Optional[BankType] = None
    amount: Optional[float] = None
    notes: Optional[str] = None


class ExclusionRule(BaseModel):
    id: int
    description_pattern: str
    bank: Optional[BankType] = None
    amount: Optional[float] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}
