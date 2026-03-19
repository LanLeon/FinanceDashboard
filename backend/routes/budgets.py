from flask import Blueprint, request, jsonify
from datetime import datetime
from ..models import Budget, Transaction
from ..extensions import db

budgets_bp = Blueprint('budgets', __name__)

@budgets_bp.route('/', methods=['GET'])
def get_budgets():
    month = request.args.get('month', datetime.utcnow().month, type=int)
    year = request.args.get('year', datetime.utcnow().year, type=int)

    budgets = Budget.query.filter_by(month=month, year=year).all()
    results = []
    
    for budget in budgets:
        # Calculate spending for this category in this month
        spending = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.category_id == budget.category_id,
            Transaction.type == 'expense',
            db.extract('month', Transaction.date) == month,
            db.extract('year', Transaction.date) == year
        ).scalar() or 0.0

        burn_rate = (spending / budget.monthly_limit) * 100 if budget.monthly_limit > 0 else 0
        
        b_dict = budget.to_dict()
        b_dict['spent'] = spending
        b_dict['burn_rate'] = burn_rate
        b_dict['category_name'] = budget.category.name
        b_dict['category_color'] = budget.category.color
        results.append(b_dict)
        
    return jsonify(results)

@budgets_bp.route('/', methods=['POST'])
def set_budget():
    data = request.get_json()
    month = data.get('month', datetime.utcnow().month)
    year = data.get('year', datetime.utcnow().year)
    
    # Check if budget already exists
    existing = Budget.query.filter_by(
        category_id=data['category_id'],
        month=month,
        year=year
    ).first()
    
    if existing:
        existing.monthly_limit = float(data['monthly_limit'])
        db.session.commit()
        return jsonify(existing.to_dict())
    
    new_budget = Budget(
        category_id=data['category_id'],
        monthly_limit=float(data['monthly_limit']),
        month=month,
        year=year
    )
    db.session.add(new_budget)
    db.session.commit()
    return jsonify(new_budget.to_dict()), 201

@budgets_bp.route('/<int:id>', methods=['DELETE'])
def delete_budget(id):
    budget = Budget.query.get_or_404(id)
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'message': 'Budget deleted'})
