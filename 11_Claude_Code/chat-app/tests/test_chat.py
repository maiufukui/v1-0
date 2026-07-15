import asyncio
import subprocess

from claude_agent_sdk import ResultMessage, SystemMessage

import app.chat as app_chat
from app.chat import count_lines, generate_reply, git_log


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


def _init_message(session_id: str) -> SystemMessage:
    return SystemMessage(subtype="init", data={"session_id": session_id})


def test_generate_reply_returns_result_message_text(monkeypatch):
    app_chat._sessions.clear()

    async def fake_query(*, prompt, options):
        yield _init_message("session-abc")
        yield _result_message(f"answer to: {prompt}")

    monkeypatch.setattr("app.chat.query", fake_query)

    reply = asyncio.run(generate_reply("conv-1", "what does this repo do?"))

    assert reply == "answer to: what does this repo do?"


def test_generate_reply_returns_polite_message_on_error(monkeypatch):
    app_chat._sessions.clear()

    async def fake_query(*, prompt, options):
        raise RuntimeError("boom")
        yield

    monkeypatch.setattr("app.chat.query", fake_query)

    reply = asyncio.run(generate_reply("conv-err", "anything"))

    assert reply == "Sorry, I ran into a problem answering that. Please try again."


def test_generate_reply_stores_session_id_for_conversation(monkeypatch):
    app_chat._sessions.clear()

    async def fake_query(*, prompt, options):
        yield _init_message("session-abc")
        yield _result_message(f"answer to: {prompt}")

    monkeypatch.setattr("app.chat.query", fake_query)

    asyncio.run(generate_reply("conv-1", "what does this repo do?"))

    assert app_chat._sessions["conv-1"] == "session-abc"


def test_generate_reply_resumes_existing_session(monkeypatch):
    app_chat._sessions.clear()
    app_chat._sessions["conv-1"] = "session-abc"

    captured_options = {}

    async def fake_query(*, prompt, options):
        captured_options["resume"] = options.resume
        yield _init_message("session-abc")
        yield _result_message(f"answer to: {prompt}")

    monkeypatch.setattr("app.chat.query", fake_query)

    asyncio.run(generate_reply("conv-1", "what are its main dependencies?"))

    assert captured_options["resume"] == "session-abc"


def test_count_lines_tool_counts_file_lines(tmp_path):
    target = tmp_path / "sample.txt"
    target.write_text("line1\nline2\nline3\n")

    result = asyncio.run(count_lines.handler({"file_path": str(target)}))

    assert result["content"][0]["text"] == f"{target}: 3 lines"


def test_generate_reply_registers_count_lines_tool(monkeypatch):
    app_chat._sessions.clear()
    captured_options = {}

    async def fake_query(*, prompt, options):
        captured_options["mcp_servers"] = options.mcp_servers
        captured_options["allowed_tools"] = options.allowed_tools
        yield _init_message("session-abc")
        yield _result_message(f"answer to: {prompt}")

    monkeypatch.setattr("app.chat.query", fake_query)

    asyncio.run(generate_reply("conv-1", "how many lines is app/main.py?"))

    assert "concierge" in captured_options["mcp_servers"]
    assert "mcp__concierge__count_lines" in captured_options["allowed_tools"]


def _init_git_repo(repo_dir):
    subprocess.run(["git", "init", "-q"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_dir, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo_dir, check=True)
    for i in range(3):
        (repo_dir / f"file{i}.txt").write_text(f"content {i}")
        subprocess.run(["git", "add", "."], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-q", "-m", f"commit {i}"], cwd=repo_dir, check=True)


def test_git_log_tool_lists_recent_commits(tmp_path, monkeypatch):
    _init_git_repo(tmp_path)
    monkeypatch.setenv("CONCIERGE_REPO_PATH", str(tmp_path))

    result = asyncio.run(git_log.handler({"limit": 2}))
    lines = result["content"][0]["text"].strip().splitlines()

    assert len(lines) == 2
    assert "commit 2" in lines[0]
    assert "commit 1" in lines[1]


def test_generate_reply_registers_git_log_tool(monkeypatch):
    app_chat._sessions.clear()
    captured_options = {}

    async def fake_query(*, prompt, options):
        captured_options["allowed_tools"] = options.allowed_tools
        yield _init_message("session-abc")
        yield _result_message(f"answer to: {prompt}")

    monkeypatch.setattr("app.chat.query", fake_query)

    asyncio.run(generate_reply("conv-1", "what changed recently?"))

    assert "mcp__concierge__git_log" in captured_options["allowed_tools"]


def test_conversations_stay_isolated_across_multiple_ids(monkeypatch):
    app_chat._sessions.clear()
    resumes_seen = []

    async def fake_query(*, prompt, options):
        resumes_seen.append(options.resume)
        if prompt == "first for conv-1":
            yield _init_message("session-a")
        elif prompt == "first for conv-2":
            yield _init_message("session-b")
        else:
            yield _init_message(options.resume)
        yield _result_message(f"answer to: {prompt}")

    monkeypatch.setattr("app.chat.query", fake_query)

    asyncio.run(generate_reply("conv-1", "first for conv-1"))
    asyncio.run(generate_reply("conv-2", "first for conv-2"))
    asyncio.run(generate_reply("conv-1", "second for conv-1"))

    assert resumes_seen == [None, None, "session-a"]
    assert app_chat._sessions["conv-1"] == "session-a"
    assert app_chat._sessions["conv-2"] == "session-b"
