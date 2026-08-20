"""User endpoints: registration, login, and retrieval."""

from flask import Blueprint, jsonify
from flask_jwt_extended import create_access_token
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from models import User, db
from routes.helpers import error, get_payload, require_fields

user_routes = Blueprint("users", __name__)


@user_routes.post("/users")
def register():
    """Create a User from JSON input and save it with the session."""
    data = get_payload()

    missing = require_fields(data, "username", "email", "password")
    if missing:
        return error("missing required fields", 400, fields=missing)

    user = User(
        username=data["username"],
        email=data["email"],
        password_hash=generate_password_hash(data["password"]),
        phone_number=data.get("phone_number"),
        address=data.get("address"),
        role=data.get("role", "customer"),
    )

    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        # email carries a unique constraint
        db.session.rollback()
        return error("email already registered", 409, email=data["email"])

    return jsonify({"message": "user registered", "user": user.to_dict()}), 201


@user_routes.post("/auth/login")
def login():
    """Verify credentials and issue an access token."""
    data = get_payload()

    missing = require_fields(data, "email", "password")
    if missing:
        return error("missing required fields", 400, fields=missing)

    user = db.session.scalar(db.select(User).where(User.email == data["email"]))

    # The same generic message for both cases, so the response never reveals
    # whether the email exists.
    if user is None:
        return error("invalid email or password", 401)

    try:
        valid = check_password_hash(user.password_hash, data["password"])
    except ValueError:
        # Stored hash is not in a format werkzeug understands (legacy seed data).
        valid = False

    if not valid:
        return error("invalid email or password", 401)

    # Flask-JWT-Extended 4.x requires the identity to be a string.
    token = create_access_token(identity=str(user.id))
    return jsonify(
        {"message": "login successful", "access_token": token, "user": user.to_dict()}
    ), 200


@user_routes.get("/users/<int:user_id>")
def get_user(user_id):
    """Return a single user by id, or 404 when there is no such user."""
    user = db.session.get(User, user_id)
    if user is None:
        return error("user not found", 404, id=user_id)
    return jsonify(user.to_dict())
