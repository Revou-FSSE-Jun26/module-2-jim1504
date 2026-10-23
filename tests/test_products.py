"""Product endpoints: search and filters, storefront details, and deletion rules."""

import pytest

from models import Category, Order, Product, User, order_items


@pytest.fixture()
def catalogue(session):
    """Two categories, three products; returns their ids."""
    cpus = Category(category_name="processors")
    gpus = Category(category_name="graphics cards")
    session.add_all([cpus, gpus])
    session.flush()
    products = [
        Product(category_id=cpus.category_id, product_name="Ryzen 7 9850X3D", description="8 core, am5", price=9650000, stock_quantity=8),
        Product(category_id=gpus.category_id, product_name="GeForce RTX 5060", description="gddr7", price=5750000, stock_quantity=10),
        Product(category_id=gpus.category_id, product_name="Radeon RX 9060 XT", description="rdna 4, not rtx", price=6400000, stock_quantity=9),
    ]
    session.add_all(products)
    session.commit()
    return {"cpus": cpus.category_id, "gpus": gpus.category_id, "ids": [p.product_id for p in products]}


def test_search_matches_name_and_description_case_insensitively(client, catalogue):
    names = [p["product_name"] for p in client.get("/products?search=RTX").get_json()]

    assert names == ["GeForce RTX 5060", "Radeon RX 9060 XT"]  # the second matches its description


def test_filter_by_category(client, catalogue):
    rows = client.get(f"/products?category_id={catalogue['gpus']}").get_json()

    assert {p["category_id"] for p in rows} == {catalogue["gpus"]}
    assert len(rows) == 2


def test_bad_category_filter_is_a_400(client, catalogue):
    assert client.get("/products?category_id=abc").status_code == 400


def test_product_carries_storefront_details(client, admin_headers, catalogue):
    response = client.post(
        "/products",
        headers=admin_headers,
        json={
            "product_name": "Corsair RM850e",
            "price": 1650000,
            "category_id": catalogue["cpus"],
            "official_url": "https://www.corsair.com/rm850e",
            "overview": "A quiet 850 W supply.",
            "overview_source": "https://www.corsair.com/rm850e",
            "images": ["/products/corsair-rm850e.avif", "/products/corsair-rm850e.avif"],
            "specs": [{"group": " Power ", "label": "Wattage", "value": "850 W"}, {"label": "Modular", "value": "Full"}],
            "specs_source": "https://www.corsair.com/rm850e#specs",
        },
    )

    assert response.status_code == 201
    product = response.get_json()["product"]
    assert product["images"] == ["/products/corsair-rm850e.avif"]  # de-duplicated
    assert product["specs"][0] == {"group": "Power", "label": "Wattage", "value": "850 W"}
    assert product["official_url"] == "https://www.corsair.com/rm850e"

    # and it comes back the same way on a plain read
    fetched = client.get(f"/products/{product['product_id']}").get_json()
    assert fetched["specs"] == product["specs"]


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("images", ["https://evil.example.com/x.avif"], "images must be AVIF files"),
        ("images", ["/products/a.png"], "images must be AVIF files"),
        ("images", [f"/products/p{n}.avif" for n in range(13)], "at most 12"),
        ("specs", [{"label": "", "value": "x"}], "specs row 1"),
        ("specs", "not a list", "specs must be a list"),
        ("official_url", "javascript:alert(1)", "official_url must be an http(s) URL"),
        ("overview", "x" * 2001, "overview must be at most 2000"),
    ],
)
def test_storefront_details_are_validated(client, admin_headers, catalogue, field, value, message):
    product_id = catalogue["ids"][0]

    response = client.put(f"/products/{product_id}", headers=admin_headers, json={field: value})

    assert response.status_code == 400
    assert any(message in d for d in response.get_json()["details"])


def test_blob_upload_urls_are_accepted(client, admin_headers, catalogue):
    url = "https://abc123.public.blob.vercel-storage.com/uploads/0123456789abcdef.avif"

    response = client.put(f"/products/{catalogue['ids'][0]}", headers=admin_headers, json={"images": [url]})

    assert response.status_code == 200
    assert response.get_json()["product"]["images"] == [url]


def _order_with(session, product_id, status):
    user = User(username="buyer", email=f"buyer-{status}@example.com", password_hash="x")
    session.add(user)
    session.flush()
    order = Order(user_id=user.id, order_status=status, shipping_address="jl. test", total_amount=100)
    session.add(order)
    session.flush()
    session.execute(order_items.insert(), [{"order_id": order.order_id, "product_id": product_id, "quantity": 1, "unit_price": 100}])
    session.commit()
    return order.order_id


def test_delete_with_an_active_order_is_refused(client, session, admin_headers, catalogue):
    product_id = catalogue["ids"][0]
    _order_with(session, product_id, "paid")

    response = client.delete(f"/products/{product_id}", headers=admin_headers)

    assert response.status_code == 409
    assert response.get_json()["active_orders"] == 1


def test_delete_with_only_past_orders_withdraws_it_and_keeps_the_order(client, session, admin_headers, catalogue):
    product_id = catalogue["ids"][1]
    order_id = _order_with(session, product_id, "delivered")

    response = client.delete(f"/products/{product_id}", headers=admin_headers)

    assert response.status_code == 200
    assert response.get_json()["withdrawn"] is True
    assert client.get(f"/products/{product_id}").get_json()["is_active"] is False
    # the past order still has its line item and total
    detail = client.get(f"/orders/{order_id}", headers=admin_headers).get_json()
    assert [i["product_id"] for i in detail["items"]] == [product_id]
    assert detail["total_amount"] == 100


def test_delete_without_orders_removes_it(client, admin_headers, catalogue):
    product_id = catalogue["ids"][2]

    response = client.delete(f"/products/{product_id}", headers=admin_headers)

    assert response.status_code == 200
    assert "withdrawn" not in response.get_json()
    assert client.get(f"/products/{product_id}").status_code == 404


def test_category_list_counts_products(client, catalogue):
    counts = {c["category_id"]: c["product_count"] for c in client.get("/categories").get_json()}

    assert counts == {catalogue["cpus"]: 1, catalogue["gpus"]: 2}
