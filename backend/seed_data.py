from backend.app import create_app, db
from backend.models import Transaction, Budget, Category
from datetime import datetime, timedelta
import random

app = create_app()

def seed():
    with app.app_context():
        print("Seeding data...")
        # Clear existing data
        db.session.query(Transaction).delete()
        db.session.query(Budget).delete()
        
        # Ensure categories exist (fetching them)
        categories = {c.name: c for c in Category.query.all()}
        
        if not categories:
            print("No categories found. Run init_db.py first.")
            return

        # Base date: 1st of 6 months ago
        today = datetime.now()
        start_date = today - timedelta(days=180)
        
        transactions = []
        
        # Helper to find date for a specific month
        def get_date(month_offset, day):
            d = start_date + timedelta(days=month_offset*30)
            try:
                return datetime(d.year, d.month, day)
            except ValueError:
                return datetime(d.year, d.month, 1)

        for i in range(7): # Past 6 months + current
            month_date = start_date + timedelta(days=i*30)
            month = month_date.month
            year = month_date.year
            
            # 1. Salary (Income) - 1st of month
            transactions.append(Transaction(
                amount=3200.00,
                date=datetime(year, month, 1),
                description="Monthly Salary",
                type="income",
                category_id=categories['Salary'].id
            ))
            
            # 2. Rent (Expense) - 2nd of month
            transactions.append(Transaction(
                amount=1200.00,
                date=datetime(year, month, 2),
                description="Rent Payment",
                type="expense",
                category_id=categories['Rent'].id
            ))
            
            # 3. Transport Ticket (Expense) - 3rd of month
            transactions.append(Transaction(
                amount=89.00,
                date=datetime(year, month, 3),
                description="Public Transport Ticket",
                type="expense",
                category_id=categories['Transport'].id
            ))
            
            # 4. Variable Expenses (Food)
            # ~8-10 food transactions per month
            for _ in range(random.randint(8, 12)):
                day = random.randint(1, 28)
                amount = round(random.uniform(15.0, 120.0), 2)
                transactions.append(Transaction(
                    amount=amount,
                    date=datetime(year, month, day),
                    description=random.choice(["Supermarket", "Lunch", "Dinner", "Groceries", "Snacks", "Coffee", "Bakery"]),
                    type="expense",
                    category_id=categories['Food'].id
                ))
                
            # 5. Variable Expenses (Entertainment)
            # ~3-5 entertainment transactions
            for _ in range(random.randint(3, 6)):
                day = random.randint(1, 28)
                amount = round(random.uniform(20.0, 150.0), 2)
                transactions.append(Transaction(
                    amount=amount,
                    date=datetime(year, month, day),
                    description=random.choice(["Cinema", "Concert", "Steam Game", "Netflix", "Bar", "Club", "Spotify"]),
                    type="expense",
                    category_id=categories['Entertainment'].id
                ))

        # Add budgets for current month
        budgets = [
            Budget(category_id=categories['Food'].id, monthly_limit=600.0, month=today.month, year=today.year),
            Budget(category_id=categories['Entertainment'].id, monthly_limit=300.0, month=today.month, year=today.year),
            Budget(category_id=categories['Transport'].id, monthly_limit=100.0, month=today.month, year=today.year),
            Budget(category_id=categories['Rent'].id, monthly_limit=1300.0, month=today.month, year=today.year)
        ]
        
        db.session.add_all(transactions)
        db.session.commit() # Commit transactions first
        
        db.session.add_all(budgets)
        db.session.commit()
        print(f"Database seeded! Added {len(transactions)} transactions and {len(budgets)} budgets.")

if __name__ == "__main__":
    seed()
