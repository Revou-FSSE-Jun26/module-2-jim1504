"""Storefront content and settings: the editable homepage and About page, the store's
settings (name, time zone, contact) and its logo.

The validation rules are the storefront's own (RevoTech lib/content.ts, lib/settings.ts),
so the admin forms and this API reject exactly the same things.
"""

import re
from urllib.parse import urlparse

from flask import Blueprint, jsonify

from models import Product, SiteContent, SiteSettings, db
from routes.helpers import error, get_payload, require_permission

site_routes = Blueprint("site", __name__)

CONTENT_KEYS = ("home", "about")

# ---------------------------------------------------------------- content rules

# the banner artworks the storefront has (one slide per artwork)
SLIDE_IDS = ("new-arrivals", "rtx-50", "x3d-gaming", "nvme-speed", "peripherals", "build-your-rig")
FEATURED_MAX = 5
LIMITS = {
    "eyebrow": 40, "title": 80, "body": 240, "cta": 30, "href": 300,
    "pillarTitle": 60, "pillarBody": 200, "heading": 80,
    "name": 40, "tagline": 120, "intro": 1200,
    "skills": 16, "skillName": 40, "skillNote": 160,
    "projects": 9, "projectName": 60, "projectMeta": 80, "projectBody": 400,
}


def _is_link(value):
    """An internal path ("/products?category_id=4") or a full http(s) link."""
    if re.match(r"^/(?!/)", value):
        return True
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https") and bool(parsed.netloc)


class _Checker:
    def __init__(self):
        self.errors = []

    def text(self, value, path, limit, required=True):
        if not isinstance(value, str):
            self.errors.append(f"{path} must be text")
        elif required and not value.strip():
            self.errors.append(f"{path} is required")
        elif len(value) > limit:
            self.errors.append(f"{path} must be at most {limit} characters")

    def link(self, value, path):
        self.text(value, path, LIMITS["href"])
        if isinstance(value, str) and value.strip() and not _is_link(value.strip()):
            self.errors.append(f"{path} must start with / or https://")

    def items(self, value, path, minimum, maximum):
        """The dict entries of a list, after checking its length; [] when it isn't a list."""
        if not isinstance(value, list):
            self.errors.append(f"{path} must be a list")
            return []
        if not minimum <= len(value) <= maximum:
            span = minimum if minimum == maximum else f"{minimum} to {maximum}"
            self.errors.append(f"{path} must have {span} entries")
        entries = []
        for index, item in enumerate(value):
            if isinstance(item, dict):
                entries.append((item, f"{path}[{index}]"))
            else:
                self.errors.append(f"{path}[{index}] must be an object")
        return entries


def validate_home(doc, product_ids):
    c = _Checker()
    doc = doc if isinstance(doc, dict) else {}
    slides = doc.get("slides")
    for slide, path in c.items(slides, "slides", 1, len(SLIDE_IDS)):
        if slide.get("id") not in SLIDE_IDS:
            c.errors.append(f"{path}.id is not a known banner")
        c.text(slide.get("eyebrow"), f"{path}.eyebrow", LIMITS["eyebrow"])
        c.text(slide.get("title"), f"{path}.title", LIMITS["title"])
        c.text(slide.get("body"), f"{path}.body", LIMITS["body"])
        c.text(slide.get("cta"), f"{path}.cta", LIMITS["cta"])
        c.link(slide.get("href"), f"{path}.href")
        if not isinstance(slide.get("visible"), bool):
            c.errors.append(f"{path}.visible must be true or false")
    if isinstance(slides, list):
        if not any(isinstance(s, dict) and s.get("visible") is True for s in slides):
            c.errors.append("at least one slide must be visible")
        ids = [s.get("id") if isinstance(s, dict) else None for s in slides]
        if len(set(ids)) != len(ids):
            c.errors.append("each banner can be used once")
    for pillar, path in c.items(doc.get("pillars"), "pillars", 3, 3):
        c.text(pillar.get("title"), f"{path}.title", LIMITS["pillarTitle"])
        c.text(pillar.get("body"), f"{path}.body", LIMITS["pillarBody"])
    c.text(doc.get("featured_eyebrow"), "featured_eyebrow", LIMITS["eyebrow"])
    c.text(doc.get("featured_heading"), "featured_heading", LIMITS["heading"])
    featured = doc.get("featured_ids")
    if not isinstance(featured, list) or any(isinstance(i, bool) or not isinstance(i, int) for i in featured):
        c.errors.append("featured_ids must be a list of product ids")
    else:
        if len(featured) > FEATURED_MAX:
            c.errors.append(f"featured_ids can hold at most {FEATURED_MAX} products")
        if len(set(featured)) != len(featured):
            c.errors.append("featured_ids has duplicates")
        unknown = [str(i) for i in featured if i not in product_ids]
        if unknown:
            c.errors.append(f"featured_ids: no product {', '.join(unknown)}")
    return c.errors


def validate_about(doc):
    c = _Checker()
    doc = doc if isinstance(doc, dict) else {}
    c.text(doc.get("name"), "name", LIMITS["name"])
    c.text(doc.get("tagline"), "tagline", LIMITS["tagline"])
    c.text(doc.get("intro"), "intro", LIMITS["intro"])
    for skill, path in c.items(doc.get("skills"), "skills", 0, LIMITS["skills"]):
        c.text(skill.get("name"), f"{path}.name", LIMITS["skillName"])
        c.text(skill.get("note"), f"{path}.note", LIMITS["skillNote"], required=False)
    for project, path in c.items(doc.get("projects"), "projects", 0, LIMITS["projects"]):
        c.text(project.get("name"), f"{path}.name", LIMITS["projectName"])
        c.text(project.get("meta"), f"{path}.meta", LIMITS["projectMeta"], required=False)
        c.text(project.get("body"), f"{path}.body", LIMITS["projectBody"])
        c.link(project.get("href"), f"{path}.href")
    return c.errors


# ---------------------------------------------------------------- settings rules

TIMEZONES = ("Asia/Jakarta", "Asia/Makassar", "Asia/Jayapura", "Asia/Singapore", "UTC")
SETTINGS_LIMITS = {"shop_name": 40, "tagline": 120, "support_email": 120, "support_phone": 30}


def validate_settings(doc):
    doc = doc if isinstance(doc, dict) else {}
    errors = []
    for key, required in (("shop_name", True), ("tagline", False), ("support_email", False), ("support_phone", False)):
        value = doc.get(key)
        if not isinstance(value, str):
            errors.append(f"{key} must be text")
        elif required and not value.strip():
            errors.append(f"{key} is required")
        elif len(value) > SETTINGS_LIMITS[key]:
            errors.append(f"{key} must be at most {SETTINGS_LIMITS[key]} characters")
    email = doc.get("support_email")
    if isinstance(email, str) and email.strip() and not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email.strip()):
        errors.append("support_email must be an email address")
    phone = doc.get("support_phone")
    if isinstance(phone, str) and phone.strip() and not re.match(r"^\+?[\d\s()-]{6,}$", phone.strip()):
        errors.append("support_phone may contain digits, spaces, ( ) - and a leading +")
    if doc.get("timezone") not in TIMEZONES:
        errors.append("timezone is not one of the supported zones")
    if doc.get("clock") not in ("24h", "12h"):
        errors.append("clock must be 24h or 12h")
    if doc.get("date_style") not in ("short", "medium", "long"):
        errors.append("date_style must be short, medium or long")
    if not isinstance(doc.get("logo_glow"), bool):
        errors.append("logo_glow must be true or false")
    return errors


# The storefront writes these values straight into the logo's SVG markup, so only path
# commands/numbers and #rrggbb colours are accepted -- nothing that could close an attribute.
LOGO_MAX_PATHS = 1500
LOGO_PATH_DATA = re.compile(r"^[MLHVCSQTAZmlhvcsqtaz0-9eE.,\s+-]{1,200000}$")
LOGO_COLOUR = re.compile(r"^#[0-9a-fA-F]{6}$")


def validate_logo(doc):
    if not isinstance(doc, dict):
        return ["logo must be an object"]
    errors = []
    box = doc.get("box")
    if not isinstance(box, dict) or any(
        isinstance(box.get(k), bool) or not isinstance(box.get(k), (int, float)) for k in ("x", "y", "w", "h")
    ):
        errors.append("box must have numeric x, y, w and h")
    elif box["w"] <= 0 or box["h"] <= 0:
        errors.append("box must have a positive width and height")
    paths = doc.get("paths")
    if not isinstance(paths, list) or not paths:
        errors.append("paths must be a non-empty list")
    elif len(paths) > LOGO_MAX_PATHS:
        errors.append(f"paths can hold at most {LOGO_MAX_PATHS} shapes")
    elif any(
        not isinstance(p, dict)
        or not isinstance(p.get("d"), str)
        or not LOGO_PATH_DATA.match(p["d"])
        or not isinstance(p.get("fill"), str)
        or not LOGO_COLOUR.match(p["fill"])
        for p in paths
    ):
        errors.append("each path needs SVG path data (d) and a #rrggbb fill")
    colours = doc.get("colours")
    if not isinstance(colours, list) or any(not isinstance(c, str) or not LOGO_COLOUR.match(c) for c in colours):
        errors.append("colours must be a list of #rrggbb colours")
    return errors


def _settings_row():
    row = db.session.get(SiteSettings, 1)
    if row is None:
        raise LookupError("site_settings is empty -- run seed_db.py")
    return row


# ---------------------------------------------------------------- routes


@site_routes.get("/content/<key>")
def get_content(key):
    """The homepage ('home') or About page ('about') content document."""
    row = db.session.get(SiteContent, key) if key in CONTENT_KEYS else None
    if row is None:
        return error(f'content "{key}" not found', 404)
    return jsonify(row.content)


@site_routes.put("/content/<key>")
@require_permission("content:write")
def update_content(key):
    """Replace a page's content document, validated with the admin form's rules."""
    if key not in CONTENT_KEYS:
        return error(f'content "{key}" not found', 404)
    doc = get_payload()
    if key == "home":
        product_ids = set(db.session.scalars(db.select(Product.product_id)).all())
        errors = validate_home(doc, product_ids)
    else:
        errors = validate_about(doc)
    if errors:
        return error("validation failed", 400, details=errors)

    row = db.session.get(SiteContent, key)
    if row is None:
        db.session.add(SiteContent(key=key, content=doc))
    else:
        row.content = doc
    db.session.commit()
    return jsonify({"message": "content updated", "content": doc}), 200


@site_routes.get("/settings")
def get_settings():
    """The store's settings: name, tagline, time zone, date style, contact, logo version."""
    try:
        return jsonify(_settings_row().settings)
    except LookupError as exc:
        return error(str(exc), 503)


@site_routes.put("/settings")
@require_permission("settings:write")
def update_settings():
    """Replace the settings. logo_version is the server's to change, so it is kept."""
    doc = get_payload()
    errors = validate_settings(doc)
    if errors:
        return error("validation failed", 400, details=errors)

    row = _settings_row()
    settings = {
        "shop_name": doc["shop_name"].strip(),
        "tagline": doc["tagline"].strip(),
        "timezone": doc["timezone"],
        "clock": doc["clock"],
        "date_style": doc["date_style"],
        "support_email": doc["support_email"].strip(),
        "support_phone": doc["support_phone"].strip(),
        "logo_glow": doc["logo_glow"],
        "logo_version": row.settings.get("logo_version", 1),
    }
    row.settings = settings
    db.session.commit()
    return jsonify({"message": "settings updated", "settings": settings}), 200


@site_routes.get("/settings/logo")
def get_logo():
    """The logo as vector paths, or null when the store uses the default logo."""
    row = _settings_row()
    return jsonify({"logo": row.logo, "logo_version": row.settings.get("logo_version", 1)})


def _set_logo(logo):
    row = _settings_row()
    row.logo = logo
    row.settings = {**row.settings, "logo_version": row.settings.get("logo_version", 1) + 1}
    db.session.commit()
    return row.settings


@site_routes.put("/settings/logo")
@require_permission("settings:write")
def update_logo():
    """Store a new logo (already traced to vector paths by the storefront)."""
    doc = get_payload()
    errors = validate_logo(doc)
    if errors:
        return error("validation failed", 400, details=errors)
    logo = {"box": doc["box"], "paths": [{"d": p["d"], "fill": p["fill"]} for p in doc["paths"]], "colours": doc["colours"]}
    return jsonify({"message": "logo updated", "settings": _set_logo(logo)}), 200


@site_routes.delete("/settings/logo")
@require_permission("settings:write")
def reset_logo():
    """Go back to the default logo."""
    return jsonify({"message": "logo reset", "settings": _set_logo(None)}), 200
