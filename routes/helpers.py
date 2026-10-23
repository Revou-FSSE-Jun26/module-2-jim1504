"""Shared helpers for the route modules: payload parsing, validation, errors, identity."""

from decimal import Decimal, InvalidOperation
from functools import wraps

from flask import g, jsonify, request
from flask_jwt_extended import get_jwt, get_jwt_identity, verify_jwt_in_request

from models import ROLE_CUSTOMER, can


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


def text_or_none(value):
    """A trimmed string, or None for missing/blank input."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


# ---------------------------------------------------------------- RBAC

def current_claims():
    """Return (user_id, role) from the Bearer token, or (None, None) if absent.

    The role is read from the token rather than the database so that checking a
    permission costs no query. Tokens live one day, so a role change takes effect
    at the user's next login.
    """
    verify_jwt_in_request(optional=True)
    identity = get_jwt_identity()
    if identity is None:
        return None, None
    return int(identity), (get_jwt().get("role") or ROLE_CUSTOMER)


def require_auth(fn):
    """Reject the request unless it carries a valid Bearer token; sets g.user_id / g.role."""

    @wraps(fn)
    def wrapper(*args, **kwargs):
        user_id, role = current_claims()
        if user_id is None:
            return error("authentication required -- send a Bearer token", 401)
        g.user_id, g.role = user_id, role
        return fn(*args, **kwargs)

    return wrapper


def require_permission(permission):
    """Reject the request unless the token's role holds `permission` (see models.PERMISSIONS)."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user_id, role = current_claims()
            if user_id is None:
                return error("authentication required -- send a Bearer token", 401)
            if not can(role, permission):
                return error(
                    "your role is not allowed to perform this action",
                    403,
                    role=role,
                    permission=permission,
                )
            g.user_id, g.role = user_id, role
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def has_permission(permission):
    """Whether the authenticated caller (set by require_auth) holds `permission`."""
    return can(getattr(g, "role", None), permission)
