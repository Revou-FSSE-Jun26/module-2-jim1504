"""Category endpoints -- full CRUD, including the products in each category."""

from flask import Blueprint, jsonify
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import Category, db
from routes.helpers import error, get_payload, require_fields

category_routes = Blueprint("categories", __name__)


def _validate(data, partial=False):
    """Validate category input. Returns (values, errors)."""
    values = {}
    errors = []

    if not partial:
        missing = require_fields(data, "category_name")
        if missing:
            return {}, ["category_name is required"]

    if "category_name" in data:
        name = str(data["category_name"]).strip()
        if not name:
            errors.append("category_name must not be blank")
        elif len(name) > 100:
            errors.append("category_name must be 100 characters or fewer")
        else:
            values["category_name"] = name

    if "description" in data:
        values["description"] = data["description"]

    return values, errors


@category_routes.get("/categories")
def list_categories():
    """Return every category as JSON."""
    categories = db.session.scalars(
        db.select(Category).order_by(Category.category_id)
    ).all()
    return jsonify([category.to_dict() for category in categories])


@category_routes.get("/categories/<int:category_id>")
def get_category(category_id):
    """Return one category together with the products that belong to it."""
    category = db.session.get(Category, category_id)
    if category is None:
        return error("category not found", 404, id=category_id)

    payload = category.to_dict()
    payload["products"] = [product.to_dict() for product in category.products]
    payload["product_count"] = len(category.products)
    return jsonify(payload)


@category_routes.post("/categories")
def create_category():
    """Create a category from JSON input."""
    data = get_payload()
    values, errors = _validate(data)
    if errors:
        return error("validation failed", 400, details=errors)

    category = Category(**values)
    db.session.add(category)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("category_name already exists", 409, category_name=values["category_name"])
    except SQLAlchemyError:
        db.session.rollback()
        return error("could not create category", 400)

    return jsonify({"message": "category created", "category": category.to_dict()}), 201


@category_routes.put("/categories/<int:category_id>")
def update_category(category_id):
    """Update an existing category. Only the supplied fields change."""
    category = db.session.get(Category, category_id)
    if category is None:
        return error("category not found", 404, id=category_id)

    data = get_payload()
    if not data:
        return error("no fields to update", 400)

    values, errors = _validate(data, partial=True)
    if errors:
        return error("validation failed", 400, details=errors)

    for field, value in values.items():
        setattr(category, field, value)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("category_name already exists", 409)
    except SQLAlchemyError:
        db.session.rollback()
        return error("could not update category", 400)

    return jsonify({"message": "category updated", "category": category.to_dict()}), 200


@category_routes.delete("/categories/<int:category_id>")
def delete_category(category_id):
    """Delete a category, unless products still belong to it."""
    category = db.session.get(Category, category_id)
    if category is None:
        return error("category not found", 404, id=category_id)

    # products.category_id is NOT NULL, so the foreign key would reject this
    # anyway -- reporting it as a conflict is clearer than a 500.
    attached = len(category.products)
    if attached:
        return error(
            "category cannot be deleted while products belong to it",
            409,
            id=category_id,
            product_count=attached,
        )

    try:
        db.session.delete(category)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error("could not delete category", 409, id=category_id)

    return jsonify({"message": "category deleted", "id": category_id}), 200
