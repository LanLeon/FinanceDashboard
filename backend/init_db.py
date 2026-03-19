from backend.app import create_app, db
from backend.models import Category

def init_db():
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # Check if categories exist
        if not Category.query.first():
            print("Seeding default categories...")
            defaults = [
                {'name': 'Food', 'color': '#FF5733', 'icon': 'fa-utensils'},
                {'name': 'Rent', 'color': '#33FF57', 'icon': 'fa-home'},
                {'name': 'Transport', 'color': '#3357FF', 'icon': 'fa-bus'},
                {'name': 'Entertainment', 'color': '#F333FF', 'icon': 'fa-gamepad'},
                {'name': 'Salary', 'color': '#33FFF5', 'icon': 'fa-money-bill-wave'},
            ]
            
            for cat_data in defaults:
                cat = Category(**cat_data)
                db.session.add(cat)
            
            db.session.commit()
            print("Database initialized with default categories.")
        else:
            print("Database already initialized.")

if __name__ == '__main__':
    init_db()
