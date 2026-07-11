from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_chat_echoes_message():
    response = client.post(
        "/api/chat",
        json={"message": "hello there", "conversation_id": "conv-1"},
    )
    assert response.status_code == 200
    assert response.json() == {"reply": "hello there"}


def test_post_chat_requires_message_field():
    response = client.post("/api/chat", json={"conversation_id": "conv-1"})
    assert response.status_code == 422
