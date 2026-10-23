"""Order endpoints -- creation writes into the order_items association table.

Stock moves with the order: placing it takes the items off the shelf, cancelling puts
them back, and reopening a cancelled order takes them again. Every stock change is a
conditional UPDATE (stock_quantity >= quantity) inside the order's own transaction, so
two customers can never both buy the last unit.
"""

from decimal import Decimal

from flask import Blueprint, g, jsonify
from sqlalchemy.exc import SQLAlchemyError

from models import Order, Product, User, db, order_items
from routes.helpers import (
    error,
    get_payload,
    has_permission,
    parse_int,
    require_auth,
    require_permission,
)

order_routes = Blueprint("orders", __name__)

VALID_STATUSES = ("pending", "paid", "shipped", "delivered", "cancelled")


class OutOfStock(Exception):
    """Raised inside a transaction when a product no longer has enough stock."""


def _summary(order, username, item_count):
    payload = order.to_dict()
    payload["username"] = username
    payload["item_count"] = item_count
    return payload


def _order_detail(order):
    """Serialise an order together with its line items and product details."""
    rows = db.session.execute(
        db.select(
            order_items.c.order_item_id,
            order_items.c.product_id,
            order_items.c.quantity,
            order_items.c.unit_price,
            Product.product_name,
        )
        .join(Product, Product.product_id == order_items.c.product_id)
        .where(order_items.c.order_id == order.order_id)
        .order_by(order_items.c.order_item_id)
    ).all()

    payload = _summary(order, order.user.username if order.user else None, sum(row.quantity for row in rows))
    payload["items"] = [
        {
            "order_item_id": row.order_item_id,
            "product_id": row.product_id,
            "product_name": row.product_name,
            "quantity": row.quantity,
            "unit_price": float(row.unit_price),
            "line_total": float(row.unit_price * row.quantity),
        }
        for row in rows
    ]
    return payload


def _lines(order_id):
    return db.session.execute(
        db.select(order_items.c.product_id, order_items.c.quantity).where(order_items.c.order_id == order_id)
    ).all()


def _move_stock(lines, sign):
    """Add (sign=+1) or take (sign=-1) stock for (product_id, quantity) lines.

    Taking is conditional on enough stock being left; raises OutOfStock otherwise.
    Must run inside the caller's transaction.
    """
    for product_id, quantity in lines:
        statement = db.update(Product).where(Product.product_id == product_id)
        if sign < 0:
            statement = statement.where(Product.stock_quantity >= quantity)
        result = db.session.execute(statement.values(stock_quantity=Product.stock_quantity + sign * quantity))
        if result.rowcount != 1:
            product = db.session.get(Product, product_id)
            raise OutOfStock(f"only {product.stock_quantity if product else 0} left of {product.product_name if product else product_id}")


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
        if not product.is_active:
            errors.append(f"{product.product_name} is not available")
            continue
        if quantity > product.stock_quantity:
            errors.append(f"only {product.stock_quantity} left of {product.product_name}")
            continue

        # unit_price freezes the price paid now, so the order keeps its
        # original total even if the product price changes later.
        rows.append({"product_id": product_id, "quantity": quantity, "unit_price": Decimal(product.price)})

    return rows, errors


def _visible(order):
    """The owner and order managers may see an order."""
    return order.user_id == g.user_id or has_permission("orders:manage")


@order_routes.get("/orders")
@require_auth
def list_orders():
    """Newest first. Order managers (admin, superadmin) see every order; others their own."""
    item_count = (
        db.select(db.func.coalesce(db.func.sum(order_items.c.quantity), 0))
        .where(order_items.c.order_id == Order.order_id)
        .scalar_subquery()
    )
    query = (
        db.select(Order, User.username, item_count)
        .join(User, User.id == Order.user_id)
        .order_by(Order.ordered_at.desc(), Order.order_id.desc())
    )
    if not has_permission("orders:manage"):
        query = query.where(Order.user_id == g.user_id)

    rows = db.session.execute(query).all()
    return jsonify([_summary(order, username, count) for order, username, count in rows])


@order_routes.get("/orders/<int:order_id>")
@require_auth
def get_order(order_id):
    """One order with its line items. Own orders only, unless you manage orders."""
    order = db.session.get(Order, order_id)
    if order is None:
        return error("order not found", 404, id=order_id)
    if not _visible(order):
        return error("you may only view your own orders", 403, id=order_id)
    return jsonify(_order_detail(order))


@order_routes.post("/orders")
@require_auth
def create_order():
    """Place a new order for the authenticated user, taking the items' stock.

    The owner is taken from the token, never from the request body -- otherwise any
    signed-in customer could order in someone else's name. Order managers may order on
    another user's behalf (`user_id`) and set the initial `order_status`; everyone else's
    order starts as pending.
    """
    data = get_payload()

    user_id = g.user_id
    status = "pending"
    if has_permission("orders:manage"):
        if data.get("user_id") is not None:
            user_id, message = parse_int(data["user_id"], "user_id", minimum=1)
            if message:
                return error("validation failed", 400, details=[message])
        status = data.get("order_status", "pending")
        if status not in VALID_STATUSES:
            return error("validation failed", 400, details=[f"order_status must be one of {list(VALID_STATUSES)}"])

    if db.session.get(User, user_id) is None:
        return error("user does not exist", 400, user_id=user_id)

    shipping_address = str(data.get("shipping_address", "")).strip()
    if not shipping_address:
        return error("validation failed", 400, details=["shipping_address is required"])

    rows, errors = _collect_items(data.get("items"))
    if errors:
        return error("validation failed", 400, details=errors)

    total = sum(row["unit_price"] * row["quantity"] for row in rows)
    order = Order(user_id=user_id, order_status=status, shipping_address=shipping_address, total_amount=total)

    try:
        if status != "cancelled":
            _move_stock([(row["product_id"], row["quantity"]) for row in rows], -1)
        db.session.add(order)
        db.session.flush()  # assigns order_id before the item rows are written
        db.session.execute(order_items.insert(), [dict(row, order_id=order.order_id) for row in rows])
        db.session.commit()
    except OutOfStock as exc:
        db.session.rollback()
        return error("validation failed", 409, details=[str(exc)])
    except SQLAlchemyError as exc:
        db.session.rollback()
        return error("could not create order", 400, detail=str(exc.orig if hasattr(exc, "orig") else exc))

    return jsonify({"message": "order created", "order": _order_detail(order)}), 201


@order_routes.put("/orders/<int:order_id>")
@require_permission("orders:manage")
def update_order(order_id):
    """Change an order's status and/or shipping address (order managers).

    Cancelling puts the items back in stock; reopening a cancelled order takes them
    again and is refused if there is no longer enough. `stock_changed` says whether
    stock moved, so a client knows to refresh the catalogue.
    """
    order = db.session.get(Order, order_id)
    if order is None:
        return error("order not found", 404, id=order_id)

    data = get_payload()
    if not data:
        return error("no fields to update", 400)

    next_status = order.order_status
    if "order_status" in data:
        if data["order_status"] not in VALID_STATUSES:
            return error(
                "validation failed",
                400,
                details=[f"order_status must be one of {list(VALID_STATUSES)}"],
            )
        next_status = data["order_status"]

    if "shipping_address" in data:
        address = str(data["shipping_address"]).strip()
        if not address:
            return error("validation failed", 400, details=["shipping_address must not be blank"])
        order.shipping_address = address

    cancelling = order.order_status != "cancelled" and next_status == "cancelled"
    reopening = order.order_status == "cancelled" and next_status != "cancelled"
    order.order_status = next_status

    try:
        if cancelling or reopening:
            _move_stock(_lines(order_id), 1 if cancelling else -1)
        db.session.commit()
    except OutOfStock as exc:
        db.session.rollback()
        return error("validation failed", 400, details=[str(exc)])
    except SQLAlchemyError:
        db.session.rollback()
        return error("could not update order", 400)

    return jsonify(
        {"message": "order updated", "order": _order_detail(order), "stock_changed": cancelling or reopening}
    ), 200


@order_routes.delete("/orders/<int:order_id>")
@require_auth
def delete_order(order_id):
    """Delete an order (own, or any for order managers). Unless it was cancelled, its
    items go back in stock. order_items rows go with it via ON DELETE CASCADE."""
    order = db.session.get(Order, order_id)
    if order is None:
        return error("order not found", 404, id=order_id)
    if not _visible(order):
        return error("you may only delete your own orders", 403, id=order_id)

    try:
        if order.order_status != "cancelled":
            _move_stock(_lines(order_id), 1)
        db.session.delete(order)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        return error("could not delete order", 409, id=order_id)

    return jsonify({"message": "order deleted", "id": order_id}), 200
