import inspect
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from dotenv import load_dotenv
from openrouter import OpenRouter

# This is just for coloring the terminal
from rich import print

load_dotenv()

# This just sets up the LLM API we're going to use
openrouter_api = OpenRouter(
    api_key=os.getenv("OPENROUTER_API_KEY", ""),
)

model = os.getenv("OPENROUTER_MODEL")


# Just a helper to make paths easier
def to_abs_path(path_str):
    """
    file.py -> /Users/you/project/file.py
    """
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def wrap_input(str):
    return f"[grey][bold]User:[/bold]{str}[/grey]"


def main():
    # We're going to hold our conversation here
    conversation = [{"role": "system", "content": ""}]
    print(f"[bold red]Model:[/bold red] [underline]{model}[/underline]")
    while True:
        try:
            user_input = input("> ")
        except (KeyboardInterrupt, EOFError):
            break
        conversation.append({"role": "user", "content": user_input.strip()})
        print(wrap_input(user_input.strip()))
        # TODO: Send request to LLM
        # TODO: Tool Calls


if __name__ == "__main__":
    main()
