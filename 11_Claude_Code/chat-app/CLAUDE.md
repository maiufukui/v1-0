# chat-app

A chat web app. FastAPI backend, plain HTML/CSS/JS frontend, no framework. The backend is a read-only "codebase concierge" powered by the Claude Agent SDK — it answers questions about a target repo (defaults to this one) using `Read`, `Glob`, `Grep`, and two custom tools (`count_lines`, `git_log`), and can't write or delete anything.

The frontend supports multiple conversations: a sidebar lists them, each has its own SDK session (so context doesn't bleed between them), and the list persists in the browser's `localStorage`. Sending a message streams the agent's progress live (e.g. "Reading app/main.py...") via Server-Sent Events, instead of showing a blank spinner until the final answer.

## How to run it

```bash
uv run uvicorn app.main:app --reload
```

Then open http://localhost:8000 in a browser, or test the API directly without a browser:

```bash
curl -X POST http://localhost:8000/api/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "hello", "conversation_id": "test-123"}'
```

Run the automated tests:

```bash
uv run pytest
```

## The one thing to know before changing code

All agent options (system prompt, tools, allowlist, target repo, session resume) are built in one place: `_build_options()` in `app/chat.py`. It calls the Claude Agent SDK with a read-only tool allowlist (`Read`, `Glob`, `Grep`, `mcp__concierge__count_lines`, `mcp__concierge__git_log`) so it can answer questions about the repo at `CONCIERGE_REPO_PATH` (defaults to this repo). If you need to change how the agent behaves — its persona, which repo it answers about, which tools it can use — this is the only function that needs to change.

Two ways to actually get a reply, both built on `_build_options()`:
- `generate_reply(conversation_id, message)` — returns the final answer as a plain string. Used by `POST /api/chat`.
- `stream_reply(conversation_id, message)` — an async generator that yields `{"type": "tool", ...}` events as the agent calls tools, then a final `{"type": "result", "text": ...}` event. Used by `POST /api/chat/stream`, which wraps it as Server-Sent Events.

Conversation memory: `_sessions` (a dict) maps `conversation_id` → the SDK's `session_id`, so resuming a conversation resumes the actual agent session. Each conversation the frontend creates gets its own ID, which is how the sidebar keeps them isolated.

Adding a new custom tool: define it with `@tool(name, description, input_schema)` in `app/chat.py`, add it to the `tools=[...]` list passed to `create_sdk_mcp_server(...)`, and add `"mcp__concierge__<name>"` to the `allowed_tools` list in `_build_options()`.

## Rules for this codebase

- No frontend framework (React, Vue, etc.) — plain HTML/CSS/JS only.
- Don't move the reply logic out of `_build_options()` / `generate_reply()` / `stream_reply()` — keep agent config in one place so swapping it later stays a small, contained change.
