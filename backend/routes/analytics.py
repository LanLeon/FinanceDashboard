from flask import Blueprint, jsonify, request

analytics_bp = Blueprint('analytics', __name__)

from ..models import Transaction, Category, db
from sqlalchemy import func
from datetime import datetime, timedelta

@analytics_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    today = datetime.utcnow()
    month = request.args.get('month', today.month, type=int)
    year = request.args.get('year', today.year, type=int)
    
    # 1. Spending Donut Data (Expenses by Category for current month)
    spending_by_category = db.session.query(
        Category.name,
        Category.color,
        func.sum(Transaction.amount)
    ).join(Transaction).filter(
        Transaction.type == 'expense',
        db.extract('month', Transaction.date) == month,
        db.extract('year', Transaction.date) == year
    ).group_by(Category.id).all()
    
    donut_data = {
        'labels': [item[0] for item in spending_by_category],
        'colors': [item[1] for item in spending_by_category],
        'values': [item[2] for item in spending_by_category]
    }
    
    # 2. Cashflow Line Chart (Last 6 months)
    cashflow_data = {
        'labels': [],
        'income': [],
        'expense': []
    }
    
    for i in range(5, -1, -1):
        # Loop over the last 6 months
        m = (month - i - 1) % 12 + 1
        y = year + (month - i - 1) // 12
        if month - i <= 0:
            y = year - 1
            m = month - i + 12
        else:
            y = year
            m = month - i
            
        month_name = datetime(y, m, 1).strftime('%b')
        cashflow_data['labels'].append(month_name)
        
        inc = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'income',
            db.extract('month', Transaction.date) == m,
            db.extract('year', Transaction.date) == y
        ).scalar() or 0
        
        exp = db.session.query(func.sum(Transaction.amount)).filter(
            Transaction.type == 'expense',
            db.extract('month', Transaction.date) == m,
            db.extract('year', Transaction.date) == y
        ).scalar() or 0
        
        cashflow_data['income'].append(inc)
        cashflow_data['expense'].append(exp)

    return jsonify({
        'donut': donut_data,
        'cashflow': cashflow_data
    })
