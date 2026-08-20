"""Order endpoints -- creation writes into the order_items association table."""

from decimal import Decimal

from flask import Blueprint, jsonify
from sqlalchemy.exc import SQLAlchemyError

from models import Order, Product, User, db, order_items
from routes.helpers import error, get_payload, parse_int, resolve_user_id

order_routes = Blueprint("orders", __name__)

VALID_STATUSES = ("pending", "paid", "shipped", "delivered", "cancelled")


def _order_detail(order):
    """Serialise an order together with its line items and product details."""
    rows = db.session.execute(
        db.select(
            order_items.c.product_id,
            order_items.c.quantity,
            order_items.c.unit_price,
            Product.product_name,
        )
        .join(Product, Product.product_id == order_items.c.product_id)
        .where(order_items.c.order_id == order.order_id)
        .order_by(order_items.c.product_id)
    ).all()

    payload = order.to_dict()
    payload["items"] = [
        {
            "product_id": row.product_id,
            "product_name": row.product_name,
            "quantity": row.quantity,
            "unit_price": float(row.unit_price),
            "line_total": float(row.unit_price * row.quantity),
        }
        for row in rows
    ]
    payload["item_count"] = len(payload["items"])
    return payload


def _collect_items(raw_items):
    """Validate the items list and freeze each product's current price."""
    if not isinstance(raw_items, list) or not raw_items:
        return None, ["items must be a non-empty list"]

    rows = []
    errors = []
    seen = set()

    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            errors.append(f"items[{index}] must be an object")
            continue

        product_id, message = parse_int(item.get("product_id"), f"items[{index}].product_id", minimum=1)
        if message:
            errors.append(message)
            continue

        quantity, message = parse_int(item.get("quantity", 1), f"items[{index}].quantity", minimum=1)
        if message:
            errors.append(message)
            continue

        if product_id in seen:
            errors.append(f"product_id {product_id} appears more than once")
            continue
        seen.add(product_id)

        product = db.session.get(Product, product_id)
        if product is None:
            errors.append(f"product_id {product_id} does not exist")
            continue

        # unit_price freezes the price paid now, so the order keeps its
        # original total even if the product price changes later.
        rows.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": Decimal(product.price),
            }
        )

    return rows, errors


@order_routes.get("/orders")
def list_orders():
    """List the current user's orders. Identity comes from a token or user_id."""
    user_id = resolve_user_id()
    if user_id is None:
        return error("user_id is required (send a token or ?user_id=)", 400)

    orders = db.session.scalars(
        db.select(Order).where(Order.user_id == user_id).order_by(Order.order_id)
    ).all()
    return jsonify([order.to_dict() for order in orders])


@order_routes.get("/orders/<int:order_id>")
def get_order(order_id):
    """Return one order with its order items and product details."""
    order = db.session.get(Order, order_id)
    if order is None:
        return error("order not found", 404, id=order_id)
    return jsonify(_order_detail(order))


@order_routes.post("/orders")
def create_order():
    """Place a new order for the current user."""
    data = get_payload()

    user_id = resolve_user_id(data)
    if user_id is None:
        return error("user_id is required (send a token or user_id in the body)", 400)
    if db.session.get(User, user_id) is None:
        return error("user does not exist", 400, user_id=user_id)

    shipping_address = str(data.get("shipping_address", "")).strip()
    if not shipping_address:
        return error("validation failed", 400, details=["shipping_address is required"])

    rows, errors = _collect_items(data.get("items"))
    if errors:
        return error("validation failed", 400, details=errors)

    total = sum(row["unit_price"] * row["quantity"] for row in rows)

    order = Order(
        user_id=user_id,
        order_status=data.get("order_status", "pending"),
        shipping_address=shipping_address,
        total_amount=total,
    )
    if order.order_status not in VALID_STATUSES:
        return error("validation failed", 400, details=[f"order_status must be one of {list(VALID_STATUSES)}"])

    try:
        db.session.add(order)
        db.session.flush()  # assigns order_id before the item rows are written
        db.session.execute(
            order_items.insert(),
            [dict(row, order_id=order.order_id) for row in rows],
        )
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return error("could not create order", 400, detail=str(exc.orig if hasattr(exc, "orig") else exc))

    return jsonify({"message": "order created", "order": _order_detail(order)}), 201


@order_routes.put("/orders/<int:order_id>")
def update_order(order_id):
    """Update an order's status or shipping address."""
    order = db.session.get(Order, order_id)
    if order is None:
        return error("order not found", 404, id=order_id)

    data = get_payload()
    if not data:
        return error("no fields to update", 400)

    if "order_status" in data:
        if data["order_status"] not in VALID_STATUSES:
            return error(
                "validation failed",
                400,
                details=[f"order_status must be one of {list(VALID_STATUSES)}"],
            )
        order.order_status = data["order_status"]

    if "shipping_address" in data:
        address = str(data["shipping_address"]).strip()
        if not address:
            return error("validation failed", 400, details=["shipping_address must not be blank"])
        order.shipping_address = address

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error("could not update order", 400)

    return jsonify({"message": "order updated", "order": _order_detail(order)}), 200


@order_routes.delete("/orders/<int:order_id>")
def delete_order(order_id):
    """Delete an order. Its order_items rows go with it via ON DELETE CASCADE."""
    order = db.session.get(Order, order_id)
    if order is None:
        return error("order not found", 404, id=order_id)

    try:
        db.session.delete(order)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error("could not delete order", 409, id=order_id)

    return jsonify({"message": "order deleted", "id": order_id}), 200
