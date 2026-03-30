import csv
import hashlib
from datetime import datetime
from io import StringIO


def parse_monzo_csv(file_content: str) -> list[dict]:
    """
    Parse Monzo CSV export.

    Columns:
    - 0: Transaction ID
    - 1: Date (DD/MM/YYYY)
    - 4: Name (description)
    - 6: Category (Monzo's category)
    - 7: Amount (negative = expense)
    """
    transactions = []

    if not file_content.strip():
        return transactions

    reader = csv.reader(StringIO(file_content))
    try:
        header = next(reader)  # Skip header row
    except StopIteration:
        return transactions

    for row in reader:
        if len(row) < 8:
            continue

        date_str = row[1]
        description = row[4]
        category = row[6]
        amount_str = row[7]

        try:
            date = datetime.strptime(date_str, "%d/%m/%Y").date()
            amount = float(amount_str)
        except (ValueError, IndexError):
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
