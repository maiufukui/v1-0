from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_static_css_is_served():
    response = client.get("/static/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


def test_static_js_is_served():
    response = client.get("/static/app.js")
    assert response.status_code == 200
    assert "javascript" in response.headers["content-type"]
