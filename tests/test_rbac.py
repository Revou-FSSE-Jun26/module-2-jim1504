"""Role-based access control tests.

Three roles, each a set of permissions (models.PERMISSIONS):

    superadmin   everything: catalogue, orders, page content, store settings, users
    admin        catalogue, every order, page content -- not settings or users
    customer     shop, and manage their own orders and profile

Catalogue reads are public; orders and profiles need a token.
"""

from werkzeug.security import generate_password_hash

from models import PERMISSIONS, ROLE_ADMIN, ROLE_CUSTOMER, ROLE_SUPERADMIN, Order, User, can, db


# ------------------------------------------------------------ the role model

def test_permission_table_matches_the_storefront():
    assert PERMISSIONS[ROLE_SUPERADMIN] >= PERMISSIONS[ROLE_ADMIN]
    assert can(ROLE_ADMIN, "products:write") and can(ROLE_ADMIN, "orders:manage")
    assert not can(ROLE_ADMIN, "settings:write") and not can(ROLE_ADMIN, "users:manage")
    assert not PERMISSIONS[ROLE_CUSTOMER]
    assert not can("content_manager", "products:write")  # the old role name grants nothing


# ------------------------------------------------------- reads stay public

def test_anonymous_can_read_products(client):
    assert client.get("/products").status_code == 200


def test_anonymous_can_read_categories(client):
    assert client.get("/categories").status_code == 200


# ------------------------------------------- catalogue writes need a role

def test_anonymous_cannot_create_category(client):
    response = client.post("/categories", json={"category_name": "smuggled"})

    assert response.status_code == 401
    assert "authentication required" in response.get_json()["error"]


def test_customer_cannot_create_category(client, customer_headers):
    response = client.post("/categories", headers=customer_headers, json={"category_name": "smuggled"})

    assert response.status_code == 403
    body = response.get_json()
    assert body["role"] == ROLE_CUSTOMER
    assert body["permission"] == "categories:write"


def test_admin_can_create_category(client, admin_headers):
    response = client.post("/categories", headers=admin_headers, json={"category_name": "networking"})

    assert response.status_code == 201


def test_superadmin_can_create_category(client, superadmin_headers):
    response = client.post("/categories", headers=superadmin_headers, json={"category_name": "storage"})

    assert response.status_code == 201


def test_customer_cannot_delete_product(client, customer_headers, category_with_product):
    listing = client.get(f"/categories/{category_with_product}").get_json()
    product_id = listing["products"][0]["product_id"]

    response = client.delete(f"/products/{product_id}", headers=customer_headers)

    assert response.status_code == 403


def test_admin_can_create_product(client, admin_headers, sample_category):
    response = client.post(
        "/products",
        headers=admin_headers,
        json={"product_name": "cat6 patch cable", "price": 45000, "category_id": sample_category},
    )

    assert response.status_code == 201


# ------------------------------------------------------------ registration

def test_registration_ignores_a_requested_role(client, session):
    """Self-registration is always a customer, whatever the client asks for."""
    response = client.post(
        "/users",
        json={"username": "sneaky", "email": "sneaky@example.com", "password": "password123", "role": ROLE_SUPERADMIN},
    )

    assert response.status_code == 201
    assert response.get_json()["user"]["role"] == ROLE_CUSTOMER


def test_login_token_carries_the_role(client, session):
    user = User(
        username="rina",
        email="rina@example.com",
        password_hash=generate_password_hash("password123"),
        role=ROLE_SUPERADMIN,
    )
    session.add(user)
    session.commit()

    login = client.post("/auth/login", json={"email": "rina@example.com", "password": "password123"})

    assert login.status_code == 200
    assert login.get_json()["user"]["role"] == ROLE_SUPERADMIN

    token = login.get_json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.get_json()["id"] == user.id
    # the token works on a superadmin-only route
    assert client.get("/users", headers={"Authorization": f"Bearer {token}"}).status_code == 200


def test_bad_tokens_answer_401_in_the_api_error_shape(client):
    for header in ("Bearer not.a.token", "Bearer abc"):
        response = client.get("/orders", headers={"Authorization": header})
        assert response.status_code == 401
        assert "error" in response.get_json()


# ------------------------------------------------------------------ orders

def _stranger(session, n):
    user = User(username=f"stranger{n}", email=f"stranger{n}@example.com", password_hash="x", role=ROLE_CUSTOMER)
    session.add(user)
    session.commit()
    return user


def _order_for(session, user_id, status="cancelled"):
    # cancelled: no stock is involved, so these tests only exercise access rules
    order = Order(user_id=user_id, order_status=status, shipping_address="jl. uji coba no. 1", total_amount=0)
    session.add(order)
    session.commit()
    return order.order_id


def test_anonymous_cannot_read_or_create_orders(client, session):
    order_id = _order_for(session, _stranger(session, 0).id)

    assert client.get("/orders").status_code == 401
    assert client.get(f"/orders/{order_id}").status_code == 401
    assert client.get("/orders?user_id=1").status_code == 401  # the old plain user_id form is gone
    response = client.post("/orders", json={"user_id": 1, "shipping_address": "jl. anon", "items": [{"product_id": 1}]})
    assert response.status_code == 401


def test_customer_cannot_read_another_users_order(client, session, customer_headers):
    order_id = _order_for(session, _stranger(session, 1).id)

    response = client.get(f"/orders/{order_id}", headers=customer_headers)

    assert response.status_code == 403


def test_customer_cannot_delete_another_users_order(client, session, customer_headers):
    order_id = _order_for(session, _stranger(session, 2).id)

    response = client.delete(f"/orders/{order_id}", headers=customer_headers)

    assert response.status_code == 403
    assert "your own orders" in response.get_json()["error"]


def test_admin_can_delete_another_users_order(client, session, admin_headers):
    order_id = _order_for(session, _stranger(session, 3).id)

    response = client.delete(f"/orders/{order_id}", headers=admin_headers)

    assert response.status_code == 200


def test_customer_cannot_change_an_order_status(client, session, customer_headers):
    owner = db.session.scalar(db.select(User).where(User.email == "customer@example.com"))
    order_id = _order_for(session, owner.id)

    response = client.put(f"/orders/{order_id}", headers=customer_headers, json={"order_status": "delivered"})

    assert response.status_code == 403


def test_staff_see_every_order_while_customers_see_only_their_own(client, session, admin_headers, customer_headers):
    owner = db.session.scalar(db.select(User).where(User.email == "customer@example.com"))
    _order_for(session, owner.id)
    _order_for(session, _stranger(session, 4).id)

    mine = client.get("/orders", headers=customer_headers).get_json()
    everything = client.get("/orders", headers=admin_headers).get_json()

    assert len(mine) == 1
    assert mine[0]["user_id"] == owner.id
    assert mine[0]["username"] == owner.username
    assert len(everything) == 2


# ----------------------------------------------------------------- profiles

def test_customer_cannot_read_another_users_profile(client, session, customer_headers):
    response = client.get(f"/users/{_stranger(session, 5).id}", headers=customer_headers)

    assert response.status_code == 403


def test_admin_cannot_read_another_users_profile(client, session, admin_headers):
    """Admins run the catalogue and orders; user accounts are the superadmin's."""
    response = client.get(f"/users/{_stranger(session, 6).id}", headers=admin_headers)

    assert response.status_code == 403


def test_superadmin_can_read_any_profile(client, session, superadmin_headers):
    response = client.get(f"/users/{_stranger(session, 7).id}", headers=superadmin_headers)

    assert response.status_code == 200
    assert response.get_json()["email"] == "stranger7@example.com"
