"""Verifikasi relasi many-to-many orders <-> products.

Menampilkan isi tabel asosiasi order_items, lalu membuktikan lewat ORM bahwa
satu order berisi banyak produk dan satu produk muncul di banyak order.

    python demo_m2m.py

Script ini hanya membaca, tidak mengubah data apa pun.
"""

from app import app
from models import Order, Product, db


def show_association_table():
    """Isi tabel asosiasi -- sama dengan select * from order_items."""
    print("SELECT * FROM order_items;")
    print()
    print("order_id | product_id | quantity | unit_price")
    print("---------+------------+----------+-----------")

    rows = db.session.execute(
        db.text(
            "select order_id, product_id, quantity, unit_price "
            "from order_items order by order_id, product_id"
        )
    )
    for row in rows:
        print(
            f"{row.order_id:>8} | {row.product_id:>10} | "
            f"{row.quantity:>8} | {row.unit_price:>10}"
        )


def show_many_to_many():
    """Satu order banyak produk, dan satu produk banyak order."""
    order = db.session.get(Order, 2)
    print()
    print(f"Order {order.order_id} berisi {len(order.products)} produk:")
    for product in order.products:
        print(f"  - {product.product_name}")

    product = db.session.get(Product, 8)
    print()
    print(f"Produk '{product.product_name}' muncul di {len(product.orders)} order:")
    for linked_order in product.orders:
        print(f"  - order {linked_order.order_id}")


if __name__ == "__main__":
    with app.app_context():
        show_association_table()
        show_many_to_many()
