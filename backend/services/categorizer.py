from models import RecurringRule


def apply_rules(transactions: list[dict], rules: list[RecurringRule]) -> list[dict]:
    """
    Apply recurring rules to auto-categorize transactions.

    For each transaction, check if description matches any rule pattern.
    If matched, set category_id and is_recurring flag.
    """
    for tx in transactions:
        description = tx.get("description", "").lower()

        for rule in rules:
            pattern = rule.description_pattern.lower()

            if pattern in description:
                tx["category_id"] = rule.category_id
                if rule.mark_recurring:
                    tx["is_recurring"] = True
                break  # Stop after first match

    return transactions
