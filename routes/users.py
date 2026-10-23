"""User endpoints: registration, login, profiles and user management."""

import re

from flask import Blueprint, g, jsonify
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from models import ROLE_CUSTOMER, ROLE_SUPERADMIN, ROLES, User, db
from routes.helpers import (
    error,
    get_payload,
    has_permission,
    require_auth,
    require_fields,
    require_permission,
    text_or_none,
)

user_routes = Blueprint("users", __name__)

MIN_PASSWORD = 8
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _password_ok(user, password):
    try:
        return check_password_hash(user.password_hash, password)
    except ValueError:
        # Stored hash is not in a format werkzeug understands (legacy seed data).
        return False


@user_routes.post("/users")
def register():
    """Create a customer account from JSON input."""
    data = get_payload()

    missing = require_fields(data, "username", "email", "password")
    if missing:
        return error("missing required fields", 400, fields=missing)

    email = str(data["email"]).strip().lower()
    details = []
    if not EMAIL.match(email):
        details.append("email must be an email address")
    if len(str(data["password"])) < MIN_PASSWORD:
        details.append(f"password must be at least {MIN_PASSWORD} characters")
    if details:
        return error("validation failed", 400, details=details)

    user = User(
        username=str(data["username"]).strip(),
        email=email,
        password_hash=generate_password_hash(str(data["password"])),
        phone_number=text_or_none(data.get("phone_number")),
        address=text_or_none(data.get("address")),
        # role is deliberately NOT read from the request: self-registration is
        # always a customer. Roles are granted by a superadmin (PUT /users/<id>).
        role=ROLE_CUSTOMER,
    )

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # email carries a unique constraint
        db.session.rollback()
        return error("email already registered", 409, email=email)

    return jsonify({"message": "user registered", "user": user.to_dict()}), 201


@user_routes.post("/auth/login")
def login():
    """Verify credentials and issue an access token."""
    data = get_payload()

    missing = require_fields(data, "email", "password")
    if missing:
        return error("missing required fields", 400, fields=missing)

    user = db.session.scalar(db.select(User).where(User.email == str(data["email"]).strip().lower()))

    # The same generic message for both cases, so the response never reveals
    # whether the email exists.
    if user is None or not _password_ok(user, data["password"]):
        return error("invalid email or password", 401)

    # Flask-JWT-Extended 4.x requires the identity to be a string.
    # The role rides in the token, so checking a permission costs no query.
    token = create_access_token(identity=str(user.id), additional_claims={"role": user.role})
    return jsonify({"message": "login successful", "access_token": token, "user": user.to_dict()}), 200


@user_routes.get("/auth/me")
@require_auth
def me():
    """The user behind the Bearer token -- lets other services check who is calling."""
    user = db.session.get(User, g.user_id)
    if user is None:
        return error("user not found", 404, id=g.user_id)
    return jsonify(user.to_dict())


@user_routes.get("/users")
@require_permission("users:manage")
def list_users():
    """Every account, oldest first (superadmin)."""
    users = db.session.scalars(db.select(User).order_by(User.id)).all()
    return jsonify([user.to_dict() for user in users])


@user_routes.get("/users/<int:user_id>")
@require_auth
def get_user(user_id):
    """Return a single user by id. Own profile only, unless you manage users."""
    if user_id != g.user_id and not has_permission("users:manage"):
        return error("you may only view your own profile", 403)

    user = db.session.get(User, user_id)
    if user is None:
        return error("user not found", 404, id=user_id)
    return jsonify(user.to_dict())


@user_routes.put("/users/<int:user_id>")
@require_auth
def update_user(user_id):
    """Edit a profile. What may change depends on who is asking:

      own profile    username, email, phone_number, address; password with current_password
      users:manage   the same for anyone, a password reset without the current one, and the role

    Guard rails: an email belongs to one account, nobody changes their own role (a
    self-demotion would lock the dashboard), and the last superadmin stays one.
    """
    target = db.session.get(User, user_id)
    if target is None:
        return error("user not found", 404, id=user_id)

    manager = has_permission("users:manage")
    self_edit = user_id == g.user_id
    if not manager and not self_edit:
        return error("you can only edit your own profile", 403)

    data = get_payload()
    if not data:
        return error("no fields to update", 400)

    details = []
    changes = {}

    if "username" in data:
        username = text_or_none(data["username"])
        if username is None:
            details.append("username is required")
        else:
            changes["username"] = username

    if "email" in data:
        email = str(data["email"] or "").strip().lower()
        if not EMAIL.match(email):
            details.append("email must be an email address")
        else:
            owner = db.session.scalar(db.select(User).where(User.email == email))
            if owner is not None and owner.id != user_id:
                return error("email already registered", 409, email=email)
            changes["email"] = email

    for field in ("phone_number", "address"):
        if field in data:
            changes[field] = text_or_none(data[field])

    if "password" in data:
        password = str(data["password"] or "")
        if len(password) < MIN_PASSWORD:
            details.append(f"password must be at least {MIN_PASSWORD} characters")
        # changing your own password needs the current one, even as a superadmin
        elif self_edit and not _password_ok(target, str(data.get("current_password") or "")):
            details.append("current password is not correct")
        else:
            changes["password_hash"] = generate_password_hash(password)

    if "role" in data:
        role = data["role"]
        if not manager:
            return error("only a superadmin can change roles", 403)
        if role not in ROLES:
            details.append(f"role must be one of {', '.join(ROLES)}")
        elif self_edit and role != target.role:
            details.append("you cannot change your own role")
        elif target.role == ROLE_SUPERADMIN and role != ROLE_SUPERADMIN and (
            db.session.scalar(db.select(db.func.count()).select_from(User).where(User.role == ROLE_SUPERADMIN)) == 1
        ):
            details.append("the last superadmin cannot be demoted")
        else:
            changes["role"] = role

    if details:
        return error("validation failed", 400, details=details)

    for field, value in changes.items():
        setattr(target, field, value)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("email already registered", 409)

    return jsonify({"message": "user updated", "user": target.to_dict()}), 200
