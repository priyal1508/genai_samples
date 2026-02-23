"""Travel Planner Assistant — AutoGen 0.4+ multi-agent entry point."""

import asyncio
import json
import re

from autogen_agentchat.ui import Console
from agents.team import build_team
from config.memory import load_memory, save_memory


def _extract_preferences(messages: list) -> dict:
    """Scan agent messages for SAVE_PREFERENCE markers and extract them."""
    preferences = {}
    pattern = re.compile(r"SAVE_PREFERENCE:\s*(\{.*?\})", re.DOTALL)
    for msg in messages:
        content = getattr(msg, "content", "") or ""
        if not isinstance(content, str):
            continue
        for match in pattern.finditer(content):
            try:
                prefs = json.loads(match.group(1))
                preferences.update(prefs)
            except json.JSONDecodeError:
                pass
    return preferences


async def main() -> None:
    """Run the travel planner interactively."""
    print("\n✈️  Travel Planner Assistant")
    print("=" * 40)

    memory = load_memory()
    if memory:
        print(f"📝 Remembered preferences: {', '.join(f'{k}={v}' for k, v in memory.items())}")

    print("Describe your trip and I'll plan it for you!")
    print("Type 'quit' or 'exit' to stop.\n")

    team = build_team()

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit"):
            print("Goodbye! Happy travels! 🌍")
            break

        result = await Console(team.run_stream(task=user_input))

        # Extract and persist any preferences the planner flagged
        new_prefs = _extract_preferences(result.messages)
        if new_prefs:
            save_memory(new_prefs)
            print(f"\n📝 Saved preferences: {new_prefs}")

        # Reset the team for a fresh conversation
        await team.reset()


if __name__ == "__main__":
    asyncio.run(main())
