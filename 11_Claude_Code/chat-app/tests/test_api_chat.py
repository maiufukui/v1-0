from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_chat_returns_agent_reply(monkeypatch):
    async def fake_generate_reply(conversation_id: str, message: str) -> str:
        return f"agent reply to {conversation_id}: {message}"

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)

    response = client.post(
        "/api/chat",
        json={"message": "hello there", "conversation_id": "conv-1"},
    )

    assert response.status_code == 200
    assert response.json() == {"reply": "agent reply to conv-1: hello there"}


def test_post_chat_requires_message_field():
    response = client.post("/api/chat", json={"conversation_id": "conv-1"})
    assert response.status_code == 422
