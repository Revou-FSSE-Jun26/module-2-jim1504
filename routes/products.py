"""Product endpoints -- full CRUD backed by the database."""

from flask import Blueprint, jsonify
from sqlalchemy.exc import SQLAlchemyError

from models import Category, Order, Product, db, order_items
from routes.helpers import error, get_payload, parse_decimal, parse_int, require_fields

product_routes = Blueprint("products", __name__)

# An order still "in flight" -- delivered and cancelled orders are finished.
ACTIVE_STATUSES = ("pending", "paid", "shipped")


def _validate(data, partial=False):
    """Validate product input. Returns (values, errors)."""
    values = {}
    errors = []

    if not partial:
        missing = require_fields(data, "product_name", "price", "category_id")
        if missing:
            return {}, [f"{field} is required" for field in missing]

    if "product_name" in data:
        name = str(data["product_name"]).strip()
        if not name:
            errors.append("product_name must not be blank")
        else:
            values["product_name"] = name

    if "price" in data:
        price, message = parse_decimal(data["price"], "price", minimum=0)
        if message:
            errors.append(message)
        else:
            values["price"] = price

    if "stock_quantity" in data:
        stock, message = parse_int(data["stock_quantity"], "stock_quantity", minimum=0)
        if message:
            errors.append(message)
        else:
            values["stock_quantity"] = stock

    if "category_id" in data:
        category_id, message = parse_int(data["category_id"], "category_id", minimum=1)
        if message:
            errors.append(message)
        elif db.session.get(Category, category_id) is None:
            errors.append(f"category_id {category_id} does not exist")
        else:
            values["category_id"] = category_id

    if "description" in data:
        values["description"] = data["description"]

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            errors.append("is_active must be true or false")
        else:
            values["is_active"] = data["is_active"]

    return values, errors


def _active_order_count(product_id):
    """How many in-flight orders still reference this product."""
    return db.session.execute(
        db.select(db.func.count())
        .select_from(order_items)
        .join(Order, Order.order_id == order_items.c.order_id)
        .where(order_items.c.product_id == product_id)
        .where(Order.order_status.in_(ACTIVE_STATUSES))
    ).scalar()


@product_routes.get("/products")
def list_products():
    """Return every product as JSON."""
    products = db.session.scalars(db.select(Product).order_by(Product.product_id)).all()
    return jsonify([product.to_dict() for product in products])


@product_routes.get("/products/<int:product_id>")
def get_product(product_id):
    """Return a single product, or 404 when it does not exist."""
    product = db.session.get(Product, product_id)
    if product is None:
        return error("product not found", 404, id=product_id)
    return jsonify(product.to_dict())


@product_routes.post("/products")
def create_product():
    """Create a product from JSON input."""
    data = get_payload()
    values, errors = _validate(data)
    if errors:
        return error("validation failed", 400, details=errors)

    product = Product(**values)
    db.session.add(product)
    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return error("could not create product", 400, detail=str(exc.orig if hasattr(exc, "orig") else exc))

    return jsonify({"message": "product created", "product": product.to_dict()}), 201


@product_routes.put("/products/<int:product_id>")
def update_product(product_id):
    """Update an existing product. Only the supplied fields change."""
    product = db.session.get(Product, product_id)
    if product is None:
        return error("product not found", 404, id=product_id)

    data = get_payload()
    if not data:
        return error("no fields to update", 400)

    values, errors = _validate(data, partial=True)
    if errors:
        return error("validation failed", 400, details=errors)

    for field, value in values.items():
        setattr(product, field, value)

    try:
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return error("could not update product", 400, detail=str(exc.orig if hasattr(exc, "orig") else exc))

    return jsonify({"message": "product updated", "product": product.to_dict()}), 200


@product_routes.delete("/products/<int:product_id>")
def delete_product(product_id):
    """Delete a product, unless an active order still references it."""
    product = db.session.get(Product, product_id)
    if product is None:
        return error("product not found", 404, id=product_id)

    active = _active_order_count(product_id)
    if active:
        return error(
            "product cannot be deleted while it has active orders",
            409,
            id=product_id,
            active_orders=active,
        )

    # Only finished orders (delivered/cancelled) can still reference it. Their
    # line items go with the product, and the affected order totals are
    # recomputed so total_amount keeps matching the remaining items.
    affected = db.session.scalars(
        db.select(order_items.c.order_id).where(order_items.c.product_id == product_id)
    ).all()

    try:
        db.session.execute(
            order_items.delete().where(order_items.c.product_id == product_id)
        )
        db.session.delete(product)
        for order_id in set(affected):
            db.session.execute(
                db.text(
                    "update orders set total_amount = ("
                    "  select coalesce(sum(order_items.quantity * order_items.unit_price), 0)"
                    "  from order_items where order_items.order_id = :oid"
                    ") where order_id = :oid"
                ),
                {"oid": order_id},
            )
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return error("could not delete product", 409, detail=str(exc.orig if hasattr(exc, "orig") else exc))

    return jsonify({"message": "product deleted", "id": product_id}), 200
