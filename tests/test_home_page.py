from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_home_page_is_served():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Check a card number" in response.text


def test_static_assets_are_served():
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/styles.css").status_code == 200


def test_home_page_is_not_in_the_api_docs():
    paths = client.get("/openapi.json").json()["paths"]
    assert "/" not in paths
