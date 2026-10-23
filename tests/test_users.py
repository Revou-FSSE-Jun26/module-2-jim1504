"""Users: registration rules, the superadmin's user list, and profile/role updates."""

from werkzeug.security import check_password_hash, generate_password_hash

from models import ROLE_ADMIN, ROLE_CUSTOMER, ROLE_SUPERADMIN, User, db


def _user(email):
    return db.session.scalar(db.select(User).where(User.email == email))


def test_registration_validates_email_and_password(client, session):
    response = client.post("/users", json={"username": "x", "email": "not-an-email", "password": "short"})

    assert response.status_code == 400
    details = response.get_json()["details"]
    assert "email must be an email address" in details
    assert "password must be at least 8 characters" in details


def test_registration_lowercases_the_email(client, session):
    response = client.post("/users", json={"username": "Ana", "email": "Ana@Example.COM", "password": "password123"})

    assert response.status_code == 201
    assert response.get_json()["user"]["email"] == "ana@example.com"
    login = client.post("/auth/login", json={"email": "ANA@example.com", "password": "password123"})
    assert login.status_code == 200


def test_only_a_superadmin_lists_users(client, superadmin_headers, admin_headers, customer_headers):
    assert client.get("/users", headers=customer_headers).status_code == 403
    assert client.get("/users", headers=admin_headers).status_code == 403
    rows = client.get("/users", headers=superadmin_headers).get_json()
    assert {u["email"] for u in rows} == {"superadmin@example.com", "admin@example.com", "customer@example.com"}
    assert all("password_hash" not in u for u in rows)


def test_customer_edits_own_profile(client, customer_headers):
    me = _user("customer@example.com")

    response = client.put(
        f"/users/{me.id}",
        headers=customer_headers,
        json={"username": "Cust", "phone_number": "  ", "address": " Jl. Baru 2 "},
    )

    assert response.status_code == 200
    user = response.get_json()["user"]
    assert (user["username"], user["phone_number"], user["address"]) == ("Cust", None, "Jl. Baru 2")


def test_customer_cannot_edit_someone_else(client, admin_headers, customer_headers):
    other = _user("admin@example.com")

    assert client.put(f"/users/{other.id}", headers=customer_headers, json={"username": "x"}).status_code == 403


def test_changing_your_own_password_needs_the_current_one(client, customer_headers):
    me = _user("customer@example.com")

    wrong = client.put(f"/users/{me.id}", headers=customer_headers, json={"password": "newpassword1", "current_password": "nope"})
    right = client.put(f"/users/{me.id}", headers=customer_headers, json={"password": "newpassword1", "current_password": "password123"})

    assert wrong.status_code == 400
    assert "current password is not correct" in wrong.get_json()["details"]
    assert right.status_code == 200
    db.session.expire_all()
    assert check_password_hash(_user("customer@example.com").password_hash, "newpassword1")


def test_superadmin_resets_someone_elses_password_without_the_current_one(client, superadmin_headers, customer_headers):
    target = _user("customer@example.com")

    response = client.put(f"/users/{target.id}", headers=superadmin_headers, json={"password": "resetpass99"})

    assert response.status_code == 200
    db.session.expire_all()
    assert check_password_hash(_user("customer@example.com").password_hash, "resetpass99")


def test_email_must_stay_unique(client, admin_headers, customer_headers):
    me = _user("customer@example.com")

    response = client.put(f"/users/{me.id}", headers=customer_headers, json={"email": "ADMIN@example.com"})

    assert response.status_code == 409


def test_role_changes(client, session, superadmin_headers, admin_headers, customer_headers):
    customer = _user("customer@example.com")
    superadmin = _user("superadmin@example.com")

    # only users:manage may change a role
    assert client.put(f"/users/{customer.id}", headers=admin_headers, json={"role": ROLE_ADMIN}).status_code == 403
    assert client.put(f"/users/{customer.id}", headers=customer_headers, json={"role": ROLE_ADMIN}).status_code == 403

    promoted = client.put(f"/users/{customer.id}", headers=superadmin_headers, json={"role": ROLE_ADMIN})
    assert promoted.status_code == 200
    assert promoted.get_json()["user"]["role"] == ROLE_ADMIN

    unknown = client.put(f"/users/{customer.id}", headers=superadmin_headers, json={"role": "content_manager"})
    assert unknown.status_code == 400

    # nobody changes their own role, and the last superadmin stays one
    own = client.put(f"/users/{superadmin.id}", headers=superadmin_headers, json={"role": ROLE_CUSTOMER})
    assert "you cannot change your own role" in own.get_json()["details"]


def test_the_last_superadmin_cannot_be_demoted(client, session, superadmin_headers):
    other = User(username="boss", email="boss@example.com", password_hash=generate_password_hash("password123"), role=ROLE_SUPERADMIN)
    session.add(other)
    session.commit()

    # with two superadmins, one may demote the other
    first = client.put(f"/users/{other.id}", headers=superadmin_headers, json={"role": ROLE_ADMIN})
    assert first.status_code == 200

    # Now make `other` the only superadmin in the database. The caller's token still says
    # superadmin (tokens carry the role until they expire), so the request is allowed in --
    # and the guard, which counts superadmins in the database, must refuse it.
    db.session.get(User, other.id).role = ROLE_SUPERADMIN
    _user("superadmin@example.com").role = ROLE_CUSTOMER
    session.commit()
    last = client.put(f"/users/{other.id}", headers=superadmin_headers, json={"role": ROLE_ADMIN})
    assert last.status_code == 400
    assert "the last superadmin cannot be demoted" in last.get_json()["details"]
