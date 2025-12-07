from flask import Blueprint, request, jsonify
from models import db, Item

items_bp = Blueprint("items", __name__, url_prefix="/items")

#all items
@items_bp.get("/")
def get_items():
    category = request.args.get("category")

    query = Item.query
    
    if category:
        query = query.filter_by(category=category)
    items = query.order_by(Item.created_at.desc()).all()
    return jsonify([item.to_dict() for item in items]), 200

#one item
@items_bp.get("/<int:item_id>")
def get_item(item_id):
    item = Item.query.get_or_404(item_id)
    return jsonify(item.to_dict()), 200

@items_bp.post("/")
def create_item():
    data = request.get_json()

    item = Item(title=data["title"], description=data["description"], price=data["price"], address=data["address"], image=data.get("image"), category=data["category"])

    db.session.add(item)
    db.session.commit()

    return jsonify(item.to_dict()), 200

@items_bp.delete("/<int:item_id>")
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    return jsonify({"message": "Item deleted"}), 200    