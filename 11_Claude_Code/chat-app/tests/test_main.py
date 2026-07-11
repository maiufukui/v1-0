from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_root_returns_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Chat" in response.text
