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

from app import app as flask_app  # noqa: E402
from models import Category, Product, User, db  # noqa: E402


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
                "truncate table order_items, orders, products, categories, users "
                "restart identity cascade"
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
