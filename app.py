from flask import Flask, jsonify
from flask_migrate import Migrate
from sqlalchemy import text

from models import Category, Order, Product, User, db, order_items
from routes import product_routes, user_routes

app = Flask(__name__)

# Format: postgresql://user:password@host:port/dbname -- suka lupa
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:root@localhost:5432/revoshop_db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.json.sort_keys = False

db.init_app(app)
migrate = Migrate(app, db)

app.register_blueprint(product_routes)
app.register_blueprint(user_routes)


@app.get("/health")
def health():
    """Prove the SQLAlchemy connection to revoshop_db is live."""
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
