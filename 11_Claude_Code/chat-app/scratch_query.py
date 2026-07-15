import asyncio
from pathlib import Path

from dotenv import load_dotenv

from claude_agent_sdk import query, ClaudeAgentOptions

load_dotenv(Path(__file__).resolve().parent / ".env")


async def main():
    async for message in query(
        prompt="What does this project do? Answer in two sentences.",
        options=ClaudeAgentOptions(
            allowed_tools=["Read", "Glob", "Grep"],
            cwd=str(Path(__file__).resolve().parent),
        ),
    ):
        print(type(message).__name__)          # watch the loop's anatomy
        if hasattr(message, "result"):
            print("\n" + message.result)


asyncio.run(main())
