# chat-app

A skeleton chat web app: FastAPI backend + plain HTML/CSS/JS frontend.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
uv sync
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

Open http://localhost:8000 in your browser.

## Run tests

```bash
uv run pytest
```

## API

### `POST /api/chat`

Request body:

```json
{ "message": "hello", "conversation_id": "some-uuid" }
```

Response body:

```json
{ "reply": "hello" }
```

`generate_reply()` in `app/chat.py` currently just echoes the message back — it's a stub to be replaced with a real agent call later.
