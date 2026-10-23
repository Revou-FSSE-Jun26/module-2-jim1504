"""Load test for the RevoShop API.

Simulates a sequential shopper journey:
    0. POST /auth/login        sign in (writes now need a token)
    1. GET  /products          browse the catalogue
    2. GET  /products/<id>     open one product
    3. POST /orders            place an order for it (this takes stock)
    4. GET  /orders/<id>       review the created order
    5. DELETE /orders/<id>     cancel it again, which puts the stock back

Step 5 keeps a long run from emptying the shelves: placing an order now really
takes stock, so without it every product would sell out and later orders would
fail with "only 0 left". Only products that are for sale and in stock are picked.

Run against a production-grade server, not the Flask development server, and
tune it -- waitress defaults to 4 threads and a 100-connection limit, which caps
the results long before the API does:

    $env:FLASK_DEBUG="0"; $env:DB_POOL_SIZE="30"; $env:DB_MAX_OVERFLOW="10"
    waitress-serve --port=5000 --threads=32 --connection-limit=400 --channel-timeout=60 app:app
    locust -f locustfile.py --host http://127.0.0.1:5000

gunicorn cannot serve this on Windows (it imports fcntl); the Procfile is for the
Linux deploy host only. See README section 7 for the reasoning behind each value.

Then in the web UI at http://localhost:8089 start with 50 users
(spawn rate 5/s) and ramp up to 200.
"""

import random

from locust import HttpUser, SequentialTaskSet, between, task

# The seeded customers. Every seeded account shares this password.
SEED_EMAILS = [
    "andi.pratama@example.com",
    "siti.rahayu@example.com",
    "budi.santoso@example.com",
    "dewi.lestari@example.com",
    "rizky.ramadhan@example.com",
    "maya.kusuma@example.com",
]
SEED_PASSWORD = "password123"


class ShopperJourney(SequentialTaskSet):
    """One pass through the buying flow. Tasks run in the order defined."""

    def on_start(self):
        self.product_ids = []
        self.product_id = None
        self.order_id = None
        self.token = None
        self.login()

    def login(self):
        """Writes need a Bearer token, so each simulated shopper signs in first.

        Login happens in on_start rather than as a task, so it is not counted in
        the per-journey statistics -- the numbers stay comparable to earlier runs.
        """
        response = self.client.post(
            "/auth/login",
            json={"email": random.choice(SEED_EMAILS), "password": SEED_PASSWORD},
            name="0. POST /auth/login",
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    @property
    def auth(self):
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    @task
    def browse_products(self):
        with self.client.get(
            "/products", name="1. GET /products", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"expected 200, got {response.status_code}")
                return
            self.product_ids = [
                item["product_id"] for item in response.json() if item["is_active"] and item["stock_quantity"] > 0
            ]
            if not self.product_ids:
                response.failure("no products returned -- run seed_db.py first")

    @task
    def view_product(self):
        if not self.product_ids:
            return
        self.product_id = random.choice(self.product_ids)
        # Grouped under one name so per-id URLs do not explode the statistics.
        with self.client.get(
            f"/products/{self.product_id}",
            name="2. GET /products/<id>",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"expected 200, got {response.status_code}")

    @task
    def place_order(self):
        if self.product_id is None:
            return
        # The owner comes from the token now, so no user_id is sent.
        payload = {
            "shipping_address": "jl. load test no. 1, bandung",
            "items": [{"product_id": self.product_id, "quantity": 1}],
        }
        with self.client.post(
            "/orders",
            json=payload,
            headers=self.auth,
            name="3. POST /orders",
            catch_response=True,
        ) as response:
            if response.status_code != 201:
                response.failure(f"expected 201, got {response.status_code}")
                return
            self.order_id = response.json()["order"]["order_id"]

    @task
    def review_order(self):
        if self.order_id is None:
            return
        with self.client.get(
            f"/orders/{self.order_id}",
            headers=self.auth,
            name="4. GET /orders/<id>",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"expected 200, got {response.status_code}")

    @task
    def delete_order(self):
        if self.order_id is None:
            return
        with self.client.delete(
            f"/orders/{self.order_id}",
            headers=self.auth,
            name="5. DELETE /orders/<id>",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"expected 200, got {response.status_code}")
        self.order_id = None

    @task
    def done(self):
        # Restart the journey rather than leaving the user idle.
        self.interrupt()


class RevoShopUser(HttpUser):
    tasks = [ShopperJourney]
    wait_time = between(1, 3)
