from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()


order_items = db.Table(
    "order_items",
    db.Column("order_item_id", db.Integer, primary_key=True),
    db.Column(
        "order_id",
        db.Integer,
        db.ForeignKey("orders.order_id", name="fk_order_items_order", ondelete="CASCADE"),
        nullable=False,
    ),
    db.Column(
        "product_id",
        db.Integer,
        db.ForeignKey("products.product_id", name="fk_order_items_product"),
        nullable=False,
    ),
    db.Column("quantity", db.Integer, nullable=False, server_default="1"),
    db.Column("unit_price", db.Numeric(12, 2), nullable=False, server_default="0"),
    db.CheckConstraint("quantity > 0", name="chk_order_items_quantity"),
    db.CheckConstraint("unit_price >= 0", name="chk_order_items_unit_price"),
    db.UniqueConstraint("order_id", "product_id", name="uq_order_items_order_product"),
    db.Index("idx_order_items_order_id", "order_id"),
    db.Index("idx_order_items_product_id", "product_id"),
)


ROLE_CUSTOMER = "customer"
ROLE_ADMIN = "admin"
ROLE_SUPERADMIN = "superadmin"

# The only roles the system recognises. Enforced both here (check constraint) and
# in routes/helpers.py, so an invalid role cannot enter through either door.
ROLES = (ROLE_SUPERADMIN, ROLE_ADMIN, ROLE_CUSTOMER)

# What each role may do -- the same table as the RevoTech frontend's lib/roles.ts, so the
# dashboard only offers what this API will accept. Routes check a permission, never a role
# name, so moving a permission between roles is a one-line change here.
#
#   products:write    create/edit/withdraw products        superadmin, admin
#   categories:write  create/edit/delete categories        superadmin, admin
#   orders:manage     see every order, change its status  superadmin, admin
#   content:write     homepage and About page content      superadmin, admin
#   settings:write    shop name, logo, time zone           superadmin
#   users:manage      user list, roles, password resets    superadmin
PERMISSIONS = {
    ROLE_SUPERADMIN: frozenset(
        {"products:write", "categories:write", "orders:manage", "content:write", "settings:write", "users:manage"}
    ),
    ROLE_ADMIN: frozenset({"products:write", "categories:write", "orders:manage", "content:write"}),
    ROLE_CUSTOMER: frozenset(),
}


def can(role, permission):
    """True when `role` holds `permission`. Unknown roles hold nothing."""
    return permission in PERMISSIONS.get(role, frozenset())


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone_number = db.Column(db.String(20))
    address = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )


    role = db.Column(db.String(20), nullable=False, server_default=ROLE_CUSTOMER)

    orders = db.relationship("Order", back_populates="user")

    __table_args__ = (
        db.CheckConstraint(
            "role in ('customer', 'admin', 'superadmin')",
            name="chk_users_role",
        ),
    )

    def to_dict(self):
        """Serialise for jsonify. password_hash is deliberately never exposed."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "phone_number": self.phone_number,
            "address": self.address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<User {self.id} {self.username}>"


class Category(db.Model):
    __tablename__ = "categories"

    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    products = db.relationship("Product", back_populates="category")

    def to_dict(self):
        return {
            "category_id": self.category_id,
            "category_name": self.category_name,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self):
        return f"<Category {self.category_id} {self.category_name}>"


class Product(db.Model):
    __tablename__ = "products"
    __table_args__ = (
        db.CheckConstraint("price >= 0", name="chk_products_price"),
        db.CheckConstraint("stock_quantity >= 0", name="chk_products_stock"),
        db.Index("idx_products_category_id", "category_id"),
    )

    product_id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("categories.category_id", name="fk_products_category"),
        nullable=False,
    )
    product_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, nullable=False, server_default="0")
    is_active = db.Column(db.Boolean, nullable=False, server_default=db.true())
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    # Storefront detail: the manufacturer's page, a credited summary of it, the gallery
    # (image URLs, first = primary) and the technical specification table
    # ([{group?, label, value}]).
    official_url = db.Column(db.Text)
    overview = db.Column(db.Text)
    overview_source = db.Column(db.Text)
    images = db.Column(JSONB, nullable=False, server_default="[]")
    specs = db.Column(JSONB, nullable=False, server_default="[]")
    specs_source = db.Column(db.Text)

    category = db.relationship("Category", back_populates="products")
    orders = db.relationship("Order", secondary=order_items, back_populates="products")

    def to_dict(self):
        # price is Numeric -> Decimal, which jsonify cannot serialise on its own.
        return {
            "product_id": self.product_id,
            "category_id": self.category_id,
            "product_name": self.product_name,
            "description": self.description,
            "price": float(self.price) if self.price is not None else None,
            "stock_quantity": self.stock_quantity,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "official_url": self.official_url,
            "overview": self.overview,
            "overview_source": self.overview_source,
            "images": self.images or [],
            "specs": self.specs or [],
            "specs_source": self.specs_source,
        }

    def __repr__(self):
        return f"<Product {self.product_id} {self.product_name}>"


class Order(db.Model):
    __tablename__ = "orders"
    __table_args__ = (
        db.CheckConstraint(
            "order_status in ('pending', 'paid', 'shipped', 'delivered', 'cancelled')",
            name="chk_orders_status",
        ),
        db.CheckConstraint("total_amount >= 0", name="chk_orders_total"),
        db.Index("idx_orders_user_id", "user_id"),
    )

    order_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", name="fk_orders_user"),
        nullable=False,
    )
    order_status = db.Column(db.String(20), nullable=False, server_default="pending")
    total_amount = db.Column(db.Numeric(12, 2), nullable=False, server_default="0")
    shipping_address = db.Column(db.Text, nullable=False)
    ordered_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
    )

    user = db.relationship("User", back_populates="orders")
    products = db.relationship("Product", secondary=order_items, back_populates="orders")

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "order_status": self.order_status,
            "total_amount": float(self.total_amount) if self.total_amount is not None else None,
            "shipping_address": self.shipping_address,
            "ordered_at": self.ordered_at.isoformat() if self.ordered_at else None,
        }

    def __repr__(self):
        return f"<Order {self.order_id} {self.order_status}>"


class SiteContent(db.Model):
    """Editable page content, one JSON document per page ('home', 'about')."""

    __tablename__ = "site_content"

    key = db.Column(db.String(20), primary_key=True)
    content = db.Column(JSONB, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )


class SiteSettings(db.Model):
    """The store's settings and logo -- a single row (id = 1)."""

    __tablename__ = "site_settings"
    __table_args__ = (db.CheckConstraint("id = 1", name="chk_site_settings_single_row"),)

    id = db.Column(db.Integer, primary_key=True)
    settings = db.Column(JSONB, nullable=False)
    # the logo as vector paths ({box: {x, y, w, h}, paths: [{d, fill}], colours}), traced from
    # an upload by the storefront; null = the storefront's default logo
    logo = db.Column(JSONB)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )
