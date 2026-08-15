from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from models import User, db

product_routes = Blueprint("products", __name__)
user_routes = Blueprint("users", __name__)

HARDCODED_PRODUCTS = [
    {"id": 1, "name": "wireless mouse", "price": 18.50, "category": "electronics"},
    {"id": 2, "name": "mechanical keyboard", "price": 79.99, "category": "electronics"},
    {"id": 3, "name": "usb-c hub 7 in 1", "price": 42.00, "category": "electronics"},
    {"id": 4, "name": "noise cancelling headphones", "price": 199.00, "category": "electronics"},
    {"id": 5, "name": "ceramic coffee mug 350ml", "price": 9.75, "category": "home and kitchen"},
    {"id": 6, "name": "clean code", "price": 38.25, "category": "books"},
    {"id": 7, "name": "yoga mat 6mm", "price": 29.95, "category": "sports and outdoors"},
]

REQUIRED_FIELDS = ("username", "email", "password")


@product_routes.get("/products")
def list_products():
    """Return every hardcoded product as JSON."""
    return jsonify(HARDCODED_PRODUCTS)


@product_routes.get("/products/<int:product_id>")
def get_product(product_id):
    """Return a single hardcoded product by id, or 404 when it does not exist."""
    for product in HARDCODED_PRODUCTS:
        if product["id"] == product_id:
            return jsonify(product)

    return jsonify({"error": "product not found", "id": product_id}), 404


@user_routes.post("/register")
def register():
    """Create a User from JSON input and save it with the session."""
    data = request.get_json(silent=True) or {}

    missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
    if missing:
        return jsonify({"error": "missing required fields", "fields": missing}), 400

    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
        phone_number=data.get("phone_number"),
        address=data.get("address"),
    )

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # email carries a unique constraint
        db.session.rollback()
        return jsonify({"error": "email already registered", "email": data["email"]}), 409

    return jsonify({"message": "user registered", "user": user.to_dict()}), 201


@user_routes.get("/users/<int:user_id>")
def get_user(user_id):
    """Return a single user by id, or 404 when there is no such user."""
    user = db.session.get(User, user_id)
    if user is None:
        return jsonify({"error": "user not found", "id": user_id}), 404

    return jsonify(user.to_dict())
