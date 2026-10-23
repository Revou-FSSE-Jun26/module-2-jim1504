"""Pytest fixtures.

The suite runs against a separate database (TEST_DATABASE_URL) so it can never
touch real data. DATABASE_URL is overridden *before* app is imported, because
app.py reads it at import time and Flask-SQLAlchemy binds the engine during
init_app().
"""

import os

import pytest
from dotenv import load_dotenv

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set. Add it to your .env file.")

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from flask_jwt_extended import create_access_token  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

from app import app as flask_app  # noqa: E402
from models import (  # noqa: E402
    ROLE_ADMIN,
    ROLE_CUSTOMER,
    ROLE_SUPERADMIN,
    Category,
    Product,
    SiteContent,
    SiteSettings,
    User,
    db,
)


@pytest.fixture(scope="session")
def app():
    """Build the schema once for the whole session, then tear it down."""
    flask_app.config.update(TESTING=True)
    with flask_app.app_context():
        db.drop_all()
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def session(app):
    """Give each test a clean database, so tests never depend on each other."""
    with app.app_context():
        db.session.execute(
            db.text(
                "truncate table order_items, orders, products, categories, users, "
                "site_content, site_settings restart identity cascade"
            )
        )
        db.session.commit()
        yield db.session
        db.session.rollback()


@pytest.fixture()
def client(app, session):
    return app.test_client()


@pytest.fixture()
def sample_category(session):
    """A category with no products attached -- safe to delete."""
    category = Category(category_name="electronics", description="gadgets and audio gear")
    session.add(category)
    session.commit()
    return category.category_id


@pytest.fixture()
def category_with_product(session):
    """A category that has a product, so deletion must be refused."""
    category = Category(category_name="books", description="printed books")
    session.add(category)
    session.flush()
    session.add(
        Product(
            category_id=category.category_id,
            product_name="clean code",
            price="38.25",
            stock_quantity=30,
        )
    )
    session.commit()
    return category.category_id


# ---------------------------------------------------------------- RBAC fixtures

def _make_user(session, email, role):
    user = User(
        username=email.split("@")[0],
        email=email,
        password_hash=generate_password_hash("password123"),
        role=role,
    )
    session.add(user)
    session.commit()
    return user


def _auth_header(app, user):
    """Build the Authorization header a real client would send after logging in."""
    with app.app_context():
        token = create_access_token(
            identity=str(user.id), additional_claims={"role": user.role}
        )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def superadmin_headers(app, session):
    """Superadmin -- everything, including users and store settings."""
    return _auth_header(app, _make_user(session, "superadmin@example.com", ROLE_SUPERADMIN))


@pytest.fixture()
def admin_headers(app, session):
    """Admin -- catalogue, every order, page content; not users or settings."""
    return _auth_header(app, _make_user(session, "admin@example.com", ROLE_ADMIN))


@pytest.fixture()
def customer_headers(app, session):
    return _auth_header(app, _make_user(session, "customer@example.com", ROLE_CUSTOMER))


# ---------------------------------------------------------------- site fixtures

SETTINGS = {
    "shop_name": "RevoTech",
    "tagline": "PC parts",
    "timezone": "Asia/Jakarta",
    "clock": "24h",
    "date_style": "medium",
    "support_email": "support@example.com",
    "support_phone": "+62 21 5000 1234",
    "logo_glow": True,
    "logo_version": 1,
}

HOME = {
    "slides": [
        {"id": "rtx-50", "eyebrow": "Graphics", "title": "RTX 50", "body": "New cards.", "cta": "Shop", "href": "/products", "visible": True}
    ],
    "pillars": [{"title": f"Pillar {n}", "body": "Body."} for n in range(3)],
    "featured_eyebrow": "New arrivals",
    "featured_heading": "Fresh drops",
    "featured_ids": [],
}

ABOUT = {"name": "Jim", "tagline": "Developer", "intro": "Hello.", "skills": [], "projects": []}


@pytest.fixture()
def site(session):
    """The settings row and both content documents, as seed_db.py creates them."""
    session.add(SiteSettings(id=1, settings=dict(SETTINGS), logo=None))
    session.add_all([SiteContent(key="home", content=HOME), SiteContent(key="about", content=ABOUT)])
    session.commit()
