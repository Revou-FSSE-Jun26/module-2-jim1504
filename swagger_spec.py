"""OpenAPI description of the RevoShop API, served as Swagger UI at /apidocs.

Kept as one document here rather than as YAML docstrings inside the route
functions, so that adding documentation never touches working endpoint code.
When a route changes, update the matching entry in PATHS below.
"""

OPENAPI_VERSION = "3.0.3"

TITLE = "RevoShop API"
VERSION = "1.0.0"

DESCRIPTION = """REST API for a small online store: products, categories, orders, and user accounts.

Built on Flask, SQLAlchemy, and PostgreSQL. Orders and products form a many-to-many
relationship through the `order_items` association table, which also records the
quantity and the unit price paid at the time of purchase.

**Identity.** Endpoints under Order accept either a Bearer token from `POST /auth/login`
or a plain `user_id` in the body or query string. Both are supported deliberately.

**Note.** The public instance runs on a free tier that sleeps after 15 minutes idle,
so the first request may take around 50 seconds.
"""

# ---------------------------------------------------------------- schemas

_ERROR = {
    "type": "object",
    "properties": {
        "error": {"type": "string", "example": "product not found"},
        "id": {"type": "integer", "example": 9999},
    },
}

_VALIDATION_ERROR = {
    "type": "object",
    "properties": {
        "error": {"type": "string", "example": "validation failed"},
        "details": {
            "type": "array",
            "items": {"type": "string"},
            "example": ["price must be 0 or greater", "category_id 99 does not exist"],
        },
    },
}

_USER = {
    "type": "object",
    "properties": {
        "id": {"type": "integer", "example": 1},
        "username": {"type": "string", "example": "andi pratama"},
        "email": {"type": "string", "example": "andi.pratama@example.com"},
        "phone_number": {"type": "string", "nullable": True, "example": "+62-812-1111-0001"},
        "address": {"type": "string", "nullable": True},
        "role": {"type": "string", "example": "customer"},
        "created_at": {"type": "string", "format": "date-time"},
    },
    "description": "password_hash is never included in any response.",
}

_CATEGORY = {
    "type": "object",
    "properties": {
        "category_id": {"type": "integer", "example": 1},
        "category_name": {"type": "string", "example": "processors"},
        "description": {"type": "string", "nullable": True, "example": "cpu desktop intel dan amd"},
        "created_at": {"type": "string", "format": "date-time"},
    },
}

_PRODUCT = {
    "type": "object",
    "properties": {
        "product_id": {"type": "integer", "example": 1},
        "category_id": {"type": "integer", "example": 1},
        "product_name": {"type": "string", "example": "intel core i5-14400f"},
        "description": {"type": "string", "nullable": True},
        "price": {"type": "number", "format": "float", "example": 2850000.0},
        "stock_quantity": {"type": "integer", "example": 25},
        "is_active": {"type": "boolean", "example": True},
        "created_at": {"type": "string", "format": "date-time"},
    },
}

_ORDER = {
    "type": "object",
    "properties": {
        "order_id": {"type": "integer", "example": 1},
        "user_id": {"type": "integer", "example": 1},
        "order_status": {
            "type": "string",
            "enum": ["pending", "paid", "shipped", "delivered", "cancelled"],
            "example": "delivered",
        },
        "total_amount": {"type": "number", "format": "float", "example": 455000.0},
        "shipping_address": {"type": "string"},
        "ordered_at": {"type": "string", "format": "date-time"},
    },
}

_ORDER_ITEM = {
    "type": "object",
    "properties": {
        "product_id": {"type": "integer", "example": 16},
        "product_name": {"type": "string", "example": "arctic p12 argb case fan"},
        "quantity": {"type": "integer", "example": 2},
        "unit_price": {"type": "number", "format": "float", "example": 135000.0},
        "line_total": {"type": "number", "format": "float", "example": 270000.0},
    },
    "description": "unit_price is frozen at purchase time, so old orders keep their original total.",
}

SCHEMAS = {
    "Error": _ERROR,
    "ValidationError": _VALIDATION_ERROR,
    "User": _USER,
    "Category": _CATEGORY,
    "CategoryDetail": {
        "allOf": [
            {"$ref": "#/components/schemas/Category"},
            {
                "type": "object",
                "properties": {
                    "products": {"type": "array", "items": {"$ref": "#/components/schemas/Product"}},
                    "product_count": {"type": "integer", "example": 3},
                },
            },
        ]
    },
    "Product": _PRODUCT,
    "Order": _ORDER,
    "OrderItem": _ORDER_ITEM,
    "OrderDetail": {
        "allOf": [
            {"$ref": "#/components/schemas/Order"},
            {
                "type": "object",
                "properties": {
                    "items": {"type": "array", "items": {"$ref": "#/components/schemas/OrderItem"}},
                    "item_count": {"type": "integer", "example": 2},
                },
            },
        ]
    },
}


def _json(schema_ref, wrapper_key=None, message=None):
    """Build a response content block for one schema."""
    schema = {"$ref": f"#/components/schemas/{schema_ref}"}
    if wrapper_key:
        schema = {
            "type": "object",
            "properties": {
                "message": {"type": "string", "example": message},
                wrapper_key: schema,
            },
        }
    return {"application/json": {"schema": schema}}


def _list(schema_ref):
    return {
        "application/json": {
            "schema": {"type": "array", "items": {"$ref": f"#/components/schemas/{schema_ref}"}}
        }
    }


def _err(example_message, schema="Error"):
    return {
        "application/json": {
            "schema": {"$ref": f"#/components/schemas/{schema}"},
            "example": example_message,
        }
    }


def _body(properties, required=None, example=None):
    schema = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    content = {"schema": schema}
    if example:
        content["example"] = example
    return {"required": True, "content": {"application/json": content}}


_ID_PARAM = lambda name, example: {  # noqa: E731
    "name": name,
    "in": "path",
    "required": True,
    "schema": {"type": "integer"},
    "example": example,
}

# ---------------------------------------------------------------- paths

PATHS = {
    "/health": {
        "get": {
            "tags": ["Utility"],
            "summary": "Service and database health",
            "description": "Runs `select 1` against PostgreSQL, so a 200 proves the API *and* its database are reachable.",
            "responses": {
                "200": {
                    "description": "Both the API and the database are up.",
                    "content": {
                        "application/json": {
                            "example": {"status": "ok", "database": "connected"}
                        }
                    },
                },
                "503": {
                    "description": "The API is up but the database is unreachable.",
                    "content": {
                        "application/json": {
                            "example": {
                                "status": "error",
                                "database": "unreachable",
                                "detail": "connection refused",
                            }
                        }
                    },
                },
            },
        }
    },
    "/users": {
        "post": {
            "tags": ["User"],
            "summary": "Register a new user",
            "description": "The password is hashed with werkzeug before it is stored, and never appears in any response.",
            "requestBody": _body(
                {
                    "username": {"type": "string"},
                    "email": {"type": "string"},
                    "password": {"type": "string", "format": "password"},
                    "phone_number": {"type": "string"},
                    "address": {"type": "string"},
                    "role": {"type": "string", "default": "customer"},
                },
                required=["username", "email", "password"],
                example={
                    "username": "budi setiawan",
                    "email": "budi.setiawan@example.com",
                    "password": "password123",
                    "phone_number": "+62-812-0000-0001",
                    "address": "jl. asia afrika no. 1, bandung",
                },
            ),
            "responses": {
                "201": {"description": "User created.", "content": _json("User", "user", "user registered")},
                "400": {
                    "description": "One or more required fields are missing.",
                    "content": _err({"error": "missing required fields", "fields": ["email"]}),
                },
                "409": {
                    "description": "That email is already registered.",
                    "content": _err({"error": "email already registered", "email": "budi.setiawan@example.com"}),
                },
            },
        }
    },
    "/auth/login": {
        "post": {
            "tags": ["User"],
            "summary": "Log in and receive an access token",
            "description": "A wrong email and a wrong password return the same message, so the response never reveals which accounts exist. Every seeded user shares the password `password123`.",
            "requestBody": _body(
                {"email": {"type": "string"}, "password": {"type": "string", "format": "password"}},
                required=["email", "password"],
                example={"email": "andi.pratama@example.com", "password": "password123"},
            ),
            "responses": {
                "200": {
                    "description": "Credentials accepted. The token is valid for one day.",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "message": {"type": "string", "example": "login successful"},
                                    "access_token": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIs..."},
                                    "user": {"$ref": "#/components/schemas/User"},
                                },
                            }
                        }
                    },
                },
                "400": {"description": "email or password missing.", "content": _err({"error": "missing required fields", "fields": ["password"]})},
                "401": {"description": "Unknown email or wrong password.", "content": _err({"error": "invalid email or password"})},
            },
        }
    },
    "/users/{user_id}": {
        "get": {
            "tags": ["User"],
            "summary": "Get one user by id",
            "parameters": [_ID_PARAM("user_id", 1)],
            "responses": {
                "200": {"description": "The user.", "content": _json("User")},
                "404": {"description": "No user with that id.", "content": _err({"error": "user not found", "id": 9999})},
            },
        }
    },
    "/products": {
        "get": {
            "tags": ["Product"],
            "summary": "List all products",
            "description": "Ordered by `product_id`. Returns every product, active or not.",
            "responses": {"200": {"description": "The full catalogue.", "content": _list("Product")}},
        },
        "post": {
            "tags": ["Product"],
            "summary": "Create a product",
            "description": "`category_id` is checked against the categories table, so an unknown category is rejected rather than raising a foreign key error.",
            "requestBody": _body(
                {
                    "product_name": {"type": "string"},
                    "price": {"type": "number", "format": "float", "minimum": 0},
                    "category_id": {"type": "integer", "minimum": 1},
                    "description": {"type": "string"},
                    "stock_quantity": {"type": "integer", "minimum": 0, "default": 0},
                    "is_active": {"type": "boolean", "default": True},
                },
                required=["product_name", "price", "category_id"],
                example={
                    "product_name": "amd ryzen 5 7600",
                    "description": "6 core, 12 thread, soket am5",
                    "price": 3150000.00,
                    "stock_quantity": 18,
                    "category_id": 1,
                },
            ),
            "responses": {
                "201": {"description": "Product created.", "content": _json("Product", "product", "product created")},
                "400": {
                    "description": "Validation failed.",
                    "content": _err(
                        {"error": "validation failed", "details": ["price must be 0 or greater"]},
                        schema="ValidationError",
                    ),
                },
            },
        },
    },
    "/products/{product_id}": {
        "get": {
            "tags": ["Product"],
            "summary": "Get one product by id",
            "parameters": [_ID_PARAM("product_id", 1)],
            "responses": {
                "200": {"description": "The product.", "content": _json("Product")},
                "404": {"description": "No product with that id.", "content": _err({"error": "product not found", "id": 9999})},
            },
        },
        "put": {
            "tags": ["Product"],
            "summary": "Update a product",
            "description": "A partial update: send only the fields you want to change.",
            "parameters": [_ID_PARAM("product_id", 1)],
            "requestBody": _body(
                {
                    "product_name": {"type": "string"},
                    "description": {"type": "string"},
                    "price": {"type": "number", "format": "float", "minimum": 0},
                    "stock_quantity": {"type": "integer", "minimum": 0},
                    "category_id": {"type": "integer", "minimum": 1},
                    "is_active": {"type": "boolean"},
                },
                example={"price": 2750000.00, "stock_quantity": 30},
            ),
            "responses": {
                "200": {"description": "Product updated.", "content": _json("Product", "product", "product updated")},
                "400": {
                    "description": "Empty body, or validation failed.",
                    "content": _err({"error": "no fields to update"}, schema="ValidationError"),
                },
                "404": {"description": "No product with that id.", "content": _err({"error": "product not found", "id": 9999})},
            },
        },
        "delete": {
            "tags": ["Product"],
            "summary": "Delete a product",
            "description": "Refused while the product still belongs to an order with status `pending`, `paid`, or `shipped`. Orders that are `delivered` or `cancelled` are finished, so they do not block the delete.",
            "parameters": [_ID_PARAM("product_id", 21)],
            "responses": {
                "200": {
                    "description": "Product deleted.",
                    "content": {"application/json": {"example": {"message": "product deleted", "id": 21}}},
                },
                "404": {"description": "No product with that id.", "content": _err({"error": "product not found", "id": 9999})},
                "409": {
                    "description": "Blocked: the product is still referenced by active orders.",
                    "content": _err(
                        {
                            "error": "product cannot be deleted while it has active orders",
                            "id": 7,
                            "active_orders": 2,
                        }
                    ),
                },
            },
        },
    },
    "/categories": {
        "get": {
            "tags": ["Category"],
            "summary": "List all categories",
            "responses": {"200": {"description": "All categories.", "content": _list("Category")}},
        },
        "post": {
            "tags": ["Category"],
            "summary": "Create a category",
            "requestBody": _body(
                {
                    "category_name": {"type": "string", "maxLength": 100},
                    "description": {"type": "string"},
                },
                required=["category_name"],
                example={"category_name": "networking", "description": "router, switch, dan kartu jaringan"},
            ),
            "responses": {
                "201": {"description": "Category created.", "content": _json("Category", "category", "category created")},
                "400": {
                    "description": "Validation failed.",
                    "content": _err(
                        {"error": "validation failed", "details": ["category_name is required"]},
                        schema="ValidationError",
                    ),
                },
                "409": {"description": "That name is already taken.", "content": _err({"error": "category_name already exists"})},
            },
        },
    },
    "/categories/{category_id}": {
        "get": {
            "tags": ["Category"],
            "summary": "Get one category with its products",
            "description": "Includes the category's products inline, plus a `product_count`.",
            "parameters": [_ID_PARAM("category_id", 1)],
            "responses": {
                "200": {"description": "The category and its products.", "content": _json("CategoryDetail")},
                "404": {"description": "No category with that id.", "content": _err({"error": "category not found", "id": 999})},
            },
        },
        "put": {
            "tags": ["Category"],
            "summary": "Update a category",
            "parameters": [_ID_PARAM("category_id", 1)],
            "requestBody": _body(
                {"category_name": {"type": "string", "maxLength": 100}, "description": {"type": "string"}},
                example={"description": "cpu desktop intel, amd, dan workstation"},
            ),
            "responses": {
                "200": {"description": "Category updated.", "content": _json("Category", "category", "category updated")},
                "400": {"description": "Empty body, or validation failed.", "content": _err({"error": "no fields to update"}, schema="ValidationError")},
                "404": {"description": "No category with that id.", "content": _err({"error": "category not found", "id": 999})},
                "409": {"description": "That name is already taken.", "content": _err({"error": "category_name already exists"})},
            },
        },
        "delete": {
            "tags": ["Category"],
            "summary": "Delete a category",
            "description": "Refused while the category still has products, so no product is ever left pointing at a category that is gone.",
            "parameters": [_ID_PARAM("category_id", 7)],
            "responses": {
                "200": {"description": "Category deleted.", "content": {"application/json": {"example": {"message": "category deleted", "id": 7}}}},
                "404": {"description": "No category with that id.", "content": _err({"error": "category not found", "id": 999})},
                "409": {
                    "description": "Blocked: the category still has products.",
                    "content": _err(
                        {"error": "category cannot be deleted while it has products", "id": 1, "product_count": 3}
                    ),
                },
            },
        },
    },
    "/orders": {
        "get": {
            "tags": ["Order"],
            "summary": "List the current user's orders",
            "description": "Identity comes from a Bearer token when one is sent, otherwise from `?user_id=`.",
            "parameters": [
                {
                    "name": "user_id",
                    "in": "query",
                    "required": False,
                    "schema": {"type": "integer"},
                    "example": 1,
                    "description": "Used only when no Bearer token is supplied.",
                }
            ],
            "responses": {
                "200": {"description": "That user's orders.", "content": _list("Order")},
                "400": {
                    "description": "No identity supplied.",
                    "content": _err({"error": "user_id is required (send a token or ?user_id=)"}),
                },
            },
        },
        "post": {
            "tags": ["Order"],
            "summary": "Place a new order",
            "description": "Each item's `unit_price` is copied from the product's current price and frozen, and `total_amount` is calculated by the server. A product may not appear twice in one order.",
            "requestBody": _body(
                {
                    "user_id": {"type": "integer", "description": "Omit when sending a Bearer token."},
                    "shipping_address": {"type": "string"},
                    "order_status": {
                        "type": "string",
                        "enum": ["pending", "paid", "shipped", "delivered", "cancelled"],
                        "default": "pending",
                    },
                    "items": {
                        "type": "array",
                        "minItems": 1,
                        "items": {
                            "type": "object",
                            "required": ["product_id"],
                            "properties": {
                                "product_id": {"type": "integer", "minimum": 1},
                                "quantity": {"type": "integer", "minimum": 1, "default": 1},
                            },
                        },
                    },
                },
                required=["shipping_address", "items"],
                example={
                    "user_id": 1,
                    "shipping_address": "jl. merdeka no. 12, bandung, west java 40115",
                    "items": [{"product_id": 1, "quantity": 1}, {"product_id": 9, "quantity": 2}],
                },
            ),
            "responses": {
                "201": {"description": "Order created.", "content": _json("OrderDetail", "order", "order created")},
                "400": {
                    "description": "No identity, unknown user, blank address, or invalid items.",
                    "content": _err(
                        {
                            "error": "validation failed",
                            "details": ["product_id 999 does not exist", "items[1].quantity must be 1 or greater"],
                        },
                        schema="ValidationError",
                    ),
                },
            },
        },
    },
    "/orders/{order_id}": {
        "get": {
            "tags": ["Order"],
            "summary": "Get one order with its items",
            "description": "Each item carries the product name, quantity, frozen unit price, and the calculated line total.",
            "parameters": [_ID_PARAM("order_id", 1)],
            "responses": {
                "200": {"description": "The order and its line items.", "content": _json("OrderDetail")},
                "404": {"description": "No order with that id.", "content": _err({"error": "order not found", "id": 9999})},
            },
        },
        "put": {
            "tags": ["Order"],
            "summary": "Update an order's status or address",
            "description": "Line items cannot be changed after the order exists; delete it and place a new one instead.",
            "parameters": [_ID_PARAM("order_id", 1)],
            "requestBody": _body(
                {
                    "order_status": {
                        "type": "string",
                        "enum": ["pending", "paid", "shipped", "delivered", "cancelled"],
                    },
                    "shipping_address": {"type": "string"},
                },
                example={"order_status": "shipped"},
            ),
            "responses": {
                "200": {"description": "Order updated.", "content": _json("OrderDetail", "order", "order updated")},
                "400": {"description": "Empty body, unknown status, or blank address.", "content": _err({"error": "no fields to update"}, schema="ValidationError")},
                "404": {"description": "No order with that id.", "content": _err({"error": "order not found", "id": 9999})},
            },
        },
        "delete": {
            "tags": ["Order"],
            "summary": "Delete an order",
            "description": "The order's rows in `order_items` go with it through `ON DELETE CASCADE`. Products themselves are untouched.",
            "parameters": [_ID_PARAM("order_id", 7)],
            "responses": {
                "200": {"description": "Order deleted.", "content": {"application/json": {"example": {"message": "order deleted", "id": 7}}}},
                "404": {"description": "No order with that id.", "content": _err({"error": "order not found", "id": 9999})},
                "409": {"description": "The order could not be deleted.", "content": _err({"error": "could not delete order"})},
            },
        },
    },
}

SWAGGER_TEMPLATE = {
    "openapi": OPENAPI_VERSION,
    "info": {
        "title": TITLE,
        "version": VERSION,
        "description": DESCRIPTION,
    },
    "servers": [
        {"url": "https://module-2-jim1504.onrender.com", "description": "Production (Render)"},
        {"url": "http://127.0.0.1:5000", "description": "Local development"},
    ],
    "tags": [
        {"name": "Utility", "description": "Service health."},
        {"name": "User", "description": "Registration, login, and lookup."},
        {"name": "Product", "description": "Full CRUD, with a guard against deleting products in active orders."},
        {"name": "Category", "description": "Full CRUD, with a guard against deleting non-empty categories."},
        {"name": "Order", "description": "Orders and their line items, written through the order_items association table."},
    ],
    "components": {
        "schemas": SCHEMAS,
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Paste the `access_token` returned by POST /auth/login.",
            }
        },
    },
    "paths": PATHS,
}

SWAGGER_CONFIG = {
    # This key must live in the config, not in the template. Flasgger reads
    # `config['openapi']` to decide which version field to emit: with it set it
    # writes `openapi`, and without it it falls back to `swagger: "2.0"`. Setting
    # the version only in the template left both fields in the served document,
    # and Swagger UI refuses to render a spec that carries the two at once.
    "openapi": OPENAPI_VERSION,
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}
