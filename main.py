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


# TODO: Tell the assistant about the tools it has
SYSTEM_PROMPT = """
You are a coding assistant whose goal it is to help us solve coding tasks.
You have access to a series of tools you can execute. Here are the tools you can execute:

    {tool_list}

When you want to use a tool, reply with exactly one line in the format: 'tool: TOOL_NAME({{JSON_ARGS}})' and nothing else.
Use compact single-line JSON with double quotes. After receiving a tool_result(...) message, continue the task.
If no tool is needed, respond normally.

"""


# Just a helper to make paths easier
def to_abs_path(path_str):
    """
    file.py -> /Users/you/project/file.py
    """
    path = Path(path_str).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    return path


def list_files_tool(path: str) -> Dict[str, Any]:
    """
    Lists the files in a directory
    :param path: The path to a directory to list files from.
    :return: A list of files in the directory.
    """
    full_path = to_abs_path(path)
    all_files = []
    for item in full_path.iterdir():
        all_files.append(
            {"filename": item.name, "type": "file" if item.is_file() else "dir"}
        )
    return {"path": str(full_path), "files": all_files}


def read_file_tool(filename: str) -> Dict[str, Any]:
    """
    Gets the full content of a file
    :param filename: The name of the file to read.
    :return: The full content of the file.
    """
    full_path = to_abs_path(filename)
    print(full_path)
    with open(str(full_path), "r") as f:
        content = f.read()
    return {"file_path": str(full_path), "content": content}


TOOLS = {"list_files": list_files_tool, "read_file": read_file_tool}


def get_tool_str_representation(tool_name):
    tool = TOOLS[tool_name]
    return f"""
    Name: {tool_name}
    Description: {tool.__doc__}
    Signature: {inspect.signature(tool)}
    """


def get_system_prompt():
    tool_str_repr = ""
    for tool_name in TOOLS:
        tool_str_repr += "TOOL\n===" + get_tool_str_representation(tool_name)
        tool_str_repr += f"\n{'=' * 15}\n"
    return SYSTEM_PROMPT.format(tool_list=tool_str_repr)


def wrap_input(str):
    return f"[grey][bold]User:[/bold]{str}[/grey]"


def wrap_llm(str):
    return f"[blue][bold]LLM: [/bold]{str}[/blue]"


def extract_tool_calls(text):
    """
    Return list of (tool_name, args) requested in 'tool: name({...})' lines.
    The parser expects single-line, compact JSON in parentheses.
    """
    invocations = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("tool:"):
            continue
        try:
            after = line[len("tool:") :].strip()
            name, rest = after.split("(", 1)
            name = name.strip()
            if not rest.endswith(")"):
                continue
            json_str = rest[:-1].strip()
            args = json.loads(json_str)
            invocations.append((name, args))
        except Exception:
            continue
    return invocations


def main():
    # We're going to hold our conversation here
    conversation = [{"role": "system", "content": get_system_prompt()}]
    print(f"[bold red]Model:[/bold red] [underline]{model}[/underline]")
    while True:
        try:
            user_input = input("User: ")
        except (KeyboardInterrupt, EOFError):
            break
        conversation.append({"role": "user", "content": user_input.strip()})
        # Now, the problem is, if the llm wants to call multiple tools... what do we do?
        # Simple, we loop until the llm doesn't want to call more tools
        while True:
            response = openrouter_api.chat.send(messages=conversation, model=model)
            # Let's extract tool calls
            tool_calls = extract_tool_calls(response.choices[0].message.content)
            # In the case of tool calls, let's show we wanted to do them
            if tool_calls:
                for name, args in tool_calls:
                    print(
                        f"[purple]Tool Use Requested: {name} with args {args}[/purple]"
                    )
                    # Now we call the tool
                    resp = TOOLS[name](**args)
                    print(wrap_llm(f"tool_result({json.dumps(resp)})"))
                    conversation.append(
                        {
                            "role": "assistant",
                            "content": f"tool_result({json.dumps(resp)})",
                        }
                    )

            # Otherwise, let's print response
            else:
                print(wrap_llm(response.choices[0].message.content))
                conversation.append(
                    {
                        "role": "assistant",
                        "content": response.choices[0].message.content,
                    }
                )
                break


if __name__ == "__main__":
    main()
