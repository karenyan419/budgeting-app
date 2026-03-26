from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base


class BankType(enum.Enum):
    monzo = "monzo"
    yonder = "yonder"


class AccountType(enum.Enum):
    current_account = "current_account"
    credit_card = "credit_card"


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    bank = Column(Enum(BankType), nullable=False)
    type = Column(Enum(AccountType), nullable=False)

    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    monthly_budget = Column(Float, nullable=True)

    transactions = relationship("Transaction", back_populates="category")
    recurring_rules = relationship("RecurringRule", back_populates="category")


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=False)
    is_recurring = Column(Boolean, default=False)

    # Additional fields
    source_category = Column(String, nullable=True)  # Original category from bank (e.g. Monzo)
    hash = Column(String, unique=True, nullable=True, index=True)  # For duplicate detection
    notes = Column(String, nullable=True)  # User annotations
    created_at = Column(DateTime, default=datetime.utcnow)
    excluded = Column(Boolean, default=False)  # Exclude from reports

    account = relationship("Account", back_populates="transactions")
    category = relationship("Category", back_populates="transactions")


class RecurringRule(Base):
    __tablename__ = "recurring_rules"

    id = Column(Integer, primary_key=True, index=True)
    description_pattern = Column(String, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    mark_recurring = Column(Boolean, default=False)

    category = relationship("Category", back_populates="recurring_rules")
