import csv
import hashlib
from datetime import datetime
from io import StringIO


def parse_yonder_csv(file_content: str) -> list[dict]:
    """
    Parse Yonder CSV export.

    Columns:
    - 0: Date/Time of transaction (ISO format)
    - 1: Description
    - 2: Amount (GBP)
    - 5: Category
    - 6: Debit or Credit
    """
    transactions = []

    reader = csv.reader(StringIO(file_content))
    header = next(reader)  # Skip header row

    for row in reader:
        if len(row) < 7:
            continue

        date_str = row[0]
        description = row[1]
        amount_str = row[2]
        category = row[5]
        debit_credit = row[6]

        # Parse date (ISO format: 2026-03-18T13:55:20.413736)
        try:
            date = datetime.fromisoformat(date_str).date()
        except ValueError:
            continue

        # Parse amount
        try:
            amount = float(amount_str)
            # Make expenses negative
            if debit_credit == "Debit":
                amount = -abs(amount)
        except ValueError:
            continue

        # Skip zero amounts
        if amount == 0:
            continue

        # Generate hash for duplicate detection
        hash_input = f"{date_str}|{description}|{amount_str}"
        tx_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]

        transactions.append({
            "date": date,
            "description": description,
            "amount": amount,
            "source_category": category if category else None,
            "hash": tx_hash,
        })

    return transactions
