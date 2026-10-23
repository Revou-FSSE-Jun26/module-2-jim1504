"""Product endpoints -- full CRUD backed by the database."""

import re
from urllib.parse import urlparse

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import SQLAlchemyError

from models import Category, Order, Product, db, order_items
from routes.helpers import (
    error,
    get_payload,
    parse_decimal,
    parse_int,
    require_fields,
    require_permission,
    text_or_none,
)

product_routes = Blueprint("products", __name__)

# An order still "in flight" -- delivered and cancelled orders are finished.
ACTIVE_STATUSES = ("pending", "paid", "shipped")

MAX_IMAGES = 12
SPEC_LIMITS = {"rows": 150, "group": 60, "label": 80, "value": 400}

# Gallery entries must be AVIF files the storefront serves: the seeded product photos,
# or uploads, which the storefront converts to AVIF and stores in Vercel Blob (or serves
# from /api/images in development). Rejecting anything else keeps product pages from
# pointing at arbitrary external images.
IMAGE_URL = re.compile(
    r"^(?:/(?:products|api/images)/[a-z0-9][\w-]*\.avif"
    r"|https://[a-z0-9-]+\.public\.blob\.vercel-storage\.com/uploads/[a-f0-9]{16}\.avif)$",
    re.IGNORECASE,
)


def _is_http_url(value):
    if not isinstance(value, str) or len(value) > 500:
        return False
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


def _clean_specs(rows):
    """Validate spec rows. Returns (rows, None) or (None, message)."""
    if not isinstance(rows, list):
        return None, "specs must be a list"
    if len(rows) > SPEC_LIMITS["rows"]:
        return None, f"specs can hold at most {SPEC_LIMITS['rows']} rows"
    clean = []
    for index, row in enumerate(rows, start=1):
        label = row.get("label") if isinstance(row, dict) else None
        value = row.get("value") if isinstance(row, dict) else None
        group = row.get("group") if isinstance(row, dict) else None
        if (
            not isinstance(label, str)
            or not label.strip()
            or not isinstance(value, str)
            or not value.strip()
            or len(label) > SPEC_LIMITS["label"]
            or len(value) > SPEC_LIMITS["value"]
            or (group is not None and (not isinstance(group, str) or len(group) > SPEC_LIMITS["group"]))
        ):
            return None, (
                f"specs row {index} needs a label (max {SPEC_LIMITS['label']} chars) and a value "
                f"(max {SPEC_LIMITS['value']}), group at most {SPEC_LIMITS['group']}"
            )
        entry = {"label": label.strip(), "value": value.strip()}
        if group and group.strip():
            entry = {"group": group.strip(), **entry}
        clean.append(entry)
    return clean, None


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
        elif len(name) > 150:
            errors.append("product_name must be at most 150 characters")
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
        values["description"] = text_or_none(data["description"])

    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            errors.append("is_active must be true or false")
        else:
            values["is_active"] = data["is_active"]

    for field in ("official_url", "overview_source", "specs_source"):
        if field in data:
            url = text_or_none(data[field])
            if url is not None and not _is_http_url(url):
                errors.append(f"{field} must be an http(s) URL of at most 500 characters")
            else:
                values[field] = url

    if "overview" in data:
        overview = text_or_none(data["overview"])
        if overview is not None and len(overview) > 2000:
            errors.append("overview must be at most 2000 characters")
        else:
            values["overview"] = overview

    if "specs" in data:
        specs, message = _clean_specs(data["specs"])
        if message:
            errors.append(message)
        else:
            values["specs"] = specs

    if "images" in data:
        images = data["images"]
        if not isinstance(images, list):
            errors.append("images must be a list")
        elif len(images) > MAX_IMAGES:
            errors.append(f"images can hold at most {MAX_IMAGES} pictures")
        elif any(not isinstance(url, str) or not IMAGE_URL.match(url) for url in images):
            errors.append("images must be AVIF files uploaded through the storefront")
        else:
            values["images"] = list(dict.fromkeys(images))  # de-duplicated, order kept

    return values, errors


def _order_counts(product_id):
    """(active, total): orders that still reference this product, in flight and overall."""
    row = db.session.execute(
        db.select(
            db.func.count().filter(Order.order_status.in_(ACTIVE_STATUSES)),
            db.func.count(),
        )
        .select_from(order_items)
        .join(Order, Order.order_id == order_items.c.order_id)
        .where(order_items.c.product_id == product_id)
    ).one()
    return row[0], row[1]


@product_routes.get("/products")
def list_products():
    """Every product, oldest first. ?search= matches name and description; ?category_id= filters."""
    query = db.select(Product).order_by(Product.product_id)

    search = (request.args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.where(db.or_(Product.product_name.ilike(pattern), Product.description.ilike(pattern)))

    category_id = request.args.get("category_id")
    if category_id:
        try:
            query = query.where(Product.category_id == int(category_id))
        except ValueError:
            return error("validation failed", 400, details=["category_id must be an integer"])

    products = db.session.scalars(query).all()
    return jsonify([product.to_dict() for product in products])


@product_routes.get("/products/<int:product_id>")
def get_product(product_id):
    """Return a single product, or 404 when it does not exist."""
    product = db.session.get(Product, product_id)
    if product is None:
        return error("product not found", 404, id=product_id)
    return jsonify(product.to_dict())


@product_routes.post("/products")
@require_permission("products:write")
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
@require_permission("products:write")
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
@require_permission("products:write")
def delete_product(product_id):
    """Delete a product.

    Refused (409) while an in-flight order references it. If only finished orders
    (delivered/cancelled) reference it, it is withdrawn from sale instead -- those
    orders keep their line items, prices and totals, so order history never changes.
    """
    product = db.session.get(Product, product_id)
    if product is None:
        return error("product not found", 404, id=product_id)

    active, referenced = _order_counts(product_id)
    if active:
        return error(
            "product cannot be deleted while it has active orders",
            409,
            id=product_id,
            active_orders=active,
        )

    try:
        if referenced:
            product.is_active = False
            db.session.commit()
            return jsonify(
                {
                    "message": "product withdrawn from sale (it appears in past orders)",
                    "id": product_id,
                    "withdrawn": True,
                }
            ), 200
        db.session.delete(product)
        db.session.commit()
    except SQLAlchemyError as exc:
        db.session.rollback()
        return error("could not delete product", 409, detail=str(exc.orig if hasattr(exc, "orig") else exc))

    return jsonify({"message": "product deleted", "id": product_id}), 200
