"""
Exclusion Rules for Reports

These rules define transactions that should be excluded from spending reports
to avoid double-counting or exclude personal transfers.

Rules:
- Payments from Monzo to Yonder (credit card bill payments)
- Rent income from Chloe Tong (£500/month)
- Direct debit to Kathy Yan (£300/month)
- All transactions to/from Karen Yan or K Yan (self-transfers)
- All InvestEngine transactions (investments)
"""

# Patterns to exclude from spending reports
# Format: (account_bank, description_pattern, amount_or_none)
# - account_bank: 'monzo', 'yonder', or None to match any bank
# - amount_or_none: specific amount to match, or None to match any amount
EXCLUSION_PATTERNS = [
    # Credit card bill payments (any amount)
    ("monzo", "yonder", None),

    # Personal transfers (specific amounts)
    ("monzo", "chloe tong", 500.00),    # Rent income
    ("monzo", "kathy yan", 300.00),      # Monthly direct debit

    # Self-transfers (any amount)
    (None, "karen yan", None),
    (None, "k yan", None),

    # Investments (any amount)
    (None, "investengine", None),
]


def should_exclude(transaction, account_bank: str) -> bool:
    """
    Check if a transaction should be excluded from spending reports.

    Args:
        transaction: Transaction object with 'description' and 'amount'
        account_bank: The bank type ('monzo' or 'yonder')

    Returns:
        True if transaction should be excluded
    """
    description = transaction.description.lower() if hasattr(transaction, 'description') else transaction.get('description', '').lower()
    amount = abs(transaction.amount if hasattr(transaction, 'amount') else transaction.get('amount', 0))

    for bank, pattern, match_amount in EXCLUSION_PATTERNS:
        # Check bank match (None means any bank)
        if bank is not None and account_bank != bank:
            continue
        if pattern not in description:
            continue
        # If match_amount is None, match any amount
        # Otherwise, match specific amount (with small tolerance for floats)
        if match_amount is None or abs(amount - match_amount) < 0.01:
            return True

    return False
