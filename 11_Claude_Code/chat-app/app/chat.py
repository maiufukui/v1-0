import os
import subprocess
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    ToolUseBlock,
    create_sdk_mcp_server,
    query,
    tool,
)

BASE_DIR = Path(__file__).resolve().parent.parent

SYSTEM_PROMPT = (
    "You are a concierge for this repository. Answer questions about the "
    "codebase concisely and cite file paths when relevant."
)

_sessions: dict[str, str] = {}


@tool("count_lines", "Count lines of code in a file", {"file_path": str})
async def count_lines(args):
    with open(args["file_path"]) as f:
        n = sum(1 for _ in f)
    return {"content": [{"type": "text", "text": f"{args['file_path']}: {n} lines"}]}


@tool("git_log", "Show the most recent git commits in the repository", {"limit": int})
async def git_log(args):
    target_dir = os.environ.get("CONCIERGE_REPO_PATH", str(BASE_DIR))
    result = subprocess.run(
        ["git", "log", f"-{args['limit']}", "--oneline"],
        cwd=target_dir,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip() or "No commits found."
    return {"content": [{"type": "text", "text": output}]}


_concierge_server = create_sdk_mcp_server(
    name="concierge", version="1.0.0", tools=[count_lines, git_log]
)


def _build_options(conversation_id: str) -> ClaudeAgentOptions:
    target_dir = os.environ.get("CONCIERGE_REPO_PATH", str(BASE_DIR))
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        allowed_tools=[
            "Read",
            "Glob",
            "Grep",
            "mcp__concierge__count_lines",
            "mcp__concierge__git_log",
        ],
        mcp_servers={"concierge": _concierge_server},
        cwd=target_dir,
        max_turns=25,
        resume=_sessions.get(conversation_id),
    )


FALLBACK_MESSAGE = "Sorry, I ran into a problem answering that. Please try again."


async def generate_reply(conversation_id: str, message: str) -> str:
    options = _build_options(conversation_id)
    try:
        async for message_out in query(prompt=message, options=options):
            if isinstance(message_out, SystemMessage) and message_out.subtype == "init":
                _sessions[conversation_id] = message_out.data["session_id"]
            if isinstance(message_out, ResultMessage):
                return message_out.result or "I couldn't find an answer to that."
    except Exception:
        return FALLBACK_MESSAGE
    return FALLBACK_MESSAGE


async def stream_reply(conversation_id: str, message: str):
    """Yield progress events while the agent works, then a final result event.

    Each event is a dict:
      {"type": "tool", "name": str, "input": dict}   -- agent called a tool
      {"type": "result", "text": str}                -- final answer, last event
    """
    options = _build_options(conversation_id)
    try:
        async for message_out in query(prompt=message, options=options):
            if isinstance(message_out, SystemMessage) and message_out.subtype == "init":
                _sessions[conversation_id] = message_out.data["session_id"]
            elif isinstance(message_out, AssistantMessage):
                for block in message_out.content:
                    if isinstance(block, ToolUseBlock):
                        yield {"type": "tool", "name": block.name, "input": block.input}
            elif isinstance(message_out, ResultMessage):
                yield {
                    "type": "result",
                    "text": message_out.result or "I couldn't find an answer to that.",
                }
                return
    except Exception:
        yield {"type": "result", "text": FALLBACK_MESSAGE}
        return
    yield {"type": "result", "text": FALLBACK_MESSAGE}
