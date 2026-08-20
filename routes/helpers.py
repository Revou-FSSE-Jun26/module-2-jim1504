"""Shared helpers for the route modules: payload parsing, validation, errors, identity."""

from decimal import Decimal, InvalidOperation

from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request


def get_payload():
    """Return the JSON body as a dict, never None."""
    return request.get_json(silent=True) or {}


def error(message, status, **extra):
    """Build a consistent JSON error response."""
    payload = {"error": message}
    payload.update(extra)
    return jsonify(payload), status


def require_fields(payload, *fields):
    """Return the list of required fields that are missing or blank."""
    return [field for field in fields if payload.get(field) in (None, "")]


def parse_decimal(value, field, minimum=0):
    """Validate a money-like field. Returns (value, None) or (None, message)."""
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None, f"{field} must be a number"
    if minimum is not None and number < minimum:
        return None, f"{field} must be {minimum} or greater"
    return number, None


def parse_int(value, field, minimum=0):
    """Validate an integer field. Returns (value, None) or (None, message)."""
    if isinstance(value, bool) or value is None:
        return None, f"{field} must be an integer"
    try:
        number = int(value)
    except (TypeError, ValueError):
        return None, f"{field} must be an integer"
    if minimum is not None and number < minimum:
        return None, f"{field} must be {minimum} or greater"
    return number, None


def resolve_user_id(payload=None):
    """Identity for order endpoints.

    Prefers a Bearer token when one is supplied, and falls back to `user_id` in
    the JSON body or the query string. The checkpoint brief allows the plain
    `user_id` form, so requiring a token would break that contract; accepting
    both keeps the endpoints usable either way.
    """
    verify_jwt_in_request(optional=True)
    identity = get_jwt_identity()
    if identity is not None:
        return int(identity)

    if payload and payload.get("user_id") is not None:
        try:
            return int(payload["user_id"])
        except (TypeError, ValueError):
            return None

    return request.args.get("user_id", type=int)
