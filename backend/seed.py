"""Seed the database with default accounts, categories, and sample data."""
from database import engine, Base, SessionLocal
from models import Account, Category, ExclusionRule

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

try:
    # Check if already seeded
    if db.query(Account).first():
        print("Database already has data. Skipping seed.")
        print("Run 'POST /admin/clear-database' to reset if needed.")
        exit(0)

    # Create accounts
    accounts = [
        Account(name="Monzo", bank="monzo", type="current_account"),
        Account(name="Yonder", bank="yonder", type="credit_card"),
    ]
    db.add_all(accounts)
    print("✓ Created accounts: Monzo, Yonder")

    # Create categories with monthly budgets
    categories = [
        Category(name="Transport", monthly_budget=150.00),
        Category(name="Groceries", monthly_budget=400.00),
        Category(name="Eating Out", monthly_budget=200.00),
        Category(name="Entertainment", monthly_budget=100.00),
        Category(name="Shopping", monthly_budget=150.00),
        Category(name="Bills", monthly_budget=500.00),
        Category(name="Health", monthly_budget=50.00),
        Category(name="Other", monthly_budget=100.00),
        Category(name="Personal Care", monthly_budget=50.00),
        Category(name="Holiday", monthly_budget=200.00),
        Category(name="Charity", monthly_budget=25.00),
        Category(name="Finances", monthly_budget=50.00),
        Category(name="General", monthly_budget=100.00),
    ]
    db.add_all(categories)
    print("✓ Created 13 categories with budgets")

    # Create common exclusion rules (internal transfers, not real spending)
    exclusions = [
        ExclusionRule(
            description_pattern="yonder",
            bank="monzo",
            notes="Credit card payment from Monzo"
        ),
        ExclusionRule(
            description_pattern="monzo",
            bank="yonder",
            notes="Payment received from Monzo"
        ),
    ]
    db.add_all(exclusions)
    print("✓ Created exclusion rules for internal transfers")

    db.commit()
    print("\n✅ Database seeded successfully!")
    print("\nNext steps:")
    print("  1. Start the server: uvicorn main:app --reload")
    print("  2. Upload transactions: POST /transactions/upload/{account_id}")
    print("     - Account 1 = Monzo")
    print("     - Account 2 = Yonder")

except Exception as e:
    db.rollback()
    print(f"Error seeding database: {e}")
finally:
    db.close()
