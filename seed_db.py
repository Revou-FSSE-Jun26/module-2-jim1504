"""Load the RevoShop sample data through SQLAlchemy.

Katalognya berisi sparepart komputer dengan harga dalam rupiah (IDR):
6 user, 6 kategori, 20 produk, 6 order, dan 15 order item. Jalankan setelah
`flask db upgrade`.

    python seed_db.py

Script ini idempotent -- kelima tabel dikosongkan lebih dulu, jadi aman
dijalankan berulang kali.
"""

from decimal import Decimal

from werkzeug.security import generate_password_hash

from app import app
from models import Category, Order, Product, User, db, order_items

# Every seeded user shares this password so login can be demonstrated.
SEED_PASSWORD = "password123"

USERS = [
    ("andi pratama", "andi.pratama@example.com", SEED_PASSWORD, "+62-812-1111-0001", "jl. merdeka no. 12, bandung, west java 40115"),
    ("siti rahayu", "siti.rahayu@example.com", SEED_PASSWORD, "+62-813-2222-0002", "jl. sudirman no. 45, jakarta 10210"),
    ("budi santoso", "budi.santoso@example.com", SEED_PASSWORD, "+62-856-3333-0003", "jl. diponegoro no. 8, surabaya 60241"),
    ("dewi lestari", "dewi.lestari@example.com", SEED_PASSWORD, "+62-877-4444-0004", "jl. malioboro no. 21, yogyakarta 55213"),
    ("rizky ramadhan", "rizky.ramadhan@example.com", SEED_PASSWORD, "+62-819-5555-0005", "jl. gatot subroto no. 3, medan 20112"),
    ("maya kusuma", "maya.kusuma@example.com", SEED_PASSWORD, None, "jl. pahlawan no. 77, semarang 50241"),
]

CATEGORIES = [
    ("processors", "cpu desktop intel dan amd"),
    ("motherboards", "mainboard untuk soket lga dan am5"),
    ("memory and storage", "ram, ssd nvme, ssd sata, dan hard disk"),
    ("graphics cards", "kartu grafis untuk gaming dan rendering"),
    ("power and cooling", "power supply, pendingin cpu, fan, dan thermal paste"),
    ("peripherals", "mouse, keyboard, dan monitor"),
]

# (category_id, name, description, price in IDR, stock, is_active)
PRODUCTS = [
    # 1-3 processors
    (1, "intel core i5-14400f", "10 core, 16 thread, soket lga1700", "2850000.00", 25, True),
    (1, "intel core i7-14700k", "20 core, 28 thread, unlocked, soket lga1700", "6450000.00", 12, True),
    (1, "amd ryzen 7 7800x3d", "8 core dengan 3d v-cache, soket am5", "6900000.00", 8, True),
    # 4-6 motherboards
    (2, "asus prime b760m-a", "micro atx, ddr5, soket lga1700", "2150000.00", 20, True),
    (2, "msi mag b650 tomahawk wifi", "atx, ddr5, wifi 6e, soket am5", "3250000.00", 14, True),
    (2, "gigabyte h610m h ddr4", "micro atx hemat biaya, soket lga1700", "1350000.00", 30, True),
    # 7-10 memory and storage
    (3, "corsair vengeance ddr5 16gb", "5600 mhz, kit 1x16gb", "850000.00", 45, True),
    (3, "kingston fury beast ddr4 16gb", "3200 mhz, kit 1x16gb", "620000.00", 50, True),
    (3, "samsung 980 pro nvme 1tb", "pcie 4.0, baca hingga 7000 mb per detik", "1450000.00", 35, True),
    (3, "seagate barracuda hdd 2tb", "sata 3.5 inci, 7200 rpm", "950000.00", 22, True),
    # 11-13 graphics cards
    (4, "nvidia geforce rtx 4060 8gb", "gddr6, dukungan dlss 3", "5200000.00", 10, True),
    (4, "nvidia geforce rtx 4070 super 12gb", "gddr6x, untuk gaming 1440p", "9800000.00", 6, True),
    (4, "amd radeon rx 7600 8gb", "gddr6, arsitektur rdna 3", "4350000.00", 9, True),
    # 14-17 power and cooling
    (5, "corsair rm650e 650w 80 plus gold", "full modular, sertifikasi gold", "1250000.00", 16, True),
    (5, "deepcool ak400 cpu cooler", "single tower, empat heat pipe", "450000.00", 28, True),
    (5, "arctic p12 argb case fan", "120 mm, static pressure tinggi", "135000.00", 60, True),
    (5, "thermal grizzly kryonaut 1g", "thermal paste konduktivitas tinggi", "185000.00", 40, True),
    # 18-20 peripherals
    (6, "logitech g502 hero gaming mouse", "sensor hero 25k, 11 tombol", "685000.00", 33, True),
    (6, "keychron k8 pro mechanical keyboard", "tenkeyless, hot swappable, bluetooth", "1750000.00", 15, True),
    (6, "lg ultragear 24gn60r 144hz monitor", "24 inci, ips, 1 ms -- stok lama", "2650000.00", 7, False),
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
#
# Order 2, 3 dan 4 masih aktif (shipped/paid/pending), sehingga produk di
# dalamnya tidak bisa dihapus. Order 1, 5 dan 6 sudah selesai, jadi produknya
# boleh dihapus -- keduanya tersedia untuk menguji deletion guard.
#
# Produk 7 muncul di order 2 dan 3, produk 16 di order 1 dan 5. Keduanya
# membuktikan arah kedua dari relasi many-to-many: satu produk bisa berada
# di banyak order.
ORDER_ITEMS = [
    (1, 16, 2, "135000.00"),
    (1, 17, 1, "185000.00"),
    (2, 1, 1, "2850000.00"),
    (2, 4, 1, "2150000.00"),
    (2, 7, 2, "850000.00"),
    (3, 7, 1, "850000.00"),
    (3, 11, 1, "5200000.00"),
    (3, 14, 1, "1250000.00"),
    (4, 18, 1, "685000.00"),
    (4, 19, 1, "1750000.00"),
    (5, 9, 2, "1450000.00"),
    (5, 15, 1, "450000.00"),
    (5, 16, 1, "135000.00"),
    (6, 20, 1, "2650000.00"),
    (6, 10, 1, "950000.00"),
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
            password_hash=generate_password_hash(password_hash),
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
