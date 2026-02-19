"""Integration tests for the FastAPI endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create a TestClient with lifespan context (loads sizing data)."""
    with TestClient(app) as c:
        yield c


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_widget_js_served(self, client):
        response = client.get("/static/sizing-widget.js")
        assert response.status_code == 200
        assert "SolideaSizingConfig" in response.text


class TestSizeRecommendationEndpoint:
    def test_valid_arm_sleeve_request(self, client):
        response = client.post(
            "/api/v1/size-recommendation",
            json={
                "product_type": "arm_sleeves",
                "measurements": {
                    "upper_arm_circumference_cm": 26,
                    "forearm_circumference_cm": 22,
                    "wrist_circumference_cm": 14,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_size"] == "S"
        assert data["confidence"] == "exact"

    def test_valid_socks_request(self, client):
        response = client.post(
            "/api/v1/size-recommendation",
            json={
                "product_type": "socks",
                "measurements": {
                    "calf_circumference_cm": 40,
                    "ankle_circumference_cm": 24,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_size"] == "L"

    def test_valid_bras_request(self, client):
        response = client.post(
            "/api/v1/size-recommendation",
            json={
                "product_type": "bras",
                "measurements": {
                    "bust_circumference_cm": 130,
                    "underbust_circumference_cm": 105,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_size"] == "XXL"

    def test_invalid_product_type_rejected(self, client):
        response = client.post(
            "/api/v1/size-recommendation",
            json={
                "product_type": "hats",
                "measurements": {"head_cm": 58},
            },
        )
        assert response.status_code == 422

    def test_empty_measurements_rejected(self, client):
        response = client.post(
            "/api/v1/size-recommendation",
            json={
                "product_type": "socks",
                "measurements": {},
            },
        )
        assert response.status_code == 422

    def test_missing_product_type_rejected(self, client):
        response = client.post(
            "/api/v1/size-recommendation",
            json={
                "measurements": {"calf_circumference_cm": 35},
            },
        )
        assert response.status_code == 422

    def test_missing_measurements_rejected(self, client):
        response = client.post(
            "/api/v1/size-recommendation",
            json={
                "product_type": "socks",
            },
        )
        assert response.status_code == 422

    def test_leggings_full_measurements(self, client):
        response = client.post(
            "/api/v1/size-recommendation",
            json={
                "product_type": "leggings",
                "measurements": {
                    "height_cm": 165,
                    "weight_kg": 62,
                    "hip_circumference_cm": 93,
                    "waist_circumference_cm": 70,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_size"] in ("ML", "M", "L")
        assert data["confidence"] in ("exact", "interpolated")

    def test_response_never_500_for_valid_input(self, client):
        """Invariant: API must never return 500 for valid inputs."""
        test_cases = [
            {
                "product_type": "arm_sleeves",
                "measurements": {"upper_arm_circumference_cm": 0},
            },
            {
                "product_type": "socks",
                "measurements": {"calf_circumference_cm": 999},
            },
            {
                "product_type": "bras",
                "measurements": {"bust_circumference_cm": 50},
            },
            {
                "product_type": "leggings",
                "measurements": {"height_cm": 200, "weight_kg": 150},
            },
            {
                "product_type": "capris",
                "measurements": {"hip_circumference_cm": 80},
            },
        ]
        for case in test_cases:
            resp = client.post("/api/v1/size-recommendation", json=case)
            assert resp.status_code != 500, f"Got 500 for: {case}"
