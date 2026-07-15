# Agent Wiring (Task 6) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the echo stub in `generate_reply()` with a real Claude Agent SDK `query()` call, so the chat app becomes a read-only "codebase concierge" that answers questions about a target repo.

**Architecture:** `generate_reply()` becomes an async function that calls `query()` with a read-only tool allowlist (`Read`, `Glob`, `Grep`), a system prompt defining the concierge persona, a configurable `cwd` (env var, defaults to this repo), and a `max_turns` cap. It returns `ResultMessage.result`. Any exception from the agent loop is caught and turned into a polite chat reply instead of propagating into a 500. `/api/chat` becomes an async route that awaits it. This keeps the one-function seam from `CLAUDE.md` intact — nothing outside `app/chat.py` needs to know the reply now comes from a real model.

**Tech Stack:** `claude-agent-sdk` (`query`, `ClaudeAgentOptions`, `ResultMessage`), FastAPI async routes, `monkeypatch` for test doubles (no new test dependency — `asyncio.run()` inside sync test functions covers it).

---

### Task 1: Wire the real agent into `generate_reply()`

**Files:**
- Modify: `app/chat.py` (whole file)
- Test: `tests/test_chat.py` (whole file)

- [ ] **Step 1: Replace the echo tests with agent-behavior tests**

```python
import asyncio

from claude_agent_sdk import ResultMessage

from app.chat import generate_reply


def _result_message(result: str) -> ResultMessage:
    return ResultMessage(
        subtype="success",
        duration_ms=100,
        duration_api_ms=100,
        is_error=False,
        num_turns=1,
        session_id="test-session",
        result=result,
    )


def test_generate_reply_returns_result_message_text(monkeypatch):
    async def fake_query(*, prompt, options):
        yield _result_message(f"answer to: {prompt}")

    monkeypatch.setattr("app.chat.query", fake_query)

    reply = asyncio.run(generate_reply("what does this repo do?"))

    assert reply == "answer to: what does this repo do?"


def test_generate_reply_returns_polite_message_on_error(monkeypatch):
    async def fake_query(*, prompt, options):
        raise RuntimeError("boom")
        yield

    monkeypatch.setattr("app.chat.query", fake_query)

    reply = asyncio.run(generate_reply("anything"))

    assert reply == "Sorry, I ran into a problem answering that. Please try again."
```

This replaces `tests/test_chat.py` entirely — the old echo tests no longer describe the intended behavior.

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `uv run pytest tests/test_chat.py -v`
Expected: FAIL — `app.chat` still only has the old sync echo `generate_reply`, so `app.chat.query` doesn't exist to monkeypatch and the async assertions won't match.

- [ ] **Step 3: Implement the real `generate_reply()`**

```python
import os
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

BASE_DIR = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT = (
    "You are a concierge for this repository. Answer questions about the "
    "codebase concisely and cite file paths when relevant."
)


async def generate_reply(message: str) -> str:
    target_dir = os.environ.get("CONCIERGE_REPO_PATH", str(BASE_DIR))
    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=["Read", "Glob", "Grep"],
        cwd=target_dir,
        max_turns=25,
    )
    try:
        async for message_out in query(prompt=message, options=options):
            if isinstance(message_out, ResultMessage):
                return message_out.result or "I couldn't find an answer to that."
    except Exception:
        return "Sorry, I ran into a problem answering that. Please try again."
    return "Sorry, I ran into a problem answering that. Please try again."
```

This replaces the entire current contents of `app/chat.py`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `uv run pytest tests/test_chat.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add app/chat.py tests/test_chat.py
git commit -m "feat: wire generate_reply to a real Agent SDK query()"
```

---

### Task 2: Make `/api/chat` async so it can await the real agent

**Files:**
- Modify: `app/main.py:33-35`
- Test: `tests/test_api_chat.py` (whole file)

- [ ] **Step 1: Replace the echo-based endpoint test with a mocked-agent test**

```python
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_post_chat_returns_agent_reply(monkeypatch):
    async def fake_generate_reply(message: str) -> str:
        return f"agent reply to: {message}"

    monkeypatch.setattr("app.main.generate_reply", fake_generate_reply)

    response = client.post(
        "/api/chat",
        json={"message": "hello there", "conversation_id": "conv-1"},
    )

    assert response.status_code == 200
    assert response.json() == {"reply": "agent reply to: hello there"}


def test_post_chat_requires_message_field():
    response = client.post("/api/chat", json={"conversation_id": "conv-1"})
    assert response.status_code == 422
```

This replaces `tests/test_api_chat.py` entirely. The 422 validation test is unchanged — it never reaches `generate_reply()`.

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `uv run pytest tests/test_api_chat.py -v`
Expected: FAIL — `post_chat` is still sync and calls the real (now-async) `generate_reply` directly, so calling it returns an un-awaited coroutine instead of a string, and `ChatResponse(reply=...)` will raise a validation error.

- [ ] **Step 3: Make the route async**

In `app/main.py`, replace:

```python
@app.post("/api/chat")
def post_chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=generate_reply(request.message))
```

with:

```python
@app.post("/api/chat")
async def post_chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=await generate_reply(request.message))
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `uv run pytest tests/test_api_chat.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Run the full suite**

Run: `uv run pytest -v`
Expected: all tests pass (`test_main.py` and `test_static.py` are untouched by this change and should still pass unmodified).

- [ ] **Step 6: Commit**

```bash
git add app/main.py tests/test_api_chat.py
git commit -m "feat: await the agent reply in the /api/chat route"
```

---

### Task 3: Fix the now-stale line in `CLAUDE.md`

**Files:**
- Modify: `CLAUDE.md`

`CLAUDE.md` currently says `generate_reply()` "just returns the message it was given (an echo)" — that's no longer true after Task 1.

- [ ] **Step 1: Update the description**

Replace this paragraph:

```markdown
There is exactly one function that decides what the chatbot replies: `generate_reply()` in `app/chat.py`. It currently just returns the message it was given (an echo). When we wire up a real AI model, this is the only function that needs to change — nothing else in the app should need to be touched.
```

with:

```markdown
There is exactly one function that decides what the chatbot replies: `generate_reply()` in `app/chat.py`. It calls the Claude Agent SDK with a read-only tool allowlist (`Read`, `Glob`, `Grep`) so it can answer questions about the repo at `CONCIERGE_REPO_PATH` (defaults to this repo). If you need to change how the agent behaves — its persona, which repo it answers about, which tools it can use — this is the only function that needs to change.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md now that generate_reply calls a real agent"
```

---

### Task 4: Manual browser verification

**Files:** none — this is a verification-only task, not a code change.

- [ ] **Step 1: Start the server**

Run: `uv run uvicorn app.main:app --reload` (from `chat-app/`)

- [ ] **Step 2: Ask it about the repo through the actual UI**

Open `http://localhost:8000`, type "what does this repo do?" into the chat box, submit.

Expected: a real, specific answer referencing `app/chat.py`, `app/main.py`, or similar — not an echo of your question. This confirms the agent is really reading files (`Read`/`Glob`/`Grep`), not guessing.

- [ ] **Step 3: Confirm error handling doesn't 500**

Temporarily set an invalid `CONCIERGE_REPO_PATH` (e.g. `CONCIERGE_REPO_PATH=/nonexistent uv run uvicorn app.main:app --reload`), ask a question again.

Expected: HTTP 200 with the polite fallback reply ("Sorry, I ran into a problem answering that...") — not a 500. Then restart the server without the env var override so it goes back to normal.
