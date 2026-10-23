"""Orders: stock moves with the order, and the summary/detail shapes the storefront reads."""

import pytest

from models import Category, Product, User, db


@pytest.fixture()
def shelf(session):
    """Two products with known stock; returns their ids."""
    category = Category(category_name="cooling")
    session.add(category)
    session.flush()
    fan = Product(category_id=category.category_id, product_name="Arctic P12", price=150000, stock_quantity=5)
    paste = Product(category_id=category.category_id, product_name="Kryonaut", price=185000, stock_quantity=2)
    gone = Product(category_id=category.category_id, product_name="Old fan", price=1, stock_quantity=9, is_active=False)
    session.add_all([fan, paste, gone])
    session.commit()
    return {"fan": fan.product_id, "paste": paste.product_id, "gone": gone.product_id}


def _stock(product_id):
    db.session.expire_all()
    return db.session.get(Product, product_id).stock_quantity


def _place(client, headers, items, **extra):
    return client.post("/orders", headers=headers, json={"shipping_address": "jl. kenangan 1", "items": items, **extra})


def test_placing_an_order_takes_stock(client, customer_headers, shelf):
    response = _place(client, customer_headers, [{"product_id": shelf["fan"], "quantity": 2}])

    assert response.status_code == 201
    order = response.get_json()["order"]
    assert order["order_status"] == "pending"
    assert order["total_amount"] == 300000
    assert order["item_count"] == 2
    assert order["items"][0]["order_item_id"] > 0
    assert _stock(shelf["fan"]) == 3


def test_more_than_the_stock_is_refused_and_nothing_moves(client, customer_headers, shelf):
    response = _place(
        client,
        customer_headers,
        [{"product_id": shelf["fan"], "quantity": 1}, {"product_id": shelf["paste"], "quantity": 3}],
    )

    assert response.status_code == 400
    assert "only 2 left of Kryonaut" in response.get_json()["details"]
    assert _stock(shelf["fan"]) == 5


def test_withdrawn_products_cannot_be_ordered(client, customer_headers, shelf):
    response = _place(client, customer_headers, [{"product_id": shelf["gone"]}])

    assert response.status_code == 400
    assert "Old fan is not available" in response.get_json()["details"]


def test_customers_cannot_choose_the_status_or_the_owner(client, session, customer_headers, shelf):
    other = User(username="other", email="other@example.com", password_hash="x")
    session.add(other)
    session.commit()

    response = _place(client, customer_headers, [{"product_id": shelf["fan"]}], order_status="delivered", user_id=other.id)

    order = response.get_json()["order"]
    assert order["order_status"] == "pending"
    assert order["user_id"] != other.id


def test_cancel_returns_stock_and_reopen_takes_it_again(client, customer_headers, admin_headers, shelf):
    order_id = _place(client, customer_headers, [{"product_id": shelf["paste"], "quantity": 2}]).get_json()["order"]["order_id"]
    assert _stock(shelf["paste"]) == 0

    cancel = client.put(f"/orders/{order_id}", headers=admin_headers, json={"order_status": "cancelled"})
    assert cancel.status_code == 200
    assert cancel.get_json()["stock_changed"] is True
    assert _stock(shelf["paste"]) == 2

    reopen = client.put(f"/orders/{order_id}", headers=admin_headers, json={"order_status": "paid"})
    assert reopen.status_code == 200
    assert _stock(shelf["paste"]) == 0

    # a plain status change moves nothing
    ship = client.put(f"/orders/{order_id}", headers=admin_headers, json={"order_status": "shipped"})
    assert ship.get_json()["stock_changed"] is False


def test_reopening_without_enough_stock_is_refused(client, customer_headers, admin_headers, shelf):
    first = _place(client, customer_headers, [{"product_id": shelf["paste"], "quantity": 2}]).get_json()["order"]["order_id"]
    client.put(f"/orders/{first}", headers=admin_headers, json={"order_status": "cancelled"})
    _place(client, customer_headers, [{"product_id": shelf["paste"], "quantity": 2}])  # someone bought them meanwhile

    response = client.put(f"/orders/{first}", headers=admin_headers, json={"order_status": "pending"})

    assert response.status_code == 400
    assert "only 0 left of Kryonaut" in response.get_json()["details"]
    assert _stock(shelf["paste"]) == 0


def test_deleting_an_open_order_returns_its_stock(client, customer_headers, shelf):
    order_id = _place(client, customer_headers, [{"product_id": shelf["fan"], "quantity": 4}]).get_json()["order"]["order_id"]

    assert client.delete(f"/orders/{order_id}", headers=customer_headers).status_code == 200
    assert _stock(shelf["fan"]) == 5


def test_order_list_has_username_and_item_count_newest_first(client, customer_headers, shelf):
    _place(client, customer_headers, [{"product_id": shelf["fan"], "quantity": 1}])
    _place(client, customer_headers, [{"product_id": shelf["fan"], "quantity": 2}, {"product_id": shelf["paste"], "quantity": 1}])

    rows = client.get("/orders", headers=customer_headers).get_json()

    assert [r["item_count"] for r in rows] == [3, 1]
    assert {r["username"] for r in rows} == {"customer"}
