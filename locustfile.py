"""Load test for the RevoShop API.

Simulates a sequential shopper journey:
    1. GET  /products          browse the catalogue
    2. GET  /products/<id>     open one product
    3. POST /orders            place an order for it
    4. GET  /orders/<id>       review the created order

Run against a production-grade server, not the Flask development server:

    waitress-serve --port=5000 app:app
    locust -f locustfile.py --host http://127.0.0.1:5000

Then in the web UI at http://localhost:8089 start with 50 users
(spawn rate 5/s) and ramp up to 200.
"""

import random

from locust import HttpUser, SequentialTaskSet, between, task

# The seeded users. The brief allows identity to be a plain user_id.
USER_IDS = [1, 2, 3, 4, 5, 6]


class ShopperJourney(SequentialTaskSet):
    """One pass through the buying flow. Tasks run in the order defined."""

    def on_start(self):
        self.product_ids = []
        self.product_id = None
        self.order_id = None
        self.user_id = random.choice(USER_IDS)

    @task
    def browse_products(self):
        with self.client.get(
            "/products", name="1. GET /products", catch_response=True
        ) as response:
            if response.status_code != 200:
                response.failure(f"expected 200, got {response.status_code}")
                return
            self.product_ids = [item["product_id"] for item in response.json()]
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
        payload = {
            "user_id": self.user_id,
            "shipping_address": "jl. load test no. 1, bandung",
            "items": [{"product_id": self.product_id, "quantity": random.randint(1, 3)}],
        }
        with self.client.post(
            "/orders", json=payload, name="3. POST /orders", catch_response=True
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
            name="4. GET /orders/<id>",
            catch_response=True,
        ) as response:
            if response.status_code != 200:
                response.failure(f"expected 200, got {response.status_code}")

    @task
    def done(self):
        # Restart the journey rather than leaving the user idle.
        self.interrupt()


class RevoShopUser(HttpUser):
    tasks = [ShopperJourney]
    wait_time = between(1, 3)
