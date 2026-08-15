"""Load the checkpoint 1 sample data through SQLAlchemy.

This is the Python counterpart of seed.sql: same 6 users, 5 categories,
14 products, 6 orders and 13 order items. Run it after `flask db upgrade`.

    python seed_db.py

The script is idempotent -- it clears the five tables first, so it is safe to
re-run.
"""

from decimal import Decimal

from app import app
from models import Category, Order, Product, User, db, order_items

USERS = [
    ("andi pratama", "andi.pratama@example.com", "$2b$12$fakehashvalue000000001", "+62-812-1111-0001", "jl. merdeka no. 12, bandung, west java 40115"),
    ("siti rahayu", "siti.rahayu@example.com", "$2b$12$fakehashvalue000000002", "+62-813-2222-0002", "jl. sudirman no. 45, jakarta 10210"),
    ("budi santoso", "budi.santoso@example.com", "$2b$12$fakehashvalue000000003", "+62-856-3333-0003", "jl. diponegoro no. 8, surabaya 60241"),
    ("dewi lestari", "dewi.lestari@example.com", "$2b$12$fakehashvalue000000004", "+62-877-4444-0004", "jl. malioboro no. 21, yogyakarta 55213"),
    ("rizky ramadhan", "rizky.ramadhan@example.com", "$2b$12$fakehashvalue000000005", "+62-819-5555-0005", "jl. gatot subroto no. 3, medan 20112"),
    ("maya kusuma", "maya.kusuma@example.com", "$2b$12$fakehashvalue000000006", None, "jl. pahlawan no. 77, semarang 50241"),
]

CATEGORIES = [
    ("electronics", "gadgets, computer accessories and audio gear"),
    ("home and kitchen", "everyday items for cooking and the household"),
    ("books", "printed books on programming and technology"),
    ("fashion", "clothing and wearable accessories"),
    ("sports and outdoors", "equipment for training, yoga and outdoor trips"),
]

# (category_id, name, description, price, stock, is_active)
PRODUCTS = [
    (1, "wireless mouse", "silent 2.4 ghz mouse with usb receiver", "18.50", 120, True),
    (1, "mechanical keyboard", "tenkeyless board with brown switches", "79.99", 45, True),
    (1, "usb-c hub 7 in 1", "hdmi, sd card reader and three usb-a ports", "42.00", 60, True),
    (1, "noise cancelling headphones", "over-ear bluetooth headphones, 30 hour battery", "199.00", 25, True),
    (2, "ceramic coffee mug 350ml", "dishwasher safe mug, matte finish", "9.75", 200, True),
    (2, "stainless steel french press", "800ml double wall coffee press", "34.90", 38, True),
    (2, "bamboo cutting board", "large board with juice groove", "22.40", 75, True),
    (3, "clean code", "a handbook of agile software craftsmanship", "38.25", 30, True),
    (3, "the pragmatic programmer", "classic guide for working developers", "45.00", 18, True),
    (3, "sql for beginners", "hands-on introduction to relational databases", "27.60", 52, True),
    (4, "cotton t-shirt black", "unisex combed cotton, sizes s to xxl", "14.99", 150, True),
    (4, "denim jacket", "mid-wash jacket with two chest pockets", "64.50", 22, True),
    (5, "yoga mat 6mm", "non-slip tpe mat with carrying strap", "29.95", 64, True),
    (5, "stainless water bottle 1l", "vacuum insulated bottle, keeps cold 24 hours", "19.20", 90, False),
]

# (user_id, status, shipping_address, ordered_at)
ORDERS = [
    (1, "delivered", "jl. merdeka no. 12, bandung, west java 40115", "2026-05-04 09:15:00"),
    (2, "shipped", "jl. sudirman no. 45, jakarta 10210", "2026-05-11 14:02:00"),
    (1, "paid", "jl. merdeka no. 12, bandung, west java 40115", "2026-06-01 19:47:00"),
    (3, "pending", "jl. diponegoro no. 8, surabaya 60241", "2026-06-18 08:30:00"),
    (4, "delivered", "jl. malioboro no. 21, yogyakarta 55213", "2026-07-02 11:20:00"),
    (5, "cancelled", "jl. gatot subroto no. 3, medan 20112", "2026-07-15 16:05:00"),
]

# (order_id, product_id, quantity, unit_price)
ORDER_ITEMS = [
    (1, 2, 1, "79.99"),
    (1, 1, 2, "18.50"),
    (2, 8, 1, "38.25"),
    (2, 10, 1, "27.60"),
    (2, 9, 1, "45.00"),
    (3, 4, 1, "199.00"),
    (3, 3, 1, "42.00"),
    (4, 5, 4, "9.75"),
    (4, 6, 1, "34.90"),
    (5, 13, 1, "29.95"),
    (5, 14, 2, "19.20"),
    (5, 11, 3, "14.99"),
    (6, 12, 1, "64.50"),
]


def clear():
    """Wipe the tables and restart the identity sequences."""
    db.session.execute(
        db.text(
            "truncate table order_items, orders, products, categories, users "
            "restart identity cascade"
        )
    )
    db.session.commit()


def seed():
    clear()

    db.session.add_all(
        User(
            username=username,
            email=email,
            password_hash=password_hash,
            phone_number=phone_number,
            address=address,
        )
        for username, email, password_hash, phone_number, address in USERS
    )
    db.session.add_all(
        Category(category_name=name, description=description)
        for name, description in CATEGORIES
    )
    db.session.flush()

    db.session.add_all(
        Product(
            category_id=category_id,
            product_name=name,
            description=description,
            price=Decimal(price),
            stock_quantity=stock,
            is_active=is_active,
        )
        for category_id, name, description, price, stock, is_active in PRODUCTS
    )
    db.session.add_all(
        Order(
            user_id=user_id,
            order_status=status,
            shipping_address=address,
            ordered_at=ordered_at,
        )
        for user_id, status, address, ordered_at in ORDERS
    )
    db.session.flush()

    db.session.execute(
        order_items.insert(),
        [
            {
                "order_id": order_id,
                "product_id": product_id,
                "quantity": quantity,
                "unit_price": Decimal(unit_price),
            }
            for order_id, product_id, quantity, unit_price in ORDER_ITEMS
        ],
    )

    # Same backfill as the trailing update in seed.sql.
    db.session.execute(
        db.text(
            "update orders set total_amount = ("
            "  select coalesce(sum(order_items.quantity * order_items.unit_price), 0)"
            "  from order_items where order_items.order_id = orders.order_id"
            ")"
        )
    )
    db.session.commit()


def report():
    for label, model in [
        ("users", User),
        ("categories", Category),
        ("products", Product),
        ("orders", Order),
    ]:
        count = db.session.query(db.func.count()).select_from(model).scalar()
        print(f"  {label:<12} {count}")
    item_count = db.session.execute(
        db.select(db.func.count()).select_from(order_items)
    ).scalar()
    print(f"  {'order_items':<12} {item_count}")


if __name__ == "__main__":
    with app.app_context():
        seed()
        print("seeded revoshop_db:")
        report()
