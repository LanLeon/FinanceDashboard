from flask import Blueprint, request, jsonify
from ..models import Transaction, Category
from ..extensions import db
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__)

@transactions_bp.route('/', methods=['GET'])
def get_transactions():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_query = request.args.get('search', '')

    query = Transaction.query.order_by(Transaction.date.desc())

    if search_query:
        query = query.join(Category).filter(
            (Transaction.description.ilike(f'%{search_query}%')) |
            (Category.name.ilike(f'%{search_query}%'))
        )

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'transactions': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })

@transactions_bp.route('/', methods=['POST'])
def add_transaction():
    data = request.get_json()
    try:
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
        new_trans = Transaction(
            amount=float(data['amount']),
            date=date_obj,
            description=data.get('description', ''),
            type=data['type'],
            category_id=data['category_id']
        )
        db.session.add(new_trans)
        db.session.commit()
        return jsonify(new_trans.to_dict()), 201
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@transactions_bp.route('/<int:id>', methods=['GET'])
def get_transaction(id):
    trans = Transaction.query.get_or_404(id)
    return jsonify(trans.to_dict())

@transactions_bp.route('/<int:id>', methods=['PUT', 'PATCH'])
def update_transaction(id):
    trans = Transaction.query.get_or_404(id)
    data = request.get_json()
    try:
        if 'amount' in data:
            trans.amount = float(data['amount'])
        if 'date' in data:
            trans.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        if 'description' in data:
            trans.description = data['description']
        if 'type' in data:
            trans.type = data['type']
        if 'category_id' in data:
            trans.category_id = data['category_id']
        db.session.commit()
        return jsonify(trans.to_dict())
    except (ValueError, KeyError) as e:
        return jsonify({'error': str(e)}), 400

@transactions_bp.route('/<int:id>', methods=['DELETE'])
def delete_transaction(id):
    trans = Transaction.query.get_or_404(id)
    db.session.delete(trans)
    db.session.commit()
    return jsonify({'message': 'Transaction deleted'})

@transactions_bp.route('/bulk-delete', methods=['POST'])
def bulk_delete():
    data = request.get_json()
    ids = data.get('ids', [])
    if ids:
        Transaction.query.filter(Transaction.id.in_(ids)).delete(synchronize_session=False)
        db.session.commit()
    return jsonify({'message': f'{len(ids)} transactions deleted'})
