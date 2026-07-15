# Chat App Skeleton Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable skeleton chat web app — FastAPI backend serving a plain HTML/CSS/JS frontend, with a stubbed `/api/chat` endpoint that echoes the user's message.

**Architecture:** A `uv`-managed Python 3.12+ project. `app/main.py` defines the FastAPI app with two routes: `GET /` (serves `static/index.html`) and `POST /api/chat` (validates request with Pydantic, calls an isolated `generate_reply()` stub in `app/chat.py`, returns JSON). Static assets (`index.html`, `style.css`, `app.js`) are served via `StaticFiles` mounted at `/static`. The frontend is vanilla JS using `fetch()` — no build step, no framework.

**Tech Stack:** Python 3.12+, uv, FastAPI, uvicorn, pytest, httpx (for `TestClient`), plain HTML/CSS/JS.

---

## File Structure

```
chat-app/
├── pyproject.toml          # uv project config, deps: fastapi, uvicorn; dev: pytest, httpx
├── .python-version         # pins 3.12
├── .gitignore
├── README.md                # run instructions
├── app/
│   ├── __init__.py          # empty, makes app/ a package
│   ├── main.py               # FastAPI app: GET /, POST /api/chat, static mount
│   └── chat.py                # generate_reply() stub — isolated, replaced later
├── static/
│   ├── index.html            # chat UI markup
│   ├── style.css              # chat UI styling
│   └── app.js                  # fetch() calls to /api/chat, renders conversation
└── tests/
    ├── test_main.py            # GET / test
    ├── test_chat.py             # generate_reply() unit tests
    ├── test_api_chat.py          # POST /api/chat integration tests
    └── test_static.py             # static asset serving tests
```

Rationale: `app/chat.py` is split out from `app/main.py` specifically because the spec calls out that the stub "gets replaced by a real agent later — keep it isolated in one clearly-named function." Isolating it in its own file means the future agent-integration change touches one file, not the routing file.

---

### Task 1: Project Scaffolding

**Files:**
- Create: `pyproject.toml`
- Create: `.python-version`
- Create: `.gitignore`

- [ ] **Step 1: Write `pyproject.toml`**

```toml
[project]
name = "chat-app"
version = "0.1.0"
description = "Skeleton chat web app"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.32",
]

[dependency-groups]
dev = [
    "pytest>=8.3",
    "httpx>=0.27",
]
```

- [ ] **Step 2: Write `.python-version`**

```
3.12
```

- [ ] **Step 3: Write `.gitignore`**

```
.venv/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 4: Install dependencies and generate lockfile**

Run: `uv sync`
Expected: creates `.venv/` and `uv.lock`, no errors.

- [ ] **Step 5: Verify imports resolve**

Run: `uv run python -c "import fastapi, uvicorn; print('ok')"`
Expected: prints `ok`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml .python-version .gitignore uv.lock
git commit -m "chore: scaffold uv project for chat-app"
```

---

### Task 2: FastAPI App Skeleton — `GET /`

**Files:**
- Create: `app/__init__.py`
- Create: `static/index.html`
- Create: `app/main.py`
- Test: `tests/test_main.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_main.py
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_root_returns_index_html():
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    assert "Chat" in response.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_main.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 3: Create the `app` package**

Create `app/__init__.py` as an empty file (no content needed — its presence makes `app/` importable as a package).

- [ ] **Step 4: Write the full chat UI markup**

```html
<!-- static/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Chat</title>
    <link rel="stylesheet" href="/static/style.css" />
</head>
<body>
    <main class="chat-app">
        <h1>Chat</h1>
        <div id="history" class="history" aria-live="polite"></div>
        <form id="chat-form" class="chat-form">
            <input
                id="message-input"
                type="text"
                placeholder="Type a message..."
                autocomplete="off"
                required
            />
            <button type="submit">Send</button>
        </form>
    </main>
    <script src="/static/app.js"></script>
</body>
</html>
```

- [ ] **Step 5: Write minimal FastAPI app**

```python
# app/main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()


@app.get("/")
def read_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_main.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/__init__.py app/main.py static/index.html tests/test_main.py
git commit -m "feat: serve chat UI at GET /"
```

---

### Task 3: Stub Chat Reply Function

**Files:**
- Create: `app/chat.py`
- Test: `tests/test_chat.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_chat.py
from app.chat import generate_reply


def test_generate_reply_echoes_message():
    assert generate_reply("hello") == "hello"


def test_generate_reply_echoes_empty_string():
    assert generate_reply("") == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_chat.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.chat'`

- [ ] **Step 3: Write the stub**

```python
# app/chat.py
# Stub — replace with a real agent call. Callers only depend on this
# function's signature, so swapping the implementation later is a one-file change.
def generate_reply(message: str) -> str:
    return message
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_chat.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/chat.py tests/test_chat.py
git commit -m "feat: add generate_reply echo stub"
```

---

### Task 4: Wire `POST /api/chat`

**Files:**
- Modify: `app/main.py`
- Test: `tests/test_api_chat.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api_chat.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api_chat.py -v`
Expected: FAIL with 404 (route doesn't exist) on the first assertion

- [ ] **Step 3: Add the endpoint**

```python
# app/main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.chat import generate_reply

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI()


class ChatRequest(BaseModel):
    message: str
    conversation_id: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/")
def read_index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/chat")
def post_chat(request: ChatRequest) -> ChatResponse:
    return ChatResponse(reply=generate_reply(request.message))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_api_chat.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add app/main.py tests/test_api_chat.py
git commit -m "feat: wire POST /api/chat to generate_reply stub"
```

---

### Task 5: Static Assets (CSS/JS) + Static Mount

**Files:**
- Create: `static/style.css`
- Create: `static/app.js`
- Modify: `app/main.py`
- Test: `tests/test_static.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_static.py
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_static.py -v`
Expected: FAIL with 404 on both requests

- [ ] **Step 3: Write the stylesheet**

```css
/* static/style.css */
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: #f5f5f7;
    color: #1d1d1f;
    display: flex;
    justify-content: center;
    padding: 2rem 1rem;
}

.chat-app {
    width: 100%;
    max-width: 640px;
    background: #fff;
    border-radius: 12px;
    box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    height: 80vh;
}

h1 {
    margin: 0 0 1rem;
    font-size: 1.25rem;
}

.history {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.5rem 0;
}

.message {
    max-width: 75%;
    padding: 0.5rem 0.75rem;
    border-radius: 10px;
    line-height: 1.4;
    white-space: pre-wrap;
}

.message.user {
    align-self: flex-end;
    background: #0071e3;
    color: #fff;
}

.message.assistant {
    align-self: flex-start;
    background: #ececec;
    color: #1d1d1f;
}

.chat-form {
    display: flex;
    gap: 0.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e5e5e5;
}

#message-input {
    flex: 1;
    padding: 0.6rem 0.8rem;
    border: 1px solid #d2d2d7;
    border-radius: 8px;
    font-size: 1rem;
}

.chat-form button {
    padding: 0.6rem 1.2rem;
    border: none;
    border-radius: 8px;
    background: #0071e3;
    color: #fff;
    font-size: 1rem;
    cursor: pointer;
}

.chat-form button:hover {
    background: #0077ed;
}
```

- [ ] **Step 4: Write the frontend script**

```javascript
// static/app.js
const conversationId = crypto.randomUUID();

const historyEl = document.getElementById("history");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("message-input");

function appendMessage(role, text) {
    const el = document.createElement("div");
    el.className = `message ${role}`;
    el.textContent = text;
    historyEl.appendChild(el);
    historyEl.scrollTop = historyEl.scrollHeight;
}

async function sendMessage(message) {
    const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, conversation_id: conversationId }),
    });

    if (!response.ok) {
        throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    return data.reply;
}

formEl.addEventListener("submit", async (event) => {
    event.preventDefault();
    const message = inputEl.value.trim();
    if (!message) return;

    inputEl.value = "";
    appendMessage("user", message);

    try {
        const reply = await sendMessage(message);
        appendMessage("assistant", reply);
    } catch (err) {
        appendMessage("assistant", "Something went wrong. Please try again.");
        console.error(err);
    }
});
```

- [ ] **Step 5: Mount the static directory**

```python
# app/main.py — add these two lines
from fastapi.staticfiles import StaticFiles
```

Add the import above alongside the existing `fastapi` imports, and add this line at the end of the file, after all route definitions:

```python
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_static.py -v`
Expected: PASS

- [ ] **Step 7: Run the full test suite**

Run: `uv run pytest -v`
Expected: all tests PASS (test_main, test_chat, test_api_chat, test_static)

- [ ] **Step 8: Commit**

```bash
git add app/main.py static/style.css static/app.js tests/test_static.py
git commit -m "feat: serve static assets and wire up chat UI"
```

---

### Task 6: README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Write the README**

```markdown
# chat-app

A skeleton chat web app: FastAPI backend + plain HTML/CSS/JS frontend.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)

## Setup

\`\`\`bash
uv sync
\`\`\`

## Run

\`\`\`bash
uv run uvicorn app.main:app --reload
\`\`\`

Open http://localhost:8000 in your browser.

## Run tests

\`\`\`bash
uv run pytest
\`\`\`

## API

### `POST /api/chat`

Request body:

\`\`\`json
{ "message": "hello", "conversation_id": "some-uuid" }
\`\`\`

Response body:

\`\`\`json
{ "reply": "hello" }
\`\`\`

`generate_reply()` in `app/chat.py` currently just echoes the message back — it's a stub to be replaced with a real agent call later.
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with run instructions"
```

---

### Task 7: Manual Browser Verification

This task touches HTML/CSS/JS, so per project policy it requires a live browser check — no exceptions.

**Files:** none (verification only)

- [ ] **Step 1: Start the server**

Run: `uv run uvicorn app.main:app --reload` (or use `preview_start` if driving from Claude Code)

- [ ] **Step 2: Load the page**

Open `http://localhost:8000`. Confirm: title bar shows "Chat", heading "Chat" renders, input box and Send button are visible and styled (rounded card, blue accents — not unstyled HTML).

- [ ] **Step 3: Happy path**

Type "hello" and press Send (or click the button). Confirm: your message appears right-aligned in blue, and an echoed reply "hello" appears left-aligned in gray, within ~1 second.

- [ ] **Step 4: Rich input**

Send a message containing multiple lines / special characters, e.g. `line one\nline two <b>bold?</b>`. Confirm: the text renders as plain text (no HTML injection — this is `textContent`, not `innerHTML`, so `<b>` should show literally, not render as bold), and both lines display.

- [ ] **Step 5: Empty submit**

Press Send with an empty input. Confirm: nothing is sent (the HTML `required` attribute blocks submission), no error in console.

- [ ] **Step 6: Check console**

Open browser dev tools console. Confirm: no errors or warnings after steps 3–5.

- [ ] **Step 7: Stop the server**

Kill the `uvicorn` process.

---

## Self-Review Notes

- **Spec coverage:** GET / → static/index.html ✓ (Task 2). POST /api/chat with `{message, conversation_id}` → `{reply}` ✓ (Task 4). Stub isolated in one named function ✓ (`generate_reply` in `app/chat.py`, Task 3). Frontend calls fetch() and renders both sides ✓ (Task 5, `app.js`). README with run instructions ✓ (Task 6). uv-managed Python 3.12+ project ✓ (Task 1). Plain HTML/CSS/JS, no framework ✓ (Task 2 + 5).
- **Placeholder scan:** none found — every step has literal file content.
- **Type consistency:** `generate_reply(message: str) -> str` (Task 3) is called identically in Task 4's `post_chat`. `ChatRequest`/`ChatResponse` field names (`message`, `conversation_id`, `reply`) match what `app.js` sends and expects in Task 5.
