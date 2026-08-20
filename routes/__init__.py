"""Blueprint registration."""

from routes.categories import category_routes
from routes.orders import order_routes
from routes.products import product_routes
from routes.users import user_routes


def register_blueprints(app):
    app.register_blueprint(product_routes)
    app.register_blueprint(category_routes)
    app.register_blueprint(order_routes)
    app.register_blueprint(user_routes)
