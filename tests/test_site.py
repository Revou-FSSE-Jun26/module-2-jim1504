"""Site content, settings and logo."""

import copy

import pytest

from tests.conftest import HOME, SETTINGS

LOGO = {
    "box": {"x": 0, "y": 0, "w": 100, "h": 40},
    "paths": [{"d": "M 0 0 L 10 0 L 10 10 Z", "fill": "#ff60f2"}],
    "colours": ["#ff60f2"],
}


def test_content_is_public_and_unknown_keys_404(client, site):
    assert client.get("/content/home").get_json()["featured_heading"] == "Fresh drops"
    assert client.get("/content/about").get_json()["name"] == "Jim"
    assert client.get("/content/footer").status_code == 404


def test_admin_updates_content_and_customer_cannot(client, site, admin_headers, customer_headers):
    doc = copy.deepcopy(HOME)
    doc["featured_heading"] = "This week"

    assert client.put("/content/home", headers=customer_headers, json=doc).status_code == 403
    response = client.put("/content/home", headers=admin_headers, json=doc)

    assert response.status_code == 200
    assert client.get("/content/home").get_json()["featured_heading"] == "This week"


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda d: d["slides"][0].update(visible=False), "at least one slide must be visible"),
        (lambda d: d["slides"][0].update(id="nope"), "slides[0].id is not a known banner"),
        (lambda d: d["slides"][0].update(href="javascript:alert(1)"), "slides[0].href must start with / or https://"),
        (lambda d: d.update(pillars=d["pillars"][:2]), "pillars must have 3 entries"),
        (lambda d: d.update(featured_ids=[999]), "featured_ids: no product 999"),
    ],
)
def test_home_content_is_validated(client, site, admin_headers, change, message):
    doc = copy.deepcopy(HOME)
    change(doc)

    response = client.put("/content/home", headers=admin_headers, json=doc)

    assert response.status_code == 400
    assert message in response.get_json()["details"]


def test_settings_are_superadmin_only_and_keep_the_logo_version(client, site, superadmin_headers, admin_headers):
    doc = {**SETTINGS, "shop_name": "  Jim Store ", "logo_version": 99}

    assert client.put("/settings", headers=admin_headers, json=doc).status_code == 403
    response = client.put("/settings", headers=superadmin_headers, json=doc)

    assert response.status_code == 200
    settings = client.get("/settings").get_json()
    assert settings["shop_name"] == "Jim Store"
    assert settings["logo_version"] == 1  # the server's to change, not the client's


def test_settings_are_validated(client, site, superadmin_headers):
    doc = {**SETTINGS, "timezone": "Mars/Olympus", "support_email": "nope", "clock": "13h"}

    response = client.put("/settings", headers=superadmin_headers, json=doc)

    details = response.get_json()["details"]
    assert response.status_code == 400
    assert {"timezone is not one of the supported zones", "support_email must be an email address", "clock must be 24h or 12h"} <= set(details)


def test_logo_upload_bumps_the_version_and_reset_clears_it(client, site, superadmin_headers):
    assert client.get("/settings/logo").get_json() == {"logo": None, "logo_version": 1}

    saved = client.put("/settings/logo", headers=superadmin_headers, json=LOGO)
    assert saved.status_code == 200
    assert saved.get_json()["settings"]["logo_version"] == 2
    assert client.get("/settings/logo").get_json()["logo"]["paths"] == LOGO["paths"]

    reset = client.delete("/settings/logo", headers=superadmin_headers)
    assert reset.get_json()["settings"]["logo_version"] == 3
    assert client.get("/settings/logo").get_json()["logo"] is None


@pytest.mark.parametrize(
    "path",
    [
        {"d": 'M 0 0" onload="alert(1)', "fill": "#ff60f2"},
        {"d": "M 0 0 L 1 1", "fill": "red\"/><script>"},
        {"d": "M 0 0 L 1 1", "fill": "url(#x)"},
    ],
)
def test_logo_rejects_anything_that_could_escape_the_svg(client, site, superadmin_headers, path):
    response = client.put("/settings/logo", headers=superadmin_headers, json={**LOGO, "paths": [path]})

    assert response.status_code == 400
