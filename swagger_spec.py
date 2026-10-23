"""OpenAPI description of the RevoShop API, served as Swagger UI at /apidocs.

Kept as one document here rather than as YAML docstrings inside the route
functions, so that adding documentation never touches working endpoint code.
When a route changes, update the matching entry in PATHS below.
"""

OPENAPI_VERSION = "3.0.3"

TITLE = "RevoShop API"
VERSION = "2.0.0"

DESCRIPTION = """REST API for a small online store: products, categories, orders, and user accounts.

Built on Flask, SQLAlchemy, and PostgreSQL. Orders and products form a many-to-many
relationship through the `order_items` association table, which also records the
quantity and the unit price paid at the time of purchase.

It is also the backend of the RevoTech storefront (Next.js): products carry the storefront's
gallery, specification table and manufacturer links, and the store's page content, settings and
logo live here too.

**Identity.** Catalogue, content and settings reads are public. Everything else -- orders,
profiles, and every write -- needs the Bearer token from `POST /auth/login`. An expired or
invalid token answers `401` in the same `{"error": ...}` shape as every other error.

**Roles.** Every account holds one of three roles, each a set of permissions:

| Permission | `superadmin` | `admin` | `customer` |
| --- | :---: | :---: | :---: |
| own orders and profile | yes | yes | yes |
| `products:write`, `categories:write` | yes | yes | |
| `orders:manage` -- every order, status changes | yes | yes | |
| `content:write` -- homepage and About | yes | yes | |
| `settings:write` -- shop name, logo, time zone | yes | | |
| `users:manage` -- user list, roles, password resets | yes | | |

Self-registration through `POST /users` always creates a `customer`; a `role` field
is ignored. A protected endpoint answers `401` without a token and `403` (naming the
missing permission) when the token's role lacks it. The role rides in the token, so a
role change takes effect at the user's next login.

**Stock.** Placing an order takes its items off the shelf in the same transaction;
cancelling puts them back and reopening takes them again.

**Hosting.** The API runs as a serverless deployment on Vercel, backed by a Supabase
PostgreSQL instance in Southeast Asia (Singapore).
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
        "official_url": {"type": "string", "nullable": True, "example": "https://www.intel.com/..."},
        "overview": {"type": "string", "nullable": True, "maxLength": 2000},
        "overview_source": {"type": "string", "nullable": True},
        "images": {
            "type": "array",
            "maxItems": 12,
            "items": {"type": "string"},
            "example": ["/products/intel-core-ultra-5-250k-plus.avif"],
            "description": "AVIF image URLs, first = primary: the storefront's /products/... photos or its uploads.",
        },
        "specs": {"type": "array", "maxItems": 150, "items": {"$ref": "#/components/schemas/SpecRow"}},
        "specs_source": {"type": "string", "nullable": True},
    },
}

_SPEC_ROW = {
    "type": "object",
    "required": ["label", "value"],
    "properties": {
        "group": {"type": "string", "maxLength": 60, "example": "Performance"},
        "label": {"type": "string", "maxLength": 80, "example": "Total Cores"},
        "value": {"type": "string", "maxLength": 400, "example": "18"},
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
        "username": {"type": "string", "example": "Siti Rahayu"},
        "item_count": {"type": "integer", "example": 4, "description": "Total quantity across the line items."},
    },
}

_ORDER_ITEM = {
    "type": "object",
    "properties": {
        "order_item_id": {"type": "integer", "example": 3},
        "product_id": {"type": "integer", "example": 16},
        "product_name": {"type": "string", "example": "arctic p12 argb case fan"},
        "quantity": {"type": "integer", "example": 2},
        "unit_price": {"type": "number", "format": "float", "example": 135000.0},
        "line_total": {"type": "number", "format": "float", "example": 270000.0},
    },
    "description": "unit_price is frozen at purchase time, so old orders keep their original total.",
}

_SETTINGS = {
    "type": "object",
    "properties": {
        "shop_name": {"type": "string", "maxLength": 40, "example": "RevoTech"},
        "tagline": {"type": "string", "maxLength": 120},
        "timezone": {"type": "string", "enum": ["Asia/Jakarta", "Asia/Makassar", "Asia/Jayapura", "Asia/Singapore", "UTC"]},
        "clock": {"type": "string", "enum": ["24h", "12h"]},
        "date_style": {"type": "string", "enum": ["short", "medium", "long"]},
        "support_email": {"type": "string", "maxLength": 120},
        "support_phone": {"type": "string", "maxLength": 30},
        "logo_glow": {"type": "boolean"},
        "logo_version": {"type": "integer", "example": 1, "description": "Set by the server; bumped on every logo change."},
    },
}

_LOGO = {
    "type": "object",
    "description": "The logo as vector paths, traced from an upload by the storefront.",
    "required": ["box", "paths", "colours"],
    "properties": {
        "box": {"type": "object", "properties": {k: {"type": "number"} for k in ("x", "y", "w", "h")}},
        "paths": {
            "type": "array",
            "maxItems": 1500,
            "items": {
                "type": "object",
                "properties": {
                    "d": {"type": "string", "description": "SVG path data: commands and numbers only."},
                    "fill": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"},
                },
            },
        },
        "colours": {"type": "array", "items": {"type": "string", "pattern": "^#[0-9a-fA-F]{6}$"}},
    },
}

SCHEMAS = {
    "Error": _ERROR,
    "ValidationError": _VALIDATION_ERROR,
    "User": _USER,
    "Category": _CATEGORY,
    "CategorySummary": {
        "allOf": [
            {"$ref": "#/components/schemas/Category"},
            {"type": "object", "properties": {"product_count": {"type": "integer", "example": 3}}},
        ]
    },
    "SpecRow": _SPEC_ROW,
    "Settings": _SETTINGS,
    "Logo": _LOGO,
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


_UNAUTHORIZED = {
    "description": "No Bearer token, or an expired/invalid one.",
    "content": _err({"error": "authentication required -- send a Bearer token"}),
}


def _forbidden(permission):
    return {
        "description": f"The token's role lacks `{permission}`.",
        "content": _err(
            {"error": "your role is not allowed to perform this action", "role": "customer", "permission": permission}
        ),
    }


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
                            "example": {"status": "error", "database": "unreachable"}
                        }
                    },
                },
            },
        }
    },
    "/users": {
        "get": {
            "tags": ["User"],
            "summary": "List every user (superadmin)",
            "security": [{"bearerAuth": []}],
            "responses": {
                "200": {"description": "All accounts, oldest first.", "content": _list("User")},
                "401": _UNAUTHORIZED,
                "403": _forbidden("users:manage"),
            },
        },
        "post": {
            "tags": ["User"],
            "summary": "Register a new customer",
            "description": "The password (at least 8 characters) is hashed with werkzeug before it is stored, and never appears in any response. The email is stored lower-case. A `role` in the body is ignored: registration always creates a `customer`.",
            "requestBody": _body(
                {
                    "username": {"type": "string"},
                    "email": {"type": "string"},
                    "password": {"type": "string", "format": "password"},
                    "phone_number": {"type": "string"},
                    "address": {"type": "string"},
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
                    "description": "A required field is missing (`fields`), or the email/password is invalid (`details`).",
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
            "description": "Your own profile, or any profile with `users:manage` (superadmin).",
            "security": [{"bearerAuth": []}],
            "parameters": [_ID_PARAM("user_id", 1)],
            "responses": {
                "401": _UNAUTHORIZED,
                "403": {"description": "Not your profile, and you lack `users:manage`.", "content": _err({"error": "you may only view your own profile"})},
                "200": {"description": "The user.", "content": _json("User")},
                "404": {"description": "No user with that id.", "content": _err({"error": "user not found", "id": 9999})},
            },
        },
        "put": {
            "tags": ["User"],
            "summary": "Update a profile, password or role",
            "description": (
                "Your own profile: `username`, `email`, `phone_number`, `address`, and `password` together with "
                "`current_password`. With `users:manage` (superadmin): the same for anyone, a password reset "
                "without the current one, and `role`. Nobody changes their own role, and the last superadmin "
                "cannot be demoted."
            ),
            "security": [{"bearerAuth": []}],
            "parameters": [_ID_PARAM("user_id", 2)],
            "requestBody": _body(
                {
                    "username": {"type": "string"},
                    "email": {"type": "string"},
                    "phone_number": {"type": "string", "nullable": True},
                    "address": {"type": "string", "nullable": True},
                    "password": {"type": "string", "format": "password", "minLength": 8},
                    "current_password": {"type": "string", "format": "password"},
                    "role": {"type": "string", "enum": ["customer", "admin", "superadmin"]},
                },
                example={"address": "jl. sudirman no. 45, jakarta 10210"},
            ),
            "responses": {
                "200": {"description": "Profile updated.", "content": _json("User", "user", "user updated")},
                "400": {
                    "description": "Validation failed.",
                    "content": _err({"error": "validation failed", "details": ["current password is not correct"]}, schema="ValidationError"),
                },
                "401": _UNAUTHORIZED,
                "403": {"description": "Not your profile, or a role change without `users:manage`.", "content": _err({"error": "you can only edit your own profile"})},
                "404": {"description": "No user with that id.", "content": _err({"error": "user not found", "id": 9999})},
                "409": {"description": "That email belongs to another account.", "content": _err({"error": "email already registered"})},
            },
        },
    },
    "/auth/me": {
        "get": {
            "tags": ["User"],
            "summary": "The user behind the token",
            "description": "Lets another service (the storefront's own helper routes) check who is calling and with which role.",
            "security": [{"bearerAuth": []}],
            "responses": {"200": {"description": "The user.", "content": _json("User")}, "401": _UNAUTHORIZED},
        }
    },
    "/products": {
        "get": {
            "tags": ["Product"],
            "summary": "List products",
            "description": "Ordered by `product_id`, active or not. `search` matches the name and description (case-insensitive); `category_id` filters.",
            "parameters": [
                {"name": "search", "in": "query", "required": False, "schema": {"type": "string"}, "example": "rtx"},
                {"name": "category_id", "in": "query", "required": False, "schema": {"type": "integer"}, "example": 4},
            ],
            "responses": {
                "200": {"description": "The matching products.", "content": _list("Product")},
                "400": {"description": "category_id is not an integer.", "content": _err({"error": "validation failed", "details": ["category_id must be an integer"]}, schema="ValidationError")},
            },
        },
        "post": {
            "tags": ["Product"],
            "security": [{"bearerAuth": []}],
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
                    "official_url": {"type": "string"},
                    "overview": {"type": "string", "maxLength": 2000},
                    "overview_source": {"type": "string"},
                    "images": {"type": "array", "maxItems": 12, "items": {"type": "string"}},
                    "specs": {"type": "array", "items": {"$ref": "#/components/schemas/SpecRow"}},
                    "specs_source": {"type": "string"},
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
                "401": _UNAUTHORIZED,
                "403": _forbidden("products:write"),
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
            "security": [{"bearerAuth": []}],
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
                    "official_url": {"type": "string"},
                    "overview": {"type": "string", "maxLength": 2000},
                    "overview_source": {"type": "string"},
                    "images": {"type": "array", "maxItems": 12, "items": {"type": "string"}},
                    "specs": {"type": "array", "items": {"$ref": "#/components/schemas/SpecRow"}},
                    "specs_source": {"type": "string"},
                },
                example={"price": 2750000.00, "stock_quantity": 30},
            ),
            "responses": {
                "401": _UNAUTHORIZED,
                "403": _forbidden("products:write"),
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
            "security": [{"bearerAuth": []}],
            "summary": "Delete a product",
            "description": (
                "Refused (409) while the product belongs to an order that is `pending`, `paid` or `shipped`. "
                "If only finished orders (`delivered`/`cancelled`) reference it, it is withdrawn from sale "
                "(`is_active: false`, `withdrawn: true`) instead, so those orders keep their items and totals. "
                "A product no order references is deleted."
            ),
            "parameters": [_ID_PARAM("product_id", 21)],
            "responses": {
                "401": _UNAUTHORIZED,
                "403": _forbidden("products:write"),
                "200": {
                    "description": "Product deleted, or withdrawn from sale.",
                    "content": {
                        "application/json": {
                            "examples": {
                                "deleted": {"value": {"message": "product deleted", "id": 21}},
                                "withdrawn": {
                                    "value": {"message": "product withdrawn from sale (it appears in past orders)", "id": 16, "withdrawn": True}
                                },
                            }
                        }
                    },
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
            "responses": {"200": {"description": "All categories, each with its `product_count`.", "content": _list("CategorySummary")}},
        },
        "post": {
            "tags": ["Category"],
            "security": [{"bearerAuth": []}],
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
                "401": _UNAUTHORIZED,
                "403": _forbidden("categories:write"),
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
            "security": [{"bearerAuth": []}],
            "summary": "Update a category",
            "parameters": [_ID_PARAM("category_id", 1)],
            "requestBody": _body(
                {"category_name": {"type": "string", "maxLength": 100}, "description": {"type": "string"}},
                example={"description": "cpu desktop intel, amd, dan workstation"},
            ),
            "responses": {
                "401": _UNAUTHORIZED,
                "403": _forbidden("categories:write"),
                "200": {"description": "Category updated.", "content": _json("Category", "category", "category updated")},
                "400": {"description": "Empty body, or validation failed.", "content": _err({"error": "no fields to update"}, schema="ValidationError")},
                "404": {"description": "No category with that id.", "content": _err({"error": "category not found", "id": 999})},
                "409": {"description": "That name is already taken.", "content": _err({"error": "category_name already exists"})},
            },
        },
        "delete": {
            "tags": ["Category"],
            "security": [{"bearerAuth": []}],
            "summary": "Delete a category",
            "description": "Refused while the category still has products, so no product is ever left pointing at a category that is gone.",
            "parameters": [_ID_PARAM("category_id", 7)],
            "responses": {
                "401": _UNAUTHORIZED,
                "403": _forbidden("categories:write"),
                "200": {"description": "Category deleted.", "content": {"application/json": {"example": {"message": "category deleted", "id": 7}}}},
                "404": {"description": "No category with that id.", "content": _err({"error": "category not found", "id": 999})},
                "409": {
                    "description": "Blocked: the category still has products.",
                    "content": _err(
                        {"error": "category cannot be deleted while products belong to it", "id": 1, "product_count": 3}
                    ),
                },
            },
        },
    },
    "/orders": {
        "get": {
            "tags": ["Order"],
            "summary": "List orders",
            "description": "Newest first, each with the customer's `username` and an `item_count`. With `orders:manage` (admin, superadmin) every order; otherwise your own.",
            "security": [{"bearerAuth": []}],
            "responses": {
                "200": {"description": "The orders.", "content": _list("Order")},
                "401": _UNAUTHORIZED,
            },
        },
        "post": {
            "tags": ["Order"],
            "security": [{"bearerAuth": []}],
            "summary": "Place a new order",
            "description": (
                "The owner is the token's user. Each item's `unit_price` is copied from the product's current price and "
                "frozen, `total_amount` is calculated by the server, and the items' stock is taken in the same "
                "transaction. Withdrawn products and quantities beyond the stock are refused. Only `orders:manage` may "
                "order for another `user_id` or set the initial `order_status`; everyone else's order starts `pending`."
            ),
            "requestBody": _body(
                {
                    "user_id": {"type": "integer", "description": "Only honoured with `orders:manage`."},
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
                    "shipping_address": "jl. merdeka no. 12, bandung, west java 40115",
                    "items": [{"product_id": 1, "quantity": 1}, {"product_id": 9, "quantity": 2}],
                },
            ),
            "responses": {
                "401": _UNAUTHORIZED,
                "201": {"description": "Order created.", "content": _json("OrderDetail", "order", "order created")},
                "409": {
                    "description": "Someone else bought the last units while the order was being placed.",
                    "content": _err({"error": "validation failed", "details": ["only 0 left of Kryonaut"]}, schema="ValidationError"),
                },
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
            "description": "Your own order, or any with `orders:manage`. Each item carries the product name, quantity, frozen unit price, and the calculated line total.",
            "security": [{"bearerAuth": []}],
            "parameters": [_ID_PARAM("order_id", 1)],
            "responses": {
                "200": {"description": "The order and its line items.", "content": _json("OrderDetail")},
                "401": _UNAUTHORIZED,
                "403": {"description": "Not your order.", "content": _err({"error": "you may only view your own orders", "id": 1})},
                "404": {"description": "No order with that id.", "content": _err({"error": "order not found", "id": 9999})},
            },
        },
        "put": {
            "tags": ["Order"],
            "security": [{"bearerAuth": []}],
            "summary": "Update an order's status or address (orders:manage)",
            "description": (
                "Cancelling puts the items back in stock; reopening a cancelled order takes them again and is refused "
                "(400) without enough stock. The response's `stock_changed` says whether stock moved. Line items cannot "
                "be changed after the order exists."
            ),
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
                "401": _UNAUTHORIZED,
                "403": _forbidden("orders:manage"),
                "200": {"description": "Order updated.", "content": _json("OrderDetail", "order", "order updated")},
                "400": {"description": "Empty body, unknown status, or blank address.", "content": _err({"error": "no fields to update"}, schema="ValidationError")},
                "404": {"description": "No order with that id.", "content": _err({"error": "order not found", "id": 9999})},
            },
        },
        "delete": {
            "tags": ["Order"],
            "security": [{"bearerAuth": []}],
            "summary": "Delete an order",
            "description": "Your own order, or any with `orders:manage`. Unless the order was cancelled, its items go back in stock. Its `order_items` rows go with it through `ON DELETE CASCADE`.",
            "parameters": [_ID_PARAM("order_id", 7)],
            "responses": {
                "401": _UNAUTHORIZED,
                "403": {"description": "Not your order.", "content": _err({"error": "you may only delete your own orders", "id": 7})},
                "200": {"description": "Order deleted.", "content": {"application/json": {"example": {"message": "order deleted", "id": 7}}}},
                "404": {"description": "No order with that id.", "content": _err({"error": "order not found", "id": 9999})},
                "409": {"description": "The order could not be deleted.", "content": _err({"error": "could not delete order"})},
            },
        },
    },
    "/content/{key}": {
        "get": {
            "tags": ["Site"],
            "summary": "A page's editable content",
            "description": "`home`: hero slides, pillars and featured products. `about`: profile, skills and projects.",
            "parameters": [{"name": "key", "in": "path", "required": True, "schema": {"type": "string", "enum": ["home", "about"]}}],
            "responses": {
                "200": {"description": "The content document.", "content": {"application/json": {"schema": {"type": "object"}}}},
                "404": {"description": "Unknown page.", "content": _err({"error": 'content "footer" not found'})},
            },
        },
        "put": {
            "tags": ["Site"],
            "summary": "Replace a page's content (content:write)",
            "description": "The whole document, validated with the storefront editor's rules (lengths, links, known banners, existing product ids).",
            "security": [{"bearerAuth": []}],
            "parameters": [{"name": "key", "in": "path", "required": True, "schema": {"type": "string", "enum": ["home", "about"]}}],
            "requestBody": {"required": True, "content": {"application/json": {"schema": {"type": "object"}}}},
            "responses": {
                "200": {"description": "Saved.", "content": {"application/json": {"example": {"message": "content updated", "content": {}}}}},
                "400": {"description": "Validation failed.", "content": _err({"error": "validation failed", "details": ["at least one slide must be visible"]}, schema="ValidationError")},
                "401": _UNAUTHORIZED,
                "403": _forbidden("content:write"),
                "404": {"description": "Unknown page.", "content": _err({"error": 'content "footer" not found'})},
            },
        },
    },
    "/settings": {
        "get": {
            "tags": ["Site"],
            "summary": "The store's settings",
            "responses": {"200": {"description": "The settings.", "content": _json("Settings")}},
        },
        "put": {
            "tags": ["Site"],
            "summary": "Replace the settings (settings:write)",
            "description": "`logo_version` is the server's and is kept whatever is sent.",
            "security": [{"bearerAuth": []}],
            "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Settings"}}}},
            "responses": {
                "200": {"description": "Saved.", "content": _json("Settings", "settings", "settings updated")},
                "400": {"description": "Validation failed.", "content": _err({"error": "validation failed", "details": ["timezone is not one of the supported zones"]}, schema="ValidationError")},
                "401": _UNAUTHORIZED,
                "403": _forbidden("settings:write"),
            },
        },
    },
    "/settings/logo": {
        "get": {
            "tags": ["Site"],
            "summary": "The logo as vector paths",
            "description": "`logo` is null while the store uses the storefront's default logo.",
            "responses": {
                "200": {
                    "description": "The logo and its version.",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {"logo": {"$ref": "#/components/schemas/Logo"}, "logo_version": {"type": "integer"}},
                            }
                        }
                    },
                }
            },
        },
        "put": {
            "tags": ["Site"],
            "summary": "Store a new logo (settings:write)",
            "description": "Vector paths traced by the storefront. Only SVG path commands/numbers and #rrggbb colours are accepted, since they are written into SVG markup. Bumps `logo_version`.",
            "security": [{"bearerAuth": []}],
            "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Logo"}}}},
            "responses": {
                "200": {"description": "Saved.", "content": _json("Settings", "settings", "logo updated")},
                "400": {"description": "Validation failed.", "content": _err({"error": "validation failed", "details": ["each path needs SVG path data (d) and a #rrggbb fill"]}, schema="ValidationError")},
                "401": _UNAUTHORIZED,
                "403": _forbidden("settings:write"),
            },
        },
        "delete": {
            "tags": ["Site"],
            "summary": "Go back to the default logo (settings:write)",
            "security": [{"bearerAuth": []}],
            "responses": {
                "200": {"description": "Reset.", "content": _json("Settings", "settings", "logo reset")},
                "401": _UNAUTHORIZED,
                "403": _forbidden("settings:write"),
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
        {"url": "https://revotech-m2.vercel.app", "description": "Production (Vercel)"},
        {"url": "http://127.0.0.1:5000", "description": "Local development"},
    ],
    "tags": [
        {"name": "Utility", "description": "Service health."},
        {"name": "User", "description": "Registration, login, profiles, and user management."},
        {"name": "Product", "description": "Full CRUD with search, storefront details, and a guard against deleting products in active orders."},
        {"name": "Category", "description": "Full CRUD, with a guard against deleting non-empty categories."},
        {"name": "Order", "description": "Orders and their line items, written through the order_items association table. Stock moves with the order."},
        {"name": "Site", "description": "The storefront's page content, store settings and logo."},
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
