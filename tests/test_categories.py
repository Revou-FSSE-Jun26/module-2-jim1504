"""Category CRUD tests -- happy path and error case for all five endpoints."""


# ---------------------------------------------------------------- GET /categories

def test_list_categories_returns_all(client, sample_category):
    response = client.get("/categories")

    assert response.status_code == 200
    body = response.get_json()
    assert isinstance(body, list)
    assert len(body) == 1
    assert body[0]["category_name"] == "electronics"


def test_list_categories_empty_is_still_200(client):
    response = client.get("/categories")

    assert response.status_code == 200
    assert response.get_json() == []


# ----------------------------------------------------------- GET /categories/<id>

def test_get_category_includes_its_products(client, category_with_product):
    response = client.get(f"/categories/{category_with_product}")

    assert response.status_code == 200
    body = response.get_json()
    assert body["category_name"] == "books"
    assert body["product_count"] == 1
    assert body["products"][0]["product_name"] == "clean code"


def test_get_category_unknown_id_returns_404(client):
    response = client.get("/categories/9999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "category not found"


# ---------------------------------------------------------------- POST /categories

def test_create_category_returns_201(client, session):
    response = client.post("/categories", json={
        "category_name": "fashion",
        "description": "clothing and accessories",
    })

    assert response.status_code == 201
    body = response.get_json()
    assert body["category"]["category_name"] == "fashion"
    assert body["category"]["category_id"] is not None

    # and it is actually persisted
    assert client.get("/categories").get_json()[0]["category_name"] == "fashion"


def test_create_category_without_name_returns_400(client, session):
    response = client.post("/categories", json={"description": "no name given"})

    assert response.status_code == 400
    body = response.get_json()
    assert body["error"] == "validation failed"
    assert "category_name is required" in body["details"]


def test_create_category_duplicate_name_returns_409(client, sample_category):
    response = client.post("/categories", json={"category_name": "electronics"})

    assert response.status_code == 409
    assert response.get_json()["error"] == "category_name already exists"


# ----------------------------------------------------------- PUT /categories/<id>

def test_update_category_returns_200(client, sample_category):
    response = client.put(f"/categories/{sample_category}", json={
        "category_name": "consumer electronics",
        "description": "updated description",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["category"]["category_name"] == "consumer electronics"
    assert body["category"]["description"] == "updated description"


def test_update_category_unknown_id_returns_404(client):
    response = client.put("/categories/9999", json={"category_name": "ghost"})

    assert response.status_code == 404
    assert response.get_json()["error"] == "category not found"


def test_update_category_blank_name_returns_400(client, sample_category):
    response = client.put(f"/categories/{sample_category}", json={"category_name": "   "})

    assert response.status_code == 400
    assert "category_name must not be blank" in response.get_json()["details"]


# -------------------------------------------------------- DELETE /categories/<id>

def test_delete_category_returns_200(client, sample_category):
    response = client.delete(f"/categories/{sample_category}")

    assert response.status_code == 200
    assert response.get_json()["id"] == sample_category

    # and it is really gone
    assert client.get(f"/categories/{sample_category}").status_code == 404


def test_delete_category_unknown_id_returns_404(client):
    response = client.delete("/categories/9999")

    assert response.status_code == 404
    assert response.get_json()["error"] == "category not found"


def test_delete_category_with_products_returns_409(client, category_with_product):
    response = client.delete(f"/categories/{category_with_product}")

    assert response.status_code == 409
    body = response.get_json()
    assert body["product_count"] == 1

    # the category must survive a refused delete
    assert client.get(f"/categories/{category_with_product}").status_code == 200
