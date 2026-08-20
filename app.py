"""RevoShop API -- application entry point.

Run with:
    flask run                             
    waitress-serve --port=5000 app:app    works on Windows
    gunicorn app:app                      Linux deploy target
"""

import os
from datetime import timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from sqlalchemy import text

from models import Category, Order, Product, User, db, order_items
from routes import register_blueprints

load_dotenv()

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. Copy .env.example to .env and fill in your credentials."
    )

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
app.config["JWT_SECRET_KEY"] = app.config["SECRET_KEY"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(days=1)
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0") == "1"
app.json.sort_keys = False

db.init_app(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)

register_blueprints(app)


@app.get("/health")
def health():
    """Prove the SQLAlchemy connection to the database is live."""
    try:
        db.session.execute(text("select 1"))
    except Exception as exc:
        return jsonify({"status": "error", "database": "unreachable", "detail": str(exc)}), 503

    return jsonify({"status": "ok", "database": "connected"})


@app.shell_context_processor
def make_shell_context():
    """Preload the common objects into `flask shell`."""
    return {
        "db": db,
        "User": User,
        "Category": Category,
        "Product": Product,
        "Order": Order,
        "order_items": order_items,
    }


if __name__ == "__main__":
    app.run(debug=True)
