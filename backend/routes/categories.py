from flask import Blueprint, request, jsonify
from ..models import Category
from ..extensions import db

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    return jsonify([c.to_dict() for c in categories])

@categories_bp.route('/', methods=['POST'])
def add_category():
    data = request.get_json()
    new_cat = Category(
        name=data['name'],
        color=data.get('color', '#000000'),
        icon=data.get('icon', 'fa-tag')
    )
    db.session.add(new_cat)
    db.session.commit()
    return jsonify(new_cat.to_dict()), 201

@categories_bp.route('/<int:id>', methods=['GET'])
def get_category(id):
    cat = Category.query.get_or_404(id)
    return jsonify(cat.to_dict())

@categories_bp.route('/<int:id>', methods=['PUT', 'PATCH'])
def update_category(id):
    cat = Category.query.get_or_404(id)
    data = request.get_json()
    if 'name' in data:
        cat.name = data['name']
    if 'color' in data:
        cat.color = data['color']
    if 'icon' in data:
        cat.icon = data['icon']
    db.session.commit()
    return jsonify(cat.to_dict())

@categories_bp.route('/<int:id>', methods=['DELETE'])
def delete_category(id):
    cat = Category.query.get_or_404(id)
    db.session.delete(cat)
    db.session.commit()
    return jsonify({'message': 'Category deleted'})
